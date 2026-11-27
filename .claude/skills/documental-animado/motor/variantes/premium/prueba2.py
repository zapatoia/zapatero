#!/usr/bin/env python3
"""Prueba 2 del ESTILO PREMIUM (8 s, muda): «Tu cuerpo en un minuto». Escena 3D real con cámara que vuela, tarjetas de cristal,
profundidad de campo, reflejo, partículas, barrido de luz, desenfoque de movimiento y posproceso.

  PY prueba2.py <carpeta_salida>      → prueba-premium-2.mp4 + hoja.jpg
"""
import math, subprocess, sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MOTOR)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np                                                # noqa: E402
import skia                                                       # noqa: E402
from nucleo.texto import fuente, texto, ancho, color              # noqa: E402
from nucleo.lienzo import Lienzo, capa, relleno, trazo, rrc       # noqa: E402
from nucleo.rutas import FF                                       # noqa: E402
from nucleo.render import ENC                                     # noqa: E402
from escena3d import Camara, Plano, dibujar_plano, suelo, particulas, Post, W, H   # noqa: E402

FPS, DUR = 60, 8.0
ORO, ORO2, BG = "#E8B04A", "#FFD98A", "#06080D"
YS = -520                                                          # altura del suelo
F = dict(lab=fuente("Inter", 800, 34), num=fuente("Inter", 800, 210), uni=fuente("Inter", 600, 40), cap=fuente("Inter", 800, 70),
         capl=fuente("Inter", 400, 70), et=fuente("Inter", 800, 30), et2=fuente("Inter", 600, 26))


def ease(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def eexp(u):
    u = min(max(u, 0.0), 1.0)
    if u in (0, 1): return u
    return 2 ** (20 * u - 10) / 2 if u < .5 else (2 - 2 ** (-20 * u + 10)) / 2
def resorte(dt, k=9.0, w=13.0): return 0.0 if dt <= 0 else 1 - math.exp(-k * dt) * math.cos(w * dt)
def lerp(a, b, u): return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * u


# ---------------------------------------------------------------- iconos vectoriales (con volumen: degradado + brillo + halo)
def corazon(c, x, y, s, t):
    late = 1 + .07 * max(0, math.sin(t * 2 * math.pi * 70 / 60)) ** 8
    c.save(); c.translate(x, y); c.scale(s * late, s * late)
    p = skia.Path(); p.moveTo(0, .38); p.cubicTo(-1.05, -.25, -.55, -1.05, 0, -.55); p.cubicTo(.55, -1.05, 1.05, -.25, 0, .38); p.close()
    with capa(c, alfa=.55, blur=26): c.drawPath(p, relleno("#FF3B4A"))
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-.25, -.45), 1.1, [color("#FF8A8F"), color("#E0182B"), color("#5E0610")], [0, .5, 1])))
    c.drawOval(skia.Rect.MakeXYWH(-.52, -.62, .3, .18), relleno("#FFFFFF", .45))
    c.restore()


def pulmones(c, x, y, s, t):
    r = 1 + .06 * math.sin(t * 2 * math.pi * 15 / 60 * 3)
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawLine(0, -1.0, 0, -.35, trazo("#E9ECF3", .09)); c.drawLine(0, -.35, -.28, -.15, trazo("#E9ECF3", .07)); c.drawLine(0, -.35, .28, -.15, trazo("#E9ECF3", .07))
    for sx in (-1, 1):
        c.save(); c.translate(sx * .5, .12); c.scale(r, r)
        p = skia.Path(); p.addOval(skia.Rect.MakeXYWH(-.38, -.62, .76, 1.24))
        with capa(c, alfa=.5, blur=24): c.drawPath(p, relleno("#5FC8FF"))
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-.12 * sx, -.3), .95, [color("#BDEBFF"), color("#3D8BFF"), color("#0D2A6E")], [0, .55, 1])))
        c.drawOval(skia.Rect.MakeXYWH(-.2, -.48, .16, .26), relleno("#FFFFFF", .4))
        c.restore()
    c.restore()


def ojo(c, x, y, s, t):
    ph = (t % 3.5); cierre = max(0.0, 1 - abs(ph - 1.6) / .09) if abs(ph - 1.6) < .09 else 0.0
    c.save(); c.translate(x, y); c.scale(s, s * (1 - .92 * cierre))
    p = skia.Path(); p.moveTo(-1, 0); p.quadTo(0, -.95, 1, 0); p.quadTo(0, .95, -1, 0); p.close()
    with capa(c, alfa=.5, blur=24): c.drawPath(p, relleno("#2ED47A"))
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -.5), (0, .5)], [color("#FFFFFF"), color("#C9D3EA")])))
    c.save(); c.clipPath(p, doAntiAlias=True)
    c.drawCircle(0, 0, .42, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((0, 0), .42, [color("#0B3D2A"), color("#2ED47A"), color("#0E5A3A")], [0, .6, 1])))
    c.drawCircle(0, 0, .17, relleno("#05070A")); c.drawCircle(-.13, -.14, .07, relleno("#FFFFFF", .9))
    c.restore(); c.drawPath(p, trazo("#FFFFFF", .03, .6)); c.restore()


TARJ = [dict(n="CORAZÓN", v=70, u="latidos por minuto", ico=corazon, t0=.2),
        dict(n="PULMONES", v=15, u="respiraciones por minuto", ico=pulmones, t0=2.9),
        dict(n="OJOS", v=17, u="parpadeos por minuto", ico=ojo, t0=4.2)]


def tarjeta(k, t):
    d = TARJ[k]; w, h = 700, 920; s = skia.Surface(w, h); c = s.getCanvas(); c.clear(skia.ColorTRANSPARENT)
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(6, 6, w - 12, h - 12), 56, 56)
    c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (w, h)], [color("#1B2233", .92), color("#0A0D16", .88), color("#151A28", .92)], [0, .55, 1])))
    c.drawRRect(r, trazo("#FFFFFF", 2.5, .35)); c.drawLine(70, 8, w - 70, 8, trazo("#FFFFFF", 3, .6))
    for i in range(0, w, 46): c.drawLine(i, 0, i, h, trazo("#FFFFFF", 1, .03))
    texto(c, d["n"], 56, 80, F["lab"], ORO, alinear="i", tracking=.3)
    c.drawCircle(w - 70, 80, 9, relleno("#2ED47A")); c.drawCircle(w - 70, 80, 16, trazo("#2ED47A", 2, .4 + .3 * math.sin(t * 5)))
    d["ico"](c, w / 2, 340, 170, t)
    dt = t - d["t0"]; v = int(round(d["v"] * eexp(max(0, dt) / 1.2)))
    texto(c, str(v), w / 2, 660, F["num"], "#FFFFFF", tnum=True, sombra=(4, 14, .5))
    texto(c, d["u"], w / 2, 790, F["uni"], "#AEB6C8")
    if k == 0:                                                                      # electro en la base
        pth = skia.Path(); x0 = 60
        for i in range(0, 581, 4):
            ph = ((i / 580) * 3 - t * 1.2) % 1; yy = -55 * math.exp(-((ph - .5) / .02) ** 2) + 18 * math.exp(-((ph - .56) / .02) ** 2)
            (pth.moveTo if i == 0 else pth.lineTo)(x0 + i, 860 + yy)
        c.drawPath(pth, trazo(ORO, 3, .8))
    return s.makeImageSnapshot()


# ---------------------------------------------------------------- mundo y cámara
SPREAD = [((0, 0, 0), (0, 0, 0)), ((850, 0, 520), (0, -38, 0)), ((1700, 0, 1300), (0, -55, 0))]
STACK = [((900, 420, 900), (90, 0, -18)), ((900, 90, 900), (90, 0, -18)), ((900, -240, 900), (90, 0, -18))]
T_STACK = (4.9, 6.5)

CAM = [  # (t, ojo, mira, roll, curva)
    (0.0, (-260, 170, -2900), (0, 40, 0), -4, None),
    (2.35, (80, 40, -1750), (0, 60, 0), 2, "io"),
    (2.95, (300, 80, -1150), (850, 60, 520), -7, "exp"),
    (4.85, (420, 40, -880), (850, 70, 520), -2, "io"),
    (6.55, (-420, 1350, -900), (900, 80, 900), 0, "exp"),
    (8.0, (-200, 1450, -1100), (900, 80, 900), 0, "io"),
]


def camara(t):
    for i in range(1, len(CAM)):
        if t <= CAM[i][0] or i == len(CAM) - 1:
            a, b = CAM[i - 1], CAM[i]; u = (t - a[0]) / (b[0] - a[0]); u = eexp(u) if b[4] == "exp" else ease(u)
            return Camara(lerp(a[1], b[1], u), lerp(a[2], b[2], u), roll=a[3] + (b[3] - a[3]) * u, cy=1010), b[4] == "exp" and 0.05 < u < .95
    return Camara(CAM[-1][1], CAM[-1][2]), False


def planos(t):
    u = eexp((t - T_STACK[0]) / (T_STACK[1] - T_STACK[0]))
    out = []
    for k in range(3):
        c = lerp(SPREAD[k][0], STACK[k][0], u); r = lerp(SPREAD[k][1], STACK[k][1], u)
        out.append(Plano(tarjeta(k, t), c, 700, 920, tuple(r), nombre=TARJ[k]["n"]))
    return out, u


RNG = np.random.default_rng(5)
PTS = np.c_[RNG.uniform(-2500, 3500, 260), RNG.uniform(-450, 1900, 260), RNG.uniform(-2400, 3600, 260)]


def rotulo(c, t):
    caps = [(.15, "Tu corazón late", "70 veces"), (2.85, "y respiras unas", "15 veces"), (5.0, "todo en un solo", "minuto")]
    cur = [x for x in caps if t >= x[0]]
    if not cur: return
    t0, ctx, key = cur[-1]; dt = t - t0; nxt = [x[0] for x in caps if x[0] > t0]
    sal = min(1, max(0, ((nxt[0] if nxt else 99) - .1 - t) / .12))
    for i, (txt, f, col, d0) in enumerate(((ctx, F["capl"], "#8C93A6", 0), (key, F["cap"], "#FFFFFF", .2))):
        a = min(1, max(0, (dt - d0) / .12)) * sal
        if a <= 0: continue
        y = 300 + i * 88 + 22 * (1 - resorte(dt - d0, 10, 12))
        c.saveLayer(None, skia.Paint(Alphaf=a, ImageFilter=skia.ImageFilters.Blur(max(.01, 10 * (1 - a)), max(.01, 10 * (1 - a)))))
        texto(c, txt, 520, y, f, col); c.restore()


def escena(c, t):
    cam, rapido = camara(t)
    c.clear(color(BG))
    c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial((520, 760), 1500, [color("#151B2C"), color(BG)], [0, 1])))
    foco = float(np.linalg.norm(cam.mira - cam.ojo))
    suelo(c, cam, YS)
    pls, us = planos(t)
    # reflejos en el suelo (debajo de todo)
    for pl in pls:
        if us < .6: dibujar_plano(c, cam, pl, foco, espejo_y=YS, alfa_extra=.16 * (1 - us / .6))
    # halo dorado detrás de cada tarjeta
    for pl in pls:
        q, z = cam.pantalla(pl.c[None, :])
        if z[0] > 60:
            rr = 900 * cam.f / z[0] * .6
            c.drawCircle(float(q[0, 0]), float(q[0, 1]), rr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (float(q[0, 0]), float(q[0, 1])), rr, [color(ORO, .18), color(ORO, 0)], [0, 1])))
    orden = sorted(pls, key=lambda p: -float(cam.vista(p.c[None, :])[0, 2]))
    barr = ((t * .45) % 1.4); etqs = []
    for pl in orden:
        r = dibujar_plano(c, cam, pl, foco, barrido=barr if barr <= 1 else None)
        if r is not None: etqs.append((pl, r))
    for pl, r in etqs:
        # etiquetas con línea guía en la vista apilada
        if r is not None and us > .7:
            q, _ = r; a = min(1, (us - .7) / .3); xr, yr = float(q[1, 0]), float(q[1, 1])
            c.drawLine(xr, yr, xr + 60, yr - 50, trazo(ORO, 2, .9 * a)); c.drawCircle(xr, yr, 5, relleno(ORO2, a))
            k = [d["n"] for d in TARJ].index(pl.nombre)
            texto(c, pl.nombre, min(xr + 70, 800), yr - 62, F["et"], "#FFFFFF", alinear="i", tracking=.2, alfa=a)
            texto(c, f"{TARJ[k]['v']} / min", min(xr + 70, 800), yr - 26, F["et2"], ORO, alinear="i", alfa=a)
    particulas(c, cam, PTS, foco, t)
    rotulo(c, t)
    return rapido


def main(salida):
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True); out = salida / "prueba-premium-2.mp4"
    L = Lienzo(); post = Post(); nf = int(DUR * FPS)
    ff = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, str(out)], stdin=subprocess.PIPE)
    for f in range(nf):
        t = f / FPS; rapido = escena(L.canvas, t)
        if rapido:                                                                   # desenfoque de movimiento: 4 subcuadros
            acc = L.arr[..., :3].astype(np.float32)
            for k in range(1, 4):
                escena(L.canvas, t - k / (FPS * 4)); acc += L.arr[..., :3]
            L.arr[..., :3] = (acc / 4).astype(np.uint8)
        L.arr[..., 3] = 255; post(L.arr, t); ff.stdin.write(L.arr.tobytes())
        if f % 120 == 0: print(f"{f}/{nf}", flush=True)
    ff.stdin.close(); ff.wait()
    subprocess.run([FF, "-v", "error", "-y", "-i", str(out), "-vf", "fps=2,scale=270:-1,tile=8x2", "-frames:v", "1", str(salida / "hoja-2.jpg")], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
