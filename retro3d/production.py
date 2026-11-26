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
from . import camera as CAM
from . import physics as PH


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
        self.zones = {"claro": np.zeros(3)}
        if "casa" in script.get("scenes", []):
            from . import interior
            self.world.add_interior()
            self.zones["casa"] = interior.ORIGIN
        self.cast = {}
        for name, c in script["cast"].items():
            if c["type"] == "narrator":
                ch = Narrator()
            else:
                ch = Dog(c.get("variant", "default"), c.get("size", 1.0), c.get("head_scale", 1.0))
            ch.upload(self.r)
            x, y = c["pos"]
            ch.place = (x, y, self.world.height(x, y), c.get("yaw", 0.0))
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
        self.zoom_times = []
        self.clearance = {}
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
            c.set_beats(self.emphasis_times())
            # parpadeo natural al final de cada frase + los aleatorios que no choquen
            ends = [w["end"] + 0.1 for w in self.words if re.search(r"[.:!?»]$", w["text"])]
            c.blinks = sorted(ends + [b for b in c.blinks if all(abs(b - e) > 0.8 for e in ends)])

    # ------------------------------------------------------------ zonas
    def _z(self, v):
        """[x, y, (z), …, "zona"] → coordenadas absolutas."""
        v = list(v)
        zone = "claro"
        if v and isinstance(v[-1], str):
            zone = v.pop()
        o = self.zones[zone]
        v[0] += o[0]
        v[1] += o[1]
        return v

    # ------------------------------------------------------------ énfasis
    def emphasis_times(self, frac=0.38, min_gap=0.6):
        """Palabras acentuadas: picos de energía de la voz en palabras de ≥4 letras
        (más las marcadas en "emph" de cada segmento)."""
        cand = []
        for i, w in enumerate(self.words):
            core = _norm(w["text"])
            if len(core) < 4:
                continue
            if self.env is not None:
                a, b = int(w["start"] / 0.01), max(int(w["end"] / 0.01), int(w["start"] / 0.01) + 1)
                pk = float(np.max(self.env[a:b])) if b <= len(self.env) and a < b else 0.0
            else:
                pk = len(core)
            cand.append((pk, w["start"]))
        if not cand:
            return []
        thr = np.quantile([c[0] for c in cand], 1 - frac)
        times = sorted(t for pk, t in cand if pk >= thr)
        for si, s in enumerate(self.script["segments"]):
            for e in s.get("emph", []):
                times.append(self.t_of(si, e))
        out = []
        for t in sorted(times):
            if not out or t - out[-1] >= min_gap:
                out.append(t)
        return out

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
                for z in sh.get("zoom", []):
                    self.zoom_times.append(self.t_of(si, z))
                if sh.get("transition") == "whip":
                    self.sfx.append({"t": max(0.0, t0 - 0.05), "type": "whoosh", "why": "barrido de transición"})
                if sh.get("type") == "establish" and sh.get("transition") != "whip":
                    self.sfx.append({"t": t0 + 0.1, "type": "whoosh", "gain": -2.0, "why": "empuje de situación"})
            for z in s.get("zooms", []):
                self.zoom_times.append(self.t_of(si, z))
            for a in s.get("acts", []):
                t0 = self.seg_start(si) if a.get("at", "start") == "start" else self.t_of(si, a["at"])
                # por defecto la acción arranca 0,2 s antes de su palabra: pose asentada en el corte
                t0 += a.get("delay", -0.2 if a.get("at", "start") != "start" else 0.0)
                t0 = max(0.0, t0)
                ch = self.cast[a["who"]]
                params = {k: v for k, v in a.items() if k not in ("at", "who", "act", "delay", "place")}
                ch.play(t0, a["act"], **params)
                if "place" in a:
                    # el cambio de sitio ocurre exactamente en el corte, no antes
                    tp = self.seg_start(si) if a.get("at", "start") == "start" else self.t_of(si, a["at"]) - 0.07
                    self.places[a["who"]].append((max(0.0, tp), self._z(a["place"])))
            for p in s.get("props", []):
                self._add_prop(si, p)
            for fx in s.get("sfx", []):
                self.sfx.append({"t": self.t_of(si, fx["at"]), "type": fx["name"], "gain": fx.get("gain", 0.0), "why": "guion"})
        self.shots.sort(key=lambda x: x[0])
        for t0, sh in self.shots:
            if "punch" in sh:
                self.sfx.append({"t": max(0.0, t0 - 0.04), "type": "whoosh", "why": "zoom de golpe"})
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
                            cur = (x, y, self.world.height(x, y), yaw)
                    return cur
                ch.place_fn = fn
        self._approach()
        self._auto_sfx()

    def _set_place_fn(self, name):
        ch = self.cast[name]
        base = ch.base_place if hasattr(ch, "base_place") else ch.place
        ch.base_place = base
        keys = sorted(self.places[name])

        def fn(t, base=base, keys=keys):
            cur = base
            for (t0, pl) in keys:
                if t >= t0:
                    x, y, yaw = pl
                    cur = (x, y, self.world.height(x, y), yaw)
            return cur
        ch.place_fn = fn if keys else None

    def _approach(self):
        """Lamer con «approach»: coloca al perro (en el corte) para que el hocico quede
        frente a la superficie objetivo, a unos centímetros. Nada se anima «a ojo»."""
        for name, ch in self.cast.items():
            if ch.kind != "dog":
                continue
            for (t0, act, prm) in list(ch.timeline):
                if act != "lick" or not prm.get("approach") or "target" not in prm:
                    continue
                tgt = prm["target"]
                other = self.cast[tgt["who"]]
                ta = t0 + 0.6
                other.update(ta)
                hb = [o for o in PH.rig_obbs(other, tgt["who"]) if o.node == tgt["node"]]
                hand_c = np.mean([o.c for o in hb], axis=0)
                yaw = prm.get("yaw", 0.0)
                # pose de lamer del perro en el origen con ese yaw
                saved = (ch.place, ch.place_fn)
                ch.place_fn = None
                ch.place = (0.0, 0.0, 0.0, yaw)
                ch._last_t = None
                ch.update(ta)
                Mj = ch.world_matrices()["head"]
                snout = (Mj @ np.array([0, -0.36, 0.03, 1.0]))[:3]
                ch.place, ch.place_fn = saved
                fwd = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
                standoff = prm.get("standoff", 0.07)
                pos = hand_c - snout - fwd * (standoff + 0.05)
                tp = t0 - 0.03
                self.places[name] = [k for k in self.places[name] if abs(k[0] - tp) > 0.05]
                self.places[name].append((tp, [float(pos[0]), float(pos[1]), yaw]))
                self._set_place_fn(name)
                ch._last_t = None
                other._last_t = None

    # ------------------------------------------------------------ físicas
    def solve_physics(self, t):
        """Regla fija: pies en el suelo, contactos reales y sin interpenetraciones."""
        info = {}
        # restricciones internas: brazos fuera del torso, cabeza del perro fuera del cuerpo
        for name, ch in self.cast.items():
            if ch.kind == "narrator":
                for side, sg in (("R", 1), ("L", -1)):
                    # el codo sale hacia fuera y hacia delante hasta que antebrazo y mano no invaden el cuerpo
                    o = 0.035 * sg
                    cand = [(0, o, 0), (-0.035, 0, 0), (0.035, 0, 0), (-0.03, o, 0), (0.03, o, 0), (0, 0, 0.035), (0, 0, -0.035)]
                    PH.resolve_self(ch, name, {f"fore_{side}", f"hand_{side}"}, {"torso", "hips", "head"},
                                    f"arm_{side}", cand)
                    PH.resolve_self(ch, name, {f"hand_{side}"}, {"torso", "head"}, f"fore_{side}",
                                    [(0.04, 0, 0), (-0.04, 0, 0), (0, 0, 0.04), (0, 0, -0.04)])
                    PH.resolve_self(ch, name, {f"arm_{side}"}, {"head"}, f"arm_{side}", [(0, o, 0), (0.03, 0, 0)])
            else:
                PH.resolve_self(ch, name, {"head", "jaw"}, {"leg_FR", "leg_FL"}, "neck", [(-0.05, 0, 0), (0, 0, 0.05), (0, 0, -0.05)])
        for name, ch in self.cast.items():
            x, y = ch.transform[0, 3], ch.transform[1, 3]
            gz = self.world.height(x, y)
            air = False
            if ch.kind == "dog":
                rp = np.asarray(getattr(ch, "cur_pose", {}).get("root.p", np.zeros(3)), "f8")
                air = rp[2] > 0.005
            PH.ground_snap(ch, ch.FEET, gz, airborne=air)
        # lametones: la lengua se detiene en la superficie del objetivo
        for name, ch in self.cast.items():
            if ch.kind != "dog":
                continue
            cur, prev = None, None
            for e in ch.timeline:
                if e[0] <= t:
                    prev, cur = cur, e
            # durante el fundido de salida de un lametón la lengua sigue fuera: mantener la restricción
            if cur and cur[1] not in ("lick", "lick_paw") and prev and prev[1] in ("lick", "lick_paw") \
                    and t - cur[0] < ch.FADE + 0.05:
                cur = prev
            if not cur or cur[1] not in ("lick", "lick_paw"):
                continue
            act, prm = cur[1], cur[2]
            if act == "lick" and "target" in prm:
                tg = prm["target"]
                if getattr(ch, "_was_contact", False):
                    # la mano cede ligeramente con el lametón (antes de resolver la lengua)
                    hn = self.cast[tg["who"]].nodes[tg["node"]]
                    hn.rot = hn.rot + np.array([0.1, 0, 0.04]) * getattr(ch, "lick_out", 0.0)
                boxes = [o for o in PH.rig_obbs(self.cast[tg["who"]], tg["who"]) if o.node == tg["node"]]
                res = PH.solve_lick(ch, boxes, getattr(ch, "lick_out", 0.0), margin=0.012)
                ch._was_contact = res["contact"]
                info[name] = res
            elif act == "lick_paw":
                side = prm.get("side", "R")
                boxes = [o for o in PH.rig_obbs(ch, name) if o.node in (f"paw_F{side}", f"leg_F{side}", "body")]
                info[name] = PH.solve_lick(ch, boxes, getattr(ch, "lick_out", 0.0), push_back=False, margin=0.012)
        return info

    def check_penetrations(self):
        rigs = {n: c for n, c in self.cast.items()}
        flt = PH.make_pair_filter(rigs)
        groups = [PH.rig_obbs(c, n) for n, c in rigs.items()]
        return PH.penetrations(groups, flt)

    def _anchor_fn(self, p):
        if "anchor" not in p:
            pos = np.asarray(self._z(p["pos"]), "f8")
            if len(pos) == 2:
                pos = np.array([pos[0], pos[1], self.world.height(*pos)])
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
            if p["kind"].startswith("num:"):
                self.sfx.append({"t": t0 + 0.03, "type": "ding", "why": f"número {p['kind'][4:]}"})
            else:
                self.sfx.append({"t": t0, "type": "pop", "why": f"icono {p['kind']}"})
        elif typ == "bubble":
            pr = P.make_bubble(self.r, f"bubble{idx}", p["text"], t0, t1, follow or (lambda t, q=pos: q), w=p.get("w", 1.0))
            self.sfx.append({"t": t0, "type": "blip", "why": "bocadillo"})
        elif typ == "sign":
            pr = P.make_sign(self.r, f"sign{idx}", p["text"], t0, pos, yaw=p.get("yaw", 0.0), t_out=t1,
                             w=p.get("w", 1.3), h=p.get("h", 0.65), post=p.get("post", 1.0))
            self.sfx.append({"t": t0 + 0.1, "type": "thud", "why": "cartel"})
        elif typ == "sparkles":
            q = pos if pos is not None else None
            sp = P.Sparkles(self.r, t0, q if q is not None else np.zeros(3), n=p.get("n", 12), seed=idx,
                            color=tuple(p.get("color", (1, 0.9, 0.5, 1))))
            if follow:
                sp._follow = follow
            self.props.append(sp)
            self.sfx.append({"t": t0, "type": "pop", "gain": -2.0, "why": "chispas"})
            return
        else:
            raise ValueError(typ)
        if p.get("sfx") is not None:
            self.sfx.append({"t": t0, "type": p["sfx"], "why": "guion"})
        if "screen" in p:
            pr.screen = tuple(p["screen"])
            pr.aspect = self.W / self.H
        self.props.append(pr)

    def _auto_sfx(self):
        """Efectos ligados a la animación: SIEMPRE eventos puntuales, nunca en bucle.
        - lamer: solo los 2 primeros contactos de cada acción (lick_sfx para cambiarlo)
        - saltar: un rebote al despegar; caminar: pasos ligeros (uno por pisada)."""
        for name, ch in self.cast.items():
            tl = ch.timeline
            for i, (t0, act, prm) in enumerate(tl):
                t1 = tl[i + 1][0] if i + 1 < len(tl) else self.duration
                if act in ("lick", "lick_paw") and ch.kind == "dog":
                    rate = prm.get("rate", 3.0 if act == "lick" else 2.6)
                    ev = ch.lick_events(t0, t1, rate)[:prm.get("lick_sfx", 2)]
                    for k, tt in enumerate(ev):
                        self.sfx.append({"t": tt, "type": "lick", "gain": -2.0 * k, "why": f"{name}: lametón {k + 1}"})
                if act == "walk":
                    cyc = prm.get("cycle", 0.9 if ch.kind == "narrator" else 0.55)
                    tt = t0 + cyc * 0.25
                    while tt < t1:
                        self.sfx.append({"t": tt, "type": "step", "why": f"{name}: pisada"})
                        tt += cyc / 2
                if act == "jump":
                    self.sfx.append({"t": t0 + 0.2, "type": "boing", "why": f"{name}: despegue"})

    # ------------------------------------------------------------ cámara
    def subject_point(self, sub, h=None):
        if isinstance(sub, list):
            return np.asarray(self._z(sub), "f8")
        if "." in sub:      # parte del cuerpo: "narr.hand_L"
            who, node = sub.split(".", 1)
            return self.cast[who].point(node)
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

    def current_shot(self, t):
        cur = 0
        for i, (t0, sh) in enumerate(self.shots):
            if t0 <= t:
                cur = i
        t0, sh = self.shots[cur]
        t1 = self.shots[cur + 1][0] if cur + 1 < len(self.shots) else self.duration
        return cur, t0, t1, sh

    def in_whip(self, t):
        cur, t0, t1, sh = self.current_shot(t)
        return sh.get("transition") == "whip" and t - t0 < CAM.WHIP_DUR

    def camera(self, t):
        self._t = t
        cur, t0, t1, sh = self.current_shot(t)
        u = seg(t, t0, t1)
        lt = t - t0
        kind = CAM.subject_kind(sh.get("sub", "narr"))
        size = sh.get("size", "medium")
        h = sh.get("h", CAM.HEIGHTS[kind][size] if not isinstance(sh.get("sub"), list) else None)
        P_ = self.subject_point(sh.get("sub", "narr"), h)
        az, el, dist, lat, fov = CAM.shot_params(sh, u, lt)
        fov *= CAM.zoom_factor(t, self.zoom_times)
        az = math.radians(az + 0.5 * noise1(t * 0.3, cur))
        el = math.radians(el)
        dirv = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
        eye = P_ + dirv * dist
        right = np.cross(-dirv, (0, 0, 1))
        right /= np.linalg.norm(right)
        eye = eye + right * lat
        target = P_ + right * lat * 0.4 + np.array([0, 0, sh.get("lift", 0.0)])
        eye, clear = self._avoid(eye, P_)
        if sh.get("transition") == "whip" and lt < CAM.WHIP_DUR:
            # barrido: la cámara llega girando rápido desde un lado
            th = math.radians(sh.get("whip_deg", 75.0)) * (1 - EASE["out"](lt / CAM.WHIP_DUR))
            v = target - eye
            c, s_ = math.cos(th), math.sin(th)
            target = eye + np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1], v[2]])
        self.clearance[cur] = min(self.clearance.get(cur, 9.9), clear)
        zone = self.world.zone(P_[0], P_[1])
        if zone == "casa":
            from .style import LIGHT_INTERIOR, FOG_INTERIOR
            self.r.light, self.r.fog = LIGHT_INTERIOR, FOG_INTERIOR
        else:
            from .style import LIGHT, FOG
            self.r.light, self.r.fog = LIGHT, FOG
        self.r.shadow_center = P_.copy()
        self.r.shadow_center[2] = 0
        self.r.shadow_radius = max(6.0, min(dist, 9.0) * 1.6)
        return Camera(eye, target, fov), cur

    MIN_CLEAR = 0.3

    def _avoid(self, eye, focus):
        """La cámara nunca entra en modelos ni bajo el suelo: empuja fuera de obstáculos,
        de los volúmenes de los personajes y de las paredes del interior.
        Devuelve (ojo, holgura mínima)."""
        eye = np.array(eye, "f8")
        obs = [(x, y, r, 99.0) for (x, y, r) in self.world.obstacles]
        for ch in self.cast.values():
            x, y, z, _ = ch.place_fn(self._t) if ch.place_fn else ch.place
            hgt = 1.8 if ch.kind == "narrator" else 1.0 * ch.size
            obs.append((x, y, ch.radius, z + hgt))
        clear = 9.9
        for _ in range(4):
            for (x, y, r, top) in obs:
                if eye[2] > top + self.MIN_CLEAR:
                    continue
                d = np.array([eye[0] - x, eye[1] - y])
                n = np.linalg.norm(d)
                need = r + self.MIN_CLEAR
                if n < need:
                    d = d / (n + 1e-9) if n > 1e-6 else np.array([0, -1.0])
                    eye[0], eye[1] = x + d[0] * need, y + d[1] * need
        for (x, y, r, top) in obs:
            if eye[2] <= top + self.MIN_CLEAR:
                clear = min(clear, math.hypot(eye[0] - x, eye[1] - y) - r)
        if self.world.zone(eye[0], eye[1]) == "casa" and "casa" in self.zones:
            from . import interior as I
            o = self.zones["casa"]
            eye[0] = min(max(eye[0], o[0] - I.HALF_W + 0.35), o[0] + I.HALF_W - 0.35)
            eye[1] = min(eye[1], o[1] + I.BACK - 0.35)
            eye[2] = min(eye[2], I.HEIGHT - 0.3)
        gz = self.world.height(eye[0], eye[1]) + 0.3
        if eye[2] < gz:
            eye[2] = gz
        clear = min(clear, eye[2] - (gz - 0.3))
        return eye, clear

    # ------------------------------------------------------------ fotograma
    def frame(self, t, cam=None):
        if cam is None and self.in_whip(t) and not getattr(self, "_sub", False):
            # desenfoque de movimiento: promedio de 6 sub-fotogramas dentro del obturador
            self._sub = True
            acc = None
            for k in range(6):
                img, c = self.frame(t + k / (6 * self.fps))
                acc = img.astype(np.float32) if acc is None else acc + img
            self._sub = False
            return (acc / 6).astype(np.uint8), c
        for ch in self.cast.values():
            ch.update(t, 1 / self.fps)
        self.contacts = self.solve_physics(t)
        if cam is None:
            cam, _ = self.camera(t)
        for k, it in enumerate(getattr(self.world, "fire_items", [])):
            f = 0.5 + 0.5 * noise1(t * 7.0, k)
            it.emissive = 1.0 + 0.35 * f
            it.model = np.diag([1.0, 1.0, 0.9 + 0.2 * f, 1.0])
            o = self.zones.get("casa", np.zeros(3))
            it.model[:3, 3] = (np.eye(3) - np.diag([1.0, 1.0, 0.9 + 0.2 * f])) @ (o + np.array([1.7, 2.4, 0.2]))
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
