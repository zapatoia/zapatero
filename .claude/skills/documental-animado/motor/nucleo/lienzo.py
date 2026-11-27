"""Lienzo skia sobre numpy y primitivas de dibujo compartidas (formas, capas, brillo, sombra)."""
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import skia

from .tiempo import W, H
from .texto import color


class Lienzo:
    """Superficie RGBA premultiplicada sobre un arreglo numpy. c.canvas para dibujar; c.arr es el arreglo (H, W, 4)."""
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.arr = np.zeros((h, w, 4), np.uint8)
        self.sup = skia.Surface(self.arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.canvas = self.sup.getCanvas()

    def fondo(self, rgb):
        """Copia un fondo ya hecho (H, W, 3 u, 4, uint8) o llena con un color '#hex'."""
        if isinstance(rgb, str): self.canvas.clear(color(rgb)); return
        if rgb.shape[2] == 3: self.arr[..., :3] = rgb; self.arr[..., 3] = 255
        else: self.arr[:] = rgb


def imagen_de(arr):
    """numpy (H, W, 4) RGBA uint8 → skia.Image (no premultiplicada)."""
    return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)


def cargar_imagen(ruta):
    """Python lee el archivo (una ruta con acentos en Windows no depende de skia). Si no existe: None, como antes."""
    try: datos = Path(ruta).read_bytes()
    except OSError: return None
    return skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(datos))


@contextmanager
def transf(c, x=0, y=0, escala=1.0, rot=0.0, ex=None, ey=None):
    """Mueve el origen a (x, y), rota (grados) y escala alrededor de ese punto."""
    c.save(); c.translate(x, y)
    if rot: c.rotate(rot)
    if ex is not None or ey is not None: c.scale(ex if ex is not None else escala, ey if ey is not None else escala)
    elif escala != 1.0: c.scale(escala, escala)
    yield c
    c.restore()


@contextmanager
def capa(c, alfa=1.0, blur=0.0, modo=None, filtro=None):
    """Capa aislada con alfa de grupo, desenfoque y modo de mezcla (p. ej. skia.BlendMode.kPlus para glow aditivo)."""
    if alfa >= .999 and blur <= 0 and modo is None and filtro is None:
        yield c; return
    p = skia.Paint(Alphaf=max(0.0, min(1.0, alfa)))
    if blur > 0: p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    if filtro is not None: p.setImageFilter(filtro)
    if modo is not None: p.setBlendMode(modo)
    c.saveLayer(None, p)
    yield c
    c.restore()


def relleno(col, alfa=1.0, **kw): return skia.Paint(AntiAlias=True, Color=color(col, alfa), **kw)
def trazo(col, g, alfa=1.0, redondo=True, **kw):
    return skia.Paint(AntiAlias=True, Color=color(col, alfa), Style=skia.Paint.kStroke_Style, StrokeWidth=g,
                      StrokeCap=skia.Paint.kRound_Cap if redondo else skia.Paint.kButt_Cap, StrokeJoin=skia.Paint.kRound_Join, **kw)
def brillo(col, sigma, alfa=1.0, g=None):
    """Pintura de halo: difusa por máscara (más barata que una capa con filtro). g = grosor si es trazo."""
    p = skia.Paint(AntiAlias=True, Color=color(col, alfa), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    if g is not None: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(g); p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def rr(x, y, w, h, r): return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
def rrc(cx, cy, w, h, r): return rr(cx - w / 2, cy - h / 2, w, h, r)


def sombra_contacto(c, x, y, rx, ry, alfa=.45, sigma=None, col="#000000"):
    """Elipse difusa bajo un objeto (diorama, camara-viaja)."""
    p = brillo(col, sigma if sigma is not None else ry * .6, alfa)
    c.drawOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry), p)


def sombra_suave(c, rect, r=28, dy=14, sigma=24, alfa=.45):
    c.drawRRect(skia.RRect.MakeRectXY(rect.makeOffset(0, dy), r, r), brillo("#000000", sigma, alfa))


def degradado_lineal(p0, p1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [color(x) for x in cols], pos)


def degradado_radial(cen, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*cen), r, [color(x) for x in cols], pos)


def ruta(*puntos, cerrar=False):
    p = skia.Path(); p.moveTo(*puntos[0])
    for q in puntos[1:]: p.lineTo(*q)
    if cerrar: p.close()
    return p
