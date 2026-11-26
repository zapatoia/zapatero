"""Renderiza el vídeo vertical: pictogramas 2D (Cairo) + subtítulos palabra a palabra + voz."""
import json, math, subprocess, sys, re
import cairo
from script import SCENES, FULL

B = "../build"
W, H, FPS = 1080, 1920, 30
BLACK = (0.07, 0.07, 0.07); WHITE = (1, 1, 1)
RED = (0.90, 0.15, 0.16); YEL = (1.0, 0.80, 0.0); BLUE = (0.10, 0.40, 0.90)
FONT = "Inter"

# ---------------------------------------------------------------- timing
tm = json.load(open(f"{B}/timing.json"))
assert "".join(tm["characters"]) == FULL
CS, CE, DUR = tm["start"], tm["end"], tm["duration"] + 0.5

def word_spans(text, off):
    return [(m.start() + off, m.end() + off) for m in re.finditer(r"\S+", text)]

def span_time(i0, i1):
    # ignore trailing punctuation for end time
    j = i1 - 1
    while j > i0 and not FULL[j].isalnum(): j -= 1
    return CS[i0], CE[j]

words = []          # (display, start, end, scene)
scene_spans = []    # spoken word spans per scene: (text, start, end)
cur = 0
for k, sc in enumerate(SCENES):
    sw = []
    for d, sp in sc:
        sp = sp or d
        assert FULL[cur:cur + len(sp)] == sp, (cur, sp)
        ss = word_spans(sp, cur)
        dw = d.split()
        for a, b in ss: sw.append((FULL[a:b],) + span_time(a, b))
        if len(dw) == len(ss):
            for w, (a, b) in zip(dw, ss): words.append((w,) + span_time(a, b) + (k,))
        else:
            t0, t1 = CS[ss[0][0]], span_time(*ss[-1])[1]
            for i, w in enumerate(dw):
                words.append((w, t0 + (t1 - t0) * i / len(dw), t0 + (t1 - t0) * (i + 1) / len(dw), k))
        cur += len(sp) + 1
    scene_spans.append(sw)

SC_START = [0.0] + [max(0, scene_spans[k][0][1] - 0.12) for k in range(1, len(SCENES))]
SC_END = SC_START[1:] + [DUR]

def wt(k, sub):
    """time (relative to scene k start) when the spoken word containing `sub` begins"""
    for w, a, b in scene_spans[k]:
        if sub.lower() in w.lower(): return a - SC_START[k]
    raise KeyError(sub)

# ---------------------------------------------------------------- subtitles grouping
groups = []
g = []
for i, w in enumerate(words):
    if g and (w[3] != g[-1][3] or len(g) >= 4 or len(" ".join(x[0] for x in g + [w])) > 20):
        groups.append(g); g = []
    g.append(w)
    if re.search(r"[.:!?…]$", w[0]) or (w[0].endswith(",") and len(g) >= 2):
        groups.append(g); g = []
if g: groups.append(g)

# ---------------------------------------------------------------- easing
def cl(x): return max(0.0, min(1.0, x))
def pr(t, t0, d): return cl((t - t0) / d)
def eo(x): return 1 - (1 - x) ** 3
def eback(x):
    c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2 if x > 0 else 0.0
def pop(t, t0, d=0.45): return eback(pr(t, t0, d))

# ---------------------------------------------------------------- primitives
def col(c, rgb, a=1.0): c.set_source_rgba(*rgb, a)

def line(c, x0, y0, x1, y1, lw, rgb=BLACK):
    c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); col(c, rgb)
    c.move_to(x0, y0); c.line_to(x1, y1); c.stroke()

def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    c.close_path()

def circle(c, x, y, r, rgb=BLACK):
    col(c, rgb); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

def text(c, s, x, y, size, rgb=BLACK, scale=1.0, alpha=1.0, anchor="c"):
    if scale <= 0.001 or alpha <= 0: return
    c.save(); c.translate(x, y); c.scale(scale, scale)
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s)
    dx = -e.x_advance / 2 if anchor == "c" else (0 if anchor == "l" else -e.x_advance)
    c.move_to(dx, size * 0.36); col(c, rgb, alpha); c.show_text(s); c.restore()

def tw(c, s, size):
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    return c.text_extents(s).x_advance

def nz(v): return v if abs(v) > 1e-3 else (1e-3 if v >= 0 else -1e-3)

def xform(c, x, y, s, sx=None, rot=0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(nz(s if sx is None else sx), nz(s))

# ---------------------------------------------------------------- pictograms
def person(c, x, y, h, phase=0.0, swing=0.0, d=1, feet=None, hat=None, prop=None, lean=0.0, feet_hl=0.0):
    xform(c, x, y, h, rot=lean)
    hipy, L = -0.42, 0.365
    for side, ph in ((-1, 0), (1, math.pi)):
        a = swing * math.sin(phase + ph)
        hx = side * 0.055
        ex, ey = hx + L * math.sin(a), hipy + L * math.cos(a)
        line(c, hx, hipy, ex, ey, 0.11)
        fx = ex + d * 0.075
        line(c, ex, ey, fx, ey, 0.11)
        grow = 1 + 0.35 * feet_hl
        if feet == "wrap":
            col(c, YEL); c.save(); c.translate(ex + d * 0.035, ey); c.scale(grow, grow)
            c.scale(0.12, 0.075); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            for o in (-0.03, 0.03): line(c, ex + d * 0.035 + o, ey - 0.06 * grow, ex + d * 0.035 + o + 0.02, ey + 0.06 * grow, 0.018)
        elif feet in ("sandal", "boot"):
            line(c, ex - d * 0.06, ey + 0.07, fx + d * 0.06, ey + 0.07, 0.035 * grow, YEL)
            if feet == "boot":
                for k in (0.55, 0.75):
                    px, py = hx + L * k * math.sin(a), hipy + L * k * math.cos(a)
                    line(c, px - 0.065 * grow, py, px + 0.065 * grow, py, 0.03, YEL)
    # arms
    for side, ph in ((-1, math.pi), (1, 0)):
        a = swing * 0.9 * math.sin(phase + ph)
        sx, sy = side * 0.19, -0.745
        ex, ey = sx + 0.30 * math.sin(a) + side * 0.02, sy + 0.30 * math.cos(a)
        line(c, sx, sy, ex, ey, 0.095)
        if prop == "club" and side == d:
            c.save(); c.translate(ex, ey); c.rotate(-d * 0.9 + a)
            col(c, BLACK); c.move_to(-0.025, 0); c.line_to(0.025, 0); c.line_to(0.06, -0.3); c.line_to(-0.06, -0.3); c.close_path(); c.fill()
            c.arc(0, -0.3, 0.065, 0, 2 * math.pi); c.fill(); c.restore()
        if prop == "spear" and side == d:
            line(c, ex, ey + 0.25, ex, ey - 0.75, 0.035)
            col(c, BLACK); c.move_to(ex - 0.05, ey - 0.72); c.line_to(ex, ey - 0.88); c.line_to(ex + 0.05, ey - 0.72); c.close_path(); c.fill()
    col(c, BLACK); rrect(c, -0.135, -0.80, 0.27, 0.40, 0.075); c.fill()
    circle(c, 0, -0.915, 0.088)
    if hat == "cave":
        for i in range(5):
            ang = -math.pi + (i + 0.5) * math.pi / 5
            bx, by = 0.075 * math.cos(ang), -0.915 + 0.075 * math.sin(ang)
            c.move_to(bx - 0.03, by); c.line_to(bx + 0.13 * math.cos(ang - 0.3), by + 0.13 * math.sin(ang - 0.3)); c.line_to(bx + 0.03, by)
            c.close_path(); col(c, BLACK); c.fill()
    elif hat == "egypt":
        col(c, BLACK); c.move_to(-0.1, -1.01); c.line_to(0.1, -1.01); c.line_to(0.16, -0.80); c.line_to(-0.16, -0.80); c.close_path(); c.fill()
        for yy in (-0.95, -0.89, -0.83): line(c, -0.12 - (yy + 0.95) * 0.3, yy, 0.12 + (yy + 0.95) * 0.3, yy, 0.022, YEL)
    elif hat == "rome":
        col(c, BLACK); c.arc(0, -0.93, 0.115, math.pi, 2 * math.pi); c.fill()
        col(c, RED); c.save(); c.translate(-0.02, -1.06); c.scale(0.16, 0.07); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
        rrect(c, -0.16, -1.07, 0.30, 0.04, 0.02); c.fill()
    c.restore()

def mammoth(c, x, y, s, phase):
    xform(c, x, y, s)
    for i, lx in enumerate((-0.38, -0.18, 0.15, 0.35)):
        a = 0.25 * math.sin(phase + (i % 2) * math.pi)
        line(c, lx, -0.45, lx + 0.4 * math.sin(a), -0.07 * 0 - 0.4 * (1 - math.cos(a)) * 0 - 0.08, 0.17)
    col(c, BLACK); c.save(); c.translate(0, -0.6); c.scale(0.58, 0.38); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    circle(c, 0.52, -0.82, 0.27)
    # hump hair
    for i in range(4):
        hx = 0.32 + i * 0.09
        c.move_to(hx, -1.0 - 0.02 * i); c.line_to(hx + 0.05, -1.17 + 0.02 * i); c.line_to(hx + 0.1, -1.0); c.fill()
    # trunk
    c.set_line_width(0.14); c.set_line_cap(cairo.LINE_CAP_ROUND); col(c, BLACK)
    sw = 0.06 * math.sin(phase * 0.5)
    c.move_to(0.72, -0.78); c.curve_to(0.92, -0.6, 0.85 + sw, -0.25, 0.98 + sw, -0.12); c.stroke()
    # tusk (outlined)
    for lw, rgb in ((0.10, BLACK), (0.05, WHITE)):
        c.set_line_width(lw); col(c, rgb); c.move_to(0.68, -0.6); c.curve_to(0.78, -0.35, 1.0, -0.38, 1.12, -0.55); c.stroke()
    circle(c, 0.6, -0.9, 0.035, WHITE)
    c.set_line_width(0.03); col(c, WHITE); c.arc(0.4, -0.78, 0.13, 1.6, 4.4); c.stroke()
    line(c, -0.57, -0.7, -0.68, -0.45, 0.04)
    c.restore()

def shoe(c, x, y, s, flip=1, rgb=BLACK, laces=True, rot=0):
    """leather shoe side view, local width ~1, origin bottom-center"""
    xform(c, x, y, s, sx=s * flip, rot=rot)
    col(c, rgb)
    c.move_to(-0.5, 0); c.line_to(0.42, 0)
    c.curve_to(0.55, 0, 0.56, -0.2, 0.42, -0.24)
    c.curve_to(0.25, -0.28, 0.1, -0.32, -0.08, -0.46)
    c.line_to(-0.46, -0.46); c.curve_to(-0.5, -0.3, -0.52, -0.1, -0.5, 0); c.close_path(); c.fill()
    if laces:
        for i in range(3):
            lx = 0.0 - i * 0.09
            line(c, lx, -0.30 - i * 0.04, lx + 0.07, -0.26 - i * 0.04, 0.03, WHITE)
    line(c, -0.48, -0.06, 0.48, -0.06, 0.025, WHITE)
    c.restore()

def sneaker(c, x, y, s, flip=1, cracked=0.0, rot=0):
    """high-top basketball sneaker"""
    xform(c, x, y, s, sx=s * flip, rot=rot)
    col(c, BLACK)
    c.move_to(-0.5, -0.1); c.line_to(-0.5, -0.78); c.line_to(-0.18, -0.82)
    c.curve_to(-0.1, -0.55, 0.0, -0.4, 0.3, -0.3); c.curve_to(0.5, -0.25, 0.55, -0.18, 0.55, -0.1); c.close_path(); c.fill()
    # toe cap
    col(c, WHITE); c.move_to(0.28, -0.1); c.curve_to(0.3, -0.25, 0.45, -0.25, 0.5, -0.2); c.line_to(0.53, -0.1); c.close_path(); c.fill()
    # sole
    col(c, BLACK); rrect(c, -0.53, -0.12, 1.1, 0.12, 0.05); c.fill()
    line(c, -0.48, -0.06, 0.52, -0.06, 0.02, WHITE)
    circle(c, -0.36, -0.6, 0.085, BLUE); circle(c, -0.36, -0.6, 0.035, WHITE)
    for i in range(4): line(c, -0.12 + i * 0.07, -0.55 + i * 0.06, -0.02 + i * 0.07, -0.57 + i * 0.06, 0.03, WHITE)
    if cracked > 0:
        c.set_line_width(0.035); col(c, RED, cracked); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(-0.25, -0.75); c.line_to(-0.15, -0.55); c.line_to(-0.28, -0.42); c.line_to(-0.15, -0.2); c.stroke()
        for i in range(3):  # stink lines
            ox = -0.3 + i * 0.25; w = 0.05 * math.sin(i)
            c.move_to(ox, -0.95); c.curve_to(ox + 0.08, -1.05, ox - 0.08, -1.15, ox + w, -1.25); c.stroke()
    c.restore()

def sandal_top(c, x, y, s, rot=0):
    xform(c, x, y, s, rot=rot)
    col(c, BLACK); c.move_to(0, -0.5)
    c.curve_to(0.26, -0.5, 0.24, -0.1, 0.16, 0.15); c.curve_to(0.12, 0.42, 0.1, 0.5, 0, 0.5)
    c.curve_to(-0.1, 0.5, -0.12, 0.42, -0.16, 0.15); c.curve_to(-0.24, -0.1, -0.26, -0.5, 0, -0.5); c.fill()
    for yy in (-0.22, 0.05, 0.3): line(c, -0.24, yy - 0.04, 0.24, yy + 0.04, 0.07, YEL)
    # bark texture
    for i in range(4): line(c, -0.08 + i * 0.05, -0.42, -0.09 + i * 0.05, 0.42, 0.012, WHITE)
    c.restore()

def footprint(c, x, y, s, sx=1.0, rgb=BLACK):
    """right footprint (top view); sx=-1 mirrors to left"""
    if abs(sx) < 0.02: sx = 0.02 if sx >= 0 else -0.02
    xform(c, x, y, s, sx=s * sx)
    col(c, rgb)
    c.move_to(0.02, -0.38)
    c.curve_to(0.26, -0.38, 0.22, -0.05, 0.12, 0.12); c.curve_to(0.06, 0.25, 0.14, 0.48, -0.02, 0.5)
    c.curve_to(-0.16, 0.5, -0.14, 0.3, -0.14, 0.12); c.curve_to(-0.14, -0.1, -0.2, -0.38, 0.02, -0.38); c.fill()
    toes = [(-0.12, -0.5, 0.075), (0.0, -0.54, 0.055), (0.09, -0.52, 0.048), (0.16, -0.47, 0.042), (0.21, -0.40, 0.036)]
    for tx, ty, r in toes: circle(c, tx, ty, r, rgb)
    c.restore()

def pin(c, x, y, s, rgb=BLUE):
    xform(c, x, y, s)
    col(c, rgb); c.move_to(0, 0); c.curve_to(-0.1, -0.3, -0.45, -0.55, -0.45, -0.95)
    c.arc(0, -0.95, 0.45, math.pi, 2 * math.pi); c.curve_to(0.45, -0.55, 0.1, -0.3, 0, 0); c.fill()
    circle(c, 0, -0.95, 0.18, WHITE); c.restore()

def check(c, x, y, s, rgb=BLUE):
    xform(c, x, y, s); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_line_width(0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); col(c, rgb)
    c.move_to(-0.45, 0); c.line_to(-0.12, 0.33); c.line_to(0.5, -0.35); c.stroke(); c.restore()

def cross(c, x, y, s, rgb=RED):
    xform(c, x, y, s)
    line(c, -0.42, -0.42, 0.42, 0.42, 0.22, rgb); line(c, -0.42, 0.42, 0.42, -0.42, 0.22, rgb); c.restore()

def ground(c, y, x0=90, x1=990, lw=10):
    line(c, x0, y, x1, y, lw)

def fade_white(c, a):
    if a > 0: col(c, WHITE, a); c.paint()

# ---------------------------------------------------------------- scenes
def s1(c, t, k):
    tq = wt(k, "izquierdo")
    for i, xx in enumerate((300, 780)):
        p = pop(t, 0.1 + 0.2 * i, 0.55)
        wob = 0.08 * math.sin(t * 9) * pr(t, wt(k, "oyes") - 0.3, 0.2)
        shoe(c, xx, 900 - 60 * (1 - p), 380 * p, rot=wob)
    sp = pop(t, tq - 0.1, 0.5)
    text(c, "?", 540, 520 + 8 * math.sin(t * 5), 420, RED, scale=sp)
    a = pr(t, tq + 0.2, 0.3)
    text(c, "IZQ", 300, 1010, 64, BLACK, alpha=a); text(c, "DER", 780, 1010, 64, BLACK, alpha=a)
    text(c, "=", 540, 830, 150, BLACK, scale=pop(t, tq + 0.4))

def s2(c, t, k):
    tr = wt(k, "correr") - 0.2
    run = pr(t, tr, 0.3)
    text(c, "HACE DECENAS DE", 540, 330, 72, BLACK, scale=pop(t, wt(k, "decenas") - 0.1))
    text(c, "MILES DE AÑOS", 540, 420, 72, RED, scale=pop(t, wt(k, "miles") - 0.1))
    gy = 1130
    ground(c, gy)
    # moving ground dashes when running
    for i in range(6):
        dx = (i * 190 - (t - tr) * 900 * run) % 1140 - 30
        line(c, dx, gy + 40, dx + 70, gy + 40, 8)
    cx = 540 + 200 * eo(run)
    hl = pr(t, wt(k, "Pieles") - 0.1, 0.3) * (1 - pr(t, tr, 0.4))
    p = pop(t, 0.0, 0.55)
    person(c, cx, gy - 5, 520 * p, phase=t * (14 if run > 0 else 2), swing=0.15 + 0.55 * run,
           feet="wrap", hat="cave", prop="club", d=1, lean=0.12 * run, feet_hl=hl)
    if run > 0:
        mx = -500 + 690 * eo(pr(t, tr, 0.6))
        mammoth(c, mx, gy - 5 + 8 * math.sin(t * 14), 330, t * 14)
        for i in range(3):  # sweat drops
            a = (t * 3 + i * 0.33) % 1
            col(c, BLUE, 1 - a); c.arc(cx - 40 - 60 * a, gy - 520 + 30 * i - 40 * a, 10, 0, 2 * math.pi); c.fill()

def s3(c, t, k):
    tS = wt(k, "Salieron") - 0.15
    off = -1080 * eo(pr(t, tS, 0.45))
    c.save(); c.translate(off, 0)
    sp = pop(t, 0.0, 0.6)
    sandal_top(c, 540, 560 + 10 * math.sin(t * 3), 420 * sp, rot=-0.35 + 0.15 * math.sin(t * 2))
    text(c, "CORTEZA", 830, 360, 56, BLACK, scale=pop(t, wt(k, "corteza") - 0.1))
    line(c, 760, 400, 650, 470, 9 * pop(t, wt(k, "corteza")))
    nx = 540 + 900 * (1 - eo(pr(t, wt(k, "diez") - 0.1, 0.45)))
    text(c, "~10.000", nx, 930, 210, BLACK)
    text(c, "AÑOS", nx, 1080, 90, YEL)
    c.restore()
    if t > tS:
        c.save(); c.translate(off + 1080, 0)
        col(c, BLACK); c.save(); c.translate(540, 1000); c.scale(380, 110); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        col(c, WHITE); c.save(); c.translate(540, 1000); c.scale(370, 100); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        circle(c, 540, 1000, 18, BLACK)
        tp = wt(k, "Fort") - 0.1
        py = 1000 - 500 * (1 - eback(pr(t, tp, 0.5)))
        if t > tp - 0.2: pin(c, 540, py, 260)
        text(c, "FORT ROCK", 540, 460, 110, BLACK, scale=pop(t, tp + 0.1))
        text(c, "EE. UU.", 540, 1200, 80, BLUE, scale=pop(t, wt(k, "Estados") - 0.1))
        c.restore()

def cave(c, x, y, s):
    xform(c, x, y, s)
    col(c, BLACK); c.move_to(-1, 0); c.curve_to(-0.9, -0.9, -0.3, -1.1, 0.1, -1.0)
    c.curve_to(0.6, -1.05, 0.95, -0.6, 1, 0); c.close_path(); c.fill()
    col(c, WHITE); c.move_to(-0.42, 0); c.curve_to(-0.4, -0.6, 0.4, -0.6, 0.42, 0); c.close_path(); c.fill()
    c.restore()

def s4(c, t, k):
    tV = wt(k, "Mejor") - 0.15
    off = -1080 * eo(pr(t, tV, 0.45))
    c.save(); c.translate(off, 0)
    cp = pop(t, 0.0, 0.5)
    cave(c, 540, 860, 300 * cp)
    ts = wt(k, "cuero") - 0.3
    z = eo(pr(t, ts, 0.7))
    if t > ts:
        if z > 0.3: circle(c, 540, 1000, 150 * eo(pr(t, ts + 0.2, 0.4)), YEL)
        shoe(c, 540, 860 + 190 * z, 110 + 250 * z, flip=1, rot=-0.08 * math.sin(t * 4) * z)
    text(c, "ARENI-1", 540, 250, 110, BLACK, scale=pop(t, wt(k, "Areni") - 0.1))
    text(c, "ARMENIA", 540, 345, 60, RED, scale=pop(t, wt(k, "Armenia") - 0.1))
    # timeline
    tl = pr(t, wt(k, "cinco") - 0.25, 0.5)
    if tl > 0:
        y = 1150; x1 = 120 + 840 * eo(tl)
        line(c, 120, y, x1, y, 12)
        col(c, BLACK); c.move_to(x1 + 30, y); c.line_to(x1 - 5, y - 24); c.line_to(x1 - 5, y + 24); c.close_path(); c.fill()
        text(c, "HOY", 930, y + 60, 44, BLACK, alpha=tl)
        mp = eo(pr(t, wt(k, "cinco"), 0.6))
        mx = 930 - 700 * mp
        circle(c, mx, y, 26, YEL); circle(c, mx, y, 10, BLACK)
        text(c, "~5.500 AÑOS", 540, 470, 96, BLACK, scale=pop(t, wt(k, "quinientos") - 0.2))
    c.restore()
    if t > tV:
        c.save(); c.translate(off + 1080, 0)
        shoe(c, 290, 820, 360)
        sneaker(c, 790, 820, 340, cracked=pr(t, wt(k, "TN") - 0.2, 0.3))
        text(c, "5.500 AÑOS", 290, 900, 50, BLACK); text(c, "TUS TN", 790, 900, 50, BLACK)
        text(c, "VS", 540, 650, 90, BLACK, scale=pop(t, tV + 0.2))
        check(c, 290, 1060, 140 * pop(t, wt(k, "conservado")))
        cross(c, 790, 1060, 130 * pop(t, wt(k, "TN")))
        if t > wt(k, "hermano") - 0.2:
            text(c, "HERMANO", 540, 1210, 70, RED, scale=pop(t, wt(k, "hermano") - 0.2))
        c.restore()

def s5(c, t, k):
    gy = 1120; ground(c, gy)
    pe = eo(pr(t, 0.0, 0.8)); pr_ = eo(pr(t, wt(k, "romanos") - 0.3, 0.8))
    hs, hb = pr(t, wt(k, "sandalias") - 0.1, 0.25) * (1 - pr(t, wt(k, "botas") - 0.2, 0.3)), pr(t, wt(k, "botas") - 0.1, 0.25)
    walking = 1 if t > 0.0 else 0
    person(c, -200 + 520 * pe, gy - 5, 560, phase=t * 9, swing=0.5, d=1, feet="sandal", hat="egypt", feet_hl=hs)
    person(c, 1280 - 520 * pr_, gy - 5, 560, phase=t * 9 + 1, swing=0.5, d=-1, feet="boot", hat="rome", prop="spear", feet_hl=hb)
    text(c, "EGIPTO", 320, gy + 80, 60, BLACK, scale=pop(t, 0.3))
    text(c, "ROMA", 760, gy + 80, 60, RED, scale=pop(t, wt(k, "romanos")))
    text(c, "SANDALIAS", 320, 380, 64, BLACK, scale=pop(t, wt(k, "sandalias") - 0.1))
    text(c, "BOTAS", 760, 380, 64, BLACK, scale=pop(t, wt(k, "botas") - 0.1))
    if hs > 0: line(c, 320, 430, 320, 450, 0)

def s6(c, t, k):
    tf = wt(k, "Eso") - 0.1
    fl = eo(pr(t, tf, 0.6))
    sx = 1 - 2 * fl
    for i, xx in enumerate((330, 750)):
        p = pop(t, 0.05 + 0.15 * i, 0.5)
        footprint(c, xx, 720, 520 * p, sx=sx if i == 0 else 1)
    eq = pop(t, wt(k, "iguales") - 0.15)
    text(c, "=", 540, 700, 200, RED, scale=eq * (1 - fl))
    if fl > 0.5:
        text(c, "IZQ", 330, 1040, 72, BLUE, scale=pop(t, tf + 0.35)); text(c, "DER", 750, 1040, 72, BLUE, scale=pop(t, tf + 0.45))
    ts = wt(k, "siglo") - 0.2
    if t > ts:
        a = eo(pr(t, ts, 0.4))
        line(c, 160, 1180, 160 + 600 * a, 1180, 12)
        col(c, BLACK); x1 = 160 + 600 * a
        c.move_to(x1 + 35, 1180); c.line_to(x1 - 5, 1152); c.line_to(x1 - 5, 1208); c.close_path(); c.fill()
        text(c, "S. XIX", 540, 330, 190, BLACK, scale=pop(t, ts + 0.1))
        circle(c, 900, 1180, 34 * pop(t, ts + 0.3), YEL)

def blob(c, x, y, s, sq):
    """rubber drop that squashes into a sole"""
    xform(c, x, y, 1)
    c.scale(nz(s * (1 + 1.6 * sq)), nz(s * (1 - 0.82 * sq)))
    col(c, YEL)
    if sq < 0.5:
        c.move_to(0, -1.0); c.curve_to(0.3, -0.55, 0.62, -0.3, 0.62, 0.05); c.arc(0, 0.05, 0.62, 0, math.pi)
        c.curve_to(-0.62, -0.3, -0.3, -0.55, 0, -1.0); c.fill()
    else:
        rrect(c, -0.62, -0.6, 1.24, 1.2, 0.3); c.fill()
    c.restore()

def s7(c, t, k):
    tA = wt(k, "Adiós") - 0.15
    off = -1080 * eo(pr(t, tA, 0.45))
    text(c, "1839", 540, 330, 230, BLACK, scale=pop(t, 0.0, 0.5))
    text(c, "GOODYEAR", 540, 480, 70, RED, scale=pop(t, wt(k, "Goodyear") - 0.1))
    c.save(); c.translate(off, 0)
    tdrop = wt(k, "vulcanizó") - 0.2
    fall = pr(t, tdrop, 0.45); sq = eo(pr(t, tdrop + 0.45, 0.25))
    y = 640 + 440 * (fall ** 2)
    hang = pop(t, 0.2, 0.5)
    blob(c, 540, y + 8 * math.sin(t * 4) * (1 - fall), 110 * hang, sq)
    if fall == 0: text(c, "GOMA", 540, 760, 56, BLACK, scale=hang)
    th = wt(k, "Hola") - 0.1
    if t > th:
        sy = 1060 - 600 * (1 - eback(pr(t, th, 0.55)))
        shoe(c, 540, sy, 420)
        text(c, "SUELA DE GOMA", 540, 1200, 64, BLACK, scale=pop(t, wt(k, "suelas") - 0.1))
    c.restore()
    if t > tA:
        c.save(); c.translate(off + 1080, 0)
        gy = 1120
        for i in range(4):
            xx = 180 + i * 200; line(c, xx, gy, xx + 120, gy, 10, BLUE)
        slip = 0.5 + 0.12 * math.sin(t * 8)
        person(c, 540, gy - 5, 480, phase=0.9, swing=0.6, d=1, lean=-slip)
        cross(c, 540, 820, 330 * pop(t, tA + 0.35))
        c.restore()

def s8(c, t, k):
    text(c, "1917", 540, 330, 230, BLACK, scale=pop(t, 0.0, 0.5))
    text(c, "CONVERSE", 540, 480, 70, BLUE, scale=pop(t, wt(k, "Converse") - 0.1))
    ts = 0.15
    sx = -400 + 760 * eo(pr(t, ts, 0.6))
    tg = wt(k, "Síguenos") - 0.15
    up = eo(pr(t, tg, 0.4))
    sneaker(c, sx, 1020 - 120 * up, 460 * (1 - 0.25 * up))
    tb = wt(k, "baloncesto") - 0.25
    if t > tb:
        bt = (t - tb)
        by = 1020 - 120 * up - 45 - abs(math.sin(bt * 5.5)) * 300 * max(0.3, 1 - bt * 0.25)
        bx = 840
        circle(c, bx, by, 75, BLUE)
        c.set_line_width(7); col(c, BLACK)
        c.arc(bx, by, 75, 0, 2 * math.pi); c.stroke()
        line(c, bx - 75, by, bx + 75, by, 7); line(c, bx, by - 75, bx, by + 75, 7)
    if t > tg:
        p = pop(t, tg, 0.5) * (1 + 0.05 * math.sin((t - tg) * 10))
        c.save(); c.translate(540, 1170); c.scale(nz(p), nz(p))
        col(c, YEL); rrect(c, -330, -80, 660, 160, 80); c.fill()
        c.restore()
        text(c, "SÍGUENOS  +", 540, 1170, 80, BLACK, scale=p)

SCENE_FN = [s1, s2, s3, s4, s5, s6, s7, s8]

# ---------------------------------------------------------------- subtitles
SUB_Y, SUB_SIZE, SUB_MAXW = 1450, 86, 940

def draw_subs(c, T):
    gi = None
    for i, g in enumerate(groups):
        gend = groups[i + 1][0][1] if i + 1 < len(groups) else g[-1][2] + 0.6
        if g[0][1] - 0.05 <= T < gend: gi = i; break
    if gi is None: return
    g = groups[gi]
    ws = [w[0].upper() for w in g]
    sp = tw(c, " ", SUB_SIZE) + 22
    lines, cur, cw = [], [], 0
    for j, w in enumerate(ws):
        ww = tw(c, w, SUB_SIZE)
        if cur and cw + sp + ww > SUB_MAXW: lines.append(cur); cur, cw = [], 0
        cur.append((j, w, ww)); cw += (sp if cw else 0) + ww
    lines.append(cur)
    p = eback(pr(T, g[0][1] - 0.05, 0.22))
    s = 0.85 + 0.15 * p
    c.save(); c.translate(540, SUB_Y); c.scale(nz(s), nz(s))
    lh = SUB_SIZE * 1.3
    y0 = -lh * (len(lines) - 1) / 2
    for li, ln in enumerate(lines):
        total = sum(x[2] for x in ln) + sp * (len(ln) - 1)
        x = -total / 2; y = y0 + li * lh
        for j, w, ww in ln:
            active = g[j][1] - 0.03 <= T < (g[j + 1][1] if j + 1 < len(g) else 99)
            if active:
                col(c, YEL); rrect(c, x - 12, y - SUB_SIZE * 0.6, ww + 24, SUB_SIZE * 1.2, 16); c.fill()
            text(c, w, x, y, SUB_SIZE, BLACK, anchor="l")
            x += ww + sp
    c.restore()

# ---------------------------------------------------------------- main
def frame(c, T):
    col(c, WHITE); c.paint()
    k = max(i for i in range(len(SCENES)) if SC_START[i] <= T)
    t = T - SC_START[k]; D = SC_END[k] - SC_START[k]
    c.save()
    # gentle scene zoom
    z = 1 + 0.03 * (t / D)
    c.translate(540, 800); c.scale(z, z); c.translate(-540, -800)
    SCENE_FN[k](c, t, k)
    c.restore()
    if k < len(SCENES) - 1:
        fade_white(c, pr(t, D - 0.18, 0.18))
    fade_white(c, 1 - pr(t, 0, 0.12) if k > 0 else 0)
    draw_subs(c, T)
    # progress bar
    col(c, BLACK, 0.12); c.rectangle(0, 0, W, 14); c.fill()
    col(c, RED); c.rectangle(0, 0, W * T / DUR, 14); c.fill()

def main(out, only=None):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    c.set_antialias(cairo.ANTIALIAS_BEST)
    if only is not None:  # preview stills
        for T in only:
            frame(c, T); surf.write_to_png(f"{B}/still_{T:05.2f}.png")
        return
    n = int(math.ceil(DUR * FPS))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", f"{B}/voice_final.wav", "-map", "0:v", "-map", "1:a",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
                           "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        frame(c, i / FPS); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()
    print("done", out, n, "frames")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        main(None, [float(x) for x in sys.argv[2:]])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else "../video.mp4")
