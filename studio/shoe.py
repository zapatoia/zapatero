"""Rig del narrador: zapato oxford de cuero que habla.

Coordenadas locales: origen en el punto de apoyo de la suela, puntera hacia +x,
y negativa hacia arriba. Largo ≈ 600 px a escala 1.

El rig es puramente funcional: `draw_shoe(canvas, x, y, scale, state)` dibuja el
personaje en un estado (ShoeState). El estado lo calcula `ShoeAnimator`, que es
determinista en función del tiempo (sin simulación paso a paso), así cada
fotograma se puede renderizar en paralelo.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import skia

from .style import (C, STROKE, clamp, ease_out_back, ease_in_out, ease_out, fill,
                    lerp, spring, stroke, wobble, prog)

# ------------------------------------------------------------------ bocas
# 5 formas de boca (visemas). Parámetros: ancho, apertura, redondez, dientes.
MOUTHS = {
    "X": dict(w=1.00, h=0.00, r=0.0, teeth=0.0),   # reposo / sonrisa cerrada
    "M": dict(w=0.80, h=0.00, r=0.0, teeth=0.0),   # m, b, p (labios apretados)
    "E": dict(w=1.05, h=0.42, r=0.0, teeth=1.0),   # e, i, s, t... (ancha, dientes)
    "A": dict(w=0.95, h=1.00, r=0.2, teeth=0.3),   # a (muy abierta, lengua)
    "O": dict(w=0.58, h=0.78, r=1.0, teeth=0.0),   # o, u (redonda)
}

# Emociones: cejas (altura, ángulo interior), curvatura de la boca, entorno de ojos
EMOTIONS = {
    "neutral":   dict(brow_y=0.0, brow_in=0.0, brow_skew=0.0, smile=0.35, lid=0.0),
    "happy":     dict(brow_y=-6, brow_in=-0.10, brow_skew=0.0, smile=0.9, lid=0.18),
    "skeptic":   dict(brow_y=0.0, brow_in=0.12, brow_skew=1.0, smile=-0.1, lid=0.32),
    "worried":   dict(brow_y=-6, brow_in=-0.42, brow_skew=0.0, smile=-0.6, lid=0.0),
    "serious":   dict(brow_y=10, brow_in=0.40, brow_skew=0.0, smile=-0.25, lid=0.22),
    "surprised": dict(brow_y=-20, brow_in=-0.15, brow_skew=0.0, smile=0.0, lid=-0.1),
    "smug":      dict(brow_y=0.0, brow_in=0.18, brow_skew=0.6, smile=0.75, lid=0.38),
}

# Poses de brazos
ARM_POSES = ("none", "point", "open", "raise")


@dataclass
class ShoeState:
    # cuerpo
    squash: float = 0.0        # >0 aplasta, <0 estira
    tilt: float = 0.0          # grados, positivo = puntera hacia abajo
    lift: float = 0.0          # px por encima del suelo (salto)
    breath: float = 0.0        # -1..1
    facing: int = 1            # 1 = mira a la derecha, -1 = izquierda
    # cara
    mouth: dict = field(default_factory=lambda: dict(MOUTHS["X"]))
    talk_open: float = 0.0     # 0..1 multiplica la apertura (envolvente)
    emotion: dict = field(default_factory=lambda: dict(EMOTIONS["neutral"]))
    blink: float = 0.0         # 0 abierto, 1 cerrado
    look_x: float = 0.4        # -1..1
    look_y: float = 0.0
    brow_bounce: float = 0.0   # px (cejas suben al enfatizar)
    # brazos
    arm_near: str = "none"
    arm_far: str = "none"
    arm_near_k: float = 0.0    # 0..1 cuánto ha salido el brazo
    arm_far_k: float = 0.0
    point_angle: float = -40.0  # grados (0 = hacia delante, -90 = arriba)
    hand_wave: float = 0.0
    # secundarios
    tongue_angle: float = 0.0  # lengüeta del zapato
    lace_swing: float = 0.0


# ------------------------------------------------------------------ geometría
def _upper_path() -> skia.Path:
    p = skia.Path()
    p.moveTo(-262, -48)
    p.cubicTo(-288, -130, -290, -236, -264, -282)       # contrafuerte del talón
    p.cubicTo(-250, -306, -220, -308, -202, -290)       # borde del talón
    p.cubicTo(-176, -264, -150, -254, -118, -258)       # línea superior → garganta
    p.cubicTo(-58, -264, 2, -258, 54, -240)             # empeine bajo los cordones
    p.cubicTo(136, -214, 224, -204, 278, -164)          # pala hacia la puntera
    p.cubicTo(334, -124, 346, -66, 324, -36)            # puntera redonda
    p.lineTo(310, -30)
    p.lineTo(-250, -34)
    p.close()
    return p


def _sole_path() -> skia.Path:
    p = skia.Path()
    p.moveTo(-272, -60)
    p.lineTo(-156, -60)
    p.quadTo(-148, -60, -146, -50)
    p.lineTo(-140, -30)
    p.lineTo(240, -30)
    p.cubicTo(284, -30, 324, -40, 344, -60)             # puntera levantada
    p.cubicTo(354, -30, 334, -2, 292, 0)
    p.lineTo(-270, 0)
    p.quadTo(-286, 0, -286, -16)
    p.lineTo(-286, -46)
    p.quadTo(-286, -60, -272, -60)
    p.close()
    return p


def _heel_path() -> skia.Path:   # línea del tacón (frente del tacón)
    p = skia.Path()
    p.moveTo(-148, -26)
    p.lineTo(-148, -2)
    return p


def _quarter_seam() -> skia.Path:
    p = skia.Path()
    p.moveTo(-140, -252)
    p.cubicTo(-146, -204, -112, -178, -60, -180)
    p.cubicTo(-14, -182, 22, -206, 34, -236)
    return p


def _heel_seam() -> skia.Path:
    p = skia.Path()
    p.moveTo(-232, -40)
    p.cubicTo(-208, -110, -208, -190, -232, -278)
    return p


def _welt() -> skia.Path:
    p = skia.Path()
    p.moveTo(-126, -15)
    p.lineTo(250, -15)
    p.cubicTo(290, -15, 318, -24, 332, -36)
    return p


WELT = _welt()
UPPER = _upper_path()
SOLE = _sole_path()
HEEL = _heel_path()
QUARTER = _quarter_seam()
HEEL_SEAM = _heel_seam()

# anclajes
EYE_BACK = (100, -250, 42)
EYE_FRONT = (176, -236, 49)
MOUTH_C = (244, -122)
MOUTH_W = 104
SHOULDER_NEAR = (318, -92)     # brazo delantero: sale de la puntera
SHOULDER_FAR = (-280, -150)    # brazo trasero: sale del talón
TONGUE_BASE = (-122, -254)
BOW = (-40, -258)


# ------------------------------------------------------------------ dibujo
def draw_shoe(canvas: skia.Canvas, x: float, y: float, scale: float, st: ShoeState):
    """Dibuja el zapato con su suela apoyada en (x, y)."""
    canvas.save()
    canvas.translate(x, y - st.lift * scale)
    if st.facing < 0:
        canvas.scale(-1, 1)
    canvas.scale(scale, scale)
    # squash & stretch alrededor del punto de apoyo + respiración
    sq = st.squash
    sy = (1 - sq) * (1 + 0.012 * st.breath)
    sx = (1 + sq * 0.8) * (1 - 0.006 * st.breath)
    pivot_x = 20 if st.tilt >= 0 else -60
    canvas.translate(pivot_x, 0)
    canvas.rotate(st.tilt)
    canvas.translate(-pivot_x, 0)
    canvas.scale(sx, sy)

    sw = STROKE / max(0.55, scale) * min(1.0, 0.75 + 0.25 * scale)
    sw_detail = sw * 0.72

    # brazos (salen de detrás del cuerpo: puntera y talón)
    _draw_arm(canvas, SHOULDER_FAR, st.arm_far, st.arm_far_k, st, sw, far=True)
    _draw_arm(canvas, SHOULDER_NEAR, st.arm_near, st.arm_near_k, st, sw, far=False)

    # lengüeta del zapato (sale de la garganta, detrás del empeine)
    _draw_tongue(canvas, st, sw)

    # empeine
    canvas.drawPath(UPPER, fill(C["brown"]))
    # sombra plana interior del talón (forma, no degradado)
    canvas.save()
    canvas.clipPath(UPPER, doAntiAlias=True)
    shade = skia.Path()
    shade.moveTo(-300, -320)
    shade.cubicTo(-214, -240, -214, -90, -300, -10)
    shade.close()
    canvas.drawPath(shade, fill(C["brown_dark"]))
    # brillo plano en la puntera y talón
    _draw_shine(canvas)
    canvas.restore()

    canvas.drawPath(QUARTER, stroke(C["cream"], sw_detail))
    canvas.drawPath(HEEL_SEAM, stroke(C["cream"], sw_detail))
    _draw_laces(canvas, st, sw_detail)
    canvas.drawPath(UPPER, stroke(C["cream"], sw))

    # suela y tacón
    canvas.drawPath(SOLE, fill(C["brown_dark"]))
    canvas.drawPath(SOLE, stroke(C["cream"], sw))
    canvas.drawPath(HEEL, stroke(C["cream"], sw_detail))
    stitch = stroke(C["cream"], sw * 0.32)
    stitch.setPathEffect(skia.DashPathEffect.Make([10, 12], 0))
    canvas.drawPath(WELT, stitch)

    # cara
    _draw_mouth(canvas, st, sw)
    _draw_eyes(canvas, st, sw)
    canvas.restore()


def _draw_shine(canvas):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-262, -250, -244, -150), 9, 9))
    canvas.drawPath(p, fill(C["brown_light"]))
    # brillo en la puntera: media luna plana + punto
    sh = skia.Path()
    sh.moveTo(262, -178)
    sh.cubicTo(296, -160, 318, -138, 326, -110)
    sh.cubicTo(312, -126, 290, -148, 262, -166)
    sh.close()
    canvas.drawPath(sh, fill(C["shine"]))
    canvas.drawPath(sh, stroke(C["shine"], 9))


def _draw_tongue(canvas, st, sw):
    bx, by = TONGUE_BASE
    canvas.save()
    canvas.translate(bx, by)
    canvas.rotate(-12 + st.tongue_angle)
    p = skia.Path()
    p.moveTo(-26, 20)
    p.cubicTo(-34, -20, -30, -58, -6, -66)
    p.cubicTo(18, -72, 34, -56, 34, -30)
    p.lineTo(40, 24)
    p.close()
    canvas.drawPath(p, fill(C["brown_light"]))
    canvas.drawPath(p, stroke(C["cream"], sw))
    canvas.restore()


def _draw_laces(canvas, st, sw):
    # ojales a lo largo de la abertura
    pts = [(-108, -254), (-72, -256), (-36, -253), (0, -247)]
    # cordón en zigzag (crema)
    lace = skia.Path()
    lace.moveTo(*pts[0])
    for a, b in zip(pts, pts[1:]):
        lace.lineTo(b[0], b[1] + 2)
    canvas.drawPath(lace, stroke(C["cream"], sw * 0.9))
    for (ex, ey) in pts:
        canvas.drawCircle(ex, ey + 12, sw * 0.75, fill(C["ink"]))
        canvas.drawCircle(ex, ey + 12, sw * 0.75, stroke(C["cream"], sw * 0.5))
    # lazada con movimiento secundario
    bx, by = BOW
    swing = st.lace_swing
    for side, k in ((-1, 0.9), (1, 1.0)):
        loop = skia.Path()
        loop.moveTo(bx, by)
        ang = math.radians(side * 38 - 70 + swing * 0.6)
        lx, ly = bx + math.cos(ang) * 46 * k, by + math.sin(ang) * 46 * k
        nx, ny = math.cos(ang + 1.57) * 18, math.sin(ang + 1.57) * 18
        loop.cubicTo(bx + nx + (lx - bx) * 0.3, by + ny + (ly - by) * 0.3,
                     lx + nx, ly + ny, lx, ly)
        loop.cubicTo(lx - nx, ly - ny, bx - nx + (lx - bx) * 0.3, by - ny + (ly - by) * 0.3,
                     bx, by)
        canvas.drawPath(loop, stroke(C["cream"], sw * 0.9))
    # cabos colgando
    for side, ln in ((-1, 44), (1, 56)):
        end = skia.Path()
        end.moveTo(bx, by)
        ang = math.radians(90 + side * 24 + swing)
        ex, ey = bx + math.cos(ang) * ln, by + math.sin(ang) * ln
        end.quadTo(bx + side * 6 + swing * 0.4, by + ln * 0.5, ex, ey)
        canvas.drawPath(end, stroke(C["cream"], sw * 0.9))
    canvas.drawCircle(bx, by, sw * 0.9, fill(C["cream"]))


def _draw_eyes(canvas, st, sw):
    emo = st.emotion
    lid = clamp(emo["lid"] + (1 - emo["lid"]) * st.blink, -0.2, 1.0)
    for i, (ex, ey, r) in enumerate((EYE_BACK, EYE_FRONT)):
        # globo ocular
        eye = skia.Path()
        eye.addCircle(ex, ey, r)
        canvas.drawPath(eye, fill(C["eye"]))
        canvas.save()
        canvas.clipPath(eye, doAntiAlias=True)
        # pupila
        px = ex + st.look_x * r * 0.38
        py = ey + st.look_y * r * 0.35 + 3
        pr = r * 0.46
        canvas.drawCircle(px, py, pr, fill(C["ink"]))
        canvas.drawCircle(px + pr * 0.38, py - pr * 0.4, pr * 0.3, fill(C["eye"]))
        # párpado (forma plana del color de la piel)
        if lid > 0.01:
            lid_y = ey - r - 2 + (2 * r + 4) * lid
            lp = skia.Path()
            lp.addRect(skia.Rect(ex - r - 4, ey - r - 6, ex + r + 4, lid_y))
            canvas.drawPath(lp, fill(C["brown"]))
            canvas.drawLine(ex - r, lid_y, ex + r, lid_y, stroke(C["cream"], sw * 0.8))
        canvas.restore()
        canvas.drawCircle(ex, ey, r, stroke(C["cream"], sw))
        # ceja: dos trazos expresivos (uno por ojo)
        side = -1 if i == 0 else 1
        skew = emo["brow_skew"] * (12 if i == 1 else -4)
        by = ey - r - 24 + emo["brow_y"] - st.brow_bounce - skew
        tilt = emo["brow_in"] * (1 if i == 1 else -1)
        hw = r * 0.62
        x0, x1 = ex - hw, ex + hw
        # ángulo: el extremo interior (hacia el otro ojo) baja con brow_in
        y0 = by + (tilt * 26 if i == 1 else 0)
        y1 = by + (0 if i == 1 else -tilt * 26)
        bp = skia.Path()
        bp.moveTo(x0, y0)
        bp.quadTo((x0 + x1) / 2, min(y0, y1) - 10, x1, y1)
        canvas.drawPath(bp, stroke(C["cream"], sw * 1.15))


def _draw_mouth(canvas, st, sw):
    m = st.mouth
    emo = st.emotion
    cx, cy = MOUTH_C
    w = MOUTH_W * m["w"]
    open_h = 66 * m["h"] * st.talk_open
    smile = emo["smile"]
    hw = w / 2
    if open_h < 5:
        # boca cerrada: curva con sonrisa/mueca y comisuras
        p = skia.Path()
        lift = -smile * 18
        p.moveTo(cx - hw, cy + lift * 0.6)
        p.quadTo(cx, cy + smile * 22, cx + hw, cy + lift)
        canvas.drawPath(p, stroke(C["cream"], sw))
        if m["w"] < 0.9:  # labios apretados (M): comisuras marcadas
            canvas.drawLine(cx - hw - 6, cy - 4 + lift * 0.6, cx - hw + 4, cy + 6 + lift * 0.6,
                            stroke(C["cream"], sw * 0.8))
        return
    r = m["r"]
    # contorno de boca abierta: labio superior casi recto, inferior muy curvo
    top_ctrl = cy - open_h * (0.12 + 0.55 * r) - smile * 6
    bot_ctrl = cy + open_h * (1.35 + 0.25 * r)
    corner_y = cy - smile * 10
    p = skia.Path()
    p.moveTo(cx - hw, corner_y)
    p.cubicTo(cx - hw * (0.6 - 0.25 * r), top_ctrl, cx + hw * (0.6 - 0.25 * r), top_ctrl,
              cx + hw, corner_y)
    p.cubicTo(cx + hw * (0.75 - 0.1 * r), bot_ctrl, cx - hw * (0.75 - 0.1 * r), bot_ctrl,
              cx - hw, corner_y)
    p.close()
    canvas.drawPath(p, fill(C["ink"]))
    canvas.save()
    canvas.clipPath(p, doAntiAlias=True)
    # lengua
    tongue_h = open_h * 0.55
    if open_h > 14:
        canvas.drawOval(skia.Rect(cx - hw * 0.62, cy + open_h * 0.62 - tongue_h * 0.15,
                                  cx + hw * 0.52, cy + open_h * 1.5 + tongue_h),
                        fill(C["tongue"]))
    # dientes superiores
    if m["teeth"] > 0.05:
        th = 5 + 6 * m["teeth"]
        canvas.drawRect(skia.Rect(cx - hw, top_ctrl - 20, cx + hw, cy - smile * 10 + th),
                        fill(C["eye"]))
    canvas.restore()
    canvas.drawPath(p, stroke(C["cream"], sw))


def _arm_geometry(shoulder, pose, k, st, far):
    """Devuelve (codo, mano, tipo_mano, ángulo_mano) en coords locales."""
    sx, sy = shoulder
    L = 120.0
    d = -1 if far else 1          # el brazo trasero va hacia atrás
    if pose == "point":
        a = math.radians(st.point_angle) if not far else math.radians(180 - st.point_angle)
        ex, ey = sx + d * 46, sy - 6
        hx, hy = ex + math.cos(a) * L, ey + math.sin(a) * L
        hand = "point"
        hang = math.degrees(a)
    elif pose == "open":               # palmas arriba, explicando / encogerse
        ex, ey = sx + d * 72, sy + 18
        hx, hy = ex + d * 52, ey - 64
        hand = "open"
        hang = -60 if not far else -120
    elif pose == "raise":             # mano arriba (saludo / "atención")
        wave = math.sin(st.hand_wave) * 14
        ex, ey = sx + d * 58, sy - 40
        hx, hy = ex + d * 18 + wave, ey - 120
        hand = "open"
        hang = -90 + wave
    else:
        return None
    # crecimiento desde el hombro
    ex, ey = lerp(sx, ex, k), lerp(sy, ey, k)
    hx, hy = lerp(sx, hx, k), lerp(sy, hy, k)
    return (ex, ey), (hx, hy), hand, hang


def _draw_arm(canvas, shoulder, pose, k, st, sw, far):
    if pose == "none" or k <= 0.02:
        return
    geo = _arm_geometry(shoulder, pose, k, st, far)
    if geo is None:
        return
    (ex, ey), (hx, hy), hand, hang = geo
    sx, sy = shoulder
    col = C["cream"]
    p = skia.Path()
    p.moveTo(sx, sy)
    p.quadTo(ex, ey, hx, hy)
    canvas.drawPath(p, stroke(col, sw * 0.95))
    # mano
    hs = 19 * clamp(k * 1.2)
    canvas.save()
    canvas.translate(hx, hy)
    canvas.rotate(hang)
    canvas.drawCircle(0, 0, hs, fill(col))
    if hand == "point":
        canvas.drawLine(0, 0, hs * 2.1, 0, stroke(col, hs * 0.75))
        canvas.drawCircle(-hs * 0.1, -hs * 0.85, hs * 0.42, fill(col))  # pulgar
    else:
        # mano abierta: tres dedos cortos en abanico + pulgar
        for j, da in enumerate((-32, 0, 32)):
            a = math.radians(da)
            canvas.drawLine(0, 0, math.cos(a) * hs * 1.55, math.sin(a) * hs * 1.55,
                            stroke(col, hs * 0.62))
        canvas.drawLine(0, 0, hs * 0.2, hs * 1.3, stroke(col, hs * 0.62))
    canvas.restore()


# ------------------------------------------------------------------ animación
class ShoeAnimator:
    """Calcula el estado del zapato en cada instante.

    events: lista de dicts con 't' y 'kind':
      hop (salto en el sitio), land (caída desde arriba), tilt (inclinación),
      arms (cambio de pose de brazos), emotion, look, nod.
    visemes: función t -> (dict de forma, apertura 0..1) del módulo lipsync.
    """

    def __init__(self, seed=1, visemes=None, events=None, base_emotion="neutral",
                 facing=1, energy=None):
        self.seed = seed
        self.visemes = visemes
        self.events = sorted(events or [], key=lambda e: e["t"])
        self.base_emotion = base_emotion
        self.facing = facing
        self.energy = energy  # función t -> 0..1 (envolvente de la voz)
        rnd = random.Random(seed)
        # parpadeos cada 2-4 s (a veces dobles)
        self.blinks = []
        t = rnd.uniform(0.6, 1.6)
        while t < 600:
            self.blinks.append(t)
            if rnd.random() < 0.2:
                self.blinks.append(t + 0.28)
            t += rnd.uniform(2.0, 4.0)

    # -- utilidades
    def _blink(self, t):
        v = 0.0
        for b in self.blinks:
            if b - 0.1 < t < b + 0.2:
                d = t - b
                v = max(v, clamp(1 - abs(d) / 0.09) if d < 0 else clamp(1 - d / 0.13))
            if b > t + 1:
                break
        return v

    def state(self, t: float) -> ShoeState:
        st = ShoeState(facing=self.facing)
        st.breath = math.sin(t * 2 * math.pi / 3.2)
        st.blink = self._blink(t)
        emo_name = self.base_emotion
        emo_prev, emo_t = self.base_emotion, -10
        arm_near, arm_far, arm_t, arm_prev_n, arm_prev_f = "none", "none", -10, "none", "none"
        point_angle = -40.0
        look = (0.4, -0.05)
        look_prev, look_t = look, -10
        squash = 0.0
        lift = 0.0
        tilt = wobble(t, self.seed, 2.0, 0.7)
        sec = 0.0  # excitación de movimiento secundario
        brow = 0.0

        for e in self.events:
            dt = t - e["t"]
            if dt < -0.3:
                break
            kind = e["kind"]
            if kind == "land":       # cae desde arriba y aterriza en e['t'] + 0.35
                fall = 0.35
                if dt < 0:
                    continue
                if dt < fall:
                    u = dt / fall
                    lift += (1 - u * u) * e.get("height", 900)
                    squash += -0.12 * u
                else:
                    d = dt - fall
                    squash += 0.24 * math.exp(-9 * d) * math.cos(14 * d)
                    sec += spring(d, 2.2, 3.5) * 1.0
            elif kind == "hop":
                dur = e.get("dur", 0.42)
                h = e.get("height", 70)
                if -0.08 < dt < 0:          # anticipación
                    squash += 0.14 * (1 - abs(dt) / 0.08) * 0.0 + 0.14 * prog(dt, -0.08, 0.08)
                elif 0 <= dt < dur:
                    u = dt / dur
                    lift += 4 * h * u * (1 - u)
                    squash += -0.10 * math.sin(math.pi * u)
                    tilt += e.get("spin", 0) * math.sin(math.pi * u)
                elif dt >= dur:
                    d = dt - dur
                    squash += 0.16 * math.exp(-10 * d) * math.cos(16 * d)
                    sec += spring(d, 2.4, 4.0) * 0.8
                if dt >= 0:
                    sec += spring(dt, 2.0, 3.0) * 0.6
            elif kind == "tilt":     # cabeceo / inclinación expresiva
                if dt >= 0:
                    a = e.get("angle", 8)
                    hold = e.get("hold", 0.8)
                    if dt < hold:
                        tilt += a * ease_out_back(prog(dt, 0, 0.25), 2.5)
                    else:
                        tilt += a * (1 - ease_in_out(prog(dt, hold, 0.35)))
                    sec += spring(dt, 1.8, 3.0) * a * 0.12
            elif kind == "nod":
                if 0 <= dt < 0.5:
                    tilt += 6 * math.sin(dt / 0.5 * math.pi * 2) * (1 - dt / 0.5)
                    brow += 6 * math.sin(dt / 0.5 * math.pi)
            elif kind == "emotion":
                if dt >= 0:
                    emo_prev, emo_name, emo_t = emo_name, e["name"], e["t"]
            elif kind == "arms":
                if dt >= 0:
                    arm_prev_n, arm_prev_f = arm_near, arm_far
                    arm_near, arm_far = e.get("near", "none"), e.get("far", "none")
                    arm_t = e["t"]
                    point_angle = e.get("angle", point_angle)
            elif kind == "look":
                if dt >= 0:
                    look_prev, look, look_t = look, (e.get("x", 0.4), e.get("y", 0)), e["t"]
            elif kind == "brow":
                if dt >= 0:
                    brow += 10 * math.exp(-5 * dt) * (1 if dt > 0.05 else dt / 0.05)

        # habla: ligera vibración de cuerpo con la energía de la voz
        en = self.energy(t) if self.energy else 0.0
        squash += 0.022 * en * math.sin(t * 31)
        tilt += 1.2 * en * math.sin(t * 7.3)
        sec += 0.25 * en * math.sin(t * 9)

        # emociones con transición suave
        k = ease_in_out(prog(t, emo_t, 0.25))
        e0, e1 = EMOTIONS[emo_prev], EMOTIONS[emo_name]
        st.emotion = {key: lerp(e0[key], e1[key], k) for key in e0}

        # brazos: los anteriores se recogen, los nuevos salen con rebote
        ka = prog(t, arm_t, 0.32)
        if arm_near != "none":
            st.arm_near, st.arm_near_k = arm_near, ease_out_back(ka, 1.6)
        elif arm_prev_n != "none" and ka < 1:
            st.arm_near, st.arm_near_k = arm_prev_n, 1 - ease_in_out(ka)
        if arm_far != "none":
            st.arm_far, st.arm_far_k = arm_far, ease_out_back(prog(t, arm_t + 0.05, 0.32), 1.6)
        elif arm_prev_f != "none" and ka < 1:
            st.arm_far, st.arm_far_k = arm_prev_f, 1 - ease_in_out(ka)
        st.point_angle = point_angle + wobble(t, self.seed + 3, 4, 1.4)
        st.hand_wave = t * 9

        kl = ease_in_out(prog(t, look_t, 0.18))
        st.look_x = lerp(look_prev[0], look[0], kl) + wobble(t, self.seed + 9, 0.05, 2)
        st.look_y = lerp(look_prev[1], look[1], kl)

        st.squash = squash
        st.lift = max(0.0, lift)
        st.tilt = tilt
        st.brow_bounce = brow + 5 * en
        st.tongue_angle = -tilt * 0.8 + sec * 14 + wobble(t, self.seed + 5, 3, 1.1) - st.lift * 0.02
        st.lace_swing = sec * 18 + wobble(t, self.seed + 7, 5, 1.3) + st.tilt * 1.5

        if self.visemes:
            shape, amt = self.visemes(t)
            st.mouth = shape
            st.talk_open = amt
        return st
