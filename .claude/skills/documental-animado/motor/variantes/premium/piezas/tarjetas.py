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


# ---- cachés (las texturas se componen de piezas guardadas: fondo fijo + icono a 20 fps + cifra por texto) → render rápido
_C = {}
def _cache(clave, hacer, tope=600):
    if clave not in _C:
        if len(_C) > tope: _C.clear()
        _C[clave] = hacer()
    return _C[clave]


def _base_tarjeta(d, w, h):
    def hacer():
        s, c = _sup(w, h); _vidrio(c, w, h)
        texto(c, d.get("titulo", ""), 56, 80, F["lab"], ORO, alinear="i", tracking=.3)
        c.drawCircle(w - 70, 80, 9, relleno("#2ED47A"))
        texto(c, d.get("unidad", ""), w / 2, 790, F["uni"], "#AEB6C8")
        return s.makeImageSnapshot()
    return _cache(("base", d.get("titulo"), d.get("unidad"), w, h), hacer)


def icono_img(nombre, t, s=160, caja=440, **kw):
    """Icono pre-dibujado en su caja (se refresca a 20 fps)."""
    tq = round(t * 20) / 20
    def hacer():
        sf, c = _sup(caja, caja); ICONOS[nombre](c, caja / 2, caja / 2, s, tq, **kw); return sf.makeImageSnapshot()
    return _cache(("ico", nombre, tq, s, caja, tuple(sorted((k, round(v, 2)) for k, v in kw.items()))), hacer)


def cifra_img(txt, fn, ancho_max, blur=0.0):
    b = round(blur)
    def hacer():
        esc = min(1.0, ancho_max / max(1, ancho(txt, fn))); ww, hh = int(ancho_max + 40), int(fn.px * 1.5 + 2 * b + 40)
        sf, c = _sup(ww, hh); c.translate(ww / 2, hh / 2); c.scale(esc, esc)
        if b > 0: c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(.01, b + .01))); texto(c, txt, 0, 0, fn, "#FFFFFF", tnum=True); c.restore()
        else: texto(c, txt, 0, 0, fn, "#FFFFFF", tnum=True, sombra=(4, 14, .5))
        return sf.makeImageSnapshot()
    return _cache(("num", txt, fn.px, ancho_max, b), hacer)


def tarjeta(d, t, u=1.0):
    """d: titulo, icono, valor, dec, prefijo, sufijo, unidad, extra. u = avance del contador (0–1)."""
    w, h = 700, 920; s, c = _sup(w, h); c.drawImage(_base_tarjeta(d, w, h), 0, 0)
    c.drawCircle(w - 70, 80, 16, trazo("#2ED47A", 2, .4 + .3 * math.sin(t * 5)))
    ico = d.get("icono")
    if ico in ICONOS:
        kw = dict(nivel=round(u, 2)) if ico == "gota" else {}
        im = icono_img(ico, t, **kw); c.drawImage(im, w / 2 - im.width() / 2, 330 - im.height() / 2)
    v = d.get("valor", 0) * u; dec = d.get("dec", 0)
    txt = f"{d.get('prefijo', '')}{num_es(v, dec)}{d.get('sufijo', '')}"
    im = cifra_img(txt, F["num"], w - 80, 14 * (1 - u) if u < 1 else 0); c.drawImage(im, w / 2 - im.width() / 2, 660 - im.height() / 2)
    if d.get("extra") == "ecg":
        p = skia.Path()
        for i in range(0, 581, 4):
            ph = ((i / 580) * 3 - t * 1.2) % 1; yy = -55 * math.exp(-((ph - .5) / .02) ** 2) + 18 * math.exp(-((ph - .56) / .02) ** 2)
            (p.moveTo if i == 0 else p.lineTo)(60 + i, 860 + yy)
        c.drawPath(p, trazo(ORO, 3, .8))
    return s.makeImageSnapshot()


def placa_titulo(d, t):
    w, h = 900, 620; s, c = _sup(w, h)
    c.drawImage(_cache(("placa", d.get("texto"), d.get("sub")), lambda: _placa_base(d, w, h)), 0, 0)
    ico = d.get("icono")
    if ico in ICONOS: im = icono_img(ico, t * d.get("vel_reloj", 8), s=120, caja=330); c.drawImage(im, w / 2 - 165, 210 - 165)
    return s.makeImageSnapshot()


def _placa_base(d, w, h):
    s, c = _sup(w, h); _vidrio(c, w, h, 64)
    txt = d.get("texto", ""); fn = F["tit"]; esc = min(1.0, (w - 80) / max(1, ancho(txt, fn)))
    c.save(); c.translate(w / 2, 450); c.scale(esc, esc)
    for k in range(6, 0, -1): texto(c, txt, k * 1.2, k * 2.0, fn, "#5A4318", alfa=.9)        # relieve dorado
    with capa(c, alfa=.5, blur=18): texto(c, txt, 0, 0, fn, ORO)
    texto(c, txt, 0, 0, fn, "#FFFFFF", paint=skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -70), (0, 70)], [color("#FFFFFF"), color(ORO2)])))
    c.restore()
    if d.get("sub"): texto(c, d["sub"], w / 2, 560, F["tit2"], "#AEB6C8")
    return s.makeImageSnapshot()


def placa_contador(d, t, u=1.0):
    """Cifra enorme con cada dígito en su ficha metálica; rueda con desenfoque vertical mientras u < 1 (guardada por texto)."""
    v = d.get("valor", 0) * u; txt = num_es(v)
    return _cache(("cont", d.get("titulo"), txt, round((1 - u) * 22)), lambda: _placa_contador(d, txt, u))


def _placa_contador(d, txt, u):
    n = len(txt)
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
    if d.get("icono") in ICONOS: ICONOS[d["icono"]](c, w - 90, 70, 26, 0.0)
    return s.makeImageSnapshot()
