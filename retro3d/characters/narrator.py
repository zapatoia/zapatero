"""NARRADOR FIJO: persona con pasamontañas magenta, sudadera oversize con la
capucha bajada, pantalón cargo ancho y zapatillas gruesas.

Se define UNA vez en config/narrator.json (medidas, colores, rig, caras, poses)
y se construye aquí. Ningún vídeo puede modificarlo: los guiones solo eligen
acciones/poses, expresiones (`expr`), ropa alternativa (`outfit`, si existe) y
planos. La huella del JSON se comprueba con config/narrator.lock.

Ejes: mira hacia -Y. Lado «R» (derecha del personaje) en -X.
"""
import hashlib
import json
import math
import os
import numpy as np

from .. import mesh as M
from .. import textures as T
from ..mesh import hexcol
from ..rig import Node
from ..anim import Spring, EASE, seg, noise1, blink_times, blink_state
from .base import Character, add

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG = os.path.join(ROOT, "config", "narrator.json")
LOCK = os.path.join(ROOT, "config", "narrator.lock")

LEGACY_EYES = {"open": ("neutral", "open"), "wide": ("surprised", "open"), "happy": ("happy", "open"),
               "half": (None, "half"), "closed": (None, "closed")}


def config_hash():
    with open(CONFIG, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_config(check_lock=True):
    if check_lock and os.path.exists(LOCK):
        with open(LOCK) as f:
            want = f.read().split()[0]
        if want != config_hash():
            raise RuntimeError("config/narrator.json ha cambiado y no coincide con narrator.lock. "
                               "El narrador es fijo: solo se modifica por petición explícita del usuario "
                               "(luego: python tools/lock_narrator.py).")
    with open(CONFIG) as f:
        return json.load(f)


def _mir(v, side):
    rx, ry, rz = v
    return (rx, ry, rz) if side == "R" else (rx, -ry, -rz)


class Narrator(Character):
    def __init__(self, outfit="default"):
        self.cfg = cfg = load_config()
        if outfit not in cfg["outfits"]:
            raise ValueError(f"ropa «{outfit}» no definida en config/narrator.json")
        self.outfit = cfg["outfits"][outfit]
        rg = cfg["rig"]
        root = Node("root")
        hips = root.add(Node("hips", (0, 0, rg["hips_z"])))
        torso = hips.add(Node("torso", (0, 0, rg["torso_z"])))
        torso.add(Node("head", (0, 0, rg["head_z"])))
        for side, sx in (("R", -1), ("L", 1)):
            a = torso.add(Node(f"arm_{side}", (sx * rg["shoulder_x"], 0, rg["shoulder_z"])))
            f = a.add(Node(f"fore_{side}", (0, 0, -rg["upper_arm"])))
            f.add(Node(f"hand_{side}", (0, 0, -rg["forearm"])))
            th = hips.add(Node(f"thigh_{side}", (sx * rg["hip_x"], 0, -0.04)))
            th.add(Node(f"shin_{side}", (0, 0, -rg["thigh"])))
        torso.add(Node("strings", (0, -0.185, 0.44)))
        super().__init__(root)
        self._build()
        self.env_fn = lambda t: 0.0
        lo, hi = cfg["face"]["blink_interval_s"]
        self.blinks = blink_times(240, seed=5, lo=lo, hi=hi)
        self.springs = {"strings": Spring(45, 5, np.zeros(3))}
        self.beats = []

    # ------------------------------------------------------------ modelo
    def C(self, key, k=1.0):
        pal = self.cfg["palette"]
        name = self.outfit.get(key, key)
        r, g, b, a = hexcol(pal[name])
        return (min(r * k, 1), min(g * k, 1), min(b * k, 1), a)

    def _build(self):
        n, d, C = self.nodes, self.cfg["dims"], self.C
        hd = n["head"]
        hx, hy, hz = d["head"]
        mask = C("balaclava")
        hd.attach(M.box(hx, hy, hz, mask, center=(0, 0, hz / 2 + 0.02), bevel=d["head_bevel"], taper=(0.9, 0.92)), "white")
        hd.attach(M.cylinder(0.12, 0.13, 0.12, 6, mask, center=(0, 0, -0.01), rot=0.26), "white")
        fc = self.cfg["face"]
        front = -hy / 2 - 0.0015
        hd.decals.append((M.decal(fc["eyes"]["w"], fc["eyes"]["h"], center=(0, front, fc["eyes"]["z"])), "face_narr", "eyes"))
        hd.decals.append((M.decal(fc["mouth"]["w"], fc["mouth"]["h"], center=(0, front, fc["mouth"]["z"])), "face_narr", "mouth"))
        # sudadera oversize con la capucha bajada
        to = n["torso"]
        tx, ty, tz = d["torso"]
        hood = C("hoodie")
        to.attach(M.box(tx, ty, tz, hood, center=(0, 0, tz / 2), bevel=0.06, taper=(0.94, 0.96)), "white")
        to.attach(M.cylinder(0.22, 0.19, 0.08, 6, C("hoodie_dark"), center=(0, 0.01, tz + 0.01), rot=0.26), "white")
        hx2, hy2, hz2 = d["hood"]
        to.attach(M.box(hx2, hy2, hz2, hood, center=(0, ty / 2 + hy2 / 2 - 0.06, tz - 0.02), bevel=0.05), "white")
        n["strings"].attach(M.box(0.022, 0.02, 0.15, C("string"), center=(-0.055, 0, -0.075)), "white")
        n["strings"].attach(M.box(0.022, 0.02, 0.13, C("string"), center=(0.055, 0, -0.065)), "white")
        hp = n["hips"]
        ex, ey, ez = d["hem"]
        hp.attach(M.box(ex, ey, ez, hood, center=(0, 0, 0.02), bevel=0.03), "white")
        hp.attach(M.box(ex + 0.01, ey + 0.01, 0.04, C("hoodie_dark"), center=(0, 0, -0.055)), "white")
        px, py, pz = d["pelvis"]
        hp.attach(M.box(px, py, pz, C("pants"), center=(0, 0, -0.04)), "white")
        for side, sx in (("R", -1), ("L", 1)):
            ux, uy, uz = d["upper_arm"]
            n[f"arm_{side}"].attach(M.box(ux, uy, uz, hood, center=(0, 0, -uz / 2 + 0.03), bevel=0.03), "white")
            fx, fy, fz = d["forearm"]
            n[f"fore_{side}"].attach(M.box(fx, fy, fz, hood, center=(0, 0, -fz / 2)), "white")
            cx, cy, cz = d["cuff"]
            n[f"fore_{side}"].attach(M.box(cx, cy, cz, C("hoodie_dark"), center=(0, 0, -fz + cz / 2)), "white")
            hx3, hy3, hz3 = d["hand"]
            n[f"hand_{side}"].attach(M.box(hx3, hy3, hz3, C("skin"), center=(0, 0, -hz3 / 2 + 0.01), bevel=0.02), "white")
            n[f"hand_{side}"].attach(M.box(0.05, 0.05, 0.07, C("skin"), center=(-sx * 0.035, -0.07, -0.03)), "white")
            thx, thy, thz = d["thigh"]
            th = n[f"thigh_{side}"]
            th.attach(M.box(thx, thy, thz, C("pants"), center=(0, 0, -thz / 2 + 0.02), bottom_taper=(0.96, 0.96)), "white")
            th.attach(M.box(0.035, 0.13, 0.11, C("pants_dark"), center=(sx * (thx / 2 + 0.012), 0, -0.13)), "white")
            sh = n[f"shin_{side}"]
            shx, shy, shz = d["shin"]
            sh.attach(M.box(shx, shy, shz, C("pants"), center=(0, 0, -shz / 2 + 0.03)), "white")
            sox, soy, soz = d["shoe"]
            sh.attach(M.box(sox, soy, soz, C("shoe"), center=(0, -0.05, -0.17), bevel=0.035), "white")
            slx, sly, slz = d["sole"]
            sh.attach(M.box(slx, sly, slz, C("sole"), center=(0, -0.05, -0.25)), "white")

    def upload(self, r):
        pal = self.cfg["palette"]
        img, uv = T.balaclava_atlas(pal["skin"], pal["ink"], pal["balaclava_dark"])
        r.add_texture("face_narr", img, repeat=False)
        for k, v in uv.items():
            self.decal_uv[k.replace("eye_", "eyes_")] = v
        super().upload(r)

    # ------------------------------------------------------------ poses de config
    def jpose(self, name, swap=False, u=1.0):
        """Pose del JSON escalada por u. swap=True intercambia R/L (p. ej. señalar con la otra mano)."""
        src = self.cfg["poses"][name]
        sides = {k: src[k] for k in ("R", "L") if k in src}
        if "L" not in sides and "R" in sides:
            sides["L"] = sides["R"]
        if "R" not in sides and "L" in sides:
            sides["R"] = sides["L"]
        if swap:
            sides = {"R": sides["L"], "L": sides["R"]}
        p = {}
        for side, v in sides.items():
            for part, key in (("upper", "arm"), ("fore", "fore"), ("hand", "hand")):
                p[f"{key}_{side}"] = np.asarray(_mir(v.get(part, (0, 0, 0)), side), "f8") * u
        for k, v in src.items():
            if k in ("R", "L", "expr") or k.startswith("_"):
                continue
            vv = np.asarray(v, "f8")
            if swap and k in ("torso", "head", "hips"):
                vv = vv * np.array([1, -1, -1])
            if swap and k.startswith(("thigh_", "shin_", "arm_")):
                k = k.replace("_R", "_X").replace("_L", "_R").replace("_X", "_L")
            p[k] = vv * u
        if "expr" in src:
            p["eyes"] = src["expr"]
        return p

    # ------------------------------------------------------------ capas
    def secondary(self, t, dt, pose):
        tr = np.asarray(pose.get("torso", np.zeros(3)), "f8")
        hp = np.asarray(pose.get("hips.p", np.zeros(3)), "f8")
        target = np.array([-tr[0] * 0.9 - hp[2] * 3.0, -tr[1] * 0.6, -tr[2] * 0.3])
        pose = dict(pose)
        pose["strings"] = self.springs["strings"].step(target, dt)
        return pose

    def base_layer(self, t):
        """Respiración, microbalanceo y cambio de peso de pie (ciclo de 9 s)."""
        b = math.sin(t * 2 * math.pi * 0.3)
        w = max(-1.0, min(1.0, 1.6 * math.sin(2 * math.pi * t / 9.0)))
        return {
            "torso": (-0.015 * b + 0.01 * noise1(t * 0.7, 1), 0.02 * w, 0.02 * noise1(t * 0.4, 2)),
            "torso.s": (1 + 0.008 * b, 1 + 0.008 * b, 1 + 0.014 * b),
            "head": (0.025 * noise1(t * 0.9, 3), 0.03 * noise1(t * 0.6, 7) - 0.015 * w, 0.05 * noise1(t * 0.45, 5)),
            "hips.p": (0.028 * w, 0, 0.004 * b - 0.006 * abs(w)),
            "hips": (0, -0.04 * w, 0.03 * w),
            "thigh_R": (-0.09 * max(0, w), 0.04 * w, 0), "shin_R": (0.18 * max(0, w), 0, 0),
            "thigh_L": (-0.09 * max(0, -w), 0.04 * w, 0), "shin_L": (0.18 * max(0, -w), 0, 0),
        }

    BEAT_KINDS = ("nod", "chop", "lift_L", "tilt", "chop", "lift_R", "nod", "tilt")

    def set_beats(self, times, seed=7):
        rng = np.random.default_rng(seed)
        self.beats = [(t, self.BEAT_KINDS[i % len(self.BEAT_KINDS)], rng.uniform(0.8, 1.15))
                      for i, t in enumerate(sorted(times))]

    def beat_layer(self, t):
        """Gestos de énfasis: anticipación breve → golpe (easeOutBack) → caída suave."""
        d = {}
        for (tb, kind, amp) in self.beats:
            lt = t - tb + 0.12
            if lt < 0 or lt > 0.75:
                continue
            if lt < 0.08:
                w = -0.25 * math.sin(lt / 0.08 * math.pi)
            elif lt < 0.24:
                w = EASE["back"]((lt - 0.08) / 0.16, 2.0)
            else:
                w = 1 - EASE["inout"]((lt - 0.24) / 0.51)
            w *= amp

            def acc(k, v):
                d[k] = np.asarray(d.get(k, np.zeros(3))) + np.asarray(v) * w
            if kind == "nod":
                acc("head", (0.16, 0, 0)); acc("torso", (0.05, 0, 0))
            elif kind == "chop":
                acc("fore_R", (-0.4, 0, 0)); acc("fore_L", (-0.4, 0, 0)); acc("torso", (0.06, 0, 0)); acc("head", (0.06, 0, 0))
            elif kind in ("lift_L", "lift_R"):
                side = kind[-1]
                acc(f"arm_{side}", (-0.45, 0, 0)); acc(f"fore_{side}", (-0.5, 0, 0))
                acc("head", (-0.05, (0.08 if side == "L" else -0.08), 0))
            elif kind == "tilt":
                acc("head", (-0.06, 0.16, 0.06)); acc("torso", (-0.03, 0, 0))
                if 0.05 < lt < 0.5:
                    d["eyes"] = "surprised"
            acc("hips.p", (0, 0, -0.012))
        return d

    def action_pose(self, name, lt, params, t):
        p = super().action_pose(name, lt, params, t)
        if params.get("expr"):
            p["eyes"] = params["expr"]
        return p

    def pose_at(self, t):
        p = super().pose_at(t)
        p = add(p, self.beat_layer(t))
        p = add(p, self.base_layer(t))
        ev = p.get("eyes") or "neutral"
        expr, lid = LEGACY_EYES.get(ev, (ev, "open"))
        expr = expr or "neutral"
        bs = blink_state(t, self.blinks)
        if bs and expr != "happy" and lid == "open":
            lid = bs
        p["eyes"] = f"{expr}_{lid}"
        return p

    # ------------------------------------------------------------ acciones
    def act_idle(self, lt, t=0, **kw):
        return self.jpose("idle")

    def act_talk(self, lt, t=0, energy=1.0, **kw):
        """Hablar a cámara: manos que acompañan el ritmo de la voz."""
        e = self.env_fn(t) * energy
        beat = math.sin(t * 2 * math.pi * 1.7)
        beat2 = math.sin(t * 2 * math.pi * 1.1 + 1.0)
        p = self.jpose("talk")
        p["fore_R"] = p["fore_R"] + np.array([-0.25 * e * beat, 0, 0])
        p["fore_L"] = p["fore_L"] + np.array([-0.2 * e * beat2, 0, 0])
        p["torso"] = p.get("torso", np.zeros(3)) + np.array([0.03 * e * beat, 0, 0.06 * beat2 * e])
        p["head"] = p.get("head", np.zeros(3)) + np.array([-0.04 + 0.08 * e * max(0.0, beat), 0.03 * beat2, 0])
        return p

    def act_explain(self, lt, t=0, **kw):
        e = self.env_fn(t)
        p = self.jpose("explain", u=EASE["back"](seg(lt, 0, 0.35)))
        bob = math.sin(t * 2 * math.pi * 1.5) * 0.12 * (0.4 + e)
        p["fore_R"] = p["fore_R"] + np.array([bob, 0, 0])
        p["fore_L"] = p["fore_L"] + np.array([bob, 0, 0])
        p["head"] = p.get("head", np.zeros(3)) + np.array([-0.05 + 0.05 * e, 0, 0])
        return p

    def act_point(self, lt, t=0, side="L", up=0.0, **kw):
        """Señalar con anticipación: recoge el brazo y lo lanza."""
        a = seg(lt, 0, 0.14)
        b = EASE["back"](seg(lt, 0.12, 0.45))
        pull = math.sin(a * math.pi) * 0.4 * (1 - b)
        p = self.jpose("point", swap=(side == "R"), u=b)
        p[f"arm_{side}"] = p[f"arm_{side}"] + np.array([pull - up * b, 0, 0])
        p["torso"] = p.get("torso", np.zeros(3)) + np.array([0, 0, math.sin(lt * 9) * 0.03 * math.exp(-lt * 2)])
        return p

    def act_shrug(self, lt, t=0, **kw):
        a = seg(lt, 0, 0.12)
        u = EASE["back"](seg(lt, 0.1, 0.45))
        dip = math.sin(a * math.pi) * 0.06 * (1 - u)
        p = self.jpose("shrug", u=u)
        hold = math.sin(lt * 5) * 0.02
        p["arm_R.p"] = p["arm_R.p"] + np.array([0, 0, hold])
        p["arm_L.p"] = p["arm_L.p"] + np.array([0, 0, hold])
        p["torso"] = p["torso"] + np.array([dip, 0, 0])
        p["hips.p"] = np.array([0, 0, -dip * 0.3])
        if lt < 0.15:
            p["eyes"] = "neutral"
        return p

    def act_cross_arms(self, lt, t=0, **kw):
        p = self.jpose("cross_arms", u=EASE["inout"](seg(lt, 0, 0.45)))
        p["torso"] = p["torso"] + np.array([0, 0, 0.03 * math.sin(t * 0.8)])
        return p

    def act_lean_in(self, lt, t=0, **kw):
        return self.jpose("lean_in", u=EASE["back"](seg(lt, 0, 0.5)))

    def act_laugh(self, lt, t=0, **kw):
        bounce = abs(math.sin(lt * 2 * math.pi * 2.6))
        p = self.jpose("laugh")
        p["torso"] = p["torso"] + np.array([0.06 * bounce, 0, 0])
        p["head"] = p["head"] + np.array([0.08 * bounce, 0, 0])
        p["hips.p"] = np.array([0, 0, 0.015 * bounce])
        p["mouth"] = "A"
        return p

    def act_offer_hand(self, lt, t=0, side="L", **kw):
        return self.jpose("offer_hand", swap=(side == "R"), u=EASE["back"](seg(lt, 0, 0.4)))

    def act_look_down(self, lt, t=0, turn=0.35, **kw):
        u = EASE["inout"](seg(lt, 0, 0.4))
        p = self.jpose("look_down", u=u)
        p["head"] = np.array([0.32 * u, 0, turn * u])
        p["torso"] = np.array([0.06 * u, 0, turn * 0.4 * u])
        return p

    def act_wave(self, lt, t=0, side="R", **kw):
        u = EASE["back"](seg(lt, 0, 0.35))
        p = self.jpose("wave", swap=(side == "L"), u=u)
        w = math.sin(lt * 2 * math.pi * 2.2) * 0.35
        p[f"fore_{side}"] = np.asarray(_mir((-0.15 * u, (1.25 + w) * u, 0.0), side))
        return p

    def act_walk(self, lt, t=0, cycle=0.9, **kw):
        ph = 2 * math.pi * lt / cycle
        s, c = math.sin(ph), math.cos(ph)
        p = {"thigh_R": (-0.55 * s, 0, 0), "thigh_L": (0.55 * s, 0, 0),
             "shin_R": (0.5 * max(0, -c) + 0.15, 0, 0), "shin_L": (0.5 * max(0, c) + 0.15, 0, 0)}
        for side, k in (("R", 1), ("L", -1)):
            p[f"arm_{side}"] = np.asarray(_mir((0.45 * s * k, 0.12, 0), side))
            p[f"fore_{side}"] = np.asarray(_mir((-0.45, 0, 0), side))
        p["hips.p"] = (0, 0, 0.035 * abs(c) - 0.02)
        p["hips"] = (0, 0, 0.08 * s)
        p["torso"] = (0.06, 0, -0.12 * s)
        p["head"] = (-0.03, 0, 0.05 * s)
        return p

    def step_events(self, t0, t1, cycle=0.9):
        out, k = [], 0
        while True:
            tt = t0 + cycle * (0.25 + 0.5 * k)
            if tt > t1:
                break
            out.append(tt)
            k += 1
        return out
