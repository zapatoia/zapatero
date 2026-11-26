"""Perro low-poly original: canela con pecho y hocico crema, orejas caídas
tostadas, collar rojo con chapa. Variantes de paleta/escala para cachorro y madre.

Mira hacia -Y. Pata «R» (derecha del perro) en -X.
"""
import math
import numpy as np

from .. import mesh as M
from .. import textures as T
from ..mesh import Mesh, hexcol
from ..mathutil import translate, euler
from ..rig import Node
from ..anim import Spring, EASE, seg, noise1, blink_times, blink_state
from ..style import PAL
from .base import Character, add

VARIANTS = {
    "default": {"fur": "fur", "dark": "fur_dark", "light": "fur_light", "ear": "ear", "collar": "collar"},
    "pup": {"fur": "pup_fur", "dark": "pup_dark", "light": "fur_light", "ear": "pup_dark", "collar": None},
    "mom": {"fur": "mom_fur", "dark": "mom_dark", "light": "mom_light", "ear": "mom_dark", "collar": "tunic"},
}


def C(n, k=1.0):
    r, g, b, a = hexcol(PAL[n])
    return (min(r * k, 1), min(g * k, 1), min(b * k, 1), a)


class Dog(Character):
    FADE = 0.22
    FEET = ("paw_FR", "paw_FL", "paw_BR", "paw_BL")
    COLLISION_GROUPS = [{"head", "jaw", "tongue", "neck", "ear_R", "ear_L"}, {"body", "tail1", "tail2", "tail3"},
                        {"body", "head", "neck"}]   # la cabeza apoya en el pecho por diseño

    def __init__(self, variant="default", size=1.0, head_scale=1.0):
        self.v = VARIANTS[variant]
        self.size = size
        root = Node("root")
        body = root.add(Node("body", (0, 0, 0.40)))
        neck = body.add(Node("neck", (0, -0.25, 0.1)))
        head = neck.add(Node("head", (0, -0.07, 0.13)))
        jaw = head.add(Node("jaw", (0, -0.17, -0.035)))
        jaw.add(Node("tongue", (0, -0.03, 0.02)))
        for side, sx in (("R", -1), ("L", 1)):
            head.add(Node(f"ear_{side}", (sx * 0.15, 0.0, 0.22)))
            f = body.add(Node(f"leg_F{side}", (sx * 0.1, -0.2, -0.1)))
            f.add(Node(f"paw_F{side}", (0, 0, -0.15)))
            b = body.add(Node(f"leg_B{side}", (sx * 0.1, 0.19, -0.08)))
            b.add(Node(f"paw_B{side}", (0, 0.02, -0.15)))
        t1 = body.add(Node("tail1", (0, 0.27, 0.1)))
        t2 = t1.add(Node("tail2", (0, 0, 0.13)))
        t2.add(Node("tail3", (0, 0, 0.12)))
        super().__init__(root)
        self.head_scale = head_scale
        self._build()
        self.blinks = blink_times(120, seed=11, lo=2.2, hi=3.8)
        self.springs = {"ears": Spring(55, 5.5, np.zeros(3)), "tail": Spring(70, 6, np.zeros(3))}
        self.root.scl = np.ones(3)
        self.tex_name = f"face_dog_{variant}"

    def _build(self):
        """Versión minimalista: cuerpo, cabeza, hocico, orejas, patas y cola; collar como acento."""
        n = self.nodes
        J = 0.0
        fur, light, ear = C(self.v["fur"]), C(self.v["light"]), C(self.v["ear"])
        b = n["body"]
        b.attach(M.box(0.3, 0.56, 0.28, fur, center=(0, 0.02, 0.0), bevel=0.06, jitter=J), "white")
        b.attach(M.box(0.31, 0.24, 0.32, fur, center=(0, -0.19, 0.0), bevel=0.06, jitter=J), "white")
        ne = n["neck"]
        ne.attach(M.box(0.2, 0.19, 0.2, fur, center=(0, -0.03, 0.06), jitter=J), "white")
        if self.v["collar"]:
            ne.attach(M.cylinder(0.125, 0.125, 0.055, 6, C(self.v["collar"]), center=(0, -0.02, 0.06), rot=0.25, jitter=J), "white")
        hd = n["head"]
        hd.attach(M.box(0.34, 0.3, 0.28, fur, center=(0, -0.01, 0.1), bevel=0.06, jitter=J), "white")
        hd.attach(M.box(0.21, 0.25, 0.14, light, center=(0, -0.215, 0.02), bevel=0.03, taper=(0.85, 0.92), jitter=J), "white")
        hd.attach(M.box(0.24, 0.1, 0.12, fur, center=(0, -0.12, 0.015), jitter=J), "white")
        hd.attach(M.box(0.085, 0.05, 0.06, C("nose"), center=(0, -0.35, 0.06), jitter=J), "white")
        hd.attach(M.box(0.15, 0.17, 0.02, C("tongue_dark", 0.6), center=(0, -0.255, -0.05), jitter=J), "white")
        hd.decals.append((M.decal(0.31, 0.155, center=(0, -0.1615, 0.165)), self_tex(self), "eyes"))
        ja = n["jaw"]
        ja.attach(M.box(0.16, 0.17, 0.05, light, center=(0, -0.075, -0.012), jitter=J), "white")
        ja.attach(M.box(0.14, 0.15, 0.012, C("tongue_dark", 0.7), center=(0, -0.075, 0.014), jitter=J), "white")
        n["tongue"].attach(M.box(0.095, 0.15, 0.022, C("tongue"), center=(0, -0.075, 0.0), jitter=J), "white")
        for side, sx in (("R", -1), ("L", 1)):
            n[f"ear_{side}"].attach(M.box(0.06, 0.14, 0.22, ear, center=(sx * 0.02, 0, -0.1), bottom_taper=(1.0, 0.75),
                                          jitter=J), "white")
            n[f"leg_F{side}"].attach(M.box(0.1, 0.115, 0.17, fur, center=(0, 0, -0.07), jitter=J), "white")
            pf = n[f"paw_F{side}"]
            pf.attach(M.box(0.09, 0.095, 0.11, fur, center=(0, 0, -0.05), jitter=J), "white")
            pf.attach(M.box(0.11, 0.15, 0.06, fur, center=(0, -0.025, -0.12), jitter=J), "white")
            n[f"leg_B{side}"].attach(M.box(0.12, 0.19, 0.2, fur, center=(0, 0.0, -0.05), bevel=0.03, jitter=J), "white")
            pb = n[f"paw_B{side}"]
            pb.attach(M.box(0.085, 0.095, 0.12, fur, center=(0, 0, -0.05), jitter=J), "white")
            pb.attach(M.box(0.11, 0.15, 0.06, fur, center=(0, -0.025, -0.12), jitter=J), "white")
        n["tail1"].attach(M.box(0.075, 0.075, 0.15, fur, center=(0, 0, 0.065), jitter=J), "white")
        n["tail2"].attach(M.box(0.065, 0.065, 0.14, fur, center=(0, 0, 0.06), jitter=J), "white")
        n["tail3"].attach(M.box(0.055, 0.055, 0.11, fur, center=(0, 0, 0.04), taper=(0.5, 0.5), jitter=J), "white")

    def upload(self, r):
        img, uv = T.face_atlas(dog=True)
        r.add_texture(self.tex_name, img, repeat=False)
        for k, v in uv.items():
            self.decal_uv[k.replace("eye_", "eyes_")] = v
        if "fur" not in r.textures:
            r.add_texture("fur", T.fur())
        super().upload(r)

    # -------------------------------------------------------------- capas
    def pose_at(self, t):
        p = super().pose_at(t)
        b = math.sin(t * 2 * math.pi * 0.55)
        base = {"body.s": (1 + 0.015 * b, 1, 1 + 0.02 * b),
                "head": (0.03 * noise1(t * 0.8, 2), 0.04 * noise1(t * 0.6, 5), 0.06 * noise1(t * 0.5, 8))}
        bs = blink_state(t, self.blinks)
        if bs and p.get("eyes", "open") in ("open", "wide", None):
            base["eyes"] = bs
        p = add(p, base)
        p["root.s"] = (self.size, self.size, self.size)
        if self.head_scale != 1.0:
            p["head.s"] = np.asarray(p.get("head.s", np.ones(3))) * self.head_scale
        return p

    def secondary(self, t, dt, pose):
        g = lambda k: np.asarray(pose.get(k, np.zeros(3)), "f8")
        hb = g("body") + g("neck") + g("head")
        bp = g("body.p") + g("root.p")
        cur = np.array([hb[0] + bp[2] * 6.0, hb[2], hb[1]])
        ex = self.springs["ears"].step(cur, dt)
        lag = np.clip(ex - cur, -0.8, 0.8)
        pose = dict(pose)
        flap = float(np.asarray(pose.pop("ear_flap", 0.0)).ravel()[0])
        for side, sx in (("R", -1), ("L", 1)):
            base = g(f"ear_{side}")
            pose[f"ear_{side}"] = base + np.array([0.12 + lag[0] * 1.4, sx * (0.22 + 0.5 * abs(lag[0])) + lag[2] * 0.8 - sx * flap,
                                                    lag[1] * 0.9])
        tb = g("body")
        tcur = np.array([tb[0] + bp[2] * 4, tb[2], 0])
        tx = self.springs["tail"].step(tcur, dt)
        tl = np.clip(tx - tcur, -0.8, 0.8)
        for i, k in enumerate(("tail1", "tail2", "tail3")):
            pose[k] = g(k) + np.array([tl[0] * (0.6 + 0.3 * i), 0, tl[1] * (0.7 + 0.4 * i)])
        return pose

    # -------------------------------------------------------------- acciones
    def _tail(self, t, speed=4.0, amp=0.25, up=-0.75):
        w = math.sin(t * speed)
        w2 = math.sin(t * speed - 0.9)
        return {"tail1": (up, 0, amp * w), "tail2": (0.25, 0, amp * 0.8 * w2), "tail3": (0.2, 0, amp * 0.6 * w2)}

    def act_idle(self, lt, t=0, **kw):
        p = self._tail(t, 3.2, 0.22)
        p["head"] = (0.05 * math.sin(t * 0.7), 0.0, 0.25 * noise1(t * 0.35, 3))
        p["eyes"] = "open"
        return p

    def act_wag(self, lt, t=0, pant=True, **kw):
        u = EASE["out"](seg(lt, 0, 0.25))
        p = self._tail(t, 15.0, 0.75 * u, up=-0.95)
        wig = math.sin(t * 15.0) * 0.07 * u
        p["body"] = (0, 0, wig)
        p["neck"] = (0, 0, -wig * 0.8)
        p["head"] = (-0.12 * u, 0.18 * u * math.sin(t * 1.3), 0)
        p["leg_BR"] = (0, -wig, 0)
        p["leg_BL"] = (0, -wig, 0)
        p["eyes"] = "happy"
        if pant:
            pn = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 3.2)
            p["jaw"] = ((0.22 + 0.1 * pn) * u, 0, 0)
            p["tongue"] = (0.15 * u, 0, 0)
            p["tongue.p"] = (0, -0.03 * u, -0.012)
            p["tongue.s"] = (1, 0.9 + 0.15 * pn, 1)
        return p

    def _sit(self, u):
        return {"body": (-0.55 * u, 0, 0), "body.p": (0, 0.04 * u, -0.1 * u),
                "neck": (0.32 * u, 0, 0), "head": (0.18 * u, 0, 0),
                "leg_FR": (0.55 * u, 0, 0), "leg_FL": (0.55 * u, 0, 0),
                "leg_BR": (-0.85 * u, 0.12 * u, 0), "leg_BL": (-0.85 * u, -0.12 * u, 0),
                "paw_BR": (1.55 * u, 0, 0), "paw_BL": (1.55 * u, 0, 0),
                "tail1": (-0.15 * u, 0, 0)}

    def act_sit(self, lt, t=0, wag=True, **kw):
        u = EASE["back"](seg(lt, 0, 0.45), 1.2) if lt < 0.45 else 1.0
        p = self._sit(u)
        tail = self._tail(t, 9.0 if wag else 2.5, 0.45 if wag else 0.15, up=0.6)
        for k, v in tail.items():
            p[k] = np.asarray(p.get(k, np.zeros(3))) + np.asarray(v) * np.array([u, 1, 1])
        p["head"] = (0.18 * u + 0.04 * math.sin(t * 1.1), 0.12 * math.sin(t * 0.6) * u, 0.1 * noise1(t * 0.4, 1))
        p["eyes"] = "open"
        return p

    def act_head_tilt(self, lt, t=0, **kw):
        """Sentado, cabeza ladeada: «¿eh?»."""
        p = self.act_sit(lt + 1.0, t, wag=False)
        u = EASE["back"](seg(lt, 0.1, 0.45), 2.0)
        p["head"] = (0.18, 0.42 * u, 0.1 * u)
        p["ear_flap"] = 0.35 * u
        p["eyes"] = "wide"
        return p

    def act_jump(self, lt, t=0, height=0.5, **kw):
        """Anticipación → salto en arco → aterrizaje con aplastamiento. Dura ~1 s y repite."""
        if lt > 1.1:   # un solo salto; después, contento en el sitio
            return self.act_wag(lt - 1.1, t=t, pant=True)
        T_ = lt
        p = self._tail(t, 15, 0.6, up=-0.9)
        if T_ < 0.2:
            u = EASE["inout"](T_ / 0.2)
            p["body.p"] = (0, 0, -0.08 * u)
            p["body"] = (0.12 * u, 0, 0)
            p["body.s"] = (1.05, 1, 1 - 0.08 * u)
            for s in "RL":
                p[f"leg_F{s}"] = (0.4 * u, 0, 0); p[f"paw_F{s}"] = (-0.6 * u, 0, 0)
                p[f"leg_B{s}"] = (-0.5 * u, 0, 0); p[f"paw_B{s}"] = (0.8 * u, 0, 0)
            p["eyes"] = "open"
        elif T_ < 0.68:
            u = (T_ - 0.2) / 0.48
            h = 4 * height * u * (1 - u)
            p["root.p"] = (0, 0, h)
            p["body"] = (-0.35 * (1 - u) + 0.25 * u, 0, 0)
            p["body.s"] = (0.95, 1.08, 1.0)
            for s in "RL":
                p[f"leg_F{s}"] = (-0.9 + 0.6 * u, 0, 0); p[f"paw_F{s}"] = (0.5, 0, 0)
                p[f"leg_B{s}"] = (0.7 - 0.4 * u, 0, 0); p[f"paw_B{s}"] = (0.2, 0, 0)
            p["jaw"] = (0.3, 0, 0)
            p["tongue.p"] = (0, -0.03, -0.01)
            p["eyes"] = "happy"
        else:
            u = (T_ - 0.68) / 0.42
            sq = math.sin(min(u * 2, 1) * math.pi) * (1 - u)
            p["body.p"] = (0, 0, -0.07 * sq)
            p["body.s"] = (1 + 0.08 * sq, 1, 1 - 0.1 * sq)
            p["eyes"] = "happy"
            p["jaw"] = (0.25 * (1 - u), 0, 0)
        return p

    def _lick_cycle(self, lt, rate=3.0):
        """Fase de lametón: lengua fuera-dentro con easeInOut, boca abre antes."""
        ph = (lt * rate) % 1.0
        out = math.sin(ph * math.pi) ** 2
        return ph, out

    def act_lick(self, lt, t=0, up=0.35, reach=0.0, rate=3.0, **kw):
        """Lamer algo por delante/arriba (una mano, una cara)."""
        u = EASE["back"](seg(lt, 0, 0.3))
        ph, out = self._lick_cycle(lt, rate)
        self.lick_out = out * u
        p = self._tail(t, 13, 0.55, up=-0.9)
        p["body"] = (0.05 * u, 0, 0)
        p["neck"] = (-up * 0.6 * u, 0, 0)
        p["neck.p"] = (0, -reach * u, 0.0)
        p["head"] = (-up * 0.5 * u + 0.18 * out, 0, 0.05 * math.sin(lt * 6))
        p["jaw"] = ((0.18 + 0.32 * out) * u, 0, 0)
        p["tongue"] = (-0.25 * out * u, 0, 0)
        p["tongue.p"] = (0, -0.1 * out * u, -0.01)
        p["tongue.s"] = (1, 0.6 + 0.9 * out * u, 1)
        p["eyes"] = "closed" if out > 0.4 else "happy"
        return p

    def act_lick_paw(self, lt, t=0, rate=2.6, side="R", **kw):
        """Sentado lamiéndose una pata delantera (lamido excesivo)."""
        u = EASE["inout"](seg(lt, 0, 0.4))
        sg = 1 if side == "R" else -1
        p = self._sit(1.0)
        ph, out = self._lick_cycle(lt, rate)
        self.lick_out = out * u
        p[f"leg_F{side}"] = (0.55 - 0.95 * u, sg * 0.2 * u, 0)
        p[f"paw_F{side}"] = (0.8 * u, 0, 0)
        p["neck"] = (0.32 + 0.4 * u, 0, -sg * 0.4 * u)
        p["head"] = (0.3 * u + 0.12 * out, sg * 0.2 * u, -sg * 0.35 * u)
        p["jaw"] = ((0.15 + 0.3 * out) * u, 0, 0)
        p["tongue.p"] = (0, -0.09 * out * u, -0.01)
        p["tongue.s"] = (1, 0.6 + 0.8 * out * u, 1)
        p["tongue"] = (-0.3 * out * u, 0, 0)
        p["eyes"] = "half"
        tail = self._tail(t, 2.0, 0.1, up=0.6)
        for k, v in tail.items():
            p[k] = np.asarray(p.get(k, np.zeros(3))) + np.asarray(v)
        return p

    def act_walk(self, lt, t=0, cycle=0.55, **kw):
        ph = 2 * math.pi * lt / cycle
        s, c = math.sin(ph), math.cos(ph)
        p = self._tail(t, 9, 0.4, up=-0.85)
        a = 0.5
        p["leg_FR"] = (a * s, 0, 0); p["paw_FR"] = (-0.5 * max(0, c), 0, 0)
        p["leg_BL"] = (a * s, 0, 0); p["paw_BL"] = (0.5 * max(0, c), 0, 0)
        p["leg_FL"] = (-a * s, 0, 0); p["paw_FL"] = (-0.5 * max(0, -c), 0, 0)
        p["leg_BR"] = (-a * s, 0, 0); p["paw_BR"] = (0.5 * max(0, -c), 0, 0)
        p["body.p"] = (0, 0, 0.02 * abs(c))
        p["body"] = (0.03 * math.sin(2 * ph), 0, 0.05 * s)
        p["head"] = (-0.04 * math.sin(2 * ph), 0, -0.05 * s)
        p["eyes"] = "open"
        return p

    def act_nuzzle(self, lt, t=0, **kw):
        """De pie, baja la cabeza hacia delante (madre atendiendo al cachorro)."""
        u = EASE["inout"](seg(lt, 0, 0.5))
        p = self._tail(t, 3.0, 0.2)
        p["neck"] = (0.55 * u, 0, 0.05 * math.sin(t * 0.8))
        p["head"] = (0.25 * u + 0.04 * math.sin(t * 1.7), 0.08 * math.sin(t * 0.9), 0)
        p["eyes"] = "half" if (t % 3.0) < 2.2 else "closed"
        p["body"] = (0.06 * u, 0, 0)
        return p

    def act_calm(self, lt, t=0, **kw):
        """Tumbado-sentado relajado, ojos entornados, cola lenta (endorfinas)."""
        p = self.act_sit(lt + 1.0, t, wag=False)
        p["head"] = (0.28 + 0.03 * math.sin(t * 1.2), 0.15 * math.sin(t * 0.5), 0)
        p["eyes"] = "closed" if (t % 2.6) < 1.9 else "half"
        p["jaw"] = (0.06, 0, 0)
        return p

    def lick_events(self, t0, t1, rate=3.0, phase0=0.3):
        """Instantes de máxima extensión de la lengua (para el sonido)."""
        out = []
        k = 0
        while True:
            tt = t0 + phase0 + (k + 0.5) / rate
            if tt > t1:
                break
            out.append(tt)
            k += 1
        return out


def self_tex(dog):
    return f"face_dog_{dog_variant_name(dog)}"


def dog_variant_name(dog):
    for k, v in VARIANTS.items():
        if v is dog.v:
            return k
    return "default"
