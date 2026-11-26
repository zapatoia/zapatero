"""Escenas: el zapato protagonista y las infografías animadas.

Cada escena es una función `fn(c, ctx)` que dibuja en coordenadas de pantalla
(1080x1920) dentro de la zona de contenido. `ctx` aporta el tiempo local, la
duración, los parámetros del guion, los acentos y el acceso al zapato.

Reglas: dos acentos por escena (ctx.a1, ctx.a2); algo cambia cada 2-3 s;
nada fuera de las zonas seguras.
"""
from __future__ import annotations

import math

import skia

from . import style as S
from .style import (C, STROKE, arrow, badge, cap_height, check, clamp, coin, cross,
                    draw_text, ease_in_out, ease_out, ease_out_back, fill, icon, lerp,
                    number_circle, person, pop_in, prog, rrect, stroke, text_width,
                    warning_triangle, with_alpha, wobble)

CX = S.SAFE_CX            # 510: centro del área segura
MINI = dict(x=215, y=1215, scale=0.46)


# ------------------------------------------------------------------ utilidades
def fit_size(text, max_w, size, weight="black", min_size=30):
    while size > min_size and text_width(text, size, weight) > max_w:
        size -= 2
    return size


def card(c, x0, y0, x1, y1, color=None, r=34, p=1.0, outline=True):
    k = ease_out_back(p, 1.8)
    if k <= 0:
        return
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c.save()
    c.translate(cx, cy)
    c.scale(k, k)
    c.translate(-cx, -cy)
    path = rrect(x0, y0, x1, y1, r)
    c.drawPath(path, fill(C["navy_light"] if color is None else color))
    if outline:
        c.drawPath(path, stroke())
    c.restore()


def scaled(c, x, y, k):
    """Context manager-like helper: escala alrededor de (x, y)."""
    c.save()
    c.translate(x, y)
    c.scale(k, k)
    c.translate(-x, -y)


def count_text(v, decimals=0, thousands=True):
    if decimals:
        s = f"{v:.{decimals}f}".replace(".", ",")
    else:
        s = f"{int(round(v)):,}".replace(",", ".") if thousands else str(int(round(v)))
    return s


def label_pill(c, text, x, y, size, bg, fg=None, p=1.0, pad=22):
    k = ease_out_back(p, 2.0)
    if k <= 0:
        return
    w = text_width(text, size, "black") + pad * 2
    h = size * 1.35
    scaled(c, x, y, k)
    path = rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, h / 2)
    c.drawPath(path, fill(bg))
    c.drawPath(path, stroke())
    draw_text(c, text, x, y + cap_height(size) / 2, size, C["navy"] if fg is None else fg)
    c.restore()


def multiline(c, lines, x, y, size, color=None, weight="black", lh=1.12, align="center",
              p=1.0, stagger=0.0, t=None):
    for i, ln in enumerate(lines):
        draw_text(c, ln, x, y + i * size * lh, size, color, weight, align)


def headline(c, ctx, text, y=330, size=64, color=None, t0=0.0):
    """Titular superior pequeño (contexto de la infografía)."""
    if not text:
        return
    p = prog(ctx.t, t0, 0.4)
    if p <= 0:
        return
    size = fit_size(text, 820, size)
    k = ease_out(p)
    c.save()
    c.translate(0, (1 - k) * 30)
    a = int(255 * k)
    col = with_alpha(C["cream"] if color is None else color, k)
    draw_text(c, text, CX, y, size, col, "black")
    c.restore()


# ------------------------------------------------------------------ contexto
class Ctx:
    def __init__(self, video, scene, t_local, T0):
        self.video = video
        self.scene = scene
        self.p = scene.params
        self.t = t_local
        self.T0 = T0
        self.dur = scene.dur
        self.a1 = C[self.p.get("accent", "orange")]
        self.a2 = C[self.p.get("accent2", "yellow")]
        self.index = scene.index

    def at(self, word, default=0.0):
        """Tiempo local en que se dice `word` dentro de este beat."""
        if word is None:
            return default
        if isinstance(word, (int, float)):
            return float(word)
        key = word.lower().strip("*¿?¡!.,:;")
        for w in self.scene.words:
            d = w.display.lower().strip("¿?¡!.,:;«»\"")
            if d.startswith(key):
                return w.start - self.T0
        return default

    def stagger(self, n, start=0.15, end_frac=0.6):
        span = max(0.2, self.dur * end_frac - start)
        return [start + span * i / max(1, n - 1) if n > 1 else start for i in range(n)]

    def shoe(self, x, y, scale, facing=1, appear=0.0, pop=True, overrides=None):
        st = self.video.animator.state(self.T0 + self.t)
        st.facing = facing
        if overrides:
            for k, v in overrides.items():
                setattr(st, k, v)
        k = 1.0
        if pop:
            k = ease_out_back(prog(self.t, appear, 0.45), 2.0)
        if k <= 0:
            return
        # sombra plana
        sw = 300 * scale * k * (1 - min(st.lift, 500) / 700)
        c = self.video.canvas
        c.drawOval(skia.Rect(x - sw + 30 * scale * facing, y - 12 * scale,
                             x + sw + 30 * scale * facing, y + 16 * scale),
                   fill(C["navy_deep"]))
        from .shoe import draw_shoe
        draw_shoe(c, x, y, scale * k, st)

    def mini_shoe(self, appear=0.05, **kw):
        m = dict(MINI)
        m.update(self.p.get("mini", {}))
        m.update(kw)
        if m.get("hide"):
            return
        self.shoe(m["x"], m["y"], m["scale"], m.get("facing", 1), appear)


# ------------------------------------------------------------------ zapato protagonista
HERO = dict(x=440, y=1190, scale=1.06)


def scene_shoe(c, ctx):
    p = ctx.p
    prop = p.get("prop")
    if prop:
        draw_prop(c, ctx, prop)
    first = ctx.scene.first_hero
    ctx.shoe(HERO["x"], HERO["y"], HERO["scale"], p.get("facing", 1), pop=False)


def draw_prop(c, ctx, prop):
    kind = prop.get("kind", "icon")
    t = ctx.t
    t0 = min(ctx.at(prop.get("at"), 0.12), prop.get("max_delay", 0.9))
    p = prog(t, t0, 0.5)
    bob = math.sin((ctx.T0 + t) * 2.2) * 8
    y = prop.get("y", 560) + bob
    x = prop.get("x", CX)
    if kind == "icon":
        k = ease_out_back(p, 1.8)
        if k > 0:
            R = prop.get("plate", 190)
            c.drawCircle(x, y, R * k, fill(C["navy_light"]))
            c.drawCircle(x, y, R * k, stroke())
            c.drawCircle(x, y, (R + 26) * k, stroke(with_alpha(C["cream"], 0.25), 4))
        icon(c, prop["name"], x, y, prop.get("size", 105), prog(t, t0 + 0.08, 0.45),
             accent_color=ctx.a1)
        if prop.get("badge"):
            badge(c, x + 140, y - 130, 50, prop["badge"], ctx.a2, prog(t, t0 + 0.35, 0.4))
    elif kind == "icons":   # varios iconos que aparecen uno tras otro
        names = prop["names"]
        n = len(names)
        gap = prop.get("gap", 270)
        ts = [ctx.at(a, t0 + i * 0.5) for i, a in enumerate(prop.get("ats", [None] * n))]
        for i, name in enumerate(names):
            xx = x + (i - (n - 1) / 2) * gap
            k = ease_out_back(prog(t, ts[i], 0.45), 1.8)
            if k > 0:
                c.drawCircle(xx, y, 125 * k, fill(C["navy_light"]))
                c.drawCircle(xx, y, 125 * k, stroke())
            icon(c, name, xx, y, prop.get("size", 70), prog(t, ts[i] + 0.06, 0.45),
                 accent_color=ctx.a1 if i % 2 == 0 else ctx.a2)
            if i < n - 1 and prop.get("arrows", True):
                arrow(c, xx + 140, y, xx + gap - 140, y, prog(t, ts[i + 1] - 0.2, 0.3),
                      C["cream"], STROKE, 22)
    elif kind == "sign":    # cartel con texto
        lines = prop["lines"]
        size = prop.get("size", 92)
        maxw = max(text_width(l, size) for l in lines)
        size = fit_size(max(lines, key=len), 760, size) if maxw > 760 else size
        maxw = max(text_width(l, size) for l in lines)
        w = maxw + 110
        h = len(lines) * size * 1.12 + 80
        k = ease_out_back(p, 2.0)
        if k <= 0:
            return
        rot = prop.get("rot", -3) + wobble(ctx.T0 + t, 4, 1.2, 1.5)
        c.save()
        c.translate(x, y)
        c.rotate(rot * k)
        c.scale(k, k)
        path = rrect(-w / 2, -h / 2, w / 2, h / 2, 30)
        c.drawPath(path, fill(ctx.a1))
        c.drawPath(path, stroke())
        y0 = -h / 2 + 40 + cap_height(size)
        for i, ln in enumerate(lines):
            col = C["navy"]
            draw_text(c, ln, 0, y0 + i * size * 1.12, size, col)
        c.restore()
    elif kind == "bubble":  # bocadillo de pensamiento con icono o texto
        k = ease_out_back(p, 2.0)
        if k <= 0:
            return
        r = prop.get("r", 190)
        c.save()
        c.translate(x, y)
        c.scale(k, k)
        c.drawCircle(0, 0, r, fill(C["navy_light"]))
        c.drawCircle(0, 0, r, stroke())
        for i, (dx, dy, rr) in enumerate(((150, 230, 30), (190, 300, 18))):
            c.drawCircle(dx * 0.6, dy, rr, fill(C["navy_light"]))
            c.drawCircle(dx * 0.6, dy, rr, stroke())
        if prop.get("name"):
            icon(c, prop["name"], 0, 0, r * 0.55, 1, accent_color=ctx.a1)
        if prop.get("text"):
            size = fit_size(prop["text"], r * 1.6, 90)
            draw_text(c, prop["text"], 0, cap_height(size) / 2, size, ctx.a2)
        c.restore()
    elif kind == "stamp":
        stamp(c, ctx, prop["lines"], x, y, t0, prop.get("size", 110))


def stamp(c, ctx, lines, x, y, t0, size=110, color=None):
    t = ctx.t
    u = prog(t, t0, 0.35)
    if u <= 0:
        return
    color = ctx.a1 if color is None else color
    k = lerp(2.2, 1.0, ease_out(u)) if u < 1 else 1 + 0.06 * math.exp(-8 * (t - t0 - 0.35)) * math.cos(20 * (t - t0 - 0.35))
    size = min(size, *[fit_size(l, 760, size) for l in lines])
    w = max(text_width(l, size) for l in lines) + 90
    h = len(lines) * size * 1.08 + 70
    c.save()
    c.translate(x, y)
    c.rotate(-6)
    c.scale(k, k)
    alpha = clamp(u * 2)
    path = rrect(-w / 2, -h / 2, w / 2, h / 2, 26)
    c.drawPath(path, fill(with_alpha(C["navy"], alpha)))
    c.drawPath(path, stroke(with_alpha(color, alpha), STROKE * 1.5))
    y0 = -h / 2 + 35 + cap_height(size)
    for i, ln in enumerate(lines):
        draw_text(c, ln, 0, y0 + i * size * 1.08, size, with_alpha(color, alpha))
    c.restore()


# ------------------------------------------------------------------ cifra grande
def scene_big_number(c, ctx):
    p, t = ctx.p, ctx.t
    value = float(p["value"])
    suffix = p.get("suffix", "")
    prefix = p.get("prefix", "")
    t0 = ctx.at(p.get("at"), 0.05)
    count_dur = p.get("count_dur", 0.9)
    u = ease_out(prog(t, t0, count_dur))
    v = value * u
    cy = p.get("y", 640)
    R = 265
    # anillo de porcentaje
    if p.get("ring", suffix.strip() == "%"):
        kr = ease_out_back(prog(t, t0 - 0.05, 0.4), 1.6)
        c.save()
        c.translate(CX, cy)
        c.scale(kr, kr)
        c.drawCircle(0, 0, R, stroke(with_alpha(C["cream"], 0.16), 44))
        arc = skia.Path()
        arc.addArc(skia.Rect(-R, -R, R, R), -90, 360 * (v / 100.0))
        c.drawPath(arc, stroke(ctx.a1, 44))
        c.drawCircle(0, 0, R + 28, stroke(C["cream"], 5))
        c.drawCircle(0, 0, R - 28, stroke(C["cream"], 5))
        c.restore()
    txt = prefix + count_text(v, p.get("decimals", 0)) + suffix
    size = p.get("size", 230)
    full = prefix + count_text(value, p.get("decimals", 0)) + suffix
    size = fit_size(full, 440 if p.get("ring", suffix.strip() == "%") else 820, size)
    kpop = 1 + 0.08 * math.exp(-7 * max(0, t - t0 - count_dur)) * (t > t0 + count_dur)
    scaled(c, CX, cy, kpop * ease_out_back(prog(t, t0, 0.3), 2))
    draw_text(c, txt, CX, cy + cap_height(size) / 2, size, C["cream"], outline=0)
    c.restore()
    # etiqueta debajo (pastilla de acento) y fuente arriba
    if p.get("label"):
        tl = ctx.at(p.get("label_at"), t0 + count_dur * 0.8)
        label_pill(c, p["label"], CX, cy + R + 105, 60, ctx.a2, p=prog(t, tl, 0.4))
    if p.get("source"):
        headline(c, ctx, p["source"], y=cy - R - 75, size=42, color=with_alpha(C["cream"], 0.75),
                 t0=t0 + 0.2)
    ctx.mini_shoe(appear=ctx.p.get("mini_at", 0.25))


# ------------------------------------------------------------------ rejilla de personas
def scene_people(c, ctx):
    p, t = ctx.p, ctx.t
    cols, rows = p.get("cols", 10), p.get("rows", 5)
    n = cols * rows
    hi = int(round(n * p["percent"] / 100.0))
    t0 = ctx.at(p.get("at"), 0.1)
    gx, gy = 78, 120
    x0 = CX - (cols - 1) * gx / 2
    y0 = p.get("y", 520)
    headline(c, ctx, p.get("title"), y=y0 - 140, size=60, t0=0)
    fill_t = ctx.at(p.get("fill_at"), t0 + 0.6)
    fill_dur = p.get("fill_dur", 1.4)
    for i in range(n):
        r, col = divmod(i, cols)
        x = x0 + col * gx
        y = y0 + r * gy + 50
        app = t0 + (r * cols + col) * 0.012
        lit = i < hi and t >= fill_t + fill_dur * (i / max(1, hi))
        color = ctx.a1 if lit else with_alpha(C["cream"], 0.85)
        if lit:
            dt = t - (fill_t + fill_dur * (i / max(1, hi)))
            jump = 1 + 0.25 * math.exp(-10 * dt)
            person(c, x, y, 82 * jump, color, 1)
        else:
            person(c, x, y, 82, color, prog(t, app, 0.35))
    # contador
    shown = min(hi, int(hi * clamp((t - fill_t) / fill_dur))) if t > fill_t else 0
    pct = round(100 * shown / n)
    yb = y0 + rows * gy + 130
    if t > fill_t:
        draw_text(c, f"{pct} %", CX, yb, 120, ctx.a1)
        if p.get("label"):
            label_pill(c, p["label"], CX, yb + 85, 50, ctx.a2, p=prog(t, fill_t + fill_dur, 0.4))
    ctx.mini_shoe(appear=0.3, hide=p.get("hide_mini", True))


# ------------------------------------------------------------------ barras
def scene_bars(c, ctx):
    p, t = ctx.p, ctx.t
    bars = p["bars"]
    n = len(bars)
    title = p.get("title")
    headline(c, ctx, title, y=330, size=58)
    base_y = p.get("base_y", 1040)
    max_h = p.get("max_h", 560)
    bw = min(190, 640 / n)
    gap = (760 - bw * n) / max(1, n - 1) if n > 1 else 0
    x_start = CX - (bw * n + gap * (n - 1)) / 2
    vmax = p.get("max", 100)
    c.drawLine(x_start - 40, base_y, x_start + bw * n + gap * (n - 1) + 40, base_y, stroke())
    for i, b in enumerate(bars):
        t0 = ctx.at(b.get("at"), 0.2 + i * 0.55)
        u = ease_out_back(prog(t, t0, 0.7), 1.2)
        x = x_start + i * (bw + gap)
        if isinstance(b["value"], (list, tuple)):     # rango (p.ej. 74-89 %)
            lo, hi = b["value"]
            h_lo = max_h * lo / vmax * u
            h_hi = max_h * hi / vmax * u
            col = C[b.get("color", "orange")] if b.get("color") else ctx.a1
            if h_hi > 1:
                c.drawPath(rrect(x, base_y - h_hi, x + bw, base_y, 22), fill(with_alpha(col, 0.35)))
                c.drawPath(rrect(x, base_y - h_lo, x + bw, base_y, 22), fill(col))
                c.drawPath(rrect(x, base_y - h_hi, x + bw, base_y, 22), stroke())
                c.drawLine(x + 10, base_y - h_lo, x + bw - 10, base_y - h_lo, stroke(C["cream"], 5))
            vtxt = f"{int(round(lo * clamp(u)))}-{int(round(hi * clamp(u)))} %"
            vh = h_hi
        else:
            v = b["value"]
            h = max_h * v / vmax * u
            col = C[b["color"]] if b.get("color") else (ctx.a1 if i % 2 == 0 else ctx.a2)
            if h > 1:
                c.drawPath(rrect(x, base_y - h, x + bw, base_y, 22), fill(col))
                c.drawPath(rrect(x, base_y - h, x + bw, base_y, 22), stroke())
            vtxt = f"{int(round(v * clamp(u)))}{b.get('suffix', ' %')}"
            vh = h
        if u > 0.05:
            vs = fit_size(vtxt, bw + gap * 0.9, 74)
            draw_text(c, vtxt, x + bw / 2, base_y - vh - 30, vs, C["cream"])
            lab = b.get("label", "")
            for j, ln in enumerate(lab.split("\n")):
                ls = fit_size(ln, bw + gap * 0.8, 40, "bold")
                draw_text(c, ln, x + bw / 2, base_y + 60 + j * 46, ls,
                          with_alpha(C["cream"], 0.85), "bold")
    ctx.mini_shoe(appear=0.3, hide=p.get("hide_mini", True))


# ------------------------------------------------------------------ apalancamiento
def scene_lever(c, ctx):
    p, t = ctx.p, ctx.t
    t_coin = ctx.at(p.get("at_coin"), 0.1)
    t_mult = ctx.at(p.get("at_mult"), 1.0)
    headline(c, ctx, p.get("title", "APALANCAMIENTO"), y=330, size=62)
    # balancín
    fy = 900
    u = ease_out_back(prog(t, t_mult, 0.6), 1.4)
    ang = lerp(8, -10, clamp(u))
    # fulcro (triángulo)
    tri = skia.Path()
    tri.moveTo(CX, fy)
    tri.lineTo(CX + 60, fy + 100)
    tri.lineTo(CX - 60, fy + 100)
    tri.close()
    c.drawPath(tri, fill(ctx.a2))
    c.drawPath(tri, stroke())
    c.drawLine(CX - 330, fy + 104, CX + 330, fy + 104, stroke())
    c.save()
    c.translate(CX, fy)
    c.rotate(ang)
    c.drawPath(rrect(-370, -14, 370, 14, 14), fill(C["navy_light"]))
    c.drawPath(rrect(-370, -14, 370, 14, 14), stroke())
    # moneda (tu dinero) a la izquierda
    pc = prog(t, t_coin, 0.45)
    drop = (1 - ease_out_back(pc, 1.5)) * -300
    coin(c, -280, -84 + drop, 66, ctx.a2, 1 if pc > 0 else 0)
    if pc > 0:
        draw_text(c, p.get("left", "100 €"), -280, -190 + drop, 62, C["cream"])
    # bloque grande (lo que mueves) a la derecha
    if u > 0:
        bh = 260 * clamp(u)
        c.drawPath(rrect(140, -14 - bh, 380, -14, 22), fill(ctx.a1))
        c.drawPath(rrect(140, -14 - bh, 380, -14, 22), stroke())
        for i in range(4):
            yy = -14 - bh * (i + 1) / 5
            c.drawLine(170, yy, 350, yy, stroke(C["navy"], 6))
        size = fit_size(p.get("right", "1.000 €"), 230, 64)
        draw_text(c, p.get("right", "1.000 €"), 260, -14 - bh - 40, size, C["cream"])
    c.restore()
    # multiplicador
    if t > t_mult:
        label_pill(c, p.get("mult", "×10"), CX, 610, 84, ctx.a1, p=prog(t, t_mult + 0.1, 0.45))
    ctx.mini_shoe(appear=0.4, hide=p.get("hide_mini", False),
                  **p.get("mini", {"x": 200, "y": 1230}))


# ------------------------------------------------------------------ sube / baja
def scene_updown(c, ctx):
    p, t = ctx.p, ctx.t
    rows = p["rows"]  # [{dir:'up', pct:'+5 %', money:'+50 €', at:'sube'}, ...]
    headline(c, ctx, p.get("title"), y=330, size=58)
    for i, r in enumerate(rows):
        t0 = ctx.at(r.get("at"), 0.15 + i * 1.2)
        pr = prog(t, t0, 0.5)
        y = 520 + i * 300
        up = r["dir"] == "up"
        col = C["mint"] if up else C["red"]
        card(c, 110, y - 120, 910, y + 120, p=pr)
        if pr <= 0:
            continue
        k = ease_out_back(pr, 1.6)
        scaled(c, CX, y, k)
        # flecha de precio
        ax = 220
        if up:
            arrow(c, ax - 50, y + 60, ax + 50, y - 60, prog(t, t0 + 0.1, 0.4), col, STROKE * 1.6, 34)
        else:
            arrow(c, ax - 50, y - 60, ax + 50, y + 60, prog(t, t0 + 0.1, 0.4), col, STROKE * 1.6, 34)
        draw_text(c, r["pct"], 300, y + cap_height(84) / 2, 84, C["cream"], align="left")
        arrow(c, 540, y, 620, y, prog(t, t0 + 0.3, 0.3), C["cream"], STROKE, 20)
        tm = t0 + 0.45
        if t > tm:
            km = ease_out_back(prog(t, tm, 0.35), 2.4)
            scaled(c, 760, y, km)
            size = fit_size(r["money"], 250, 92)
            draw_text(c, r["money"], 770, y + cap_height(size) / 2, size, col)
            c.restore()
        c.restore()
        if r.get("note") and t > tm + 0.4:
            label_pill(c, r["note"], 700, y + 140, 44, ctx.a2, p=prog(t, tm + 0.4, 0.35))
    ctx.mini_shoe(appear=0.3, hide=p.get("hide_mini", False))


# ------------------------------------------------------------------ aviso tipo broker
def scene_warning(c, ctx):
    p, t = ctx.p, ctx.t
    t0 = ctx.at(p.get("at"), 0.1)
    y0, y1 = 360, 1020
    card(c, 100, y0, 920, y1, color=C["navy_light"], p=prog(t, t0, 0.5))
    pr = prog(t, t0, 0.5)
    if pr <= 0:
        return
    k = ease_out_back(pr, 1.6)
    scaled(c, CX, (y0 + y1) / 2, k)
    # cabecera con triángulo
    c.drawPath(rrect(100, y0, 920, y0 + 150, 34), fill(ctx.a2))
    c.drawRect(skia.Rect(100, y0 + 110, 920, y0 + 150), fill(ctx.a2))
    c.drawLine(100, y0 + 150, 920, y0 + 150, stroke())
    c.drawPath(rrect(100, y0, 920, y1, 34), stroke())
    tri_t = t0 + 0.2
    shake = math.sin(t * 40) * 6 * math.exp(-4 * max(0, t - tri_t)) if t > tri_t else 0
    c.save()
    c.translate(shake, 0)
    warning_triangle(c, 200, y0 + 82, 110, C["navy"], prog(t, tri_t, 0.4))
    c.restore()
    title = p.get("title", "AVISO")
    ts = fit_size(title, 560, 62)
    draw_text(c, title, 270, y0 + 75 + cap_height(ts) / 2, ts, C["navy"], align="left")
    # cifra / rango
    big = p.get("big", "74-89 %")
    tb = ctx.at(p.get("big_at"), t0 + 0.6)
    if t > tb:
        kb = ease_out_back(prog(t, tb, 0.4), 2.2)
        scaled(c, CX, y0 + 330, kb)
        bs = fit_size(big, 740, 170)
        draw_text(c, big, CX, y0 + 330 + cap_height(bs) / 2, bs, ctx.a1)
        c.restore()
    body = p.get("body", [])
    tbody = ctx.at(p.get("body_at"), tb + 0.4)
    for i, ln in enumerate(body):
        pp = prog(t, tbody + i * 0.18, 0.35)
        if pp <= 0:
            continue
        a = ease_out(pp)
        bs = fit_size(ln, 740, 50, "bold")
        draw_text(c, ln, CX, y0 + 480 + i * 62 + (1 - a) * 20, bs, with_alpha(C["cream"], a), "bold")
    c.restore()
    ctx.mini_shoe(appear=0.5, hide=p.get("hide_mini", False), x=200, y=1240)


# ------------------------------------------------------------------ línea de tiempo
def scene_timeline(c, ctx):
    p, t = ctx.p, ctx.t
    pts = p["points"]
    n = len(pts)
    headline(c, ctx, p.get("title"), y=330, size=58)
    x0, x1 = 150, 870
    y = p.get("y", 700)
    t_line = 0.1
    line_p = ease_in_out(prog(t, t_line, max(0.6, ctx.dur * 0.5)))
    c.drawLine(x0, y, lerp(x0, x1, line_p), y, stroke(C["cream"], STROKE))
    if line_p > 0.97:
        arrow(c, x1 - 1, y, x1 + 20, y, 1, C["cream"], STROKE, 26)
    for i, pt in enumerate(pts):
        fx = (i + 0.5) / n
        x = lerp(x0, x1, fx)
        t0 = ctx.at(pt.get("at"), t_line + max(0.6, ctx.dur * 0.5) * fx)
        pr = prog(t, t0, 0.45)
        if pr <= 0:
            continue
        col = C[pt["color"]] if pt.get("color") else (ctx.a1 if i % 2 == 0 else ctx.a2)
        hl = pt.get("highlight", False)
        r = 34 if not hl else 44
        k = ease_out_back(pr, 2.2)
        c.drawCircle(x, y, r * k, fill(col))
        c.drawCircle(x, y, r * k, stroke())
        up = i % 2 == 0
        a = ease_out(pr)
        ls = fit_size(pt["label"], 260, 58)
        yy = y - 80 if up else y + 80 + cap_height(ls)
        draw_text(c, pt["label"], x, yy + (1 - a) * (20 if up else -20), ls, with_alpha(C["cream"], a))
        for j, ln in enumerate(pt.get("text", "").split("\n")):
            if not ln:
                continue
            ts = fit_size(ln, 280, 40, "bold")
            ty = (yy - 70 - j * 46) if up else (yy + 56 + j * 46)
            if up:
                ty = yy - 70 - (len(pt.get("text", "").split("\n")) - 1 - j) * 46
            draw_text(c, ln, x, ty, ts, with_alpha(col, a), "bold")
    ctx.mini_shoe(appear=0.4, hide=p.get("hide_mini", False))


# ------------------------------------------------------------------ lista numerada / señales
def scene_checklist(c, ctx):
    p, t = ctx.p, ctx.t
    items = p["items"]
    mode = p.get("mode", "numbers")  # numbers | flags | checks
    n = len(items)
    headline(c, ctx, p.get("title"), y=p.get("title_y", 330), size=58)
    top = p.get("top", 420)
    row_h = min(170, (1080 - top) / max(1, n))
    for i, it in enumerate(items):
        t0 = ctx.at(it.get("at"), 0.15 + i * (ctx.dur * 0.7 / max(1, n)))
        pr = prog(t, t0, 0.45)
        if pr <= 0:
            continue
        y = top + i * row_h + row_h / 2
        a = ease_out(pr)
        x_off = (1 - ease_out_back(pr, 1.4)) * 120
        c.save()
        c.translate(x_off, 0)
        box = rrect(100, y - row_h * 0.42, 920, y + row_h * 0.42, 28)
        c.drawPath(box, fill(C["navy_light"]))
        c.drawPath(box, stroke(with_alpha(C["cream"], a)))
        if mode == "numbers":
            number_circle(c, 180, y, 46, i + 1, ctx.a1 if i % 2 == 0 else ctx.a2, pr)
        elif mode == "flags":
            badge(c, 180, y, 46, "cross", C["red"], pr)
        else:
            badge(c, 180, y, 46, "check", C["mint"], pr)
        txt = it["text"]
        lines = txt.split("\n")
        size = min(fit_size(l, 560, 56) for l in lines)
        if it.get("icon"):
            icon(c, it["icon"], 850, y, 42, prog(t, t0 + 0.15, 0.4),
                 accent_color=ctx.a2 if i % 2 == 0 else ctx.a1)
        ty = y + cap_height(size) / 2 - (len(lines) - 1) * size * 0.55
        for j, ln in enumerate(lines):
            draw_text(c, ln, 260, ty + j * size * 1.1, size, with_alpha(C["cream"], a), align="left")
        if it.get("done_at") or mode == "numbers" and it.get("check"):
            td = ctx.at(it.get("done_at"), t0 + 0.8)
            if t > td:
                badge(c, 880, y, 34, "check", C["mint"], prog(t, td, 0.35))
        c.restore()
    ctx.mini_shoe(appear=0.4, hide=p.get("hide_mini", True))


# ------------------------------------------------------------------ flujo de información
def scene_flow(c, ctx):
    p, t = ctx.p, ctx.t
    nodes = p["nodes"]   # [{icon, label, at}]
    n = len(nodes)
    headline(c, ctx, p.get("title"), y=330, size=58)
    vertical = p.get("vertical", n > 2)
    pos = []
    for i in range(n):
        if vertical:
            pos.append((CX, 500 + i * (560 / max(1, n - 1))))
        else:
            pos.append((CX + (i - (n - 1) / 2) * 400, p.get("y", 700)))
    times = [ctx.at(nd.get("at"), 0.15 + i * 0.9) for i, nd in enumerate(nodes)]
    for i in range(n - 1):
        (xa, ya), (xb, yb) = pos[i], pos[i + 1]
        ta = times[i + 1] - 0.35
        pa = prog(t, ta, 0.4)
        if pa <= 0:
            continue
        if vertical:
            arrow(c, xa, ya + 110, xb, yb - 110, pa, C["cream"], STROKE, 26)
        else:
            arrow(c, xa + 130, ya, xb - 130, yb, pa, C["cream"], STROKE, 26, bend=-0.15)
        # paquetes de datos viajando por la flecha
        if pa >= 1 and p.get("packets", True):
            for k in range(3):
                ph = ((ctx.T0 + t) * 0.9 + k / 3) % 1
                if vertical:
                    px, py = xa, lerp(ya + 110, yb - 130, ph)
                else:
                    px, py = lerp(xa + 130, xb - 150, ph), lerp(ya, yb, ph) - math.sin(ph * math.pi) * 0.15 * 260
                c.drawPath(rrect(px - 20, py - 14, px + 20, py + 14, 6), fill(ctx.a2))
                c.drawPath(rrect(px - 20, py - 14, px + 20, py + 14, 6), stroke(C["cream"], 4))
    chips = p.get("chips", [])
    if chips and n >= 2 and not vertical:
        (xa, ya), (xb, yb) = pos[0], pos[1]
        tc = times[1] + 0.2
        for k, ch in enumerate(chips):
            label_pill(c, ch, (xa + xb) / 2, ya - 300 + k * 85, 44,
                       ctx.a1 if k == 0 else ctx.a2, p=prog(t, tc + k * 0.3, 0.4))
    for i, nd in enumerate(nodes):
        x, y = pos[i]
        pr = prog(t, times[i], 0.45)
        if pr <= 0:
            continue
        c.drawCircle(x, y, 112 * ease_out_back(pr, 2), fill(C["navy_light"]))
        c.drawCircle(x, y, 112 * ease_out_back(pr, 2), stroke())
        icon(c, nd["icon"], x, y, 62, pr, accent_color=ctx.a1 if i % 2 == 0 else ctx.a2)
        if nd.get("label"):
            ls = fit_size(nd["label"], 380, 50)
            lx = x + 150 if vertical else x
            ly = y + cap_height(ls) / 2 if vertical else y + 170
            draw_text(c, nd["label"], lx, ly, ls, C["cream"], align="left" if vertical else "center")
        if nd.get("badge"):
            badge(c, x + 85, y - 85, 34, nd["badge"], ctx.a1, prog(t, times[i] + 0.3, 0.35))
    ctx.mini_shoe(appear=0.4, hide=p.get("hide_mini", vertical))


# ------------------------------------------------------------------ red de países
def scene_network(c, ctx):
    p, t = ctx.p, ctx.t
    n = p.get("n", 10)
    cy = p.get("y", 690)
    R = 300
    t0 = ctx.at(p.get("at"), 0.1)
    headline(c, ctx, p.get("title"), y=300, size=58, t0=t0)
    pts = [(CX + R * math.cos(-math.pi / 2 + i * 2 * math.pi / n),
            cy + R * math.sin(-math.pi / 2 + i * 2 * math.pi / n)) for i in range(n)]
    # conexiones automáticas: se dibujan progresivamente
    tl = ctx.at(p.get("links_at"), t0 + 0.7)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if (j - i) in (1, 3, 5)]
    for k, (i, j) in enumerate(pairs):
        pp = prog(t, tl + k * 0.035, 0.35)
        if pp <= 0:
            continue
        (xa, ya), (xb, yb) = pts[i], pts[j]
        path = skia.Path()
        path.moveTo(xa, ya)
        path.lineTo(xb, yb)
        c.drawPath(S.partial(path, ease_out(pp)), stroke(with_alpha(C["cream"], 0.35), 5))
        if pp >= 1 and k % 3 == 0:
            ph = ((ctx.T0 + t) * 0.7 + k * 0.13) % 1
            c.drawCircle(lerp(xa, xb, ph), lerp(ya, yb, ph), 10, fill(ctx.a2))
    for i, (x, y) in enumerate(pts):
        pr = prog(t, t0 + i * 0.05, 0.4)
        c.drawCircle(x, y, 46 * ease_out_back(pr, 2), fill(ctx.a1 if i % 3 else ctx.a2))
        c.drawCircle(x, y, 46 * ease_out_back(pr, 2), stroke())
        if pr > 0:
            icon(c, "doc", x, y, 20, pr, C["navy"], C["navy"])
    # centro: etiqueta
    if p.get("center"):
        tc = ctx.at(p.get("center_at"), tl + 0.4)
        k = ease_out_back(prog(t, tc, 0.45), 2)
        if k > 0:
            c.drawCircle(CX, cy, 150 * k, fill(C["navy_light"]))
            c.drawCircle(CX, cy, 150 * k, stroke())
            lines = p["center"].split("\n")
            for j, ln in enumerate(lines):
                sz = fit_size(ln, 250 * k + 1, 74 if j == 0 else 44)
                draw_text(c, ln, CX, cy + cap_height(sz) / 2 + (j - (len(lines) - 1) / 2) * 70 * k,
                          sz * k if k < 1 else sz, ctx.a2 if j == 0 else C["cream"])
    if p.get("label"):
        tlb = ctx.at(p.get("label_at"), tl + 0.8)
        label_pill(c, p["label"], CX, cy + R + 130, 52, ctx.a1, p=prog(t, tlb, 0.4))
    ctx.mini_shoe(appear=0.4, hide=p.get("hide_mini", True))


# ------------------------------------------------------------------ documento + umbral
def scene_threshold(c, ctx):
    p, t = ctx.p, ctx.t
    t0 = ctx.at(p.get("at"), 0.1)
    # documento
    pd = prog(t, t0, 0.5)
    dx, dy = CX, 560
    if pd > 0:
        k = ease_out_back(pd, 1.8)
        c.save()
        c.translate(dx, dy)
        c.rotate(-4 * k + wobble(ctx.T0 + t, 2, 1.0, 1.3))
        c.scale(k, k)
        w, h = 520, 330
        path = skia.Path()
        path.moveTo(-w / 2, -h / 2)
        path.lineTo(w / 2 - 70, -h / 2)
        path.lineTo(w / 2, -h / 2 + 70)
        path.lineTo(w / 2, h / 2)
        path.lineTo(-w / 2, h / 2)
        path.close()
        c.drawPath(path, fill(C["navy_light"]))
        c.drawPath(path, stroke())
        c.drawPath(rrect(-w / 2, -h / 2, w / 2 - 70, -h / 2 + 100, 0), fill(ctx.a1))
        c.drawPath(path, stroke())
        title = p.get("doc_title", "MODELO 721")
        ts = fit_size(title, w - 120, 70)
        draw_text(c, title, -35, -h / 2 + 50 + cap_height(ts) / 2, ts, C["navy"])
        sub = p.get("doc_sub", [])
        for i, ln in enumerate(sub):
            ss = fit_size(ln, w - 80, 40, "bold")
            draw_text(c, ln, 0, -h / 2 + 170 + i * 52, ss, C["cream"], "bold")
        c.restore()
    # medidor con umbral
    tm = ctx.at(p.get("meter_at"), t0 + 0.7)
    pm = prog(t, tm, 0.4)
    if pm > 0:
        y = 930
        x0, x1 = 140, 880
        thr = p.get("threshold_pos", 0.62)
        a = ease_out(pm)
        c.drawPath(rrect(x0, y - 34, x1, y + 34, 34), fill(with_alpha(C["navy_light"], a)))
        fill_u = ease_in_out(prog(t, tm + 0.3, p.get("fill_dur", 1.6))) * p.get("fill_to", 0.85)
        if fill_u > 0.02:
            col = ctx.a2 if fill_u < thr else ctx.a1
            c.drawPath(rrect(x0, y - 34, lerp(x0, x1, fill_u), y + 34, 34), fill(col))
        c.drawPath(rrect(x0, y - 34, x1, y + 34, 34), stroke(with_alpha(C["cream"], a)))
        xt = lerp(x0, x1, thr)
        c.drawLine(xt, y - 70, xt, y + 70, stroke(C["cream"], STROKE))
        lab = p.get("threshold_label", "50.000 €")
        ls = fit_size(lab, 400, 64)
        draw_text(c, lab, xt, y - 95, ls, C["cream"])
        if fill_u >= thr:
            badge(c, xt + 150, y + 120, 44, "excl", ctx.a1, prog(t, tm + 0.3 + p.get("fill_dur", 1.6) * thr / p.get("fill_to", 0.85), 0.35))
            if p.get("over_label"):
                draw_text(c, p["over_label"], xt - 40, y + 140, 46, ctx.a1, "black", align="right")
    ctx.mini_shoe(appear=0.4, hide=p.get("hide_mini", True))


# ------------------------------------------------------------------ búsqueda en registro
def scene_search(c, ctx):
    p, t = ctx.p, ctx.t
    t0 = ctx.at(p.get("at"), 0.1)
    headline(c, ctx, p.get("title"), y=330, size=58)
    pc = prog(t, t0, 0.45)
    card(c, 100, 400, 920, 1060, p=pc)
    if pc <= 0:
        return
    k = ease_out_back(pc, 1.6)
    scaled(c, CX, 730, k)
    # barra superior tipo navegador (genérica)
    c.drawPath(rrect(100, 400, 920, 500, 34), fill(C["navy"]))
    c.drawRect(skia.Rect(100, 460, 920, 500), fill(C["navy"]))
    for i, col in enumerate((ctx.a1, ctx.a2, C["cream"])):
        c.drawCircle(160 + i * 50, 450, 14, fill(col))
    c.drawLine(100, 500, 920, 500, stroke())
    c.drawPath(rrect(100, 400, 920, 1060, 34), stroke())
    url = p.get("url", "")
    if url:
        draw_text(c, url, 860, 462, 38, with_alpha(C["cream"], 0.7), "bold", align="right")
    # campo de búsqueda con texto que se escribe
    query = p.get("query", "Nombre de la entidad")
    tq = ctx.at(p.get("type_at"), t0 + 0.35)
    nchar = int(len(query) * clamp((t - tq) / p.get("type_dur", 0.9)))
    c.drawPath(rrect(150, 545, 870, 645, 50), fill(C["navy"]))
    c.drawPath(rrect(150, 545, 870, 645, 50), stroke())
    icon(c, "magnifier", 215, 595, 28, 1, accent_color=ctx.a1)
    qs = fit_size(query, 560, 46, "bold")
    draw_text(c, query[:nchar], 265, 595 + cap_height(qs) / 2, qs, C["cream"], "bold", align="left")
    if (t * 2) % 1 < 0.5 and nchar < len(query):
        x = 265 + text_width(query[:nchar], qs, "bold") + 6
        c.drawLine(x, 570, x, 620, stroke(C["cream"], 5))
    # línea de escaneo mientras se busca (nada quieto)
    res = p.get("results", [])
    t_last = max([ctx.at(r.get("at"), 99) for r in res] or [0])
    if t < t_last + 0.5:
        ph = ((ctx.T0 + t) * 0.6) % 1
        ys = lerp(680, 1030, ease_in_out(ph))
        c.drawPath(rrect(130, ys - 4, 890, ys + 4, 4), fill(with_alpha(ctx.a1, 0.55)))
    # resultados
    for i, r in enumerate(res):
        tr = ctx.at(r.get("at"), tq + 1.0 + i * 0.9)
        pr = prog(t, tr, 0.4)
        if pr <= 0:
            continue
        y = 735 + i * 150
        a = ease_out(pr)
        c.drawPath(rrect(150, y - 58, 870, y + 58, 28), fill(with_alpha(C["navy"], a)))
        ok = r.get("ok", True)
        badge(c, 215, y, 38, "check" if ok else "cross", C["mint"] if ok else C["red"], pr)
        lines = r["text"].split("\n")
        rs = min(fit_size(l, 560, 44, "bold") for l in lines)
        for j, ln in enumerate(lines):
            draw_text(c, ln, 275, y + cap_height(rs) / 2 + (j - (len(lines) - 1) / 2) * rs * 1.15,
                      rs, with_alpha(C["cream"], a), "bold", align="left")
    c.restore()
    ctx.mini_shoe(appear=0.5, hide=p.get("hide_mini", True))


# ------------------------------------------------------------------ sello
def scene_stamp(c, ctx):
    p, t = ctx.p, ctx.t
    t0 = ctx.at(p.get("at"), 0.15)
    if p.get("icon"):
        k = ease_out_back(prog(t, 0.05, 0.45), 1.8)
        bob = math.sin((ctx.T0 + t) * 2.2) * 8
        if k > 0:
            c.drawCircle(CX, 470 + bob, 170 * k, fill(C["navy_light"]))
            c.drawCircle(CX, 470 + bob, 170 * k, stroke())
        icon(c, p["icon"], CX, 470 + bob, 95, prog(t, 0.12, 0.45), accent_color=ctx.a2)
    stamp(c, ctx, p["lines"], CX, p.get("y", 780), t0, p.get("size", 120))
    ctx.mini_shoe(appear=0.2, hide=p.get("hide_mini", False))


# ------------------------------------------------------------------ cierre
def scene_outro(c, ctx):
    p, t = ctx.p, ctx.t
    lines = p.get("lines", ["PISA CON", "CABEZA."])
    t0 = ctx.at(p.get("at"), 0.1)
    for i, ln in enumerate(lines):
        pr = prog(t, t0 + i * 0.22, 0.45)
        if pr <= 0:
            continue
        k = ease_out_back(pr, 2.2)
        size = fit_size(ln, 820, 150)
        y = 470 + i * 170
        scaled(c, CX, y, k)
        draw_text(c, ln, CX, y + cap_height(size) / 2, size, ctx.a1 if i == len(lines) - 1 else C["cream"])
        c.restore()
    # subrayado que se dibuja
    pu = prog(t, t0 + 0.5, 0.5)
    if pu > 0:
        path = skia.Path()
        yy = 470 + (len(lines) - 1) * 170 + 110
        path.moveTo(CX - 300, yy)
        path.quadTo(CX, yy + 30, CX + 300, yy - 6)
        c.drawPath(S.partial(path, ease_out(pu)), stroke(ctx.a2, STROKE * 1.6))
    ctx.shoe(HERO["x"], HERO["y"], HERO["scale"], 1, pop=False)


SCENES = {
    "shoe": scene_shoe,
    "big_number": scene_big_number,
    "people": scene_people,
    "bars": scene_bars,
    "lever": scene_lever,
    "updown": scene_updown,
    "warning": scene_warning,
    "timeline": scene_timeline,
    "checklist": scene_checklist,
    "flow": scene_flow,
    "network": scene_network,
    "threshold": scene_threshold,
    "search": scene_search,
    "stamp": scene_stamp,
    "outro": scene_outro,
}
HERO_SCENES = {"shoe", "outro"}
