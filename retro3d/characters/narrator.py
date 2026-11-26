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
        n = self.nodes
        sk, sks = C("skin"), C("skin_shade")
        # cabeza
        hd = n["head"]
        hd.attach(M.box(0.56, 0.5, 0.5, sk, center=(0, 0, 0.27), bevel=0.085, jitter=0.0), "white")
        hd.attach(M.box(0.075, 0.07, 0.08, sks, center=(0, -0.275, 0.2), bevel=0.02, taper=(0.8, 0.6), jitter=0), "white")
        for sx in (-1, 1):
            hd.attach(M.box(0.07, 0.11, 0.14, sks, center=(sx * 0.29, 0.02, 0.24), bevel=0.02, jitter=0), "white")
            # rubor
            hd.attach(M.box(0.06, 0.01, 0.028, (0.96, 0.62, 0.55, 1), center=(sx * 0.185, -0.251, 0.165), jitter=0), "white")
        hair = Mesh()
        hc, hl = C("hair"), C("hair_light")
        hf = lambda nn, rel: hl if nn[2] > 0.6 else hc
        hair.extend(M.box(0.62, 0.56, 0.17, hc, center=(0, 0.02, 0.5), bevel=0.06, taper=(0.86, 0.86), color_fn=hf))
        hair.extend(M.box(0.6, 0.2, 0.42, hc, center=(0, 0.2, 0.33), bevel=0.05, color_fn=hf))
        for sx in (-1, 1):
            hair.extend(M.box(0.09, 0.34, 0.2, hc, center=(sx * 0.29, 0.06, 0.41), bevel=0.03, bottom_taper=(1, 0.7), color_fn=hf))
        # flequillo en mechones (cuñas) — por encima de las cejas
        for i, x in enumerate((-0.2, -0.07, 0.07, 0.2)):
            ln = (0.17, 0.13, 0.15, 0.11)[i]
            w = M.box(0.15, 0.08, ln, hc, center=(0, 0, -ln / 2), bottom_taper=(0.25, 0.6), jitter=0.04, color_fn=hf)
            hair.extend(w.transformed(translate(x, -0.25, 0.56) @ euler(0.2, 0, (0.18 if x < 0 else -0.18) * (1 if i in (0, 3) else 0.5))))
        # remolino
        hair.extend(M.box(0.1, 0.07, 0.16, hc, center=(0, 0, 0.08), taper=(0.2, 0.4), color_fn=hf).transformed(
            translate(0.08, 0.05, 0.56) @ euler(-0.5, 0.35, 0)))
        hd.attach(hair, "hair")
        # cara: decals intercambiables (ojos y boca)
        hd.decals.append((M.decal(0.42, 0.21, center=(0, -0.2515, 0.3)), "face_narr", "eyes"))
        hd.decals.append((M.decal(0.27, 0.18, center=(0, -0.2515, 0.1)), "face_narr", "mouth"))

        # torso
        to = n["torso"]
        tun, tund, trim = C("tunic"), C("tunic_dark"), C("tunic_trim")
        to.attach(M.box(0.46, 0.3, 0.46, tun, center=(0, 0, 0.25), bevel=0.05, taper=(1.1, 1.04), jitter=0.02), "cloth")
        # cuello en V ribeteado
        for sx in (-1, 1):
            to.attach(M.box(0.04, 0.02, 0.16, trim, center=(0, 0, 0)).transformed(
                translate(sx * 0.045, -0.155, 0.4) @ euler(0, sx * 0.45, 0)), "white")
        to.attach(M.box(0.09, 0.02, 0.1, sks, center=(0, -0.152, 0.43)), "white")
        to.attach(M.box(0.47, 0.32, 0.09, C("leather"), center=(0, 0, 0.035), jitter=0.02), "leather")
        to.attach(M.box(0.1, 0.04, 0.08, C("buckle"), center=(0, -0.17, 0.035), bevel=0.012, jitter=0), "white")
        # bandolera y zurrón
        strap = M.box(0.06, 0.33, 0.66, C("leather_dark"), center=(0, 0, 0))
        to.attach(strap.transformed(translate(0.02, 0, 0.27) @ euler(0, 0.72, 0)), "leather")
        to.attach(M.box(0.12, 0.2, 0.16, C("leather"), center=(0.26, 0.02, 0.02), bevel=0.025), "leather")
        to.attach(M.box(0.13, 0.21, 0.06, C("leather_dark"), center=(0.262, 0.02, 0.09), bevel=0.01), "leather")
        # bufanda
        to.attach(M.cylinder(0.205, 0.17, 0.11, 8, C("scarf"), center=(0, 0.0, 0.5), rot=0.2), "cloth")
        to.attach(M.cylinder(0.08, 0.08, 0.06, 6, sk, center=(0, 0, 0.54)), "white")
        # hombrera de metal (solo izquierda)
        pad = M.box(0.25, 0.3, 0.13, C("metal"), center=(0, 0, 0), bevel=0.04, taper=(0.7, 0.75))
        pad.extend(M.box(0.27, 0.32, 0.03, C("leather"), center=(0, 0, -0.05)))
        to.attach(pad.transformed(translate(0.29, 0, 0.47) @ euler(0, -0.35, 0)), "metal")
        # cola de la bufanda (con muelle)
        tail = Node("scarf_tail", (-0.15, -0.13, 0.49))
        to.add(tail)
        self.nodes["scarf_tail"] = tail
        tail.attach(M.box(0.1, 0.04, 0.17, C("scarf"), center=(0, 0, -0.075), bottom_taper=(0.85, 1)), "cloth")
        tail.attach(M.box(0.11, 0.045, 0.035, C("scarf_dark"), center=(0, 0, -0.155)), "cloth")

        # brazos
        for side, sx in (("R", -1), ("L", 1)):
            n[f"arm_{side}"].attach(M.box(0.135, 0.135, 0.25, tun, center=(0, 0, -0.1), bottom_taper=(0.92, 0.92)), "cloth")
            fo = n[f"fore_{side}"]
            fo.attach(M.box(0.11, 0.11, 0.18, sk, center=(0, 0, -0.07), jitter=0), "white")
            fo.attach(M.box(0.135, 0.135, 0.12, C("leather"), center=(0, 0, -0.13), bevel=0.02), "leather")
            hn = n[f"hand_{side}"]
            hn.attach(M.box(0.09, 0.13, 0.13, sk, center=(0, 0, -0.06), bevel=0.025, jitter=0), "white")
            hn.attach(M.box(0.055, 0.05, 0.075, sk, center=(-sx * 0.035, -0.07, -0.035), bevel=0.012, jitter=0), "white")
            # piernas
            n[f"thigh_{side}"].attach(M.box(0.16, 0.17, 0.24, C("pants"), center=(0, 0, -0.11), bottom_taper=(0.92, 0.92)), "cloth")
            sh = n[f"shin_{side}"]
            sh.attach(M.box(0.145, 0.155, 0.16, C("pants"), center=(0, 0, -0.06)), "cloth")
            sh.attach(M.box(0.18, 0.27, 0.15, C("boot"), center=(0, -0.04, -0.235), bevel=0.04, taper=(0.95, 0.85)), "leather")
            sh.attach(M.box(0.2, 0.2, 0.07, C("leather"), center=(0, 0, -0.135), bevel=0.02), "leather")
            sh.attach(M.box(0.185, 0.28, 0.03, C("leather_dark", 0.8), center=(0, -0.04, -0.305)), "white")
        # cadera y faldón de la túnica
        hp = n["hips"]
        hp.attach(M.box(0.4, 0.28, 0.14, C("pants"), center=(0, 0, 0.0), bevel=0.03), "cloth")
        hp.attach(M.box(0.45, 0.31, 0.2, tun, center=(0, 0, -0.02), bottom_taper=(1.1, 1.14), jitter=0.02), "cloth")
        hp.attach(M.box(0.5, 0.36, 0.04, trim, center=(0, 0, -0.115)), "cloth")

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

    def pose_at(self, t):
        p = super().pose_at(t)
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
