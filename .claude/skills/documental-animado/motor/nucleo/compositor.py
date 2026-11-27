"""Compositor: post en numpy/OpenCV (glow aditivo, bloom, viñeta, reflejo, textura, grano, buffer float) y cámara 2D.

Skia dibuja en 8 bits; cuando hace falta acumular luz (hebras de sonificación, neón) usa BufferFloat. Los fondos oscuros siempre
llevan tramado (`tramar`) para que el degradado no se vea en bandas después del H.264.
"""
import cv2
import numpy as np
import skia

from .tiempo import W, H, FPS, CURVAS, clamp, cubic_out, lerp


def hex_rgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def tramar(arrf, semilla=3, amp=0.9):
    """float 0–255 → uint8 con ruido triangular fijo (evita bandas)."""
    r = np.random.default_rng(semilla)
    n = (r.random(arrf.shape[:2], np.float32) - r.random(arrf.shape[:2], np.float32))[..., None] * amp
    return np.clip(arrf + n + .5, 0, 255).astype(np.uint8)


def fondo_degradado(arriba, abajo, w=W, h=H, semilla=3):
    u = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return tramar(np.broadcast_to(hex_rgb(arriba) * (1 - u) + hex_rgb(abajo) * u, (h, w, 3)).copy(), semilla)


def mascara_vineta(w=W, h=H, interior=.45, exterior=1.15, fuerza=1.0, cx=.5, cy=.5):
    """1 en el centro, (1−fuerza) en las esquinas. Multiplica un fondo por esto."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xs - w * cx) / (w * .5)) ** 2 * .6 + ((ys - h * cy) / (h * .5)) ** 2 * .4)
    u = np.clip((d - interior) / (exterior - interior), 0, 1); u = u * u * (3 - 2 * u)
    return (1 - fuerza * u)[..., None]


def capsula_brillo(col, cx=540, cy=960, rx=270, ry=720, sigma=120, w=W, h=H):
    """Cápsula vertical difusa: arreglo float 0–1 × color (tarjetas). Mapa alfa de una cápsula desenfocada, escala baja para ir rápido."""
    s = 4; m = np.zeros((h // s, w // s), np.float32)
    cv2.ellipse(m, (cx // s, cy // s), (rx // s, ry // s), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), sigma / s); m = cv2.resize(m, (w, h), interpolation=cv2.INTER_CUBIC)
    return np.clip(m, 0, 1)[..., None]


def glow_aditivo(arr, capa_rgb, sigmas=(8, 30), pesos=(.7, .35), nucleo=True):
    """Suma a arr (H,W,3|4 uint8) el resplandor de capa_rgb (H,W,3 uint8/float). Las 3 pasadas de camara-viaja: núcleo + 8 px + 30 px."""
    out = arr[..., :3].astype(np.float32); cf = capa_rgb.astype(np.float32)
    if nucleo: out += cf
    for s, p in zip(sigmas, pesos): out += cv2.GaussianBlur(cf, (0, 0), s) * p
    arr[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    return arr


def bloom(arr, umbral=.75, sigmas=(6, 24, 80), pesos=(.6, .3, .15), escala=1.0):
    """Bloom solo en altas luces (sonificación). 1/4 de resolución para los sigmas grandes."""
    x = arr[..., :3].astype(np.float32) / 255; m = np.clip(x - umbral, 0, None) / (1 - umbral + 1e-6) * x
    pk = cv2.resize(m, (m.shape[1] // 4, m.shape[0] // 4), interpolation=cv2.INTER_AREA); s = np.zeros_like(pk)
    for sg, p in zip(sigmas, pesos): s += cv2.GaussianBlur(pk, (0, 0), sg / 4) * p
    s = cv2.resize(s, (m.shape[1], m.shape[0]), interpolation=cv2.INTER_LINEAR)
    arr[..., :3] = np.clip((x + s * escala) * 255, 0, 255).astype(np.uint8)
    return arr


def reflejo(arr, y_suelo, alfa=.25, alcance=390, blur=1.5, puntos=((0, 1.0), (180, .2), (390, 0))):
    """Espejo bajo el suelo que se desvanece (palitos: α .25 → .05 a +180 → 0 a +390)."""
    h = arr.shape[0]; n = min(alcance, h - y_suelo, y_suelo)
    if n <= 0: return arr
    esp = arr[y_suelo - n:y_suelo, :, :3][::-1].astype(np.float32)
    if blur: esp = cv2.GaussianBlur(esp, (0, 0), blur)
    xp, fp = zip(*puntos); gr = np.interp(np.arange(n), xp, fp).astype(np.float32)[:, None, None] * alfa
    z = arr[y_suelo:y_suelo + n, :, :3].astype(np.float32)
    arr[y_suelo:y_suelo + n, :, :3] = np.clip(z + esp * gr, 0, 255).astype(np.uint8)
    return arr


def textura_ruido(w=W, h=H, escalas=(2, 8, 32), pesos=(.5, .3, .2), semilla=7):
    """Ruido turbulento −1..1 para tela, ladrillo, madera (camara-viaja). Multiplica o suma a un color."""
    r = np.random.default_rng(semilla); out = np.zeros((h, w), np.float32)
    for s, p in zip(escalas, pesos):
        n = r.standard_normal((h // s + 2, w // s + 2)).astype(np.float32)
        out += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * p
    return np.clip(out / (out.std() * 2.5 + 1e-6), -1, 1)


def aplicar_textura(arr, tex, fuerza=8.0, mascara=None):
    """Suma tex×fuerza (niveles 0–255) sobre arr; mascara opcional (H,W) 0–1."""
    d = tex * fuerza if mascara is None else tex * fuerza * mascara
    arr[..., :3] = np.clip(arr[..., :3].astype(np.float32) + d[..., None], 0, 255).astype(np.uint8)
    return arr


_GRANO = {}
def grano(arr, f, amp=2.0, semilla=11, tam=256):
    """Grano por cuadro, función pura de f: recorta un mosaico fijo con desplazamiento derivado de f."""
    k = (tam, semilla)
    if k not in _GRANO: _GRANO[k] = np.random.default_rng(semilla).standard_normal((tam, tam)).astype(np.float32)
    g = _GRANO[k]; r = np.random.default_rng(semilla + f); dx, dy = r.integers(0, tam, 2)
    h, w = arr.shape[:2]; reps = (h // tam + 2, w // tam + 2)
    t = np.tile(np.roll(g, (dy, dx), (0, 1)), reps)[:h, :w]
    arr[..., :3] = np.clip(arr[..., :3].astype(np.float32) + t[..., None] * amp, 0, 255).astype(np.uint8)
    return arr


class BufferFloat:
    """Acumulador lineal de luz. b.sumar(capa_uint8_rgb, peso) o b.x[...] += …; b.a_8bits(k) aplica tonemap 1−exp(−k·x)."""
    def __init__(self, w=W, h=H): self.x = np.zeros((h, w, 3), np.float32)
    def sumar(self, rgb, peso=1.0): self.x += rgb[..., :3].astype(np.float32) / 255 * peso; return self
    def a_8bits(self, k=1.0, fondo=None, semilla=5):
        y = 1 - np.exp(-k * self.x)
        if fondo is not None: y = 1 - (1 - y) * (1 - fondo.astype(np.float32) / 255)
        return tramar(y * 255, semilla)


class Camara2D:
    """Cámara de mundo: x,y = punto del mundo al centro del pivote; zoom = escala.

    Dos usos:
      cam = Camara2D(x0, y0, zoom0); cam.a(f0, dur, x=…, y=…, zoom=…, curva="quad_inout")   (movimientos encadenados)
    Un movimiento nuevo arranca desde la pose EXACTA en su f0, aunque el anterior no haya terminado (interrumpible: títeres).
    cam.aplicar(canvas, f) concatena la matriz; encierra en save/restore si hay HUD fuera de cámara."""
    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, pivote=(W / 2, H / 2)):
        self.ini = dict(x=x, y=y, zoom=zoom); self.mov = []; self.pivote = pivote

    def a(self, f0, dur, x=None, y=None, zoom=None, curva="cubic_out"):
        self.mov.append(dict(f0=f0, dur=dur, x=x, y=y, zoom=zoom, c=CURVAS[curva])); self.mov.sort(key=lambda m: m["f0"]); return self

    def pose(self, f):
        p = dict(self.ini)
        for m in self.mov:
            if f <= m["f0"]: break
            u = m["c"]((f - m["f0"]) / max(m["dur"], 1e-6))
            for k in ("x", "y", "zoom"):
                if m[k] is not None: p[k] = lerp(p[k], m[k], u)
        return p

    def aplicar(self, c, f):
        p = self.pose(f); c.translate(*self.pivote); c.scale(p["zoom"], p["zoom"]); c.translate(-p["x"], -p["y"])
        return p
