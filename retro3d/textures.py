"""Texturas pixeladas procedurales (32-128 px, sin filtrado).

Las texturas de «detalle» son casi grises (media ~1) y se multiplican por el
color por vértice; así una sola textura de tela sirve para túnica y bufanda.
Las texturas de «color» (hierba, tierra, piedra, caras, carteles) llevan su
propio color.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

from .mesh import hexcol
from .style import PAL
from . import font


def _rng(seed):
    return np.random.default_rng(seed)


def _c(name):
    return np.array(hexcol(PAL[name])[:3])


def _value_noise(n, cells, seed, octaves=3):
    rng = _rng(seed)
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = rng.random((c, c))
        g = np.pad(g, ((0, 1), (0, 1)), mode="wrap")
        x = np.linspace(0, c, n, endpoint=False)
        xi = x.astype(int)
        xf = x - xi
        xf = xf * xf * (3 - 2 * xf)
        a = g[xi][:, xi]
        b = g[xi][:, xi + 1]
        cc = g[xi + 1][:, xi]
        d = g[xi + 1][:, xi + 1]
        top = a + (b - a) * xf[None, :]
        bot = cc + (d - cc) * xf[None, :]
        out += amp * (top + (bot - top) * xf[:, None])
        tot += amp
        amp *= 0.5
    return out / tot


def _palette_map(v, cols, thresholds):
    out = np.zeros(v.shape + (3,))
    out[:] = cols[0]
    for c, t in zip(cols[1:], thresholds):
        out[v > t] = c
    return out


def _img(arr, alpha=None):
    a = np.clip(arr * 255, 0, 255).astype(np.uint8)
    if alpha is not None:
        al = np.clip(alpha * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(np.dstack([a, al]), "RGBA")
    return Image.fromarray(a, "RGB").convert("RGBA")


# --------------------------------------------------------------- mundo

def grass(n=64, seed=1):
    v = _value_noise(n, 5, seed) * 0.78 + _rng(seed).random((n, n)) * 0.22
    arr = _palette_map(v, [_c("grass_b"), _c("grass_a"), _c("grass_c")], [0.42, 0.66])
    # briznas: pequeños trazos verticales claros
    rng = _rng(seed + 9)
    for _ in range(45):
        x, y = rng.integers(0, n, 2)
        for k in range(rng.integers(2, 4)):
            arr[(y - k) % n, x] = _c("grass_c") * 1.05
    for _ in range(40):
        x, y = rng.integers(0, n, 2)
        arr[y, x] = _c("grass_b") * 0.85
    return _img(arr)


def dirt(n=64, seed=2):
    v = _value_noise(n, 5, seed) * 0.75 + _rng(seed).random((n, n)) * 0.25
    arr = _palette_map(v, [_c("dirt_b"), _c("dirt_a"), _c("dirt_c")], [0.40, 0.70])
    rng = _rng(seed + 3)
    for _ in range(26):  # piedrecitas
        x, y = rng.integers(0, n - 1, 2)
        arr[y, x] = _c("stone_c")
        arr[y + 1, x] = _c("stone_b")
    return _img(arr)


def stone_wall(n=64, seed=3):
    """Sillares irregulares con juntas oscuras."""
    rng = _rng(seed)
    arr = np.zeros((n, n, 3))
    arr[:] = _c("stone_b") * 0.7
    y = 0
    row = 0
    while y < n:
        h = int(rng.integers(10, 15))
        x = -int(rng.integers(0, 12)) if row % 2 else 0
        while x < n:
            w = int(rng.integers(12, 22))
            base = [_c("stone_a"), _c("stone_c"), _c("stone_b")][rng.integers(0, 3)]
            base = base * rng.uniform(0.92, 1.06)
            for yy in range(y + 1, min(y + h - 1, n)):
                for xx in range(max(x + 1, 0), min(x + w - 1, n)):
                    arr[yy, xx] = base
            # luz arriba, sombra abajo de cada piedra
            for xx in range(max(x + 1, 0), min(x + w - 1, n)):
                if y + 1 < n:
                    arr[y + 1, xx] = base * 1.12
                if y + h - 2 < n:
                    arr[min(y + h - 2, n - 1), xx] = base * 0.82
            x += w
        y += h
        row += 1
    arr += (_rng(seed + 1).random((n, n, 1)) - 0.5) * 0.06
    return _img(arr)


def planks(n=64, seed=4, vertical=False):
    rng = _rng(seed)
    arr = np.zeros((n, n, 3))
    pw = 11
    for i in range(0, n, pw):
        base = [_c("wood_a"), _c("wood_b"), _c("wood_c")][rng.integers(0, 3)] * rng.uniform(0.95, 1.05)
        arr[:, i:i + pw] = base
        arr[:, i] = base * 0.55
        # vetas
        for _ in range(4):
            x = i + rng.integers(2, pw - 1)
            y0 = rng.integers(0, n)
            L = rng.integers(8, 30)
            for k in range(L):
                arr[(y0 + k) % n, min(x, n - 1)] *= 0.86
        # nudo
        if rng.random() < 0.5:
            y = rng.integers(2, n - 2)
            x = i + pw // 2
            arr[y - 1:y + 2, x - 1:x + 2] *= 0.7
        # clavos
        for y in (3, n - 4):
            arr[y, min(i + pw // 2, n - 1)] = (0.25, 0.22, 0.2)
    if not vertical:
        arr = arr.transpose(1, 0, 2)
    return _img(arr)


def bark(n=32, seed=5):
    rng = _rng(seed)
    arr = np.zeros((n, n, 3))
    arr[:] = _c("bark")
    for x in range(n):
        if rng.random() < 0.35:
            arr[:, x] = _c("bark_dark")
    v = _value_noise(n, 4, seed)
    arr *= (0.85 + v[..., None] * 0.3)
    return _img(arr)


def roof_tiles(n=64, seed=6):
    rng = _rng(seed)
    arr = np.zeros((n, n, 3))
    rh = 8
    for r, y in enumerate(range(0, n, rh)):
        off = (r % 2) * 5
        for x in range(-off, n, 10):
            base = [_c("roof_a"), _c("roof_b")][rng.integers(0, 2)] * rng.uniform(0.92, 1.08)
            arr[y:y + rh, max(x, 0):x + 10] = base
            arr[y + rh - 1, max(x, 0):x + 10] = base * 0.6
            if x >= 0:
                arr[y:y + rh, x] = base * 0.7
            arr[y, max(x, 0):x + 10] = base * 1.15
    return _img(arr)


def leaves(n=32, seed=7, kind="leaf"):
    names = ("leaf_c", "leaf_a", "leaf_b") if kind == "leaf" else ("pine_a", "pine_b", "leaf_b")
    v = _value_noise(n, 4, seed) * 0.5 + _rng(seed).random((n, n)) * 0.5
    arr = _palette_map(v, [_c(names[0]), _c(names[1]), _c(names[2])], [0.45, 0.72])
    return _img(arr)


def grass_tuft(n=32, seed=8):
    """Matojo con transparencia (recorte alfa)."""
    rng = _rng(seed)
    arr = np.zeros((n, n, 3))
    al = np.zeros((n, n))
    for _ in range(9):
        x0 = rng.integers(3, n - 3)
        h = rng.integers(n // 2, n - 2)
        lean = rng.uniform(-0.35, 0.35)
        col = [_c("grass_a"), _c("grass_c"), _c("grass_b")][rng.integers(0, 3)]
        for k in range(h):
            x = int(round(x0 + lean * k))
            y = n - 1 - k
            if 0 <= x < n:
                arr[y, x] = col * (0.8 + 0.4 * k / h)
                al[y, x] = 1
                if k < h * 0.5 and x + 1 < n:
                    arr[y, x + 1] = col * 0.85
                    al[y, x + 1] = 1
    return _img(arr, al)


def flowers(n=32, seed=9, col="flower_r"):
    img = grass_tuft(n, seed)
    a = np.array(img).astype(float) / 255
    rng = _rng(seed)
    c = _c(col)
    for _ in range(4):
        x, y = rng.integers(3, n - 3), rng.integers(3, n // 2)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            a[y + dy, x + dx, :3] = c if (dx or dy) else _c("flower_y")
            a[y + dy, x + dx, 3] = 1
    return Image.fromarray((a * 255).astype(np.uint8), "RGBA")


def cloud(n=64, seed=10):
    v = _value_noise(n, 3, seed, 3)
    yy, xx = np.mgrid[0:n, 0:n] / n
    mask = ((xx - 0.5) / 0.5) ** 2 + ((yy - 0.6) / 0.35) ** 2
    al = ((1 - mask) * 1.4 + (v - 0.5) * 1.2 > 0.35).astype(float)
    arr = np.ones((n, n, 3))
    arr *= (0.86 + 0.14 * (1 - yy))[..., None]
    arr[..., 0] *= 1.0
    arr[..., 2] *= 0.96
    return _img(arr, al)


# --------------------------------------------------------------- detalle (gris)

def cloth(n=32, seed=11):
    rng = _rng(seed)
    arr = np.ones((n, n)) * 1.0
    arr[::2, :] *= 0.95
    arr[:, ::2] *= 0.97
    arr *= 1 + (rng.random((n, n)) - 0.5) * 0.08
    # costura
    arr[n // 2, :] *= 0.85
    for x in range(0, n, 4):
        arr[n // 2 - 1, x] *= 0.8
    return _img(np.repeat(arr[..., None], 3, 2))


def leather(n=32, seed=12):
    v = _value_noise(n, 4, seed)
    arr = 0.9 + v * 0.2
    arr += (_rng(seed).random((n, n)) - 0.5) * 0.08
    arr[1, :] *= 0.8
    arr[-2, :] *= 0.8
    for x in range(0, n, 4):
        arr[2, x] *= 0.7
        arr[-3, x] *= 0.7
    return _img(np.repeat(arr[..., None], 3, 2))


def metal(n=32, seed=13):
    yy = np.mgrid[0:n, 0:n][0] / n
    arr = 0.82 + 0.35 * (1 - yy)
    arr[2:4, :] = 1.25
    arr += (_rng(seed).random((n, n)) - 0.5) * 0.05
    for x, y in ((4, 6), (n - 5, 6), (4, n - 6), (n - 5, n - 6)):  # remaches
        arr[y, x] = 1.35
        arr[y + 1, x] = 0.6
    return _img(np.repeat(arr[..., None], 3, 2))


def fur(n=32, seed=14):
    rng = _rng(seed)
    arr = np.ones((n, n))
    for _ in range(90):
        x, y = rng.integers(0, n, 2)
        L = rng.integers(2, 5)
        d = rng.choice([0.86, 1.1])
        for k in range(L):
            arr[(y + k) % n, (x + k // 2) % n] *= d
    return _img(np.repeat(arr[..., None], 3, 2))


def hair(n=32, seed=15):
    arr = np.ones((n, n))
    rng = _rng(seed)
    for x in range(n):
        arr[:, x] *= rng.choice([0.85, 1.0, 1.12])
    arr[::5, :] *= 0.92
    return _img(np.repeat(arr[..., None], 3, 2))


def white(n=4):
    return Image.new("RGBA", (n, n), (255, 255, 255, 255))


# --------------------------------------------------------------- caras

OUT = (40, 22, 14, 255)       # contorno marrón muy oscuro (no negro puro)
IRIS = (58, 36, 22, 255)
EYE_W = (252, 248, 236, 255)
HL = (255, 255, 255, 255)
MOUTH_IN = (122, 34, 36, 255)
TEETH = (250, 246, 236, 255)
TONGUE = (226, 98, 104, 255)
BROW = (92, 44, 22, 255)

EYE_STATES = ["open", "half", "closed", "happy", "wide"]
MOUTH_STATES = ["X", "M", "E", "A", "O"]  # cerrada, pequeña, ancha, abierta, redonda


def _px(d, pts, col):
    for x, y in pts:
        d.point((x, y), fill=col)


def _draw_eye(d, ox, oy, state, mirror, brow_col=BROW, raise_brow=0):
    """Ojo chibi sin esclerótica: óvalo oscuro alto con brillo. Celda ~11x16."""
    def X(x):
        return ox + (10 - x if mirror else x)
    by = oy + 1 - raise_brow
    # ceja gruesa de 2 px, ligeramente inclinada hacia fuera
    for x in range(1, 9):
        yy = by + (1 if x <= 2 else 0)
        d.point((X(x), yy), fill=brow_col)
        d.point((X(x), yy + 1), fill=brow_col)
    ey = oy + 5
    if state in ("open", "wide"):
        rows = [(3, 6), (2, 7), (2, 7), (2, 7), (2, 7), (2, 7), (3, 6)]
        if state == "wide":
            rows = [(3, 6), (2, 7), (2, 7), (2, 7), (2, 7), (2, 7), (2, 7), (3, 6)]
            ey -= 1
        for y, (x0, x1) in enumerate(rows):
            for x in range(x0, x1 + 1):
                d.point((X(x), ey + y), fill=IRIS)
        _px(d, [(X(3), ey + 1), (X(4), ey + 1), (X(3), ey + 2), (X(4), ey + 2)], HL)
        d.point((X(6), ey + len(rows) - 2), fill=(150, 110, 80, 255))
    elif state == "half":
        rows = [(2, 7), (2, 7), (2, 7), (3, 6)]
        for x in range(1, 9):
            d.point((X(x), ey + 2), fill=OUT)
        for y, (x0, x1) in enumerate(rows):
            for x in range(x0, x1 + 1):
                d.point((X(x), ey + 3 + y), fill=IRIS)
        d.point((X(3), ey + 3), fill=HL)
    elif state == "closed":
        for x in range(1, 9):
            y = ey + 4 + (1 if 2 < x < 7 else 0)
            d.point((X(x), y), fill=OUT)
            d.point((X(x), y + 1), fill=OUT)
    elif state == "happy":  # ^ ^
        for x in range(1, 9):
            y = ey + 5 - min(x - 1, 8 - x)
            d.point((X(x), y), fill=OUT)
            d.point((X(x), y + 1), fill=OUT)


def face_atlas(skin=None, brow=BROW, dog=False):
    """Atlas 128x128: fila superior = ojos (5 estados), parte inferior = bocas (5).

    Cada celda de ojos es 32x16 (ambos ojos), cada boca 24x16.
    Devuelve (imagen, dict de rects UV)."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rects = {}
    for i, st in enumerate(EYE_STATES):
        cx, cy = (i % 4) * 32, (i // 4) * 16
        raise_b = 1 if st == "wide" else 0
        if dog:
            _draw_dog_eye(d, cx + 2, cy + 2, st, False)
            _draw_dog_eye(d, cx + 20, cy + 2, st, True)
        else:
            _draw_eye(d, cx + 1, cy, st, False, brow, raise_b)
            _draw_eye(d, cx + 20, cy, st, True, brow, raise_b)
        rects["eye_" + st] = (cx, cy, 32, 16)
    for i, st in enumerate(MOUTH_STATES):
        cx, cy = (i % 5) * 24, 48 + (i // 5) * 16
        _draw_mouth(d, cx, cy, st)
        rects["mouth_" + st] = (cx, cy, 24, 16)
    uv = {k: (x / 128, 1 - (y + h) / 128, (x + w) / 128, 1 - y / 128) for k, (x, y, w, h) in rects.items()}
    return img, uv


def _draw_dog_eye(d, ox, oy, state, mirror):
    def X(x):
        return ox + (9 - x if mirror else x)
    ey = oy + 3
    if state in ("open", "wide"):
        r = 8 if state == "wide" else 7
        for y in range(r):
            w = [4, 6, 6, 6, 6, 6, 4, 4][y]
            x0 = 5 - w // 2
            for x in range(x0, x0 + w):
                d.point((X(x), ey + y), fill=(30, 18, 12, 255))
        _px(d, [(X(3), ey + 1), (X(4), ey + 1), (X(3), ey + 2)], HL)
        d.point((X(6), ey + 4), fill=(110, 80, 60, 255))
        # ceja expresiva (mancha clara encima, típica de perro)
        for x in range(3, 7):
            d.point((X(x), ey - 2), fill=(250, 222, 170, 255))
    elif state == "half":
        for y in range(3, 6):
            for x in range(2, 8):
                d.point((X(x), ey + y), fill=(30, 18, 12, 255))
        for x in range(1, 9):
            d.point((X(x), ey + 2), fill=(70, 40, 20, 255))
        d.point((X(3), ey + 3), fill=HL)
    elif state == "closed":
        for x in range(1, 9):
            d.point((X(x), ey + 4 + (1 if 2 < x < 7 else 0)), fill=(30, 18, 12, 255))
            d.point((X(x), ey + 5 + (1 if 2 < x < 7 else 0)), fill=(30, 18, 12, 255))
    elif state == "happy":
        for x in range(1, 9):
            y = ey + 5 - min(x - 1, 8 - x)
            d.point((X(x), y), fill=(30, 18, 12, 255))
            d.point((X(x), y + 1), fill=(30, 18, 12, 255))


def _draw_mouth(d, ox, oy, st):
    if st == "X":  # cerrada con media sonrisa
        for x in range(6, 18):
            y = oy + 7 + (1 if 8 < x < 15 else 0)
            d.point((ox + x, y), fill=OUT)
            d.point((ox + x, y + 1), fill=OUT)
        d.point((ox + 5, oy + 6), fill=OUT)
        d.point((ox + 18, oy + 6), fill=OUT)
        d.point((ox + 5, oy + 7), fill=OUT)
        d.point((ox + 18, oy + 7), fill=OUT)
    elif st == "M":  # entreabierta
        d.rectangle([ox + 8, oy + 6, ox + 15, oy + 8], fill=MOUTH_IN)
        d.rectangle([ox + 8, oy + 6, ox + 15, oy + 6], fill=TEETH)
        d.rectangle([ox + 7, oy + 5, ox + 16, oy + 5], fill=OUT)
        d.rectangle([ox + 7, oy + 9, ox + 16, oy + 9], fill=OUT)
        d.point((ox + 6, oy + 6), fill=OUT); d.point((ox + 6, oy + 8), fill=OUT)
        d.point((ox + 17, oy + 6), fill=OUT); d.point((ox + 17, oy + 8), fill=OUT)
        d.rectangle([ox + 6, oy + 7, ox + 6, oy + 7], fill=OUT)
        d.rectangle([ox + 17, oy + 7, ox + 17, oy + 7], fill=OUT)
    elif st == "E":  # ancha, dientes
        d.rectangle([ox + 4, oy + 5, ox + 19, oy + 9], fill=MOUTH_IN)
        d.rectangle([ox + 5, oy + 5, ox + 18, oy + 6], fill=TEETH)
        d.rectangle([ox + 3, oy + 4, ox + 20, oy + 4], fill=OUT)
        d.rectangle([ox + 4, oy + 10, ox + 19, oy + 10], fill=OUT)
        for y in range(5, 10):
            d.point((ox + 3, oy + y), fill=OUT)
            d.point((ox + 20, oy + y), fill=OUT)
    elif st == "A":  # muy abierta
        d.ellipse([ox + 5, oy + 2, ox + 18, oy + 14], fill=OUT)
        d.ellipse([ox + 6, oy + 3, ox + 17, oy + 13], fill=MOUTH_IN)
        d.rectangle([ox + 7, oy + 3, ox + 16, oy + 4], fill=TEETH)
        d.ellipse([ox + 8, oy + 9, ox + 15, oy + 13], fill=TONGUE)
    elif st == "O":  # redonda
        d.ellipse([ox + 8, oy + 3, ox + 15, oy + 12], fill=OUT)
        d.ellipse([ox + 9, oy + 4, ox + 14, oy + 11], fill=MOUTH_IN)
        d.rectangle([ox + 10, oy + 9, ox + 13, oy + 10], fill=TONGUE)


# --------------------------------------------------------------- UI en el mundo

def pixel_text_image(text, ink=(48, 26, 12), scale=1, bg=None, pad=2):
    rows = font.text_bitmap(text)
    arr = font.bitmap_array(rows)
    h, w = arr.shape
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), bg or (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if arr[y, x]:
                px[x + pad, y + pad] = (*ink, 255)
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return img


def fit_text(text, w, h, max_scale=4):
    """Elige el reparto en líneas y la escala entera más grande que cabe en w x h."""
    words = text.split()
    layouts = [[text]]
    for n in range(2, min(4, len(words)) + 1):
        per = math.ceil(len(words) / n)
        layouts.append([" ".join(words[i:i + per]) for i in range(0, len(words), per)])
    best = None
    for lines in layouts:
        for sp in (1, 0):
            bm = font.bitmap_array(font.trim_rows(font.text_bitmap("\n".join(lines), spacing=sp)))
            th, tw = bm.shape
            sc = min(max_scale, w // tw, h // th)
            score = sc * 10 + sp - len(lines) * 0.1
            if sc >= 1 and (best is None or score > best[0]):
                best = (score, bm, sc)
    return best[1], best[2]


def sign_texture(text, w=128, h=64, seed=20):
    """Tablón de madera con texto «tallado» (oscuro con luz debajo)."""
    base = planks(64, seed)
    base = base.resize((128, 128), Image.NEAREST).crop((0, 0, w, h))
    arr = np.array(base).astype(float)
    # marco oscuro
    arr[:2, :, :3] *= 0.55
    arr[-2:, :, :3] *= 0.55
    arr[:, :2, :3] *= 0.55
    arr[:, -2:, :3] *= 0.55
    img = Image.fromarray(arr.astype(np.uint8), "RGBA").copy()
    bm, sc = fit_text(text, w - 10, h - 8)
    th, tw = bm.shape
    ox = (w - tw * sc) // 2
    oy = (h - th * sc) // 2
    px = img.load()
    for y in range(th):
        for x in range(tw):
            if bm[y, x]:
                for a in range(sc):
                    for b in range(sc):
                        X, Y = ox + x * sc + a, oy + y * sc + b
                        px[X, Y] = (52, 28, 14, 255)
                        if Y + 1 < h and not (y + 1 < th and bm[y + 1, x]) and b == sc - 1:
                            px[X, Y + 1] = (226, 176, 112, 255)
    return img


def bubble_texture(text=None, icon=None, w=128, h=80):
    """Bocadillo pixel: papel crema, borde oscuro de 2 px y cola abajo-izquierda."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (42, 26, 16, 255)
    paper = (252, 244, 222, 255)
    shade = (227, 207, 160, 255)
    bh = h - 16
    d.rounded_rectangle([1, 1, w - 2, bh], radius=10, fill=ink)
    d.rounded_rectangle([3, 3, w - 4, bh - 2], radius=8, fill=paper)
    d.rectangle([5, bh - 6, w - 6, bh - 3], fill=shade)
    # cola
    d.polygon([(22, bh - 2), (44, bh - 2), (18, h - 2)], fill=ink)
    d.polygon([(25, bh - 3), (40, bh - 3), (21, h - 6)], fill=paper)
    if text:
        bm, sc = fit_text(text, w - 14, bh - 12)
        th, tw = bm.shape
        ox, oy = (w - tw * sc) // 2, (bh - th * sc) // 2 + 1
        for y in range(th):
            for x in range(tw):
                if bm[y, x]:
                    d.rectangle([ox + x * sc, oy + y * sc, ox + x * sc + sc - 1, oy + y * sc + sc - 1], fill=(42, 26, 16, 255))
    return img


def to_rgba_bytes(img):
    return img.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM).tobytes()


def speckle(n=32, seed=16, amount=0.16):
    """Detalle gris moteado para rocas y objetos sin textura propia."""
    v = _value_noise(n, 4, seed) * 0.6 + _rng(seed).random((n, n)) * 0.4
    arr = 1.0 - amount / 2 + v * amount
    return _img(np.repeat(arr[..., None], 3, 2))
