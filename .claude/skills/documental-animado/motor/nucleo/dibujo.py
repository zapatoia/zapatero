"""Dibujo trazado por notas (sonificación serie C: una línea que dibuja, una nota por trazo).

  d = Dibujo(); d.trazo(ruta_skia, f0=nota + 1, dur=12, col="#F2C27E", g=6)   # el trazo arranca en la nota +1 cuadro
  d.dibujar(c, f)                                                             # pinta lo ya trazado y el pincel (punto con pulso)

trim(c, ruta, u, pintura) dibuja la ruta hasta la fracción u (0–1). Sirve también para cualquier «trim path» (croquis de expediente).
"""
import skia

from .tiempo import clamp, cubic_out, quad_out, tabla
from .lienzo import relleno, trazo, brillo


def _contornos(ruta_sk):
    m = skia.PathMeasure(ruta_sk, False)
    while True:
        yield m
        if not m.nextContour(): break


def largo_de(ruta_sk):
    return sum(m.getLength() for m in _contornos(ruta_sk))


def parcial(ruta_sk, u0, u1=None):
    """Tramo de la ruta entre las fracciones u0 y u1 (si u1 es None, de 0 a u0). → (skia.Path, (x, y) del punto final)"""
    if u1 is None: u0, u1 = 0.0, u0
    tot = largo_de(ruta_sk); a, b = tot * clamp(u0), tot * clamp(u1); out = skia.Path(); acum = 0.0; fin = None
    for m in _contornos(ruta_sk):
        L = m.getLength()
        if b > a and acum + L >= a and acum <= b:
            d0, d1 = max(0, a - acum), min(L, b - acum); m.getSegment(d0, d1, out, True); pos = m.getPosTan(d1)
            if pos: fin = (pos[0].x(), pos[0].y())
        acum += L
    return out, fin


def trim(c, ruta_sk, u, pintura):
    if u <= 0: return None
    if u >= 1: c.drawPath(ruta_sk, pintura); return None
    p, fin = parcial(ruta_sk, u); c.drawPath(p, pintura); return fin


class Dibujo:
    """Secuencia de trazos. Pincel = punto que viaja con el trazo activo (pico +13 % al nacer, medido en cereza)."""
    PICO = (1.0, 1.05, 1.10, 1.13, 1.08, 1.03, 1.0)

    def __init__(self, r_pincel=14, col_pincel="#FFF4DC", brillo_sigma=10, brillo_alfa=.5):
        self.trazos = []; self.r, self.col, self.sg, self.ba = r_pincel, col_pincel, brillo_sigma, brillo_alfa

    def trazo(self, ruta_sk, f0, dur=10, col="#F2C27E", g=6, curva=quad_out, relleno_col=None):
        self.trazos.append(dict(p=ruta_sk, f0=f0, dur=dur, col=col, g=g, c=curva, fill=relleno_col)); return self

    def activo(self, f):
        act = None
        for t in self.trazos:
            if t["f0"] <= f: act = t
        return act

    def dibujar(self, c, f, pincel=True, con_brillo=True):
        for t in self.trazos:
            d = f - t["f0"]
            if d < 0: continue
            u = t["c"](d / max(t["dur"], 1))
            if t["fill"] and u >= 1: c.drawPath(t["p"], relleno(t["fill"]))
            if con_brillo: trim(c, t["p"], u, brillo(t["col"], self.sg, self.ba, g=t["g"]))
            trim(c, t["p"], u, trazo(t["col"], t["g"]))
        if pincel:
            a = self.activo(f)
            if a:
                d = f - a["f0"]; u = a["c"](d / max(a["dur"], 1)); _, fin = parcial(a["p"], max(u, .001))
                if fin:
                    r = self.r * tabla(self.PICO, d)
                    c.drawCircle(fin[0], fin[1], r * 1.8, brillo(self.col, r, self.ba)); c.drawCircle(fin[0], fin[1], r * .5, relleno(self.col))
