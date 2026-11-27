"""TARJETAS y PLACAS de cristal (texturas planas que luego se colocan en 3D).

tarjeta(d, t, valor_u)  → skia.Image 700×920: título dorado con piloto, icono, cifra que rueda, unidad, extra (ecg).
placa_titulo(d, t)     → 900×620: icono + texto grande con relieve (título de entrada).
placa_contador(d, t, u) → 960×600: cifra enorme con fichas que ruedan (cada dígito en su ficha) + unidad.
"""
import math
import numpy as np
import skia

from nucleo.texto import fuente, texto, ancho, color
from nucleo.lienzo import capa, relleno, trazo, rrc
from .iconos import ICONOS

ORO, ORO2 = "#E8B04A", "#FFD98A"
F = dict(lab=fuente("Inter", 800, 34), num=fuente("Inter", 800, 210), uni=fuente("Inter", 600, 40), tit=fuente("Inter", 800, 150),
         tit2=fuente("Inter", 600, 46), dig=fuente("Inter", 800, 170), dig2=fuente("Inter", 800, 120))


def num_es(v, dec=0):
    s = f"{v:,.{dec}f}"; return s.replace(",", "§").replace(".", ",").replace("§", ".")


def _vidrio(c, w, h, rad=56):
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(6, 6, w - 12, h - 12), rad, rad)
    c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (w, h)], [color("#1B2233", .93), color("#0A0D16", .9), color("#151A28", .93)], [0, .55, 1])))
    c.save(); c.clipRRect(r, doAntiAlias=True)
    for i in range(0, w, 46): c.drawLine(i, 0, i, h, trazo("#FFFFFF", 1, .03))
    c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, h * .35)], [color("#FFFFFF", .07), color("#FFFFFF", 0)])))
    c.restore()
    c.drawRRect(r, trazo("#FFFFFF", 2.5, .35)); c.drawLine(rad + 14, 8, w - rad - 14, 8, trazo("#FFFFFF", 3, .6))


def _sup(w, h):
    s = skia.Surface(int(w), int(h)); c = s.getCanvas(); c.clear(skia.ColorTRANSPARENT); return s, c


def tarjeta(d, t, u=1.0):
    """d: titulo, icono, valor, dec, prefijo, sufijo, unidad, extra. u = avance del contador (0–1)."""
    w, h = 700, 920; s, c = _sup(w, h); _vidrio(c, w, h)
    texto(c, d.get("titulo", ""), 56, 80, F["lab"], ORO, alinear="i", tracking=.3)
    c.drawCircle(w - 70, 80, 9, relleno("#2ED47A")); c.drawCircle(w - 70, 80, 16, trazo("#2ED47A", 2, .4 + .3 * math.sin(t * 5)))
    ico = d.get("icono")
    if ico in ICONOS:
        kw = dict(nivel=u) if ico == "gota" else {}
        ICONOS[ico](c, w / 2, 330, 160, t, **kw)
    v = d.get("valor", 0) * u; dec = d.get("dec", 0)
    txt = f"{d.get('prefijo', '')}{num_es(v, dec)}{d.get('sufijo', '')}"
    fn = F["num"]; esc = min(1.0, (w - 80) / max(1, ancho(txt, fn)))
    c.save(); c.translate(w / 2, 660); c.scale(esc, esc)
    if u < 1:
        c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(.01, 14 * (1 - u) + .01))); texto(c, txt, 0, 0, fn, "#FFFFFF", tnum=True); c.restore()
    else: texto(c, txt, 0, 0, fn, "#FFFFFF", tnum=True, sombra=(4, 14, .5))
    c.restore()
    texto(c, d.get("unidad", ""), w / 2, 790, F["uni"], "#AEB6C8")
    if d.get("extra") == "ecg":
        p = skia.Path()
        for i in range(0, 581, 4):
            ph = ((i / 580) * 3 - t * 1.2) % 1; yy = -55 * math.exp(-((ph - .5) / .02) ** 2) + 18 * math.exp(-((ph - .56) / .02) ** 2)
            (p.moveTo if i == 0 else p.lineTo)(60 + i, 860 + yy)
        c.drawPath(p, trazo(ORO, 3, .8))
    return s.makeImageSnapshot()


def placa_titulo(d, t):
    w, h = 900, 620; s, c = _sup(w, h); _vidrio(c, w, h, 64)
    ico = d.get("icono")
    if ico in ICONOS: ICONOS[ico](c, w / 2, 210, 120, t * d.get("vel_reloj", 8))
    txt = d.get("texto", ""); fn = F["tit"]; esc = min(1.0, (w - 80) / max(1, ancho(txt, fn)))
    c.save(); c.translate(w / 2, 450); c.scale(esc, esc)
    for k in range(6, 0, -1): texto(c, txt, k * 1.2, k * 2.0, fn, "#5A4318", alfa=.9)        # relieve dorado
    with capa(c, alfa=.5, blur=18): texto(c, txt, 0, 0, fn, ORO)
    texto(c, txt, 0, 0, fn, "#FFFFFF", paint=skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -70), (0, 70)], [color("#FFFFFF"), color(ORO2)])))
    c.restore()
    if d.get("sub"): texto(c, d["sub"], w / 2, 560, F["tit2"], "#AEB6C8")
    return s.makeImageSnapshot()


def placa_contador(d, t, u=1.0):
    """Cifra enorme con cada dígito en su ficha metálica; rueda con desenfoque vertical mientras u < 1."""
    v = d.get("valor", 0) * u; txt = num_es(v); n = len(txt)
    fd = F["dig"] if n <= 7 else F["dig2"]; cw = 112 if n <= 7 else 84; ch = 200 if n <= 7 else 150; gap = 10
    anchos = [cw * .45 if ch_ == "." else cw for ch_ in txt]; tot = sum(anchos) + gap * (n - 1)
    w = int(max(960, tot + 120)); h = 600; s, c = _sup(w, h); _vidrio(c, w, h, 60)
    texto(c, d.get("titulo", ""), 56, 70, F["lab"], ORO, alinear="i", tracking=.3)
    x = (w - tot) / 2; y = 290
    for ch_, aw in zip(txt, anchos):
        cx = x + aw / 2
        if ch_ == ".": texto(c, ".", cx, y + 50, fd, "#FFFFFF")
        else:
            card = rrc(cx, y, aw, ch, 16)
            c.drawRRect(card, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y - ch / 2), (0, y + ch / 2)], [color("#2B2F3A"), color("#14161D"), color("#05060A")], [0, .5, 1])))
            c.drawRRect(card, trazo("#FFFFFF", 1.5, .25))
            c.save(); c.clipRRect(card, doAntiAlias=True)
            bl = (1 - u) * 22
            if bl > .5: c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(.01, bl)))
            texto(c, ch_, cx, y, fd, "#FFFFFF", tnum=True)
            if bl > .5: c.restore()
            c.drawLine(cx - aw / 2, y, cx + aw / 2, y, trazo("#000000", 3, .8))
            c.drawRect(skia.Rect.MakeXYWH(cx - aw / 2, y - ch / 2, aw, ch / 2), relleno("#FFFFFF", .05))
            c.restore()
        x += aw + gap
    texto(c, d.get("unidad", ""), w / 2, 500, F["tit2"], "#AEB6C8")
    if d.get("icono") in ICONOS: ICONOS[d["icono"]](c, w - 90, 70, 26, t)
    return s.makeImageSnapshot()
