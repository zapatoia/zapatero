"""Kit de componentes UI (tarjetas A oscura y B clara; lo aprovechan duelo y expediente). Todos dibujan en coordenadas absolutas o
alrededor de (0, 0) y reciben un TEMA. Las entradas animadas se envuelven con pop_en / subir_en.

Trampas de la ficha: el brillo es casi invisible (si se ve neón, ya te pasaste) y nada sale con fade: desaparece en seco.
"""
import math
from contextlib import contextmanager

import skia

from .tiempo import tabla, pop, POP_ALFA, POP_BLUR, clamp, cubic_out, quad_out
from .texto import fuente, texto, ancho, color
from .lienzo import capa, transf, relleno, trazo, brillo, rrc, rr, ruta, sombra_suave, degradado_lineal

TEMA_OSCURO = dict(nombre="oscuro", fondo="#040C14", tarjeta="#141C24", tarjeta2="#1A2430", borde="#2A333D", txt="#FFFFFF", gris="#8A929A", gris2="#5E666E",
                   verde="#2ECC71", rojo="#FE4A5E", amarillo="#FAD23E", cian="#22F2EA", azul="#4B9FFF", coral="#DA7656", brillo_borde=.40, sombra=0.0)
TEMA_CLARO = dict(nombre="claro", fondo="#F4F4FC", tarjeta="#FFFFFF", tarjeta2="#F4F5FA", borde="#E4E6EE", txt="#14161C", gris="#7A7F8C", gris2="#B4B8C4",
                  verde="#15B169", rojo="#FF032D", amarillo="#F2B90C", cian="#0FB5B0", azul="#2D69FF", coral="#DA7656", brillo_borde=.18, sombra=.10)


def pop_en(c, f, x, y, dibujo, rot=0.0, deriva=.0015):
    """Entrada POP medido (+17 % en f4, −4 % en f9) con alfa y desenfoque en 3 cuadros; luego deriva lenta. f<0: nada."""
    if f < 0: return
    al, bl = tabla(POP_ALFA, f), tabla(POP_BLUR, f)
    with capa(c, alfa=al, blur=bl):
        with transf(c, x, y, pop(f, deriva), rot): dibujo(c)


def subir_en(c, f, x, y, dibujo, dist=8, dur=5, blur=4):
    """Píldora/etiqueta: sube 6–10 px + alfa + desenfoque en 4–5 cuadros, ease-out."""
    if f < 0: return
    u = quad_out((f + 1) / dur)
    with capa(c, alfa=u, blur=blur * (1 - u) if u < 1 else 0):
        with transf(c, x, y + dist * (1 - u)): dibujo(c)


def tarjeta(c, cx, cy, w, h, T, estado=None, r=28, g=3, fill=None, alfa_brillo=None):
    """Relleno sólido con borde del color de estado y brillo exterior (blur 8–12 px, 40 %). En tema claro: sombra suave."""
    R = rrc(cx, cy, w, h, r); ab = T["brillo_borde"] if alfa_brillo is None else alfa_brillo
    if T["sombra"]: sombra_suave(c, skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h), r, 12, 26, T["sombra"])
    if estado: c.drawRRect(R, brillo(estado, 10, ab, g=g + 2))
    c.drawRRect(R, relleno(fill or T["tarjeta"]))
    c.drawRRect(R, trazo(estado or T["borde"], g if estado else 2))


def tile(c, cx, cy, lado, col, T, r=None, dibujo=None, relleno_alfa=.12, g=3, sobre=None, ab=None):
    """Icono: cuadro redondeado con borde de color y relleno al 12 %. dibujo(c) en coordenadas centradas."""
    r = lado * .24 if r is None else r; R = rrc(cx, cy, lado, lado, r)
    c.drawRRect(R, brillo(col, 10, T["brillo_borde"] if ab is None else ab, g=g + 2))
    c.drawRRect(R, relleno(sobre or T["tarjeta"])); c.drawRRect(R, relleno(col, relleno_alfa)); c.drawRRect(R, trazo(col, g))
    if dibujo:
        with transf(c, cx, cy): dibujo(c)


def etiqueta(c, txt, x, y, col, px=29, peso=700, tracking=.10, alfa=1.0, alinear="c"):
    texto(c, txt, x, y, fuente("Montserrat", peso, px), col, alinear, tracking, alfa)


def pildora(c, cx, cy, txt, T, col=None, extra=None, col_extra=None, px=28, icono=None, alto=None, fill=None, g=2.0):
    """Píldora con icono opcional y contador a la derecha («REQUISITO 1/3»). Devuelve el ancho."""
    fnt = fuente("Montserrat", 700, px); col = col or T["txt"]; h = alto or px * 2.0; t = .04
    w1 = ancho(txt, fnt, t); w2 = ancho(extra, fnt, t) + px * .5 if extra else 0; ic = px * 1.2 if icono else 0
    W_ = w1 + w2 + ic + px * 1.6
    R = rrc(cx, cy, W_, h, h / 2); c.drawRRect(R, relleno(fill or T["tarjeta"])); c.drawRRect(R, trazo(col_extra or col, g, .55))
    x = cx - W_ / 2 + px * .8
    if icono:
        with transf(c, x + ic * .36, cy): icono(c, px * .9, col_extra or col)
        x += ic
    texto(c, txt, x, cy, fnt, col, "i", t); x += w1 + px * .5
    if extra: texto(c, extra, x, cy, fnt, col_extra or col, "i", t)
    return W_


def sello(c, txt, col, px=66, pad=(34, 16), g=6, sigma=10, relleno_alfa=0.0, col_txt=None, check=False):
    """Sello alrededor de (0, 0), sin rotar (usa rot en pop_en: −10° según ficha). Borde 4–6 px con brillo, sin relleno."""
    fnt = fuente("Montserrat", 900, px); wt = ancho(txt, fnt, .01); ch = px * .95 if check else 0; w = wt + ch + pad[0] * 2; h = fnt.cap + pad[1] * 2 + 8; R = rrc(0, 0, w, h, 14)
    c.drawRRect(R, brillo(col, sigma, .55, g=g + 2))
    if relleno_alfa: c.drawRRect(R, relleno(col, relleno_alfa))
    c.drawRRect(R, trazo(col, g)); texto(c, txt, -ch / 2, 0, fnt, col_txt or col, "c", .01)
    if check:
        k = px / 22; x = wt / 2 + ch * .1; c.drawPath(ruta((x + 1 * k, 1 * k), (x + 7 * k, 7 * k), (x + 18 * k, -8 * k)), trazo(col_txt or col, 4.4 * k))
    return w


def anillo(c, cx, cy, r, g, u, col, base="#2B333B", sigma=8, a_brillo=.55):
    """Anillo contador: base gris + arco que arranca arriba en sentido horario. Punta redonda."""
    O = skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r)
    c.drawCircle(cx, cy, r, trazo(base, g))
    if u > 0:
        c.drawArc(O, -90, 360 * clamp(u), False, brillo(col, sigma, a_brillo * clamp(u * 1.3), g=g))
        c.drawArc(O, -90, 360 * clamp(u), False, trazo(col, g))


def barra(c, x, y, w, h, u, col, T=None, base=None):
    c.drawRRect(rr(x, y - h / 2, w, h, h / 2), relleno(base or (T["borde"] if T else "#2A333D")))
    if u > 0:
        ww = max(h, w * clamp(u)); R = rr(x, y - h / 2, ww, h, h / 2)
        c.drawRRect(R, brillo(col, 6, .45)); c.drawRRect(R, relleno(col))


def palomita(c, cx, cy, r, col="#2ECC71", tinta="#FFFFFF"):
    c.drawCircle(cx, cy, r, brillo(col, r * .35, .4)); c.drawCircle(cx, cy, r, relleno(col))
    k = r / 22; p = ruta((cx - 10 * k, cy + 1 * k), (cx - 3 * k, cy + 8 * k), (cx + 11 * k, cy - 7 * k))
    c.drawPath(p, trazo(tinta, 4.6 * k))


def equis(c, cx, cy, r, col="#FE4A5E", tinta="#FFFFFF"):
    c.drawCircle(cx, cy, r, brillo(col, r * .35, .4)); c.drawCircle(cx, cy, r, relleno(col)); k = r * .36
    c.drawLine(cx - k, cy - k, cx + k, cy + k, trazo(tinta, r * .2)); c.drawLine(cx + k, cy - k, cx - k, cy + k, trazo(tinta, r * .2))


def degr_avatar(c, cx, cy, r):
    """Avatar anónimo del comentario: degradado cian→rosa."""
    p = skia.Paint(AntiAlias=True, Shader=degradado_lineal((cx - r, cy - r), (cx + r, cy + r), ["#3EC6C0", "#F04E78"]))
    c.drawCircle(cx, cy, r, p)


def caja_comentario(c, cx, cy, w, h, escrito, placeholder, f_desde_escritura, enviado, T, cursor=True, col_envio=None):
    """Input blanco tipo comentario. escrito=texto ya tecleado; enviado=False mantiene el botón apagado hasta el final."""
    R = rrc(cx, cy, w, h, h / 2); c.drawRRect(R, brillo("#FFFFFF", 14, .12)); c.drawRRect(R, relleno("#FFFFFF")); ra = h * .30; x = cx - w / 2 + h * .52
    degr_avatar(c, x, cy, ra); x += ra + 24; fnt = fuente("Montserrat", 800 if escrito else 500, h * (.36 if escrito else .29))
    if escrito:
        a = texto(c, escrito, x, cy, fnt, "#14161C", "i", .01)
        if cursor and (f_desde_escritura // 8) % 2 == 0: c.drawRect(skia.Rect.MakeXYWH(x + a + 6, cy - fnt.cap * .75, 4, fnt.cap * 1.5), relleno("#14161C"))
    else:
        texto(c, placeholder, x, cy, fnt, "#9A9EA6", "i")
    bx = cx + w / 2 - h * .46; rb = h * .33; col = (col_envio or T["rojo"]) if enviado else "#E1E3E8"
    c.drawCircle(bx, cy, rb, relleno(col)); k = rb * .48
    c.drawPath(ruta((bx - k, cy - k * .1), (bx + k, cy - k), (bx + k * .1, cy + k), (bx - k * .1, cy + k * .1), cerrar=True), trazo("#FFFFFF" if enviado else "#FFFFFF", rb * .1))


# ------------------------------------------------------------------ iconos de línea (centrados en 0,0; s = lado aprox.)
def ic_personas(c, s, col, g=None):
    g = g or s * .075; k = s / 60; c.drawCircle(-7 * k, -11 * k, 10 * k, trazo(col, g)); c.drawCircle(14 * k, -9 * k, 7.5 * k, trazo(col, g))
    p = skia.Path(); p.moveTo(-25 * k, 20 * k); p.cubicTo(-25 * k, 2 * k, 11 * k, 2 * k, 11 * k, 20 * k); c.drawPath(p, trazo(col, g))
    p = skia.Path(); p.moveTo(14 * k, 5 * k); p.cubicTo(24 * k, 5 * k, 28 * k, 12 * k, 28 * k, 19 * k); c.drawPath(p, trazo(col, g))


def ic_ojo(c, s, col, g=None):
    g = g or s * .075; k = s / 60; p = skia.Path(); p.moveTo(-27 * k, 0); p.quadTo(0, -27 * k, 27 * k, 0); p.quadTo(0, 27 * k, -27 * k, 0); p.close()
    c.drawPath(p, trazo(col, g)); c.drawCircle(0, 0, 7.5 * k, relleno(col))


def ic_calendario(c, s, col, g=None):
    g = g or s * .075; k = s / 60; c.drawRRect(rrc(0, 3 * k, 46 * k, 42 * k, 7 * k), trazo(col, g)); c.drawLine(-23 * k, -7 * k, 23 * k, -7 * k, trazo(col, g))
    c.drawLine(-11 * k, -24 * k, -11 * k, -14 * k, trazo(col, g)); c.drawLine(11 * k, -24 * k, 11 * k, -14 * k, trazo(col, g))


def ic_chat(c, s, col, g=None):
    g = g or s * .08; k = s / 60; p = skia.Path(); p.addRRect(rrc(0, -4 * k, 50 * k, 36 * k, 8 * k))
    c.drawRRect(rrc(0, -4 * k, 50 * k, 36 * k, 8 * k), trazo(col, g)); c.drawPath(ruta((-14 * k, 15 * k), (-14 * k, 26 * k), (0, 15 * k)), trazo(col, g))


def ic_regalo(c, s, col, g=None):
    g = g or s * .075; k = s / 60; c.drawRRect(rrc(0, 9 * k, 42 * k, 30 * k, 4 * k), trazo(col, g)); c.drawRRect(rrc(0, -11 * k, 50 * k, 12 * k, 3 * k), trazo(col, g))
    c.drawLine(0, -17 * k, 0, 24 * k, trazo(col, g))
    for sg in (-1, 1):
        p = skia.Path(); p.moveTo(0, -17 * k); p.cubicTo(sg * 2 * k, -31 * k, sg * 20 * k, -29 * k, 0, -17 * k); c.drawPath(p, trazo(col, g))


def ic_play(c, s, col, g=None):
    k = s / 60; p = ruta((-13 * k, -19 * k), (20 * k, 0), (-13 * k, 19 * k), cerrar=True)
    c.drawPath(p, relleno(col)); c.drawPath(p, trazo(col, 3 * k))


def ic_lupa(c, s, col, g=None):
    g = g or s * .085; k = s / 60; c.drawCircle(-5 * k, -5 * k, 17 * k, trazo(col, g)); c.drawLine(8 * k, 8 * k, 23 * k, 23 * k, trazo(col, g * 1.2))


def ic_candado(c, s, col, g=None):
    g = g or s * .075; k = s / 60; c.drawRRect(rrc(0, 8 * k, 36 * k, 28 * k, 6 * k), trazo(col, g))
    p = skia.Path(); p.moveTo(-11 * k, -6 * k); p.lineTo(-11 * k, -12 * k); p.cubicTo(-11 * k, -28 * k, 11 * k, -28 * k, 11 * k, -12 * k); p.lineTo(11 * k, -6 * k); c.drawPath(p, trazo(col, g))


def ic_flecha_subir(c, s, col, g=None):
    g = g or s * .09; k = s / 60; c.drawLine(0, 20 * k, 0, -20 * k, trazo(col, g)); c.drawPath(ruta((-15 * k, -6 * k), (0, -21 * k), (15 * k, -6 * k)), trazo(col, g))
    c.drawLine(-22 * k, 27 * k, 22 * k, 27 * k, trazo(col, g))


def ic_estrella(c, s, col, g=None):
    k = s / 60; pts = []
    for i in range(10):
        r = (26 if i % 2 == 0 else 11) * k; a = -math.pi / 2 + i * math.pi / 5; pts.append((r * math.cos(a), r * math.sin(a)))
    c.drawPath(ruta(*pts, cerrar=True), relleno(col))


def ic_dolar(c, s, col, g=None):
    fnt = fuente("Montserrat", 900, s * .9); texto(c, "$", 0, 0, fnt, col, "c")
