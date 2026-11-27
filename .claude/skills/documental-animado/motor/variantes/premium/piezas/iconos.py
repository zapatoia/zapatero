"""ICONOS del estilo premium: vectoriales con volumen (degradado de 3 tonos, brillo especular, halo de su color), animados con t.

Uso: ICONOS[nombre](c, x, y, s, t, **extra)   (s = radio aproximado en px)
Para añadir uno: función con la misma firma + entrada en ICONOS + línea en LEEME.md (catálogo).
"""
import math
import skia

from nucleo.texto import color
from nucleo.lienzo import capa, relleno, trazo


def _px(c, blur):
    """Convierte un desenfoque en píxeles de pantalla a unidades locales (los iconos se dibujan escalados: sin esto el blur se multiplica por s)."""
    return blur / max(1e-6, abs(c.getTotalMatrix().getScaleX()))


def capa_px(c, alfa, blur):
    return capa(c, alfa=alfa, blur=_px(c, blur))


def _halo(c, p, col, a=.55, blur=26):
    with capa_px(c, a, blur): c.drawPath(p, relleno(col))


def corazon(c, x, y, s, t, lpm=70, **_):
    late = 1 + .07 * max(0, math.sin(t * 2 * math.pi * lpm / 60)) ** 8
    c.save(); c.translate(x, y); c.scale(s * late, s * late)
    p = skia.Path(); p.moveTo(0, .38); p.cubicTo(-1.05, -.25, -.55, -1.05, 0, -.55); p.cubicTo(.55, -1.05, 1.05, -.25, 0, .38); p.close()
    _halo(c, p, "#FF3B4A")
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-.25, -.45), 1.1, [color("#FF8A8F"), color("#E0182B"), color("#5E0610")], [0, .5, 1])))
    c.drawOval(skia.Rect.MakeXYWH(-.52, -.62, .3, .18), relleno("#FFFFFF", .45))
    c.restore()


def pulmones(c, x, y, s, t, rpm=15, **_):
    r = 1 + .06 * math.sin(t * 2 * math.pi * rpm / 60 * 2)
    c.save(); c.translate(x, y); c.scale(s, s)
    for a_, b_ in (((0, -1.0), (0, -.35)), ((0, -.35), (-.28, -.15)), ((0, -.35), (.28, -.15))):
        c.drawLine(*a_, *b_, trazo("#E9ECF3", .08))
    for sx in (-1, 1):
        c.save(); c.translate(sx * .5, .12); c.scale(r, r)
        p = skia.Path(); p.addOval(skia.Rect.MakeXYWH(-.38, -.62, .76, 1.24))
        _halo(c, p, "#5FC8FF", .5, 24)
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-.12 * sx, -.3), .95, [color("#BDEBFF"), color("#3D8BFF"), color("#0D2A6E")], [0, .55, 1])))
        c.drawOval(skia.Rect.MakeXYWH(-.2, -.48, .16, .26), relleno("#FFFFFF", .4))
        c.restore()
    c.restore()


def ojo(c, x, y, s, t, **_):
    ph = t % 3.2; cierre = max(0.0, 1 - abs(ph - 1.6) / .09) if abs(ph - 1.6) < .09 else 0.0
    c.save(); c.translate(x, y); c.scale(s, s * (1 - .92 * cierre))
    p = skia.Path(); p.moveTo(-1, 0); p.quadTo(0, -.95, 1, 0); p.quadTo(0, .95, -1, 0); p.close()
    _halo(c, p, "#2ED47A", .5, 24)
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -.5), (0, .5)], [color("#FFFFFF"), color("#C9D3EA")])))
    c.save(); c.clipPath(p, doAntiAlias=True)
    c.drawCircle(0, 0, .42, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((0, 0), .42, [color("#0B3D2A"), color("#2ED47A"), color("#0E5A3A")], [0, .6, 1])))
    c.drawCircle(0, 0, .17, relleno("#05070A")); c.drawCircle(-.13, -.14, .07, relleno("#FFFFFF", .9))
    c.restore(); c.drawPath(p, trazo("#FFFFFF", .03, .6)); c.restore()


def gota(c, x, y, s, t, nivel=1.0, col="#E0182B", **_):
    """Gota con líquido dentro que sube hasta `nivel` (0–1) y se mueve como una ola."""
    c.save(); c.translate(x, y); c.scale(s, s)
    p = skia.Path(); p.moveTo(0, -1.1); p.cubicTo(.35, -.55, .78, -.1, .78, .3); p.cubicTo(.78, .78, .4, 1.0, 0, 1.0)
    p.cubicTo(-.4, 1.0, -.78, .78, -.78, .3); p.cubicTo(-.78, -.1, -.35, -.55, 0, -1.1); p.close()
    _halo(c, p, col, .12 + .35 * max(0.0, min(1.0, nivel)), 24)
    c.drawPath(p, relleno("#0A0D16", .85))
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -1), (0, 1)], [color("#FFFFFF", .10), color("#FFFFFF", .04)])))
    c.save(); c.clipPath(p, doAntiAlias=True)
    yn = 1.0 - 2.1 * max(0.0, min(1.0, nivel)); ola = skia.Path(); ola.moveTo(-1, 1.2)
    for i in range(0, 41):
        xx = -1 + i / 20; ola.lineTo(xx, yn + .05 * math.sin(xx * 6 + t * 5))
    ola.lineTo(1, 1.2); ola.close()
    c.drawPath(ola, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, yn), (0, 1)], [color("#FF5A66"), color(col), color("#4A0510")], [0, .4, 1])))
    c.restore()
    c.drawPath(p, trazo("#FFFFFF", .035, .7))
    c.drawOval(skia.Rect.MakeXYWH(-.45, -.25, .16, .38), relleno("#FFFFFF", .35))
    c.restore()


def reloj(c, x, y, s, t, **_):
    """Cronómetro con aguja que barre un minuto en 60 s (se puede acelerar con t escalado)."""
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawRoundRect(skia.Rect.MakeXYWH(-.16, -1.28, .32, .2), .05, .05, relleno("#C9D3EA"))
    p = skia.Path(); p.addCircle(0, 0, 1.0)
    _halo(c, p, "#E8B04A", .4, 30)
    c.drawCircle(0, 0, 1.0, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-.3, -.4), 1.4, [color("#3A4152"), color("#151A26"), color("#05070C")], [0, .6, 1])))
    c.drawCircle(0, 0, 1.0, trazo("#E9ECF3", .07, .95)); c.drawCircle(0, 0, .86, trazo("#FFFFFF", .015, .3))
    for k in range(60):
        a = math.radians(k * 6); r0 = .72 if k % 5 == 0 else .78
        c.drawLine(r0 * math.sin(a), -r0 * math.cos(a), .84 * math.sin(a), -.84 * math.cos(a), trazo("#FFFFFF", .03 if k % 5 == 0 else .012, .8))
    a = math.radians((t * 6) % 360)
    with capa_px(c, .6, 8): c.drawLine(0, 0, .8 * math.sin(a), -.8 * math.cos(a), trazo("#E8B04A", .06))
    c.drawLine(-.15 * math.sin(a), .15 * math.cos(a), .8 * math.sin(a), -.8 * math.cos(a), trazo("#FFD98A", .035))
    c.drawCircle(0, 0, .06, relleno("#FFD98A"))
    c.drawArc(skia.Rect.MakeXYWH(-.9, -.9, 1.8, 1.8), 200, 50, False, trazo("#FFFFFF", .04, .25))
    c.restore()


def globulo(c, x, y, s, t, **_):
    """Glóbulo rojo: disco bicóncavo (borde claro, centro hundido)."""
    c.save(); c.translate(x, y); c.scale(s, s * .9)
    p = skia.Path(); p.addCircle(0, 0, 1)
    _halo(c, p, "#FF3B4A", .45, 22)
    c.drawCircle(0, 0, 1, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((0, 0), 1, [color("#7A0A16"), color("#C8142A"), color("#FF5A66"), color("#9E0E1E")], [0, .45, .8, 1])))
    c.drawOval(skia.Rect.MakeXYWH(-.6, -.75, .55, .3), relleno("#FFFFFF", .3))
    c.restore()


def aire(c, x, y, s, t, **_):
    """Corrientes de aire: tres trazos curvos que fluyen."""
    c.save(); c.translate(x, y); c.scale(s, s)
    for k, (yy, ln) in enumerate(((-.45, 1.5), (0, 1.8), (.45, 1.3))):
        p = skia.Path(); p.moveTo(-ln / 2, yy); p.cubicTo(-ln / 6, yy - .2, ln / 6, yy + .2, ln / 2, yy)
        p.arcTo(skia.Rect.MakeXYWH(ln / 2 - .18, yy - .36, .36, .36), 90, -270, False)
        ph = (t * .8 + k * .3) % 1
        pa = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=.09, StrokeCap=skia.Paint.kRound_Cap,
                        Shader=skia.GradientShader.MakeLinear([(-ln / 2, 0), (ln / 2, 0)], [color("#5FC8FF", .3), color("#E9F6FF"), color("#5FC8FF", .3)], [0, ph, 1]))
        with capa_px(c, .5, 10): c.drawPath(p, pa)
        c.drawPath(p, pa)
    c.restore()


ICONOS = dict(corazon=corazon, pulmones=pulmones, ojo=ojo, gota=gota, reloj=reloj, globulo=globulo, aire=aire)
