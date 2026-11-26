"""Recursos explicativos dentro del mundo 3D: carteles de madera con texto,
bocadillos pixel, iconos low-poly (corazón, gota de sal, interrogación, cruz de
aviso, cucurucho de patatas), números en vóxeles con rebote y chispas."""
import math
import numpy as np

from . import mesh as M
from . import textures as T
from . import font
from .mesh import Mesh, hexcol
from .mathutil import translate, euler, rot_z, scale, normalize
from .render import Item
from .anim import pop, EASE, seg, ease_out_back
from .style import PAL


def C(n, k=1.0):
    r, g, b, a = hexcol(PAL[n])
    return (min(r * k, 1), min(g * k, 1), min(b * k, 1), a)


# ------------------------------------------------------------------ mallas

def heart_mesh(size=0.5):
    pts = []
    for i in range(28):
        a = 2 * math.pi * i / 28
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((x / 34 * size, y / 34 * size))
    return M.extrude(pts, size * 0.3, C("heart"), side_col=C("heart_dark"))


def drop_mesh(size=0.5):
    """Gota de sudor/sal: lágrima extruida con bisel, punta arriba y brillo."""
    cy, r, tip = -0.15, 0.32, 0.55
    th = math.acos(r / (tip - cy))
    pts = [(0.0, tip)]
    N = 18
    for i in range(N + 1):
        a = th + (2 * math.pi - 2 * th) * i / N   # recorre el arco inferior
        pts.append((math.sin(a) * r, cy + math.cos(a) * r))
    pts = [(x * size * 1.5, z * size * 1.5) for x, z in pts[:-1]]
    return M.extrude(pts, size * 0.32, C("salt"), side_col=C("salt_dark"))


def salt_crystals(size=0.5, seed=1):
    rng = np.random.default_rng(seed)
    m = Mesh()
    for k in range(4):
        c = rng.uniform(-0.5, 0.5, 3) * size
        s = rng.uniform(0.08, 0.14) * size * 2
        m.extend(M.box(s, s, s, C("salt"), center=(0, 0, 0), jitter=0.05).transformed(
            translate(*c) @ euler(*rng.uniform(0, 1, 3))))
    return m


def voxel_text(text, cell=0.11, depth=0.16, col="gold", side="gold_dark"):
    rows = font.trim_rows(font.text_bitmap(text))
    return M.voxels(rows, cell, depth, C(col), C(side))


def bold_rows(rows):
    """Engrosa un glifo pixel: cada píxel ocupa también el de su derecha."""
    W = max(len(r) for r in rows) + 1
    out = []
    for r in rows:
        r = r.ljust(W, ".")
        out.append("".join("#" if (r[i] == "#" or (i > 0 and r[i - 1] == "#")) else "." for i in range(W)))
    return out


def medal_mesh(text, d=0.5):
    """Medallón: disco oscuro con aro dorado y cifra gruesa dorada en relieve."""
    m = Mesh()
    rx = euler(math.pi / 2, 0, 0)
    m.extend(M.cylinder(d / 2, d / 2, d * 0.12, 16, C("ui_ink"), rot=0.1, cap_col=C("ui_ink")).transformed(rx))
    rows = bold_rows(font.trim_rows(font.text_bitmap(text)))
    cell = d * 0.62 / len(rows)
    num = M.voxels(rows, cell, d * 0.12, C("gold"), C("gold_dark"))
    m.extend(num.transformed(translate(0, -d * 0.1, 0)))
    return m


def question_mesh(cell=0.1):
    rows = font.BIG["?"]
    return M.voxels(rows, cell, cell * 1.6, C("question"), C("question_dark"))


def exclaim_mesh(cell=0.1):
    return M.voxels(font.BIG["!"], cell, cell * 1.6, C("warn_red"), C("heart_dark"))


def warn_cross_mesh(size=0.6):
    """Cruz de aviso: placa circular blanca con borde rojo y cruz roja en relieve."""
    m = Mesh()
    m.extend(M.cylinder(0.5, 0.5, 0.1, 16, C("warn_red"), center=(0, 0, 0)).transformed(euler(math.pi / 2, 0, 0)))
    for (w, h) in ((0.52, 0.16), (0.16, 0.52)):
        m.extend(M.box(w, 0.14, h, C("warn_white"), center=(0, 0, 0), jitter=0))
    return m.transformed(scale(size))


def fries_mesh(size=0.5):
    m = Mesh()
    m.extend(M.box(0.5, 0.32, 0.45, C("warn_red"), center=(0, 0, 0.0), taper=(1.25, 1.2)))
    rng = np.random.default_rng(5)
    for k in range(5):
        x = -0.2 + k * 0.1
        h = rng.uniform(0.3, 0.42)
        m.extend(M.box(0.08, 0.08, h, C("flower_y"), center=(x, rng.uniform(-0.06, 0.06), 0.2 + h / 2 - 0.1)).transformed(
            euler(rng.uniform(-0.15, 0.15), rng.uniform(-0.25, 0.25), 0)))
    return m.transformed(scale(size * 1.4))


def fries_mesh_v2(size=0.5):
    """Cucurucho de patatas más legible: caja roja con banda clara y abanico de 9
    patatas doradas con la punta más tostada (sin logotipos)."""
    m = Mesh()
    red, red_d = C("warn_red"), C("heart_dark")
    gold, gold_d, tip = C("flower_y"), C("gold_dark"), C("gold")
    m.extend(M.box(0.52, 0.30, 0.46, red, center=(0, 0, 0.0), taper=(1.28, 1.2), jitter=0))
    m.extend(M.box(0.555, 0.315, 0.09, C("warn_white"), center=(0, 0, 0.08), taper=(1.04, 1.04), jitter=0))
    rng = np.random.default_rng(7)
    for k in range(9):
        u = (k - 4) / 4.0
        x = u * 0.25
        h = 0.36 + 0.10 * (1 - abs(u)) + rng.uniform(-0.03, 0.03)
        roll = u * 0.30 + rng.uniform(-0.05, 0.05)
        y = rng.uniform(-0.05, 0.05)
        f = Mesh()
        f.extend(M.box(0.075, 0.075, h, gold, center=(0, 0, h / 2), jitter=0))
        f.extend(M.box(0.078, 0.078, 0.05, tip, center=(0, 0, h - 0.02), jitter=0))
        m.extend(f.transformed(translate(x, y, 0.08) @ euler(0, roll, 0)))
    return m.transformed(scale(size * 1.4))


def ring_mesh(r0=0.42, r1=0.5, n=32):
    """Anillo plano (destello de aparición), en el plano XZ mirando a -Y."""
    m = Mesh()
    pts_o = [(math.cos(2 * math.pi * i / n) * r1, math.sin(2 * math.pi * i / n) * r1) for i in range(n)]
    pts_i = [(math.cos(2 * math.pi * i / n) * r0, math.sin(2 * math.pi * i / n) * r0) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        q = [pts_i[i], pts_o[i], pts_o[j], pts_i[j]]
        quad = Mesh()
        quad.extend(M.extrude(q, 0.002, (1, 1, 1, 1), jitter=0))
        m.extend(quad)
    return m


# halo/contorno por tipo de icono (estilo «glow»)
GLOW = {"heart": (1.0, 0.30, 0.42), "drop": (0.45, 0.75, 1.0), "salt": (0.75, 0.9, 1.0),
        "question": (1.0, 0.85, 0.25), "exclaim": (1.0, 0.35, 0.25), "warn": (1.0, 0.32, 0.28),
        "fries": (1.0, 0.72, 0.2), "tongue": (1.0, 0.45, 0.6), "num": (1.0, 0.78, 0.25), "text": (1.0, 0.95, 0.8)}


def tongue_icon(size=0.5):
    m = Mesh()
    m.extend(M.box(0.36, 0.14, 0.5, C("tongue"), center=(0, 0, 0), bevel=0.08, bottom_taper=(1.1, 1)))
    m.extend(M.box(0.04, 0.16, 0.34, C("tongue_dark"), center=(0, 0, 0.04), jitter=0))
    return m.transformed(scale(size * 1.3))


def sparkle_mesh():
    """Estrella de 4 puntas plana (se dibuja siempre de cara a cámara)."""
    pts = []
    for i in range(8):
        a = math.pi / 2 * (i / 2) + math.pi / 2
        r = 0.5 if i % 2 == 0 else 0.14
        a = i * math.pi / 4
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return M.extrude(pts, 0.02, (1, 0.95, 0.7, 1))


def sign_mesh(w=1.3, h=0.65, post=1.2):
    """Cartel: dos postes y tablón. Devuelve (madera, tablón_frontal)."""
    wood = Mesh()
    for sx in (-1, 1):
        wood.extend(M.box(0.1, 0.1, post + h, C("wood_b", 0.8), center=(sx * (w / 2 - 0.12), 0.05, (post + h) / 2), bevel=0.02,
                          taper=(0.8, 0.8)))
    wood.extend(M.box(w + 0.08, 0.1, h + 0.08, C("wood_b", 0.6), center=(0, 0.0, post + h / 2), bevel=0.02))
    face = M.decal(w, h, center=(0, -0.052, post + h / 2))
    return wood, face


# ------------------------------------------------------------------ objetos animados

class Prop:
    """Objeto animado: aparece con rebote, flota/rota y desaparece."""

    def __init__(self, r, meshes, t_in, t_out=None, pos=(0, 0, 0), follow=None, scale_=1.0, spin=0.0,
                 bob=0.05, billboard=False, face_cam=False, yaw=0.0, unlit=False, pop_in=0.35, pop_out=0.25,
                 rise=0.0, emissive=0.0, shadow=True, wobble=0.0, tilt=0.0):
        self._r = r
        self.parts = [(r.upload(m), tex, o) for (m, tex, o) in meshes]
        self._bounds = [m.bounds() for (m, tex, o) in meshes if m.tris and tex != "planks"]
        self.t_in, self.t_out = t_in, t_out
        self.pos = np.asarray(pos, "f8")
        self.follow = follow          # función t -> posición base
        self.scale_ = scale_
        self.spin, self.bob, self.billboard, self.face_cam = spin, bob, billboard, face_cam
        self.yaw, self.unlit, self.pop_in, self.pop_out = yaw, unlit, pop_in, pop_out
        self.rise, self.emissive, self.shadow, self.wobble, self.tilt = rise, emissive, shadow, wobble, tilt
        self.screen = None   # (nx, ny, profundidad): anclado al encuadre de cámara
        self.text_spec = None  # (renderer, nombre_textura, función(reveal) -> imagen, nº letras)
        self._reveal = None
        self.aspect = 9 / 16
        self.glow_col = None   # estilo «glow»: halo + contorno + destello (ver make_icon)
        self._ring = None

    def alive(self, t):
        return t >= self.t_in and (self.t_out is None or t <= self.t_out + self.pop_out)

    TEXT_RATE = 30.0       # letras por segundo
    TEXT_FADE_OUT = 0.15   # los textos salen con un fundido rápido

    def alpha_at(self, t):
        if self.text_spec is None or self.t_out is None or t <= self.t_out:
            return 1.0
        return max(0.0, 1.0 - seg(t, self.t_out, self.t_out + self.TEXT_FADE_OUT))

    def update_text(self, t):
        if self.text_spec is None:
            return
        r, name, fn, n = self.text_spec
        rv = max(0.0, min(float(n), (t - self.t_in - 0.12) * self.TEXT_RATE))
        rv = round(rv * 3) / 3          # 3 pasos de fundido por letra (~0,1 s)
        if rv != self._reveal:
            img = fn(rv if rv < n else None)
            from .textures import to_rgba_bytes
            r.textures[name].write(to_rgba_bytes(img))
            self._reveal = rv

    def scale_at(self, t):
        if t < self.t_in:
            return 0.0
        s = ease_out_back(seg(t, self.t_in, self.t_in + self.pop_in), 2.2)
        if self.text_spec is not None:
            return s
        if self.t_out is not None and t > self.t_out:
            s *= max(0.0, 1 - EASE["inback"](seg(t, self.t_out, self.t_out + self.pop_out)))
        return s

    def base(self, t, cam=None):
        if self.screen is not None and cam is not None:
            nx, ny, depth = self.screen
            f, r, u = cam.basis()
            hh = depth * math.tan(math.radians(cam.fov) / 2)
            return cam.eye + f * depth + r * nx * hh * self.aspect + u * ny * hh
        return self.follow(t) if self.follow else self.pos

    def items(self, t, cam):
        if not self.alive(t):
            return []
        s = self.scale_at(t) * self.scale_
        if s <= 1e-3:
            return []
        self.update_text(t)
        alpha = self.alpha_at(t)
        if alpha <= 0.0:
            return []
        lt = t - self.t_in
        p = self.base(t, cam) + np.array([0, 0, self.bob * math.sin(lt * 2.4) + self.rise * (1 - EASE["out"](seg(lt, 0, 0.5)))])
        if self.billboard or self.face_cam:
            d = cam.eye - p
            yaw = math.atan2(-d[0], d[1]) + math.pi if True else 0
            yaw = math.atan2(d[0], -d[1])
            R = rot_z(yaw)
            if self.billboard:
                pitch = math.atan2(d[2], math.hypot(d[0], d[1]))
                R = R @ euler(-pitch, 0, 0)
        else:
            R = rot_z(self.yaw)
        R = R @ rot_z(self.spin * lt + self.wobble * math.sin(lt * 3.0)) @ euler(self.tilt, 0, 0)
        Mx = translate(*p) @ R @ scale(s)
        self._last_M = Mx
        out = [Item(gm, Mx, tex=tex, unlit=o.get("unlit", self.unlit), emissive=o.get("emissive", self.emissive),
                    shadow=o.get("shadow", self.shadow), alpha_test=0.5, flip=o.get("flip", True),
                    rim=0.0 if o.get("unlit", self.unlit) else 0.35, alpha=alpha)
               for gm, tex, o in self.parts]
        if self.glow_col is not None:
            out = self._glow_items(out, t, lt, p, cam)
        return out

    def _glow_items(self, out, t, lt, p, cam):
        """Estilo «glow»: el icono se dibuja encima de la escena con contorno de pegatina y
        halo de su color que late suave; al aparecer y al salir, un anillo que se expande."""
        pulse = 0.82 + 0.18 * math.sin(lt * 5.0)
        k = 1.0 + 0.9 * max(0.0, 1.0 - lt / 0.35)          # destello al entrar
        g = tuple(min(1.0, c * pulse * k) for c in self.glow_col) + (1.0,)
        for it in out:
            it.overlay = True
            it.glow = g
            it.shadow = False
        d = cam.eye - p
        Rb = rot_z(math.atan2(d[0], -d[1])) @ euler(-math.atan2(d[2], math.hypot(d[0], d[1])), 0, 0)
        rad = self.scale_ * 0.9
        for t0 in [self.t_in + 0.05]:          # destello solo al entrar (al salir tapaba caras)
            u = (t - t0) / 0.42
            if 0.0 <= u <= 1.0:
                if self._ring is None:
                    self._ring = self._r.upload(ring_mesh())
                sc = rad * (0.45 + 0.85 * EASE["out"](u))
                it = Item(self._ring, translate(*p) @ Rb @ scale(sc), unlit=True, shadow=False,
                          tint=tuple(min(1.0, c * 1.15) for c in self.glow_col) + (1.0,), alpha=(1 - u) ** 1.5 * 0.9)
                it.overlay = True
                out.append(it)
        return out


class Sparkles:
    """Estallido de chispas que salen de un punto y caen (una vez)."""

    def __init__(self, r, t0, pos, n=10, color=(1, 0.9, 0.5, 1), spread=0.9, size=0.13, seed=0, dur=0.9):
        self.gm = r.upload(sparkle_mesh())
        rng = np.random.default_rng(seed)
        self.t0, self.dur = t0, dur
        self.pos = np.asarray(pos, "f8")
        self.size = size
        self.v = [np.array([rng.uniform(-1, 1), rng.uniform(-0.6, 0.6), rng.uniform(0.6, 1.4)]) * spread for _ in range(n)]
        self.sz = rng.uniform(0.6, 1.2, n)
        self.color = color

    def items(self, t, cam):
        lt = t - self.t0
        if lt < 0 or lt > self.dur:
            return []
        out = []
        d = cam.eye - self.pos
        yaw = math.atan2(d[0], -d[1])
        pitch = math.atan2(d[2], math.hypot(d[0], d[1]))
        u = lt / self.dur
        for v, s in zip(self.v, self.sz):
            p = self.pos + v * lt * 1.4 + np.array([0, 0, -1.2 * lt * lt])
            sc = self.size * s * math.sin(math.pi * min(1.0, u * 1.4 + 0.05)) * (1 - u * 0.5)
            if sc <= 0:
                continue
            Mx = translate(*p) @ rot_z(yaw) @ euler(-pitch, 0, 0) @ euler(0, lt * 6 * (1 if s > 0.9 else -1), 0) @ scale(sc)
            out.append(Item(self.gm, Mx, unlit=True, shadow=False, tint=self.color))
        return out


# ------------------------------------------------------------------ fábricas

def _letters(text):
    return sum(1 for ch in text if not ch.isspace())


def make_sign(r, name, text, t_in, pos, yaw=0.0, t_out=None, w=1.3, h=0.65, post=1.0):
    th = int(round(128 * h / w / 8)) * 8 or 64
    fn = lambda rv: T.sign_texture(text, 128, th, reveal=rv)
    r.add_texture(name, fn(0.0), repeat=False)
    wood, face = sign_mesh(w, h, post)
    pr = Prop(r, [(wood, "planks", {}), (face, name, {"shadow": False})], t_in, t_out, pos=pos, yaw=yaw,
              bob=0.0, rise=-0.0, pop_in=0.45, pop_out=0.15)
    pr.text_spec = (r, name, fn, _letters(text))
    return pr


def make_bubble(r, name, text, t_in, t_out, follow, w=1.0):
    fn = lambda rv: T.bubble_texture(text, reveal=rv)
    img = fn(0.0)
    r.add_texture(name, img, repeat=False)
    h = w * img.height / img.width
    m = M.decal(w, h, center=(w * 0.12, 0, h / 2))
    pr = Prop(r, [(m, name, {"unlit": True, "shadow": False, "flip": True})], t_in, t_out, follow=follow,
              billboard=True, bob=0.03, pop_in=0.3, pop_out=0.15)
    pr.text_spec = (r, name, fn, _letters(text))
    return pr


def make_icon(r, kind, t_in, t_out=None, pos=(0, 0, 0), follow=None, size=1.0, spin=0.0, wobble=0.25, style=None, **kw):
    if kind == "heart":
        m, tex = heart_mesh(0.55), "white"
    elif kind == "drop":
        m, tex = drop_mesh(0.55), "white"
    elif kind == "salt":
        m, tex = salt_crystals(0.4), "white"
    elif kind == "question":
        m, tex = question_mesh(0.07), "white"
    elif kind == "exclaim":
        m, tex = exclaim_mesh(0.07), "white"
    elif kind == "warn":
        m, tex = warn_cross_mesh(0.6), "white"
    elif kind == "fries":
        m, tex = (fries_mesh_v2(0.45) if style == "glow" else fries_mesh(0.45)), "white"
    elif kind == "tongue":
        m, tex = tongue_icon(0.45), "white"
    elif kind.startswith("num:"):
        m, tex = medal_mesh(kind[4:], 0.5), "white"
    elif kind.startswith("text:"):
        m, tex = voxel_text(kind[5:], cell=0.05, depth=0.08, col="ui_paper", side="ui_paper_dark"), "white"
    else:
        raise ValueError(kind)
    pr = Prop(r, [(m, tex, {"emissive": 0.18 if style != "glow" else 0.28})], t_in, t_out, pos=pos, follow=follow,
              scale_=size, spin=spin, face_cam=True, wobble=wobble, **kw)
    if style == "glow":
        pr.glow_col = GLOW.get(kind.split(":")[0], (1.0, 0.9, 0.6))
        pr.pop_in = 0.4
    return pr
