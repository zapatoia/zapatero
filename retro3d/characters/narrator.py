"""Narrador: aventurero achaparrado original, túnica verde azulada, bufanda teja,
hombrera de metal en un solo hombro, bandolera y botas con vuelta.

Ejes: mira hacia -Y. Brazo/pierna «R» (derecha del personaje) en -X.
"""
import math
import numpy as np

from .. import mesh as M
from .. import textures as T
from ..mesh import Mesh, hexcol
from ..mathutil import translate, euler, rot_z, rot_x, rot_y
from ..rig import Node
from ..anim import Spring, EASE, seg, noise1, ease_out_back, blink_times, blink_state
from ..style import PAL
from .base import Character, add


def C(n, k=1.0):
    r, g, b, a = hexcol(PAL[n])
    return (min(r * k, 1), min(g * k, 1), min(b * k, 1), a)


def _mir(v, side):
    """Convención «hacia fuera positivo»: para el lado L se invierten ry y rz."""
    rx, ry, rz = v
    return (rx, ry, rz) if side == "R" else (rx, -ry, -rz)


def arm(side, upper=(0, 0, 0), fore=(0, 0, 0), hand=(0, 0, 0)):
    return {f"arm_{side}": _mir(upper, side), f"fore_{side}": _mir(fore, side), f"hand_{side}": _mir(hand, side)}


def arms(upper=(0, 0, 0), fore=(0, 0, 0), hand=(0, 0, 0), upper_l=None, fore_l=None, hand_l=None):
    d = arm("R", upper, fore, hand)
    d.update(arm("L", upper_l or upper, fore_l or fore, hand_l or hand))
    return d


class Narrator(Character):
    def __init__(self):
        root = Node("root")
        hips = root.add(Node("hips", (0, 0, 0.58)))
        torso = hips.add(Node("torso", (0, 0, 0.06)))
        head = torso.add(Node("head", (0, 0, 0.52)))
        for side, sx in (("R", -1), ("L", 1)):
            a = torso.add(Node(f"arm_{side}", (sx * 0.275, 0, 0.42)))
            f = a.add(Node(f"fore_{side}", (0, 0, -0.22)))
            f.add(Node(f"hand_{side}", (0, 0, -0.2)))
            th = hips.add(Node(f"thigh_{side}", (sx * 0.11, 0, -0.04)))
            th.add(Node(f"shin_{side}", (0, 0, -0.23)))
        super().__init__(root)
        self._build()
        self.env_fn = lambda t: 0.0
        self.blinks = blink_times(120, seed=5)
        self.springs = {"scarf": Spring(40, 5, np.zeros(3))}
        self._prev_torso = None

    # ------------------------------------------------------------ modelo
    def _build(self):
        """Versión minimalista: bloques limpios, pocas piezas, color por vértice."""
        n = self.nodes
        sk = C("skin")
        J = 0.0  # sin variación de color por cara: superficies limpias
        # cabeza
        hd = n["head"]
        hd.attach(M.box(0.56, 0.5, 0.5, sk, center=(0, 0, 0.27), bevel=0.07, jitter=J), "white")
        for sx in (-1, 1):
            hd.attach(M.box(0.06, 0.1, 0.12, C("skin_shade"), center=(sx * 0.285, 0.02, 0.24), jitter=J), "white")
        hair = Mesh()
        hc = C("hair")
        hair.extend(M.box(0.62, 0.56, 0.16, hc, center=(0, 0.02, 0.5), bevel=0.05, taper=(0.88, 0.88), jitter=J))
        hair.extend(M.box(0.6, 0.18, 0.4, hc, center=(0, 0.2, 0.33), jitter=J))
        for sx in (-1, 1):
            hair.extend(M.box(0.08, 0.32, 0.18, hc, center=(sx * 0.29, 0.07, 0.42), jitter=J))
        # flequillo: tres mechones grandes
        for i, x in enumerate((-0.17, 0.0, 0.17)):
            ln = (0.15, 0.12, 0.15)[i]
            w = M.box(0.2, 0.07, ln, hc, center=(0, 0, -ln / 2), bottom_taper=(0.2, 0.6), jitter=J)
            hair.extend(w.transformed(translate(x, -0.25, 0.56) @ euler(0.18, 0, -x * 0.9)))
        hd.attach(hair, "white")
        # cara: decals intercambiables (ojos y boca), sin nariz ni rubor
        hd.decals.append((M.decal(0.42, 0.21, center=(0, -0.2515, 0.29)), "face_narr", "eyes"))
        hd.decals.append((M.decal(0.27, 0.18, center=(0, -0.2515, 0.11)), "face_narr", "mouth"))

        # torso
        to = n["torso"]
        tun = C("tunic")
        to.attach(M.box(0.46, 0.3, 0.46, tun, center=(0, 0, 0.25), bevel=0.04, taper=(1.1, 1.04), jitter=J), "white")
        to.attach(M.box(0.47, 0.32, 0.08, C("leather"), center=(0, 0, 0.035), jitter=J), "white")
        # bufanda (acento de color) con cola que se mueve
        to.attach(M.cylinder(0.2, 0.17, 0.11, 6, C("scarf"), center=(0, 0.0, 0.5), rot=0.2, jitter=J), "white")
        tail = Node("scarf_tail", (-0.15, -0.13, 0.49))
        to.add(tail)
        self.nodes["scarf_tail"] = tail
        tail.attach(M.box(0.1, 0.04, 0.17, C("scarf"), center=(0, 0, -0.075), jitter=J), "white")

        # brazos
        for side, sx in (("R", -1), ("L", 1)):
            n[f"arm_{side}"].attach(M.box(0.135, 0.135, 0.25, tun, center=(0, 0, -0.1), jitter=J), "white")
            n[f"fore_{side}"].attach(M.box(0.115, 0.115, 0.2, sk, center=(0, 0, -0.09), jitter=J), "white")
            hn = n[f"hand_{side}"]
            hn.attach(M.box(0.095, 0.13, 0.13, sk, center=(0, 0, -0.06), bevel=0.02, jitter=J), "white")
            # piernas y botas
            n[f"thigh_{side}"].attach(M.box(0.16, 0.17, 0.24, C("pants"), center=(0, 0, -0.11), jitter=J), "white")
            sh = n[f"shin_{side}"]
            sh.attach(M.box(0.145, 0.155, 0.16, C("pants"), center=(0, 0, -0.06), jitter=J), "white")
            sh.attach(M.box(0.18, 0.27, 0.16, C("boot"), center=(0, -0.04, -0.23), bevel=0.03, jitter=J), "white")
        # cadera y faldón
        hp = n["hips"]
        hp.attach(M.box(0.4, 0.28, 0.14, C("pants"), center=(0, 0, 0.0), jitter=J), "white")
        hp.attach(M.box(0.45, 0.31, 0.2, tun, center=(0, 0, -0.02), bottom_taper=(1.1, 1.14), jitter=J), "white")

    def setup_textures(self, r):
        img, uv = T.face_atlas()
        r.add_texture("face_narr", img, repeat=False)
        for k, v in uv.items():
            self.decal_uv[k.replace("eye_", "eyes_")] = v
        for name, fn in (("cloth", T.cloth), ("leather", T.leather), ("metal", T.metal), ("hair", T.hair)):
            if name not in r.textures:
                r.add_texture(name, fn())

    def upload(self, r):
        self.setup_textures(r)
        super().upload(r)

    # ------------------------------------------------------------ capas
    def secondary(self, t, dt, pose):
        # cola de la bufanda: cuelga y se balancea según el movimiento del torso
        tr = np.asarray(pose.get("torso", np.zeros(3)), "f8") + np.asarray(pose.get("hips", np.zeros(3)), "f8")
        hp = np.asarray(pose.get("hips.p", np.zeros(3)), "f8")
        target = np.array([-tr[0] * 0.8 - hp[2] * 3.0 + 0.1, -tr[1] * 0.6, -0.35])
        x = self.springs["scarf"].step(target, dt)
        pose = dict(pose)
        pose["scarf_tail"] = x
        return pose

    def base_layer(self, t):
        """Respiración, microbalanceo y parpadeo: nunca está quieto."""
        b = math.sin(t * 2 * math.pi * 0.32)
        d = {
            "torso": (-0.015 * b + 0.01 * noise1(t * 0.7, 1), 0.012 * noise1(t * 0.5, 4), 0.02 * noise1(t * 0.4, 2)),
            "torso.s": (1 + 0.008 * b, 1 + 0.008 * b, 1 + 0.014 * b),
            "head": (0.025 * noise1(t * 0.9, 3), 0.03 * noise1(t * 0.6, 7), 0.05 * noise1(t * 0.45, 5)),
            "hips.p": (0.008 * noise1(t * 0.5, 9), 0, 0.004 * b),
        }
        bs = blink_state(t, self.blinks)
        if bs:
            d["eyes"] = bs
        return d

    # ------------------------------------------------------------ énfasis
    BEAT_KINDS = ("nod", "chop", "lift_L", "tilt", "chop", "lift_R", "nod", "tilt")

    def set_beats(self, times, seed=7):
        """Gestos de énfasis en instantes dados (palabras acentuadas)."""
        rng = np.random.default_rng(seed)
        self.beats = [(t, self.BEAT_KINDS[i % len(self.BEAT_KINDS)], rng.uniform(0.8, 1.15))
                      for i, t in enumerate(sorted(times))]

    def beat_layer(self, t):
        d = {}
        for (tb, kind, amp) in getattr(self, "beats", []):
            lt = t - tb + 0.12           # el gesto empieza 0,12 s antes de la sílaba
            if lt < 0 or lt > 0.75:
                continue
            # anticipación breve → golpe rápido (easeOutBack) → caída suave
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
                acc("fore_R", (-0.4, 0, 0)); acc("fore_L", (-0.4, 0, 0)); acc("torso", (0.06, 0, 0))
                acc("head", (0.06, 0, 0))
            elif kind in ("lift_L", "lift_R"):
                side = kind[-1]
                acc(f"arm_{side}", (-0.45, 0, 0)); acc(f"fore_{side}", (-0.5, 0, 0))
                acc("head", (-0.05, (0.08 if side == "L" else -0.08), 0))
            elif kind == "tilt":
                acc("head", (-0.06, 0.16, 0.06)); acc("torso", (-0.03, 0, 0))
                if 0.05 < lt < 0.5:
                    d["eyes"] = "wide"
            acc("hips.p", (0, 0, -0.012))
        return d

    def pose_at(self, t):
        p = super().pose_at(t)
        p = add(p, self.beat_layer(t))
        base = self.base_layer(t)
        if p.get("eyes") in ("happy", "closed") and "eyes" in base:
            base.pop("eyes")
        return add(p, base)

    # ------------------------------------------------------------ acciones
    def act_idle(self, lt, t=0, **kw):
        s = math.sin(t * 1.3)
        return {**arms((0.05, 0.12, 0), (-0.25, 0, 0.1), (0, 0, 0)),
                "arm_R": (0.05 + 0.02 * s, 0.12, 0), "eyes": "open", "mouth": "X"}

    def act_talk(self, lt, t=0, energy=1.0, **kw):
        """Hablar a cámara: manos que acompañan el ritmo de la voz."""
        e = self.env_fn(t) * energy
        beat = math.sin(t * 2 * math.pi * 1.7)
        beat2 = math.sin(t * 2 * math.pi * 1.1 + 1.0)
        p = arms((-0.25 - 0.1 * e, 0.2, 0.0), (-1.1 - 0.25 * e * beat, 0.0, -0.3), (0.0, 0, 0.6),
                 upper_l=(-0.1 - 0.05 * e, 0.16, 0.0), fore_l=(-0.75 - 0.2 * e * beat2, 0.0, -0.15), hand_l=(0, 0, 0.3))
        p["torso"] = (0.04 + 0.03 * e * beat, 0, 0.06 * beat2 * e)
        p["head"] = (-0.04 + 0.08 * e * max(0.0, beat), 0.03 * beat2, 0)
        return p

    def act_explain(self, lt, t=0, **kw):
        """Ambas manos delante, palmas arriba, con un pequeño rebote."""
        e = self.env_fn(t)
        u = EASE["back"](seg(lt, 0, 0.35))
        bob = math.sin(t * 2 * math.pi * 1.5) * 0.12 * (0.4 + e)
        p = arms((-0.4 * u, 0.25 * u, 0), (-1.3 * u + bob, 0, -0.45 * u), (0.0, 0, 0.9 * u))
        p["torso"] = (0.05, 0, 0)
        p["head"] = (-0.05 + 0.05 * e, 0, 0)
        return p

    def act_point(self, lt, t=0, side="L", up=0.25, **kw):
        """Señalar hacia un lado con anticipación (recoge el brazo y lo lanza)."""
        a = seg(lt, 0, 0.14)
        b = EASE["back"](seg(lt, 0.12, 0.45))
        pull = math.sin(a * math.pi) * 0.4 * (1 - b)
        other = "R" if side == "L" else "L"
        p = {}
        p.update(arm(side, (-1.05 * b - up * b + pull, 0.95 * b - pull * 0.5, -0.2 * b), (-0.15 * b - 0.6 * (1 - b), 0, 0), (0, 0.3 * b, 0)))
        p.update(arm(other, (0.1, 0.12, 0), (-0.5, 0, 0.3), (0, 0, 0)))
        sgn = 1 if side == "L" else -1
        wig = math.sin(lt * 9) * 0.03 * math.exp(-lt * 2)
        p["torso"] = (0.02, 0.0, sgn * 0.22 * b + wig)
        p["head"] = (0.0, -sgn * 0.08 * b, sgn * 0.12 * b)
        p["hips"] = (0, 0, sgn * 0.05 * b)
        return p

    def act_shrug(self, lt, t=0, **kw):
        a = seg(lt, 0, 0.12)
        u = EASE["back"](seg(lt, 0.1, 0.45))
        dip = math.sin(a * math.pi) * 0.06 * (1 - u)
        hold = math.sin(lt * 5) * 0.02
        p = arms((-0.1 * u, 0.35 * u, 0.0), (-1.45 * u, 0.0, -1.0 * u), (0.0, 0.0, 1.2 * u))
        p["arm_R.p"] = (0, 0, 0.045 * u + hold)
        p["arm_L.p"] = (0, 0, 0.045 * u + hold)
        p["torso"] = (-0.04 * u + dip, 0, 0)
        p["head"] = (-0.06 * u, 0.2 * u, 0.0)
        p["hips.p"] = (0, 0, -dip * 0.3)
        p["eyes"] = "half" if lt > 0.15 else None
        return p

    def act_lean_in(self, lt, t=0, **kw):
        """Confidencia: se inclina hacia cámara con la mano junto a la boca."""
        u = EASE["back"](seg(lt, 0, 0.5))
        p = arms((0.05, 0.15, 0), (-0.4, 0, 0), (0, 0, 0))
        p.update(arm("L", (-0.95 * u, 0.25 * u, 0), (-2.0 * u, 0, 0.5 * u), (0, 0, -0.4 * u)))
        p["torso"] = (0.22 * u, 0, -0.08 * u)
        p["head"] = (-0.12 * u, -0.1 * u, -0.1 * u)
        p["hips.p"] = (0, -0.03 * u, -0.02 * u)
        p["eyes"] = "half"
        return p

    def act_laugh(self, lt, t=0, **kw):
        bounce = abs(math.sin(lt * 2 * math.pi * 2.6))
        p = arms((0.0, 0.2, 0), (-1.0, 0, -0.3), (0, 0, 0.3))
        p["torso"] = (-0.12 + 0.06 * bounce, 0, 0)
        p["head"] = (-0.22 + 0.08 * bounce, 0, 0)
        p["hips.p"] = (0, 0, 0.015 * bounce)
        p["eyes"] = "happy"
        p["mouth"] = "A"
        return p

    def act_offer_hand(self, lt, t=0, side="L", **kw):
        """Mano tendida hacia abajo/delante (para que el perro la lama)."""
        u = EASE["back"](seg(lt, 0, 0.4))
        p = arm(side, (-0.7 * u, 0.62 * u, 0), (-0.3 * u, 0, 0), (0.3 * u, 0, -1.4 * u))
        p.update(arm("R" if side == "L" else "L", (0.05, 0.12, 0), (-0.3, 0, 0), (0, 0, 0)))
        p["torso"] = (0.18 * u, 0, 0.12 * u * (1 if side == "L" else -1))
        p["head"] = (0.25 * u, 0, 0.1 * u * (1 if side == "L" else -1))
        p["hips.p"] = (0, 0, -0.04 * u)
        for s in ("R", "L"):
            p[f"thigh_{s}"] = (-0.25 * u, 0, 0)
            p[f"shin_{s}"] = (0.45 * u, 0, 0)
        return p

    def act_look_down(self, lt, t=0, turn=0.0, **kw):
        u = EASE["inout"](seg(lt, 0, 0.4))
        p = self.act_idle(lt, t)
        p["head"] = (0.32 * u, 0, turn * u)
        p["torso"] = (0.06 * u, 0, turn * 0.4 * u)
        return p

    def act_wave(self, lt, t=0, side="R", **kw):
        u = EASE["back"](seg(lt, 0, 0.35))
        w = math.sin(lt * 2 * math.pi * 2.2) * 0.35
        p = arm(side, (-0.3 * u, 1.9 * u, 0), (-0.2 * u, 0, 0), (0, 0, 0))
        p[f"fore_{side}"] = _mir((-0.2 * u, w * u - 0.3 * u, 0.0), side)
        p.update(arm("L" if side == "R" else "R", (0.05, 0.12, 0), (-0.3, 0, 0), (0, 0, 0)))
        p["head"] = (0, 0.08 * u, 0)
        return p

    def act_walk(self, lt, t=0, cycle=0.9, **kw):
        ph = 2 * math.pi * lt / cycle
        s, c = math.sin(ph), math.cos(ph)
        p = {}
        p["thigh_R"] = (-0.55 * s, 0, 0)
        p["thigh_L"] = (0.55 * s, 0, 0)
        p["shin_R"] = (0.5 * max(0, -c) + 0.15, 0, 0)
        p["shin_L"] = (0.5 * max(0, c) + 0.15, 0, 0)
        p.update(arm("R", (0.45 * s, 0.1, 0), (-0.45, 0, 0), (0, 0, 0)))
        p.update(arm("L", (-0.45 * s, 0.1, 0), (-0.45, 0, 0), (0, 0, 0)))
        p["hips.p"] = (0, 0, 0.035 * abs(math.cos(ph)) - 0.02)
        p["hips"] = (0, 0, 0.08 * s)
        p["torso"] = (0.06, 0, -0.12 * s)
        p["head"] = (-0.03, 0, 0.05 * s)
        return p

    def step_events(self, t0, t1, cycle=0.9):
        """Instantes de pasos (para efectos de sonido) en una acción de caminar."""
        out = []
        k = 0
        while True:
            tt = t0 + cycle * (0.25 + 0.5 * k)
            if tt > t1:
                break
            out.append(tt)
            k += 1
        return out
