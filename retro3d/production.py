"""Director: guion JSON + tiempos por palabra → escena animada fotograma a fotograma.

Anclas de tiempo ("at"/"until") dentro de cada segmento:
  3            → inicio de la palabra 3 del segmento (0 = primera; negativos desde el final)
  "sal"        → primera palabra del segmento que empieza por «sal»
  "start"/"end"→ inicio/fin del segmento
  [ancla, 0.2] → ancla + 0,2 s
"""
import math
import re
import numpy as np

from .render import Renderer, Camera
from .world import World, ground_h
from .characters.narrator import Narrator
from .characters.dog import Dog
from . import props as P
from .anim import EASE, seg, noise1
from .lipsync import LipSync


def _norm(s):
    s = s.lower()
    for a, b in zip("áéíóúü", "aeiouu"):
        s = s.replace(a, b)
    return re.sub(r"[^a-zñ0-9]", "", s)


class Production:
    def __init__(self, script, words, duration, W=1080, H=1920, env=None, fps=30, renderer=None):
        self.script = script
        self.words = words
        self.duration = duration
        self.fps = fps
        self.r = renderer or Renderer(W, H)
        self.W, self.H = W, H
        clear = [(c["pos"][0], c["pos"][1], 1.6) for c in script["cast"].values()]
        self.world = World(self.r, extra_clear=clear)
        self.cast = {}
        for name, c in script["cast"].items():
            if c["type"] == "narrator":
                ch = Narrator()
            else:
                ch = Dog(c.get("variant", "default"), c.get("size", 1.0), c.get("head_scale", 1.0))
            ch.upload(self.r)
            x, y = c["pos"]
            ch.place = (x, y, float(ground_h(x, y)), c.get("yaw", 0.0))
            ch.radius = 0.45 if c["type"] == "narrator" else 0.55 * c.get("size", 1.0)
            ch.kind = c["type"]
            self.cast[name] = ch
        # palabras de cada segmento
        self.seg_words = []
        k = 0
        for s in script["segments"]:
            n = len(s["text"].split())
            self.seg_words.append(list(range(k, k + n)))
            k += n
        assert k == len(words), f"palabras del guion ({k}) != palabras con tiempo ({len(words)})"
        self.lips = LipSync(words, env)
        self.env = env
        self.shots = []
        self.props = []
        self.sfx = []
        self.places = {n: [] for n in self.cast}
        self._build()
        n_frames = int(math.ceil(duration * fps))
        self.mouth = self.lips.state_frames(n_frames + 2, fps)
        narr = [c for c in self.cast.values() if c.kind == "narrator"]
        for c in narr:
            c.env_fn = self._env_at
            c.face_override = self._narr_face

    # ------------------------------------------------------------ tiempos
    def t_of(self, si, a):
        ws = self.seg_words[si]
        off = 0.0
        if isinstance(a, list):
            a, off = a
        if a == "start":
            t = self.words[ws[0]]["start"] - 0.08 if si > 0 else 0.0
        elif a == "end":
            t = self.words[ws[-1]]["end"]
        elif isinstance(a, int):
            t = self.words[ws[a]]["start"]
        else:
            key = _norm(a)
            hits = [i for i in ws if _norm(self.words[i]["text"]) == key] or \
                   [i for i in ws if _norm(self.words[i]["text"]).startswith(key)]
            if not hits:
                raise KeyError(f"ancla «{a}» no encontrada en el segmento {si}")
            t = self.words[hits[0]]["start"]
        return max(0.0, t + off)

    def seg_start(self, si):
        if si == 0:
            return 0.0
        prev_end = self.words[self.seg_words[si - 1][-1]]["end"]
        nxt = self.words[self.seg_words[si][0]]["start"]
        return prev_end + (nxt - prev_end) * 0.6

    def _env_at(self, t):
        if self.env is None:
            return 0.6 if any(w["start"] <= t <= w["end"] for w in self.words) else 0.0
        return self.lips.level(t)

    def _narr_face(self, t, face):
        k = int(round(t * self.fps))
        m = self.mouth[min(max(k, 0), len(self.mouth) - 1)]
        speaking = any(w["start"] - 0.05 <= t <= w["end"] + 0.05 for w in self.words)
        if speaking:
            if face.get("mouth") == "A" and m == "X":
                return None
            return {"mouth": m}
        return None

    # ------------------------------------------------------------ construcción
    def _build(self):
        S = self.script
        for si, s in enumerate(S["segments"]):
            t_seg = self.seg_start(si)
            for sh in s.get("shots", []):
                at = sh.get("at", "start")
                t0 = t_seg if at == "start" else self.t_of(si, at) - 0.07
                self.shots.append((max(0.0, t0), sh))
            for a in s.get("acts", []):
                t0 = self.seg_start(si) if a.get("at", "start") == "start" else self.t_of(si, a["at"])
                # por defecto la acción arranca 0,2 s antes de su palabra: pose asentada en el corte
                t0 += a.get("delay", -0.2 if a.get("at", "start") != "start" else 0.0)
                t0 = max(0.0, t0)
                ch = self.cast[a["who"]]
                params = {k: v for k, v in a.items() if k not in ("at", "who", "act", "delay", "place")}
                ch.play(t0, a["act"], **params)
                if "place" in a:
                    self.places[a["who"]].append((t0, a["place"]))
            for p in s.get("props", []):
                self._add_prop(si, p)
            for fx in s.get("sfx", []):
                self.sfx.append((self.t_of(si, fx["at"]), fx["name"], fx.get("gain", 0.0)))
        self.shots.sort(key=lambda x: x[0])
        # colocaciones (cambios de sitio instantáneos, normalmente en un corte)
        for name, keys in self.places.items():
            if keys:
                ch = self.cast[name]
                base = ch.place
                keys = sorted(keys)

                def fn(t, base=base, keys=keys):
                    cur = base
                    for (t0, pl) in keys:
                        if t >= t0:
                            x, y, yaw = pl
                            cur = (x, y, float(ground_h(x, y)), yaw)
                    return cur
                ch.place_fn = fn
        self._auto_sfx()

    def _anchor_fn(self, p):
        if "anchor" not in p:
            pos = np.asarray(p["pos"], "f8")
            if len(pos) == 2:
                pos = np.array([pos[0], pos[1], ground_h(*pos)])
            return None, pos
        ch = self.cast[p["anchor"]]
        off = np.asarray(p.get("off", (0, 0, 0)), "f8")
        node = p.get("node")

        def follow(t, ch=ch, off=off, node=node):
            if node:
                return ch.point(node) + off
            x, y, z, yaw = ch.place_fn(t) if ch.place_fn else ch.place
            return np.array([x, y, z]) + off
        return follow, None

    def _add_prop(self, si, p):
        t0 = self.t_of(si, p.get("at", "start")) if p.get("at", "start") != "start" else self.seg_start(si)
        t0 += p.get("delay", 0.0)
        t1 = None
        if "until" in p:
            u = p["until"]
            if isinstance(u, str) and u.startswith("seg+"):
                si2 = si + int(u[4:])
                t1 = self.seg_start(si2) - 0.25 if si2 < len(self.seg_words) else self.duration - 0.3
            elif u == "next":
                t1 = self.seg_start(si + 1) - 0.25 if si + 1 < len(self.seg_words) else self.duration - 0.3
            else:
                t1 = self.t_of(si, u) - 0.2
        follow, pos = self._anchor_fn(p) if "screen" not in p else (None, np.zeros(3))
        typ = p["type"]
        idx = len(self.props)
        if typ == "icon":
            pr = P.make_icon(self.r, p["kind"], t0, t1, pos=pos if pos is not None else (0, 0, 0), follow=follow,
                             size=p.get("size", 1.0), spin=p.get("spin", 0.0), wobble=p.get("wobble", 0.25))
            self.sfx.append((t0, "pop", 0.0))
            if p["kind"].startswith("num:"):
                self.sfx.append((t0 + 0.05, "ding", 0.0))
        elif typ == "bubble":
            pr = P.make_bubble(self.r, f"bubble{idx}", p["text"], t0, t1, follow or (lambda t, q=pos: q), w=p.get("w", 1.0))
            self.sfx.append((t0, "blip", 0.0))
        elif typ == "sign":
            pr = P.make_sign(self.r, f"sign{idx}", p["text"], t0, pos, yaw=p.get("yaw", 0.0), t_out=t1,
                             w=p.get("w", 1.3), h=p.get("h", 0.65), post=p.get("post", 1.0))
            self.sfx.append((t0 + 0.1, "thud", 0.0))
        elif typ == "sparkles":
            q = pos if pos is not None else None
            sp = P.Sparkles(self.r, t0, q if q is not None else np.zeros(3), n=p.get("n", 12), seed=idx,
                            color=tuple(p.get("color", (1, 0.9, 0.5, 1))))
            if follow:
                sp._follow = follow
            self.props.append(sp)
            self.sfx.append((t0, "ding", -4.0))
            return
        else:
            raise ValueError(typ)
        if p.get("sfx") is not None:
            self.sfx.append((t0, p["sfx"], 0.0))
        if "screen" in p:
            pr.screen = tuple(p["screen"])
            pr.aspect = self.W / self.H
        self.props.append(pr)

    def _auto_sfx(self):
        for name, ch in self.cast.items():
            tl = ch.timeline
            for i, (t0, act, prm) in enumerate(tl):
                t1 = tl[i + 1][0] if i + 1 < len(tl) else self.duration
                if act in ("lick", "lick_paw") and ch.kind == "dog":
                    rate = prm.get("rate", 3.0 if act == "lick" else 2.6)
                    for k, tt in enumerate(ch.lick_events(t0, t1, rate)):
                        self.sfx.append((tt, "lick", -3.0 if k % 2 else 0.0))
                if act == "walk":
                    cyc = prm.get("cycle", 0.9 if ch.kind == "narrator" else 0.55)
                    tt = t0 + cyc * 0.25
                    while tt < t1:
                        self.sfx.append((tt, "step", -4.0 if ch.kind == "dog" else 0.0))
                        tt += cyc / 2
                if act == "jump":
                    tt = t0 + 0.2
                    while tt < t1:
                        self.sfx.append((tt, "boing", 0.0))
                        tt += 1.1

    # ------------------------------------------------------------ cámara
    def subject_point(self, sub, h=None):
        if isinstance(sub, list):
            return np.asarray(sub, "f8")
        if sub == "two":
            pts = [self.subject_point("narr", 0.95), self.subject_point("dog", 0.95)]
            return (pts[0] + pts[1]) / 2 if h is None else (pts[0] + pts[1]) / 2 + np.array([0, 0, h - 0.95])
        if "+" in sub:
            names = sub.split("+")
            pts = [self.subject_point(n, h) for n in names]
            return sum(pts) / len(pts)
        ch = self.cast[sub]
        x, y, z, yaw = ch.place_fn(self._t) if ch.place_fn else ch.place
        if h is None:
            h = 1.2 if ch.kind == "narrator" else 0.55 * ch.size
        return np.array([x, y, z + h])

    def camera(self, t):
        self._t = t
        cur = None
        for i, (t0, sh) in enumerate(self.shots):
            if t0 <= t:
                cur = i
        if cur is None:
            cur = 0
        t0, sh = self.shots[cur]
        t1 = self.shots[cur + 1][0] if cur + 1 < len(self.shots) else self.duration
        u = EASE[sh.get("ease", "inout")](seg(t, t0, t1))
        rng = lambda k, d: (sh.get(k, d) if isinstance(sh.get(k, d), (list, tuple)) else [sh.get(k, d)] * 2)
        d0, d1 = rng("dist", 3.0)
        a0, a1 = rng("az", 0.0)
        e0, e1 = rng("el", 12.0)
        dist = d0 + (d1 - d0) * u
        az = math.radians(a0 + (a1 - a0) * u + 0.6 * noise1(t * 0.3, cur))
        el = math.radians(e0 + (e1 - e0) * u)
        fov = sh.get("fov", 38.0)
        P_ = self.subject_point(sh.get("sub", "narr"), sh.get("h"))
        dirv = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
        eye = P_ + dirv * dist
        # encuadre: el sujeto algo por encima del centro (los subtítulos van abajo)
        lift = sh.get("lift", 0.2)
        fwd = -dirv
        right = np.cross(fwd, (0, 0, 1))
        right /= np.linalg.norm(right)
        upv = np.cross(right, fwd)
        half_h = dist * math.tan(math.radians(fov) / 2)
        target = P_ - upv * lift * half_h + right * sh.get("side", 0.0) * half_h * self.W / self.H
        eye = eye - upv * lift * half_h + right * sh.get("side", 0.0) * half_h * self.W / self.H
        eye = self._avoid(eye, P_)
        self.r.shadow_center = P_.copy()
        self.r.shadow_center[2] = 0
        self.r.shadow_radius = max(6.0, dist * 1.6)
        return Camera(eye, target, fov), cur

    def _avoid(self, eye, focus):
        """Nunca dentro de un modelo: empuja la cámara fuera de obstáculos y del suelo."""
        obs = list(self.world.obstacles)
        for ch in self.cast.values():
            x, y, z, _ = ch.place_fn(self._t) if ch.place_fn else ch.place
            obs.append((x, y, ch.radius))
        for _ in range(3):
            for (x, y, r) in obs:
                d = np.array([eye[0] - x, eye[1] - y])
                n = np.linalg.norm(d)
                if n < r + 0.25:
                    d = d / (n + 1e-9) if n > 1e-6 else np.array([0, -1.0])
                    eye[0], eye[1] = x + d[0] * (r + 0.25), y + d[1] * (r + 0.25)
        gz = float(ground_h(eye[0], eye[1])) + 0.3
        if eye[2] < gz:
            eye[2] = gz
        return eye

    # ------------------------------------------------------------ fotograma
    def frame(self, t, cam=None):
        for ch in self.cast.values():
            ch.update(t, 1 / self.fps)
        if cam is None:
            cam, _ = self.camera(t)
        items = list(self.world.items)
        for ch in self.cast.values():
            items += ch.items()
        for p in self.props:
            if hasattr(p, "_follow"):
                p.pos = p._follow(t)
            items += p.items(t, cam)
        return self.r.render(cam, items), cam

    def shot_report(self):
        out = []
        for i, (t0, sh) in enumerate(self.shots):
            t1 = self.shots[i + 1][0] if i + 1 < len(self.shots) else self.duration
            out.append((i, t0, t1, sh))
        return out
