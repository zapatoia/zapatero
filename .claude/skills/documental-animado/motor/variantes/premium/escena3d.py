"""Mini motor 2.5D/3D para el ESTILO PREMIUM: planos con textura en un mundo 3D, cámara con mirada (lookAt), profundidad de campo,
reflejo en el suelo, partículas en profundidad, barrido de luz sobre el cristal y posproceso (viñeta, aberración cromática, grano).

Coordenadas del mundo: x derecha, y arriba, z hacia el fondo (unidades ≈ px a 1 m de distancia focal). Todo dibujado con skia.
"""
import math
import numpy as np
import skia

from nucleo.texto import color
from nucleo.lienzo import relleno, trazo

W, H = 1080, 1920


def norm(v): v = np.asarray(v, float); return v / (np.linalg.norm(v) + 1e-9)


def rot_euler(rx, ry, rz):
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


class Camara:
    def __init__(self, ojo, mira, fov=42.0, roll=0.0, cx=520, cy=900):
        self.ojo = np.asarray(ojo, float); self.mira = np.asarray(mira, float); self.fov = fov; self.roll = roll
        self.cx, self.cy = cx, cy
        self.f = (H / 2) / math.tan(math.radians(fov) / 2)
        fw = norm(self.mira - self.ojo); r = norm(np.cross(np.array([0, 1.0, 0]), fw)); u = np.cross(fw, r)
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        self.r, self.u = r * cr + u * sr, -r * sr + u * cr; self.fw = fw

    def vista(self, P):
        d = np.atleast_2d(P) - self.ojo
        return np.c_[d @ self.r, d @ self.u, d @ self.fw]

    def pantalla(self, P):
        v = self.vista(P); z = np.maximum(v[:, 2], 1e-3)
        return np.c_[self.cx + self.f * v[:, 0] / z, self.cy - self.f * v[:, 1] / z], v[:, 2]


class Plano:
    """Imagen colocada en el mundo: centro c, tamaño (w, h), rotación (rx, ry, rz) en grados."""
    def __init__(self, img, c, w, h, rot=(0, 0, 0), alfa=1.0, brillo=True, reflejo=True, nombre=""):
        self.img, self.c, self.w, self.h, self.rot, self.alfa = img, np.asarray(c, float), w, h, rot, alfa
        self.brillo, self.reflejo, self.nombre = brillo, reflejo, nombre

    def esquinas(self, espejo_y=None):
        R = rot_euler(*self.rot); w, h = self.w / 2, self.h / 2
        P = np.array([(-w, h, 0), (w, h, 0), (w, -h, 0), (-w, -h, 0)]) @ R.T + self.c
        if espejo_y is not None: P[:, 1] = 2 * espejo_y - P[:, 1]
        return P


def dibujar_plano(c, cam, pl, foco, dof=.0016, espejo_y=None, alfa_extra=1.0, barrido=None):
    P = pl.esquinas(espejo_y); q, z = cam.pantalla(P)
    if (z < 40).any(): return None
    zc = float(z.mean()); bl = min(28.0, abs(zc - foco) * dof * 10)
    m = skia.Matrix(); iw, ih = pl.img.width(), pl.img.height()
    m.setPolyToPoly([skia.Point(0, 0), skia.Point(iw, 0), skia.Point(iw, ih), skia.Point(0, ih)], [skia.Point(float(a), float(b)) for a, b in q])
    p = skia.Paint(Alphaf=max(0.0, min(1.0, pl.alfa * alfa_extra)))
    if bl > .6: p.setImageFilter(skia.ImageFilters.Blur(bl, bl))
    c.save(); c.concat(m)
    c.drawImage(pl.img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
    c.restore()
    if barrido is not None and pl.brillo and espejo_y is None:                  # barrido de luz diagonal recortado al plano
        pth = skia.Path(); pth.addPoly([skia.Point(float(a), float(b)) for a, b in q], True)
        x0 = float(q[:, 0].min()); x1 = float(q[:, 0].max()); xb = x0 + (x1 - x0 + 600) * barrido - 300
        c.save(); c.clipPath(pth, doAntiAlias=True)
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeLinear([(xb - 160, 0), (xb + 160, 300)],
                                                                      [color("#FFFFFF", 0), color("#FFFFFF", .22 * pl.alfa), color("#FFFFFF", 0)], [0, .5, 1])))
        c.restore()
    return q, zc


def suelo(c, cam, y=-520, oro="#E8B04A", alfa=1.0):
    """Rejilla del suelo en perspectiva que se funde con la distancia."""
    for k in range(-14, 15):
        a = np.array([[k * 220, y, -2600.0], [k * 220, y, 4200.0]])
        _draw_linea3d(c, cam, a, oro, .10 * alfa)
    for k in range(-12, 32):
        a = np.array([[-3200, y, k * 220.0], [3200, y, k * 220.0]])
        _draw_linea3d(c, cam, a, oro, .10 * alfa)


def _draw_linea3d(c, cam, P, col, a):
    v = cam.vista(P)
    if (v[:, 2] < 60).all(): return
    if (v[:, 2] < 60).any():                                                    # recorta al plano cercano
        i, j = (0, 1) if v[0, 2] < 60 else (1, 0); u = (60 - v[i, 2]) / (v[j, 2] - v[i, 2]); P = P.copy(); P[i] = P[i] + (P[j] - P[i]) * u
    q, z = cam.pantalla(P); fade = max(0.0, 1 - float(z.mean()) / 6000)
    c.drawLine(float(q[0, 0]), float(q[0, 1]), float(q[1, 0]), float(q[1, 1]), trazo(col, 1.4, a * fade))


def particulas(c, cam, pts, foco, t, oro="#FFD98A"):
    v = cam.vista(pts + np.c_[np.zeros(len(pts)), 12 * np.sin(t * .7 + pts[:, 0] * .01), np.zeros(len(pts))])
    ok = v[:, 2] > 60
    for (x, y, z) in v[ok]:
        sx = cam.cx + cam.f * x / z; sy = cam.cy - cam.f * y / z
        if not (-50 < sx < W + 50 and -50 < sy < H + 50): continue
        r = max(1.0, 2400 / z); bl = min(12, abs(z - foco) * .004)
        c.drawCircle(sx, sy, r + bl * .5, skia.Paint(AntiAlias=True, Color=color(oro, max(.05, .55 - bl * .04)),
                                                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, bl + .3)))


class Post:
    """Viñeta + aberración cromática en los bordes + grano (numpy, sobre el cuadro final)."""
    def __init__(self, seed=1):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H * .47) / (H * .6)) ** 2)
        self.vig = np.clip(1.08 - .55 * d ** 2.2, .35, 1.0)[..., None]
        self.rng = np.random.default_rng(seed)

    def __call__(self, arr, t):
        x = arr[..., :3].astype(np.float32)
        r = np.roll(x[..., 0], 2, axis=1); b = np.roll(x[..., 2], -2, axis=1)
        m = np.clip((np.abs(np.arange(W) - W / 2) / (W / 2)) ** 2, 0, 1)[None, :]
        x[..., 0] = x[..., 0] * (1 - m) + r * m; x[..., 2] = x[..., 2] * (1 - m) + b * m
        x *= self.vig
        x += self.rng.normal(0, 3.2, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
        arr[..., :3] = np.clip(x, 0, 255).astype(np.uint8); return arr
