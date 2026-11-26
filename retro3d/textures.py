"""Texturas pixeladas procedurales, versión MINIMALISTA (32-64 px, sin filtrado).

Regla: pocas tonalidades, poco contraste, manchas grandes. La textura solo
insinúa el material; el color lo pone el vértice y la forma la geometría.
Las texturas de detalle de personajes son planas (blanco): color por vértice.
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


def _value_noise(n, cells, seed, octaves=2):
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


def _img(arr, alpha=None):
    a = np.clip(arr * 255, 0, 255).astype(np.uint8)
    if alpha is not None:
        al = np.clip(alpha * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(np.dstack([a, al]), "RGBA")
    return Image.fromarray(a, "RGB").convert("RGBA")


def _two_tone(n, base, k=0.06, cells=3, seed=0, thr=0.55):
    """Dos tonos en manchas grandes: base y base*(1+k)."""
    v = _value_noise(n, cells, seed)
    arr = np.zeros((n, n, 3))
    arr[:] = base
    arr[v > thr] = base * (1 + k)
    return arr


# --------------------------------------------------------------- mundo

def grass(n=32, seed=1):
    arr = _two_tone(n, _c("grass_a"), 0.05, 3, seed)
    rng = _rng(seed + 9)
    for _ in range(6):  # alguna brizna clara suelta
        x, y = rng.integers(0, n, 2)
        arr[y, x] = _c("grass_c")
        arr[(y - 1) % n, x] = _c("grass_c")
    return _img(arr)


def dirt(n=32, seed=2):
    arr = _two_tone(n, _c("dirt_a"), -0.06, 3, seed)
    rng = _rng(seed + 3)
    for _ in range(4):
        x, y = rng.integers(0, n, 2)
        arr[y, x] = _c("dirt_c")
    return _img(arr)


def stone_wall(n=32, seed=3):
    """Sillares lisos con juntas finas."""
    rng = _rng(seed)
    arr = np.zeros((n, n, 3))
    arr[:] = _c("stone_a")
    joint = _c("stone_b") * 0.85
    y = 0
    row = 0
    while y < n:
        h = 8
        arr[y, :] = joint
        x = 0 if row % 2 == 0 else 6
        while x < n:
            arr[y:y + h, x % n] = joint
            x += int(rng.integers(10, 15))
        y += h
        row += 1
    return _img(arr)


def planks(n=32, seed=4, vertical=False):
    arr = np.zeros((n, n, 3))
    arr[:] = _c("wood_a")
    for i in range(0, n, 8):
        arr[:, i] = _c("wood_b") * 0.85
    if not vertical:
        arr = arr.transpose(1, 0, 2)
    return _img(arr)


def bark(n=16, seed=5):
    arr = np.zeros((n, n, 3))
    arr[:] = _c("bark")
    arr[:, ::5] = _c("bark_dark")
    return _img(arr)


def roof_tiles(n=32, seed=6):
    arr = np.zeros((n, n, 3))
    arr[:] = _c("roof_a")
    arr[::8, :] = _c("roof_b")
    return _img(arr)


def leaves(n=16, seed=7, kind="leaf"):
    base = _c("leaf_a") if kind == "leaf" else _c("pine_a")
    return _img(_two_tone(n, base, 0.05, 2, seed))


def grass_tuft(n=16, seed=8):
    """Matojo: tres briznas gruesas en recorte alfa."""
    arr = np.zeros((n, n, 3))
    al = np.zeros((n, n))
    for x0, h, lean in ((4, 10, -0.25), (8, 13, 0.0), (11, 9, 0.3)):
        for k in range(h):
            x = int(round(x0 + lean * k))
            y = n - 1 - k
            if 0 <= x < n - 1:
                arr[y, x:x + 2] = _c("grass_c") * (0.92 + 0.08 * k / h)
                al[y, x:x + 2] = 1
    return _img(arr, al)


def flowers(n=16, seed=9, col="flower_r"):
    img = grass_tuft(n, seed)
    a = np.array(img).astype(float) / 255
    for x, y in ((5, 5), (10, 3)):
        a[y:y + 2, x:x + 2, :3] = _c(col)
        a[y:y + 2, x:x + 2, 3] = 1
    return Image.fromarray((a * 255).astype(np.uint8), "RGBA")


def cloud(n=32, seed=10):
    yy, xx = np.mgrid[0:n, 0:n] / n
    m = np.zeros((n, n))
    for cx, cy, r in ((0.35, 0.6, 0.22), (0.58, 0.5, 0.26), (0.75, 0.64, 0.18)):
        m = np.maximum(m, (((xx - cx) / r) ** 2 + ((yy - cy) / (r * 0.8)) ** 2 < 1).astype(float))
    m[yy > 0.72] = 0
    arr = np.ones((n, n, 3))
    return _img(arr, m)


def flat(n=4):
    return Image.new("RGBA", (n, n), (255, 255, 255, 255))


# detalle de personajes: plano (color por vértice)
cloth = leather = metal = fur = hair = white = lambda *a, **k: flat()


def speckle(n=16, seed=16, amount=0.06):
    return _img(np.repeat((_two_tone(n, np.array([1.0, 1.0, 1.0]), -amount, 2, seed))[..., :1], 3, 2))


# --------------------------------------------------------------- caras minimalistas

INK = (52, 32, 24, 255)        # un solo tono oscuro para ojos y bocas
EYE_STATES = ["open", "half", "closed", "happy", "wide"]
MOUTH_STATES = ["X", "M", "E", "A", "O"]  # cerrada, pequeña, ancha, abierta, redonda


def _rect(d, x0, y0, x1, y1, col=INK):
    d.rectangle([x0, y0, x1, y1], fill=col)


def _draw_eye(d, ox, oy, state):
    """Ojo de 4x6 px como máximo, centrado en (ox, oy). Solo forma, sin brillos."""
    if state == "open":
        _rect(d, ox - 1, oy - 4, ox + 1, oy + 3)
        _rect(d, ox - 2, oy - 3, ox + 2, oy + 2)
    elif state == "wide":
        _rect(d, ox - 2, oy - 5, ox + 2, oy + 4)
        _rect(d, ox - 3, oy - 4, ox + 3, oy + 3)
    elif state == "half":
        _rect(d, ox - 2, oy, ox + 2, oy + 1)
        _rect(d, ox - 1, oy + 2, ox + 1, oy + 2)
    elif state == "closed":
        _rect(d, ox - 2, oy + 1, ox + 2, oy + 1)
    elif state == "happy":
        _rect(d, ox - 2, oy + 1, ox - 2, oy + 1)
        _rect(d, ox - 1, oy, ox + 1, oy)
        _rect(d, ox + 2, oy + 1, ox + 2, oy + 1)


def _draw_mouth(d, ox, oy, st):
    """Boca de un tono en una celda 24x16 (centro en ox+12, oy+8)."""
    cx, cy = ox + 12, oy + 8
    if st == "X":  # media sonrisa mínima
        _rect(d, cx - 2, cy + 1, cx + 2, cy + 1)
        _rect(d, cx - 3, cy, cx - 3, cy)
        _rect(d, cx + 3, cy, cx + 3, cy)
    elif st == "M":
        _rect(d, cx - 2, cy - 1, cx + 2, cy)
    elif st == "E":
        _rect(d, cx - 4, cy - 1, cx + 4, cy + 1)
    elif st == "A":
        _rect(d, cx - 2, cy - 3, cx + 2, cy + 2)
        _rect(d, cx - 3, cy - 2, cx + 3, cy + 1)
    elif st == "O":
        _rect(d, cx - 1, cy - 2, cx + 1, cy + 2)
        _rect(d, cx - 2, cy - 1, cx + 2, cy + 1)


def face_atlas(dog=False, **kw):
    """Atlas 128x128: ojos (pareja por celda 32x16) y bocas (celdas 24x16)."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rects = {}
    sep = 8 if not dog else 9
    for i, st in enumerate(EYE_STATES):
        cx, cy = (i % 4) * 32, (i // 4) * 16
        _draw_eye(d, cx + 16 - sep, cy + 8, st)
        _draw_eye(d, cx + 16 + sep, cy + 8, st)
        rects["eye_" + st] = (cx, cy, 32, 16)
    for i, st in enumerate(MOUTH_STATES):
        cx, cy = (i % 5) * 24, 48
        _draw_mouth(d, cx, cy, st)
        rects["mouth_" + st] = (cx, cy, 24, 16)
    uv = {k: (x / 128, 1 - (y + h) / 128, (x + w) / 128, 1 - y / 128) for k, (x, y, w, h) in rects.items()}
    return img, uv


# --------------------------------------------------------------- UI en el mundo

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
                best = (score, bm, sc, lines, sp)
    return best[1], best[2]


def fit_layout(text, w, h, max_scale=4):
    """Como fit_text, pero devuelve también las líneas y el espaciado (para escribir letra a letra)."""
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
                best = (score, lines, sp, sc)
    return best[1], best[2], best[3]


def progressive_bitmaps(lines, sp, reveal):
    """Bitmaps con las letras reveladas (enteras) y la siguiente (parcial), misma maquetación
    que el texto completo. Devuelve (bm_lleno, bm_parcial, alfa_parcial)."""
    full_rows = font.text_bitmap("\n".join(lines), spacing=sp)
    nz = [i for i, r in enumerate(full_rows) if "#" in r]
    r0, r1 = nz[0], nz[-1]
    flat = "\n".join(lines)
    k = int(math.floor(reveal))
    frac = reveal - k

    def masked(n):
        out, cnt = [], 0
        for ch in flat:
            if ch == "\n":
                out.append(ch)
                continue
            out.append(ch if cnt < n or ch == " " else " ")
            cnt += 1
        return "".join(out)
    a = font.bitmap_array(font.text_bitmap(masked(k), spacing=sp)[r0:r1 + 1])
    b = font.bitmap_array(font.text_bitmap(masked(k + 1), spacing=sp)[r0:r1 + 1])
    return a, b & ~a, frac


def _blit_text(img, bm, sc, ox, oy, col):
    d = ImageDraw.Draw(img)
    th, tw = bm.shape
    for y in range(th):
        for x in range(tw):
            if bm[y, x]:
                d.rectangle([ox + x * sc, oy + y * sc, ox + x * sc + sc - 1, oy + y * sc + sc - 1], fill=col)


def _blit_progressive(img, text, w, h, ox_pad, oy_pad, ink, bg, reveal):
    lines, sp, sc = fit_layout(text, w, h)
    full = font.bitmap_array(font.trim_rows(font.text_bitmap("\n".join(lines), spacing=sp)))
    th, tw = full.shape
    ox, oy = ox_pad + (w - tw * sc) // 2, oy_pad + (h - th * sc) // 2
    if reveal is None:
        _blit_text(img, full, sc, ox, oy, ink)
        return
    a, b, frac = progressive_bitmaps(lines, sp, reveal)
    _blit_text(img, a, sc, ox, oy, ink)
    if frac > 0:   # letra en curso: se funde y sube 1 píxel
        mix = tuple(int(bg[i] + (ink[i] - bg[i]) * frac) for i in range(3)) + (255,)
        _blit_text(img, b, sc, ox, oy + (sc if frac < 0.5 else 0), mix)


def sign_texture(text, w=128, h=64, seed=20, reveal=None):
    """Tablón liso con marco y texto oscuro (reveal = nº de letras visibles, con decimales)."""
    bg = tuple(int(c * 255) for c in _c("wood_c")) + (255,)
    img = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(img)
    fr = tuple(int(c * 255) for c in _c("wood_b") * 0.8) + (255,)
    d.rectangle([0, 0, w - 1, h - 1], outline=fr, width=3)
    _blit_progressive(img, text, w - 12, h - 10, 6, 5, (52, 30, 16, 255), bg, reveal)
    return img


def bubble_texture(text=None, icon=None, w=128, h=80, reveal=None):
    """Bocadillo: papel claro con borde oscuro de 2 px y cola."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (42, 26, 16, 255)
    paper = (252, 246, 230, 255)
    bh = h - 16
    d.rounded_rectangle([1, 1, w - 2, bh], radius=12, fill=ink)
    d.rounded_rectangle([3, 3, w - 4, bh - 2], radius=10, fill=paper)
    d.polygon([(22, bh - 2), (44, bh - 2), (18, h - 2)], fill=ink)
    d.polygon([(25, bh - 3), (40, bh - 3), (21, h - 6)], fill=paper)
    if text:
        _blit_progressive(img, text, w - 16, bh - 14, 8, 8, ink, paper, reveal)
    return img


def to_rgba_bytes(img):
    return img.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM).tobytes()


# --------------------------------------------------------------- cara del narrador (pasamontañas)

def _hexrgba(h):
    r, g, b, _ = hexcol(h)
    return (int(r * 255), int(g * 255), int(b * 255), 255)


# cejas por expresión: (y_exterior, y_interior) relativas a la fila base; negativo = más arriba
_BROWS = {"neutral": (0, 0), "happy": (-1, -1), "surprised": (-2, -2), "angry": (-1, 1),
          "sad": (1, -1), "skeptical": None}


def _brow(d, x_out, x_in, y_out, y_in, col):
    """Ceja de 5 px y 1-2 px de grosor entre dos alturas."""
    n = abs(x_in - x_out)
    step = 1 if x_in > x_out else -1
    for k in range(n + 1):
        x = x_out + k * step
        y = round(y_out + (y_in - y_out) * k / max(1, n))
        d.point((x, y), fill=col)
        d.point((x, y + 1), fill=col)


def _eye_shape(d, cx, cy, expr, lid, col):
    if lid == "closed" or (expr == "happy" and lid != "open"):
        for x in range(cx - 2, cx + 3):
            d.point((x, cy + 1), fill=col)
        return
    if expr == "happy":   # ^ ^
        for x, y in ((cx - 2, cy + 1), (cx - 1, cy), (cx, cy - 1), (cx + 1, cy), (cx + 2, cy + 1)):
            d.point((x, y), fill=col)
            d.point((x, y + 1), fill=col)
        return
    h = 5 if expr == "surprised" else 4
    if lid == "half":
        d.rectangle([cx - 2, cy - 1, cx + 2, cy - 1], fill=col)    # párpado
        d.rectangle([cx - 1, cy, cx + 1, cy + 1], fill=col)
        return
    d.rectangle([cx - 1, cy - h // 2, cx + 1, cy - h // 2 + h - 1], fill=col)


def balaclava_atlas(skin="#C98B62", ink="#2B1420", rim="#B0166F"):
    """Atlas 128x128 del narrador.
    Ojos: celdas 32x16 = franja de piel abierta en el pasamontañas con cejas y ojos.
    Claves: eye_<expr>_<lid>. Bocas (fila y=96): abertura ovalada de piel + forma."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S, K, R = _hexrgba(skin), _hexrgba(ink), _hexrgba(rim)
    rects = {}
    exprs = ["neutral", "happy", "surprised", "angry", "sad", "skeptical"]
    lids = ["open", "half", "closed"]
    i = 0
    for e in exprs:
        for l in lids:
            cx0, cy0 = (i % 4) * 32, (i // 4) * 16
            # franja abierta: rectángulo redondeado con borde magenta oscuro
            d.rounded_rectangle([cx0 + 1, cy0 + 2, cx0 + 30, cy0 + 14], radius=4, fill=R)
            d.rounded_rectangle([cx0 + 2, cy0 + 3, cx0 + 29, cy0 + 13], radius=3, fill=S)
            ex = (cx0 + 10, cx0 + 21)
            base = cy0 + 4
            if e == "skeptical":
                _brow(d, ex[0] - 3, ex[0] + 2, base - 1, base - 2, K)   # ceja izq. arriba
                _brow(d, ex[1] + 3, ex[1] - 2, base + 1, base + 1, K)   # der. baja
            else:
                yo, yi = _BROWS[e]
                _brow(d, ex[0] - 3, ex[0] + 2, base + yo, base + yi, K)
                _brow(d, ex[1] + 3, ex[1] - 2, base + yo, base + yi, K)
            for k, cx in enumerate(ex):
                ll = l if not (e == "skeptical" and k == 1 and l == "open") else "half"
                _eye_shape(d, cx, cy0 + 11, e, ll, K)
            rects[f"eye_{e}_{l}"] = (cx0, cy0, 32, 16)
            i += 1
    for j, m in enumerate(["X", "M", "E", "A", "O"]):
        ox, oy = j * 24, 96
        d.ellipse([ox + 3, oy + 1, ox + 20, oy + 14], fill=R)
        d.ellipse([ox + 4, oy + 2, ox + 19, oy + 13], fill=S)
        _draw_mouth(d, ox, oy, m)
        rects[f"mouth_{m}"] = (ox, oy, 24, 16)
    # recolorear bocas al tono de tinta del narrador
    px = img.load()
    for y in range(96, 112):
        for x in range(0, 120):
            if px[x, y] == INK:
                px[x, y] = K
    uv = {k: (x / 128, 1 - (y + h) / 128, (x + w) / 128, 1 - y / 128) for k, (x, y, w, h) in rects.items()}
    return img, uv


def camo(n=32, seed=21, cols=("#6B7350", "#474E33", "#9C8D62")):
    """Camuflaje militar de 3 tonos en manchas grandes (32 px)."""
    a, b, c = (np.array(hexcol(h)[:3]) for h in cols)
    v1 = _value_noise(n, 3, seed)
    v2 = _value_noise(n, 3, seed + 7)
    arr = np.zeros((n, n, 3))
    arr[:] = a
    arr[v1 > 0.58] = b
    arr[(v2 > 0.62) & (v1 <= 0.58)] = c
    return _img(arr)


def jersey_number(text="00", col="#F4F2EC", w=32, h=32):
    """Número de jersey en píxeles gruesos sobre transparente."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rows = font.trim_rows(font.text_bitmap(text, spacing=1))
    bm = font.bitmap_array(rows)
    th, tw = bm.shape
    sc = max(1, min((w - 2) // tw, (h - 2) // th))
    r, g, b, _ = hexcol(col)
    _blit_text(img, bm, sc, (w - tw * sc) // 2, (h - th * sc) // 2, (int(r * 255), int(g * 255), int(b * 255), 255))
    return img
