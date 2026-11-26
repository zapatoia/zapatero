"""Librería de estilo: paleta, trazos, tipografía, easing y pictogramas.

Estética: tarjeta de seguridad de avión en versión oscura. Trazo crema uniforme,
grueso y redondeado; rellenos planos; como máximo dos acentos por escena.
Todo lo que se dibuja en el estudio debe pasar por aquí.
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

import skia

# ---------------------------------------------------------------- formato
W, H = 1080, 1920
FPS = 30

# Zonas seguras: nada en el 20 % inferior ni en el 12 % derecho.
SAFE_BOTTOM = int(H * 0.80)   # 1536
SAFE_RIGHT = int(W * 0.88)    # 950
SAFE_TOP = 230                # bajo la interfaz superior de la app
SAFE_LEFT = 70
SAFE_CX = (SAFE_LEFT + SAFE_RIGHT) / 2  # centro óptico del área segura (510)

# Zona de contenido (escenas) y zona de subtítulos
CONTENT_TOP, CONTENT_BOTTOM = 250, 1200
CAPTION_Y = 1370


# ---------------------------------------------------------------- paleta
def hexc(h: str, a: int = 255) -> int:
    h = h.lstrip("#")
    return skia.ColorSetARGB(a, int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


PALETTE = {
    "navy": "#0E1A2B",
    "cream": "#F3EBDD",
    "orange": "#FF7A1A",
    "yellow": "#FFC93C",
    "mint": "#4FD1A5",
    "red": "#FF4D4D",
    # personaje
    "brown": "#8A4B2A",
    "brown_dark": "#5E2F18",
    "brown_light": "#B7774C",
    "shine": "#E9C9A4",
    "ink": "#08111D",
    "tongue": "#E2574C",
    "eye": "#FFFDF6",
    # fondos internos
    "navy_light": "#16263D",
    "navy_deep": "#0A1422",
}
C = {k: hexc(v) for k, v in PALETTE.items()}


def with_alpha(color: int, a: float) -> int:
    return skia.ColorSetA(color, max(0, min(255, int(a * 255))))


def accent(name: str) -> int:
    return C[name]


# ---------------------------------------------------------------- trazo
STROKE = 11.0        # trazo principal (px a 1080 de ancho)
STROKE_THIN = 7.0


def fill(color: int) -> skia.Paint:
    return skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kFill_Style)


def stroke(color: int = None, width: float = STROKE) -> skia.Paint:
    return skia.Paint(
        AntiAlias=True,
        Color=C["cream"] if color is None else color,
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=width,
        StrokeCap=skia.Paint.kRound_Cap,
        StrokeJoin=skia.Paint.kRound_Join,
    )


def draw_shape(canvas, path: skia.Path, fill_color=None, stroke_color=None, width=STROKE):
    if fill_color is not None:
        canvas.drawPath(path, fill(fill_color))
    if stroke_color is not False:
        canvas.drawPath(path, stroke(stroke_color, width))


def partial(path: skia.Path, p: float) -> skia.Path:
    """Devuelve el tramo inicial de un path (para animar trazos que se dibujan)."""
    if p >= 0.999:
        return path
    out = skia.Path()
    if p <= 0:
        return out
    pm = skia.PathMeasure(path, False)
    lengths = []
    while True:
        lengths.append(pm.getLength())
        if not pm.nextContour():
            break
    total = sum(lengths)
    remaining = total * p
    pm = skia.PathMeasure(path, False)
    for L in lengths:
        if remaining <= 0:
            break
        pm.getSegment(0, min(L, remaining), out, True)
        remaining -= L
        pm.nextContour()
    return out


def rrect(x0, y0, x1, y1, r) -> skia.Path:
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r))
    return p


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def prog(t, t0, dur):
    """Progreso lineal 0..1 de una animación que empieza en t0 y dura dur."""
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / dur)


def ease_out_back(x, s=1.70158):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def ease_in_back(x, s=1.70158):
    x = clamp(x)
    return x * x * ((s + 1) * x - s)


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_out_elastic(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def spring(t, freq=3.0, damp=6.0):
    """Respuesta a impulso amortiguada (0 en t<=0, oscila y se apaga)."""
    if t <= 0:
        return 0.0
    return math.exp(-damp * t) * math.sin(2 * math.pi * freq * t)


def pop_in(t, t0, dur=0.45):
    """Escala de aparición con rebote (0 → 1 pasando por ~1.1)."""
    return ease_out_back(prog(t, t0, dur), 2.2)


def wobble(t, seed=0, amp=1.0, speed=1.0):
    """Ruido suave determinista (suma de senos) para micro-movimiento."""
    r = random.Random(seed)
    a = [r.uniform(0.6, 1.4) for _ in range(3)]
    ph = [r.uniform(0, 6.28) for _ in range(3)]
    return amp * (
        math.sin(t * 1.3 * speed * a[0] + ph[0]) * 0.5
        + math.sin(t * 2.1 * speed * a[1] + ph[1]) * 0.3
        + math.sin(t * 3.7 * speed * a[2] + ph[2]) * 0.2
    )


# ---------------------------------------------------------------- tipografía
FONT_DIR = "/usr/share/fonts/opentype/inter/"
FONT_FILES = {
    "black": "InterDisplay-Black.otf",
    "xbold": "InterDisplay-ExtraBold.otf",
    "bold": "InterDisplay-Bold.otf",
    "semi": "InterDisplay-SemiBold.otf",
    "medium": "InterDisplay-Medium.otf",
}


@lru_cache(maxsize=None)
def typeface(weight="black"):
    tf = skia.Typeface.MakeFromFile(FONT_DIR + FONT_FILES[weight])
    if tf is None:
        tf = skia.Typeface("Inter", skia.FontStyle.Bold())
    return tf


@lru_cache(maxsize=512)
def font(size: float, weight="black") -> skia.Font:
    f = skia.Font(typeface(weight), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def text_width(s: str, size: float, weight="black") -> float:
    return font(size, weight).measureText(s)


def draw_text(canvas, s, x, y, size, color=None, weight="black", align="center",
              outline=0.0, outline_color=None, tracking=0.0):
    """Texto con contorno opcional. (x, y) = punto de anclaje en la línea base."""
    f = font(size, weight)
    color = C["cream"] if color is None else color
    w = f.measureText(s) + tracking * max(0, len(s) - 1)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if tracking:
        blob = _tracked_blob(s, f, tracking)
    else:
        blob = skia.TextBlob.MakeFromString(s, f)
    if blob is None:
        return w
    if outline > 0:
        p = stroke(C["navy"] if outline_color is None else outline_color, outline)
        canvas.drawTextBlob(blob, x, y, p)
    canvas.drawTextBlob(blob, x, y, fill(color))
    return w


def _tracked_blob(s, f, tracking):
    glyphs = f.textToGlyphs(s)
    widths = f.getWidths(glyphs)
    xs, cx = [], 0.0
    for wd in widths:
        xs.append(cx)
        cx += wd + tracking
    builder = skia.TextBlobBuilder()
    builder.allocRunPosH(f, glyphs, xs, 0)
    return builder.make()


def cap_height(size):  # altura aproximada de mayúsculas de Inter
    return size * 0.727


# ---------------------------------------------------------------- fondo
_GRID = 72


def draw_background(canvas, cam_x=0.0, cam_y=0.0, t=0.0):
    """Fondo azul noche con cuadrícula muy sutil y partículas con parallax."""
    canvas.clear(C["navy"])
    # cuadrícula (parallax 0.25)
    ox = (-cam_x * 0.25) % _GRID
    oy = (-cam_y * 0.25 - t * 6) % _GRID
    p = stroke(with_alpha(C["cream"], 0.045), 2)
    x = ox - _GRID
    while x < W + _GRID:
        canvas.drawLine(x, 0, x, H, p)
        x += _GRID
    y = oy - _GRID
    while y < H + _GRID:
        canvas.drawLine(0, y, W, y, p)
        y += _GRID
    # cruces en intersecciones cada 4 celdas
    pc = stroke(with_alpha(C["cream"], 0.09), 2.5)
    step = _GRID * 4
    x = ox - step + _GRID * 2
    while x < W + step:
        y = oy - step + _GRID * 2
        while y < H + step:
            canvas.drawLine(x - 7, y, x + 7, y, pc)
            canvas.drawLine(x, y - 7, x, y + 7, pc)
            y += step
        x += step
    # partículas geométricas flotando (parallax 0.6)
    rnd = random.Random(7)
    for i in range(14):
        bx = rnd.uniform(0, W)
        by = rnd.uniform(0, H)
        kind = rnd.choice(["ring", "plus", "dot"])
        sp = rnd.uniform(4, 12)
        px = (bx - cam_x * 0.6 + math.sin(t * 0.4 + i) * 10) % (W + 80) - 40
        py = (by - cam_y * 0.6 - t * sp) % (H + 80) - 40
        a = 0.07 + 0.04 * math.sin(t * 0.8 + i * 1.7)
        col = with_alpha(C["cream"], a)
        if kind == "ring":
            canvas.drawCircle(px, py, rnd.uniform(8, 16), stroke(col, 3))
        elif kind == "plus":
            s = rnd.uniform(7, 12)
            canvas.drawLine(px - s, py, px + s, py, stroke(col, 3))
            canvas.drawLine(px, py - s, px, py + s, stroke(col, 3))
        else:
            canvas.drawCircle(px, py, 4, fill(col))


# ---------------------------------------------------------------- pictogramas
# Todas las funciones dibujan centradas en (x, y) con tamaño s y aceptan
# p (0..1) como progreso de aparición cuando tiene sentido.

def arrow(canvas, x0, y0, x1, y1, p=1.0, color=None, width=STROKE, head=26, bend=0.0):
    """Flecha con punta redondeada. bend curva la flecha (fracción de longitud)."""
    color = C["cream"] if color is None else color
    path = skia.Path()
    path.moveTo(x0, y0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    cx, cy = mx + nx * bend * L, my + ny * bend * L
    path.quadTo(cx, cy, x1, y1)
    seg = partial(path, p)
    canvas.drawPath(seg, stroke(color, width))
    if p > 0.92:
        # dirección final de la curva
        tx, ty = x1 - cx, y1 - cy
        tl = math.hypot(tx, ty) or 1
        tx, ty = tx / tl, ty / tl
        k = ease_out_back((p - 0.92) / 0.08)
        hl = head * k
        for sgn in (1, -1):
            ang = math.atan2(ty, tx) + math.pi + sgn * 0.62
            canvas.drawLine(x1, y1, x1 + math.cos(ang) * hl, y1 + math.sin(ang) * hl,
                            stroke(color, width))


def number_circle(canvas, x, y, r, n, color=None, p=1.0, text_color=None):
    color = C["orange"] if color is None else color
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(k, k)
    canvas.drawCircle(0, 0, r, fill(color))
    canvas.drawCircle(0, 0, r, stroke())
    size = r * 1.15
    draw_text(canvas, str(n), 0, cap_height(size) / 2, size,
              C["navy"] if text_color is None else text_color)
    canvas.restore()


def warning_triangle(canvas, x, y, s, color=None, p=1.0):
    color = C["yellow"] if color is None else color
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(k, k)
    h = s * 0.87
    path = skia.Path()
    path.moveTo(0, -h * 0.62)
    path.lineTo(s / 2, h * 0.38)
    path.lineTo(-s / 2, h * 0.38)
    path.close()
    canvas.drawPath(path, fill(color))
    canvas.drawPath(path, stroke(C["cream"], STROKE * 1.4))
    canvas.drawLine(0, -h * 0.25, 0, h * 0.06, stroke(C["navy"], s * 0.09))
    canvas.drawCircle(0, h * 0.22, s * 0.05, fill(C["navy"]))
    canvas.restore()


def person(canvas, x, y, s, color=None, p=1.0, arms="down", outline=True):
    """Silueta sin rasgos estilo tarjeta de seguridad. (x, y) = pies."""
    color = C["cream"] if color is None else color
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(k, k)
    # piernas
    lp = stroke(color, s * 0.13)
    canvas.drawLine(-s * 0.1, -s * 0.45, -s * 0.12, -s * 0.05, lp)
    canvas.drawLine(s * 0.1, -s * 0.45, s * 0.12, -s * 0.05, lp)
    # brazos
    if arms == "up":
        canvas.drawLine(-s * 0.18, -s * 0.85, -s * 0.36, -s * 1.15, lp)
        canvas.drawLine(s * 0.18, -s * 0.85, s * 0.36, -s * 1.15, lp)
    else:
        canvas.drawLine(-s * 0.2, -s * 0.85, -s * 0.28, -s * 0.5, lp)
        canvas.drawLine(s * 0.2, -s * 0.85, s * 0.28, -s * 0.5, lp)
    # torso
    canvas.drawPath(rrect(-s * 0.2, -s * 0.95, s * 0.2, -s * 0.42, s * 0.13), fill(color))
    # cabeza
    canvas.drawCircle(0, -s * 1.12, s * 0.14, fill(color))
    canvas.restore()


def coin(canvas, x, y, r, color=None, p=1.0, symbol="€", rot=0.0):
    color = C["yellow"] if color is None else color
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(k * max(0.15, abs(math.cos(rot))), k)
    canvas.drawCircle(0, 0, r, fill(color))
    canvas.drawCircle(0, 0, r, stroke())
    canvas.drawCircle(0, 0, r * 0.72, stroke(C["navy"], STROKE_THIN * 0.8))
    size = r * 0.95
    draw_text(canvas, symbol, 0, cap_height(size) / 2, size, C["navy"])
    canvas.restore()


def check(canvas, x, y, s, color=None, p=1.0, width=None):
    color = C["mint"] if color is None else color
    path = skia.Path()
    path.moveTo(x - s * 0.5, y)
    path.lineTo(x - s * 0.15, y + s * 0.35)
    path.lineTo(x + s * 0.5, y - s * 0.35)
    canvas.drawPath(partial(path, p), stroke(color, width or STROKE * 1.5))


def cross(canvas, x, y, s, color=None, p=1.0, width=None):
    color = C["red"] if color is None else color
    a = partial(_line(x - s / 2, y - s / 2, x + s / 2, y + s / 2), clamp(p * 2))
    b = partial(_line(x + s / 2, y - s / 2, x - s / 2, y + s / 2), clamp(p * 2 - 1))
    canvas.drawPath(a, stroke(color, width or STROKE * 1.5))
    canvas.drawPath(b, stroke(color, width or STROKE * 1.5))


def _line(x0, y0, x1, y1):
    p = skia.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)
    return p


def badge(canvas, x, y, s, kind, color=None, p=1.0):
    """Círculo con pictograma dentro (check / cross / warn / euro / clock / plus)."""
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    color = color if color is not None else C["orange"]
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(k, k)
    canvas.drawCircle(0, 0, s, fill(color))
    canvas.drawCircle(0, 0, s, stroke())
    if kind == "check":
        check(canvas, 0, 0, s * 0.9, C["navy"], 1, s * 0.2)
    elif kind == "cross":
        cross(canvas, 0, 0, s * 0.75, C["navy"], 1, s * 0.2)
    elif kind == "clock":
        canvas.drawLine(0, 0, 0, -s * 0.55, stroke(C["navy"], s * 0.16))
        canvas.drawLine(0, 0, s * 0.38, s * 0.12, stroke(C["navy"], s * 0.16))
    elif kind == "excl":
        canvas.drawLine(0, -s * 0.5, 0, s * 0.12, stroke(C["navy"], s * 0.2))
        canvas.drawCircle(0, s * 0.45, s * 0.11, fill(C["navy"]))
    else:
        size = s * 1.1
        draw_text(canvas, kind, 0, cap_height(size) / 2, size, C["navy"])
    canvas.restore()


# --- objetos reducidos a lo esencial -------------------------------------

def icon(canvas, name, x, y, s, p=1.0, color=None, accent_color=None):
    """Pictogramas de línea. s ≈ semilado. Usa crema + un acento plano."""
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    col = C["cream"] if color is None else color
    acc = C["orange"] if accent_color is None else accent_color
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(k, k)
    sp = stroke(col)
    fn = _ICONS.get(name)
    if fn:
        fn(canvas, s, sp, acc, col)
    canvas.restore()


def _i_phone(c, s, sp, acc, col):
    c.drawPath(rrect(-s * 0.52, -s, s * 0.52, s, s * 0.16), fill(C["navy_light"]))
    c.drawPath(rrect(-s * 0.52, -s, s * 0.52, s, s * 0.16), sp)
    c.drawPath(rrect(-s * 0.36, -s * 0.72, s * 0.36, s * 0.62, s * 0.06), fill(acc))
    c.drawLine(-s * 0.12, s * 0.82, s * 0.12, s * 0.82, sp)
    # mini gráfico en pantalla
    path = skia.Path()
    path.moveTo(-s * 0.26, s * 0.35)
    path.lineTo(-s * 0.06, s * 0.05)
    path.lineTo(s * 0.06, s * 0.2)
    path.lineTo(s * 0.26, -s * 0.4)
    c.drawPath(path, stroke(C["navy"], STROKE * 0.9))


def _i_bank(c, s, sp, acc, col):
    roof = skia.Path()
    roof.moveTo(-s, -s * 0.35)
    roof.lineTo(0, -s * 0.95)
    roof.lineTo(s, -s * 0.35)
    roof.close()
    c.drawPath(roof, fill(acc))
    c.drawPath(roof, sp)
    for i in range(4):
        cx = -s * 0.66 + i * s * 0.44
        c.drawLine(cx, -s * 0.18, cx, s * 0.6, stroke(col, STROKE * 1.3))
    c.drawPath(rrect(-s * 1.0, s * 0.72, s * 1.0, s * 0.92, s * 0.06), fill(col))


def _i_doc(c, s, sp, acc, col):
    path = skia.Path()
    path.moveTo(-s * 0.7, -s)
    path.lineTo(s * 0.35, -s)
    path.lineTo(s * 0.7, -s * 0.65)
    path.lineTo(s * 0.7, s)
    path.lineTo(-s * 0.7, s)
    path.close()
    c.drawPath(path, fill(C["navy_light"]))
    c.drawPath(path, sp)
    for i in range(4):
        yy = -s * 0.45 + i * s * 0.32
        c.drawLine(-s * 0.42, yy, s * (0.42 if i < 3 else 0.05), yy, stroke(col, STROKE * 0.8))
    c.drawCircle(s * 0.38, s * 0.62, s * 0.2, fill(acc))


def _i_magnifier(c, s, sp, acc, col):
    c.drawCircle(-s * 0.15, -s * 0.15, s * 0.58, fill(acc))
    c.drawCircle(-s * 0.15, -s * 0.15, s * 0.58, stroke(col, STROKE * 1.2))
    c.drawLine(s * 0.28, s * 0.28, s * 0.8, s * 0.8, stroke(col, STROKE * 2.2))


def _i_lock(c, s, sp, acc, col):
    arc = skia.Path()
    arc.addArc(skia.Rect(-s * 0.45, -s * 0.95, s * 0.45, -s * 0.05), 180, 180)
    c.drawPath(arc, stroke(col, STROKE * 1.4))
    c.drawLine(-s * 0.45, -s * 0.5, -s * 0.45, -s * 0.1, stroke(col, STROKE * 1.4))
    c.drawLine(s * 0.45, -s * 0.5, s * 0.45, -s * 0.1, stroke(col, STROKE * 1.4))
    c.drawPath(rrect(-s * 0.72, -s * 0.1, s * 0.72, s * 0.9, s * 0.14), fill(acc))
    c.drawPath(rrect(-s * 0.72, -s * 0.1, s * 0.72, s * 0.9, s * 0.14), sp)
    c.drawCircle(0, s * 0.35, s * 0.11, fill(C["navy"]))


def _i_hourglass(c, s, sp, acc, col):
    top = skia.Path()
    top.moveTo(-s * 0.55, -s * 0.85)
    top.lineTo(s * 0.55, -s * 0.85)
    top.lineTo(0, 0)
    top.close()
    bot = skia.Path()
    bot.moveTo(-s * 0.55, s * 0.85)
    bot.lineTo(s * 0.55, s * 0.85)
    bot.lineTo(0, 0)
    bot.close()
    sand = skia.Path()
    sand.moveTo(-s * 0.4, s * 0.85)
    sand.lineTo(s * 0.4, s * 0.85)
    sand.lineTo(0, s * 0.4)
    sand.close()
    c.drawPath(sand, fill(acc))
    c.drawPath(top, sp)
    c.drawPath(bot, sp)
    c.drawLine(-s * 0.75, -s * 0.85, s * 0.75, -s * 0.85, stroke(col, STROKE * 1.3))
    c.drawLine(-s * 0.75, s * 0.85, s * 0.75, s * 0.85, stroke(col, STROKE * 1.3))


def _i_gift(c, s, sp, acc, col):
    c.drawPath(rrect(-s * 0.75, -s * 0.2, s * 0.75, s * 0.85, s * 0.1), fill(acc))
    c.drawPath(rrect(-s * 0.75, -s * 0.2, s * 0.75, s * 0.85, s * 0.1), sp)
    c.drawPath(rrect(-s * 0.88, -s * 0.5, s * 0.88, -s * 0.2, s * 0.08), fill(acc))
    c.drawPath(rrect(-s * 0.88, -s * 0.5, s * 0.88, -s * 0.2, s * 0.08), sp)
    c.drawLine(0, -s * 0.5, 0, s * 0.85, sp)
    for sg in (-1, 1):
        lp = skia.Path()
        lp.moveTo(0, -s * 0.5)
        lp.cubicTo(sg * s * 0.2, -s * 1.05, sg * s * 0.65, -s * 0.9, 0, -s * 0.5)
        c.drawPath(lp, sp)


def _i_megaphone(c, s, sp, acc, col):
    body = skia.Path()
    body.moveTo(-s * 0.6, -s * 0.25)
    body.lineTo(s * 0.55, -s * 0.75)
    body.lineTo(s * 0.55, s * 0.75)
    body.lineTo(-s * 0.6, s * 0.25)
    body.close()
    c.drawPath(body, fill(acc))
    c.drawPath(body, sp)
    c.drawPath(rrect(-s * 0.85, -s * 0.28, -s * 0.55, s * 0.28, s * 0.06), fill(col))
    c.drawLine(-s * 0.4, s * 0.3, -s * 0.3, s * 0.75, stroke(col, STROKE * 1.3))


def _i_eye(c, s, sp, acc, col):
    path = skia.Path()
    path.moveTo(-s, 0)
    path.quadTo(0, -s * 0.95, s, 0)
    path.quadTo(0, s * 0.95, -s, 0)
    path.close()
    c.drawPath(path, sp)
    c.drawCircle(0, 0, s * 0.33, fill(acc))
    c.drawCircle(0, 0, s * 0.33, sp)


def _i_globe(c, s, sp, acc, col):
    c.drawCircle(0, 0, s * 0.9, fill(C["navy_light"]))
    c.drawCircle(0, 0, s * 0.9, sp)
    c.drawOval(skia.Rect(-s * 0.4, -s * 0.9, s * 0.4, s * 0.9), sp)
    c.drawLine(-s * 0.9, 0, s * 0.9, 0, sp)
    c.drawLine(-s * 0.78, -s * 0.45, s * 0.78, -s * 0.45, stroke(col, STROKE * 0.8))
    c.drawLine(-s * 0.78, s * 0.45, s * 0.78, s * 0.45, stroke(col, STROKE * 0.8))


def _i_chart(c, s, sp, acc, col):
    c.drawLine(-s * 0.85, -s * 0.85, -s * 0.85, s * 0.85, sp)
    c.drawLine(-s * 0.85, s * 0.85, s * 0.85, s * 0.85, sp)
    path = skia.Path()
    path.moveTo(-s * 0.6, -s * 0.5)
    path.lineTo(-s * 0.25, -s * 0.1)
    path.lineTo(s * 0.05, -s * 0.3)
    path.lineTo(s * 0.65, s * 0.55)
    c.drawPath(path, stroke(acc, STROKE * 1.4))


def _i_wallet(c, s, sp, acc, col):
    c.drawPath(rrect(-s * 0.9, -s * 0.6, s * 0.9, s * 0.7, s * 0.16), fill(C["navy_light"]))
    c.drawPath(rrect(-s * 0.9, -s * 0.6, s * 0.9, s * 0.7, s * 0.16), sp)
    c.drawPath(rrect(s * 0.25, -s * 0.18, s * 0.95, s * 0.28, s * 0.12), fill(acc))
    c.drawPath(rrect(s * 0.25, -s * 0.18, s * 0.95, s * 0.28, s * 0.12), sp)
    c.drawCircle(s * 0.5, s * 0.05, s * 0.06, fill(C["navy"]))


def _i_crown(c, s, sp, acc, col):  # gurú
    path = skia.Path()
    path.moveTo(-s * 0.85, s * 0.5)
    path.lineTo(-s * 0.85, -s * 0.5)
    path.lineTo(-s * 0.4, -s * 0.05)
    path.lineTo(0, -s * 0.7)
    path.lineTo(s * 0.4, -s * 0.05)
    path.lineTo(s * 0.85, -s * 0.5)
    path.lineTo(s * 0.85, s * 0.5)
    path.close()
    c.drawPath(path, fill(acc))
    c.drawPath(path, sp)


def _i_exchange(c, s, sp, acc, col):  # plataforma cripto genérica: hexágono con flechas
    hexp = skia.Path()
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        (hexp.moveTo if i == 0 else hexp.lineTo)(math.cos(a) * s * 0.95, math.sin(a) * s * 0.95)
    hexp.close()
    c.drawPath(hexp, fill(acc))
    c.drawPath(hexp, sp)
    nv = C["navy"]
    arrow(c, -s * 0.4, -s * 0.18, s * 0.4, -s * 0.18, 1, nv, STROKE * 0.9, s * 0.2)
    arrow(c, s * 0.4, s * 0.22, -s * 0.4, s * 0.22, 1, nv, STROKE * 0.9, s * 0.2)


def _i_calendar(c, s, sp, acc, col):
    c.drawPath(rrect(-s * 0.85, -s * 0.7, s * 0.85, s * 0.85, s * 0.14), fill(C["navy_light"]))
    c.drawPath(rrect(-s * 0.85, -s * 0.7, s * 0.85, -s * 0.25, s * 0.14), fill(acc))
    c.drawPath(rrect(-s * 0.85, -s * 0.7, s * 0.85, s * 0.85, s * 0.14), sp)
    c.drawLine(-s * 0.4, -s * 0.9, -s * 0.4, -s * 0.5, sp)
    c.drawLine(s * 0.4, -s * 0.9, s * 0.4, -s * 0.5, sp)
    for i in range(3):
        for j in range(2):
            c.drawCircle(-s * 0.45 + i * s * 0.45, s * 0.1 + j * s * 0.38, s * 0.08, fill(col))


def _i_shield(c, s, sp, acc, col):
    path = skia.Path()
    path.moveTo(0, -s)
    path.lineTo(s * 0.8, -s * 0.65)
    path.cubicTo(s * 0.8, s * 0.2, s * 0.4, s * 0.7, 0, s)
    path.cubicTo(-s * 0.4, s * 0.7, -s * 0.8, s * 0.2, -s * 0.8, -s * 0.65)
    path.close()
    c.drawPath(path, fill(acc))
    c.drawPath(path, sp)
    check(c, 0, 0, s * 0.8, C["navy"], 1, STROKE * 1.3)


def _i_cash(c, s, sp, acc, col):
    for i, off in enumerate((0.18, 0.0)):
        c.save()
        c.translate(s * off, -s * off)
        c.drawPath(rrect(-s, -s * 0.55, s, s * 0.55, s * 0.12), fill(acc if i else C["navy_light"]))
        c.drawPath(rrect(-s, -s * 0.55, s, s * 0.55, s * 0.12), sp)
        c.restore()
    draw_text(c, "€", 0, cap_height(s * 0.8) / 2, s * 0.8, C["navy"])


_ICONS = {
    "phone": _i_phone, "bank": _i_bank, "doc": _i_doc, "magnifier": _i_magnifier,
    "lock": _i_lock, "hourglass": _i_hourglass, "gift": _i_gift, "megaphone": _i_megaphone,
    "eye": _i_eye, "globe": _i_globe, "chart": _i_chart, "wallet": _i_wallet,
    "crown": _i_crown, "exchange": _i_exchange, "calendar": _i_calendar,
    "shield": _i_shield, "cash": _i_cash,
}
ICON_NAMES = sorted(_ICONS)
