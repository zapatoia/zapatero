"""Los 6 modos de subtítulo de las fichas. Todos: s = Modo(bloques, …); s.dibujar(canvas, f).

  bloques = bloques_de(palabras, "SI EL AGUA / NO SE *QUEDA")   ← cortes a mano (lo normal)
  bloques = bloques_auto(palabras, max_palabras=4)               ← por tamaño y pausas

| Modo              | Estilos                       | Mecánica                                                           |
|-------------------|-------------------------------|--------------------------------------------------------------------|
| FraseFija         | tarjetas A/B                     | frase entera, palabra que suena en verde en seco, 1 cuadro vacío   |
| PalabraSeleccion  | camara-viaja, diorama    | activa blanca, dicha gris, sin decir no existe, caja tipo Figma    |
| PalabraPorPalabra | tarjetas C, duelo             | entra gris 1–2 cuadros y sube a blanco; acumula; banda opcional    |
| Paginas           | títeres                    | páginas en MAYÚSCULAS sobre tira, fade 5 cuadros, contorno         |
| KaraokeCondensada | expediente                  | Barlow Condensed, caja amarilla que salta de palabra               |
| TituloFijo        | palitos, sonificación   | dos líneas fijas, línea 2 en color y con back-out (sin voz)        |
"""
import re

import skia

from .tiempo import f_de_t, norm, tabla, FRASE_ALFA, TITULO_BACK10, TITULO_ALFA, clamp, W
from .texto import fuente, texto, ancho, color, partir_lineas
from .lienzo import capa, relleno, trazo, rrc, brillo, transf


class Bloque:
    __slots__ = ("palabras", "f0", "f1", "clave")
    def __init__(self, palabras, f0, f1, clave=None): self.palabras, self.f0, self.f1, self.clave = palabras, f0, f1, clave or set()
    @property
    def textos(self): return [p["w"] for p in self.palabras]


def _cerrar(lista, fin_f):
    for a, b in zip(lista, lista[1:]): a.f1 = b.f0
    if lista: lista[-1].f1 = fin_f
    return lista


def bloques_de(palabras, texto_cortes, fin_f=None, primero_en_0=True):
    """`texto_cortes`: palabras del guion con «/» entre bloques y *clave* opcional. Se valida contra palabras.json."""
    trozos = [x.strip() for x in re.split(r"/", texto_cortes) if x.strip()]
    out, i = [], 0
    for tz in trozos:
        ws = tz.split(); ps = palabras[i:i + len(ws)]
        for a, b in zip(ws, ps):
            if norm(a.strip("*")) != norm(b["w"]): raise ValueError(f"Subtítulo «{a}» ≠ voz «{b['w']}» (palabra {i})")
        if len(ps) < len(ws): raise ValueError(f"Faltan palabras para «{tz}»")
        out.append(Bloque(ps, f_de_t(ps[0]["s"]), 0, {k for k, a in enumerate(ws) if a.startswith("*")})); i += len(ws)
    if i != len(palabras): raise ValueError(f"Subtítulos: {i} palabras de {len(palabras)}")
    if primero_en_0 and out: out[0].f0 = 0
    return _cerrar(out, fin_f if fin_f is not None else f_de_t(palabras[-1]["e"]) + 1)


def bloques_auto(palabras, max_palabras=4, max_chars=26, pausa=.28, fin_f=None):
    out, cur = [], []
    for i, p in enumerate(palabras):
        cur.append(p); sig = palabras[i + 1] if i + 1 < len(palabras) else None
        n = sum(len(x["w"]) + 1 for x in cur)
        if sig is None or len(cur) >= max_palabras or n + len(sig["w"]) > max_chars or sig["s"] - p["e"] > pausa or p["w"][-1] in ".,:;?!":
            out.append(Bloque(cur, f_de_t(cur[0]["s"]), 0)); cur = []
    if out: out[0].f0 = 0
    return _cerrar(out, fin_f if fin_f is not None else f_de_t(palabras[-1]["e"]) + 1)


def _limpia(w): return re.sub(r"^[«\"(]+|[»\".,:;)…]+$", "", w) or w


class _Modo:
    def __init__(self, bloques): self.bloques = bloques
    def bloque_en(self, f):
        for b in self.bloques:
            if b.f0 <= f < b.f1: return b
        return None
    @staticmethod
    def activa(b, f):
        """Índice de la palabra que suena (se queda encendida hasta que arranca la siguiente)."""
        k = -1
        for i, p in enumerate(b.palabras):
            if f_de_t(p["s"]) <= f: k = i
        return k


def _maqueta(ws, fnt, esp, ancho_max, cx, cy, inter, tracking=0.0):
    """Posiciones (x_izq, y_centro, ancho) de cada palabra; bloque maquetado antes de mostrarse, así no salta."""
    lineas = partir_lineas(ws, fnt, ancho_max, esp, tracking); pos = [None] * len(ws)
    y = cy - (len(lineas) - 1) * inter / 2
    for L in lineas:
        an = [ancho(ws[i], fnt, tracking) for i in L]; tot = sum(an) + esp * (len(L) - 1); x = cx - tot / 2
        for i, a in zip(L, an): pos[i] = (x, y, a); x += a + esp
        y += inter
    return pos


class FraseFija(_Modo):
    """tarjetas A. Frase fija de 2–4 palabras; aparece en 4 cuadros; la que suena pasa a verde en seco; corte con 1 cuadro vacío."""
    def __init__(self, bloques, y=300, fnt=None, activo="#2ECC71", base="#FFFFFF", espacio=2.0, inter=1.05, ancho_max=990, vacio=1, sombra=(3, 5, .55)):
        super().__init__(bloques); self.y, self.activo, self.base, self.vacio, self.sombra = y, activo, base, vacio, sombra
        self.fnt = fnt or fuente("Montserrat", 800, 68); self.ancho_max = ancho_max
        self.esp = ancho(" ", self.fnt) * espacio; self.inter = self.fnt.px * inter

    def dibujar(self, c, f):
        b = self.bloque_en(f)
        if b is None or (f >= b.f1 - self.vacio and b is not self.bloques[-1] and b.f1 - b.f0 > 6): return
        ws = [_limpia(w).upper() for w in b.textos]; pos = _maqueta(ws, self.fnt, self.esp, self.ancho_max, 540, self.y, self.inter)
        al = tabla(FRASE_ALFA, f - b.f0) if b.f0 > 0 else 1.0; k = self.activa(b, f)
        for i, (w, (x, y, _)) in enumerate(zip(ws, pos)):
            texto(c, w, x, y, self.fnt, self.activo if i == k else self.base, "i", alfa=al, sombra=self.sombra)


class PalabraSeleccion(_Modo):
    """camara-viaja / diorama. Una palabra blanca Bold; lo dicho gris Medium; lo no dicho no existe. *clave* lleva caja azul de selección."""
    def __init__(self, bloques, y=400, familia="Figtree", px=70, inter=81, gris="#888198", ancho_max=820, azul="#2F8BFF", caja_alto=84, velo=None):
        super().__init__(bloques); self.y, self.gris, self.azul, self.inter, self.ancho_max, self.caja_alto, self.velo = y, gris, azul, inter, ancho_max, caja_alto, velo
        self.f_on = fuente(familia, 700, px); self.f_off = fuente(familia, 500, px); self.esp = ancho(" ", self.f_on)

    def _velo(self, c):
        if self.velo is None: return
        y0, y1, a = self.velo
        p = skia.Paint(Shader=skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [color("#000000", a), color("#000000", 0)]))
        c.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), p)

    def dibujar(self, c, f):
        self._velo(c); b = self.bloque_en(f)
        if b is None: return
        ws = b.textos; pos = _maqueta(ws, self.f_on, self.esp, self.ancho_max, 540, self.y, self.inter); k = self.activa(b, f)
        for i in range(k + 1):
            x, y, a = pos[i]; d = f - f_de_t(b.palabras[i]["s"])
            if i == k:
                if d < 2:
                    with capa(c, alfa=.5, blur=6 / (d + 1)): texto(c, ws[i], x, y, self.f_on, "#FFFFFF", "i")
                else: texto(c, ws[i], x, y, self.f_on, "#FFFFFF", "i")
            else: texto(c, ws[i], x, y, self.f_off, self.gris, "i")
            if i in b.clave and d >= 2:
                h = self.caja_alto; R = skia.Rect.MakeLTRB(x - 9, y - h / 2, x + a + 9, y + h / 2)
                c.drawRoundRect(R, 6, 6, trazo(self.azul, 3))
                for px_, py_ in ((R.left(), R.top()), (R.right(), R.bottom())):
                    c.drawCircle(px_, py_, 8, relleno("#FFFFFF")); c.drawCircle(px_, py_, 8, trazo(self.azul, 3))


class PalabraPorPalabra(_Modo):
    """tarjetas C/B, duelo. MAYÚSCULAS 72 px; cada palabra entra gris (alfa 40 %) 1–2 cuadros y sube a blanco; se acumula. Banda opcional."""
    def __init__(self, bloques, y=1300, fnt=None, ancho_max=940, banda=None, espacio=1.4, entrada=2, contorno=None, color_palabra=None):
        super().__init__(bloques); self.y, self.ancho_max, self.banda, self.entrada, self.contorno = y, ancho_max, banda, entrada, contorno
        self.fnt = fnt or fuente("Montserrat", 800, 72); self.esp = ancho(" ", self.fnt) * espacio; self.color_palabra = color_palabra or (lambda w: "#FFFFFF")

    def dibujar(self, c, f):
        if self.banda:
            col, alto, a = self.banda
            cu = skia.GradientShader.MakeLinear([skia.Point(0, self.y - alto / 2), skia.Point(0, self.y + alto / 2)],
                                                [color(col, 0), color(col, a), color(col, a), color(col, 0)], [0, .3, .7, 1])
            c.drawRect(skia.Rect.MakeXYWH(0, self.y - alto / 2, W, alto), skia.Paint(Shader=cu))
        b = self.bloque_en(f)
        if b is None: return
        ws = [_limpia(w).upper() for w in b.textos]; pos = _maqueta(ws, self.fnt, self.esp, self.ancho_max, 540, self.y, self.fnt.px * 1.08)
        for i, w in enumerate(ws):
            d = f - f_de_t(b.palabras[i]["s"])
            if d < 0 and not (i == 0 and b.f0 == 0): continue
            al = .4 + .6 * clamp(d / self.entrada); x, y, _ = pos[i]; col = self.color_palabra(w)
            if self.contorno:
                texto(c, w, x, y, self.fnt, "#000000", "i", alfa=al, paint=trazo(self.contorno[0], self.contorno[1], al))
            texto(c, w, x, y, self.fnt, col, "i", alfa=al)


class Paginas(_Modo):
    """títeres. Páginas en MAYÚSCULAS, centradas, sobre tira con bordes difuminados; fade lineal de 5 cuadros; contorno oscuro. Color por rol."""
    def __init__(self, bloques, y=1536, fnt=None, inter=68, ancho_max=650, tira=(1410, 1665, "#000000", .85), contorno=("#000000", 5), color_rol=None, fade=5):
        super().__init__(bloques); self.y, self.inter, self.ancho_max, self.tira, self.contorno, self.color_rol, self.fade = y, inter, ancho_max, tira, contorno, color_rol or (lambda b: "#FFFFFF"), fade
        self.fnt = fnt or fuente("Montserrat", 800, 64)

    def dibujar(self, c, f):
        if self.tira:
            a, b_, col, al = self.tira; d = 30 / (b_ - a)
            s = skia.GradientShader.MakeLinear([skia.Point(0, a), skia.Point(0, b_)], [color(col, 0), color(col, al), color(col, al), color(col, 0)], [0, d, 1 - d, 1])
            c.drawRect(skia.Rect.MakeLTRB(0, a, W, b_), skia.Paint(Shader=s))
        b = self.bloque_en(f)
        if b is None: return
        al = clamp((f - b.f0 + 1) / self.fade); ws = [w.upper() for w in b.textos]
        L = partir_lineas(ws, self.fnt, self.ancho_max); y = self.y - (len(L) - 1) * self.inter / 2; col = self.color_rol(b)
        for li in L:
            s_ = " ".join(ws[i] for i in li)
            if self.contorno: texto(c, s_, 540, y, self.fnt, "#000", "c", paint=trazo(self.contorno[0], self.contorno[1], al))
            texto(c, s_, 540, y, self.fnt, col, "c", alfa=al); y += self.inter


class KaraokeCondensada(_Modo):
    """expediente. Barlow Condensed en MAYÚSCULAS con tracking +3 %; caja amarilla #FFC933 con texto negro que salta a cada palabra
    en 1 cuadro; *clave* ya dicha queda en amarillo. Entrada: fundido 3 cuadros + subida 12 px; sale en corte directo. Sombra difusa."""
    def __init__(self, bloques, y=1425, px=80, inter=90, ancho_max=720, amarillo="#FFC933", peso=700, entrada=3, subida=12):
        super().__init__(bloques); self.y, self.inter, self.ancho_max, self.am, self.entrada, self.subida = y, inter, ancho_max, amarillo, entrada, subida
        self.fnt = fuente("BarlowCondensed", peso, px); self.track = .03; self.esp = ancho(" ", self.fnt, self.track) * 1.6

    def dibujar(self, c, f):
        b = self.bloque_en(f)
        if b is None: return
        ws = [_limpia(w).upper() for w in b.textos]; pos = _maqueta(ws, self.fnt, self.esp, self.ancho_max, 540, self.y, self.inter, self.track)
        d = f - b.f0; al = clamp((d + 1) / self.entrada) if b.f0 > 0 else 1.0; dy = self.subida * (1 - clamp((d + 1) / self.entrada)) if b.f0 > 0 else 0
        k = self.activa(b, f)
        for i, (w, (x, y, a)) in enumerate(zip(ws, pos)):
            y += dy
            if i == k:
                c.drawRoundRect(skia.Rect.MakeLTRB(x - 10, y - self.fnt.cap / 2 - 11, x + a + 10, y + self.fnt.cap / 2 + 11), 6, 6, relleno(self.am, al))
                texto(c, w, x, y, self.fnt, "#000000", "i", self.track, al)
            else:
                col = self.am if i in b.clave and i < k else "#FFFFFF"
                texto(c, w, x, y, self.fnt, col, "i", self.track, al, sombra=(0, 8, .8))


class TituloFijo:
    """palitos / sonificación. Sin voz: dos líneas fijas en una ventana de cuadros.
    títulos = [dict(l1="¿CUÁNTOS LADRILLOS", l2="LLEVAS?", col2="#FF6E7E", f0=0, f1=90, retraso=4)]; f0=0 → la línea 1 ya está en el cuadro 0."""
    def __init__(self, titulos, fnt=None, y1=402, y2=493, tracking=.14, halo=(6, .4), salida=5, curva_l2=True):
        self.titulos, self.y1, self.y2, self.tracking, self.halo, self.salida, self.curva = titulos, y1, y2, tracking, halo, salida, curva_l2
        self.fnt = fnt or fuente("JetBrainsMono", 700, 63)

    def _linea(self, c, s, y, col, al, esc):
        with transf(c, 540, y, esc):
            if self.halo:
                sg, a = self.halo; bl = brillo(col, sg, a * al)
                texto(c, s, 0, 0, self.fnt, col, "c", self.tracking, paint=bl)
            texto(c, s, 0, 0, self.fnt, col, "c", self.tracking, al)

    def dibujar(self, c, f):
        for t in self.titulos:
            if not (t["f0"] <= f < t["f1"]): continue
            d = f - t["f0"]; sal = clamp((t["f1"] - f) / self.salida) if self.salida else 1.0
            ini = t["f0"] == 0
            e1 = tabla((1.077, 1.04, 1.01, 1.0), d) if ini else 1.0
            a1 = 1.0 if ini else clamp((d + 1) / 4)
            if t.get("l1"): self._linea(c, t["l1"], self.y1, t.get("col1", "#FFFFFF"), a1 * sal, e1)
            if t.get("l2"):
                r = d - t.get("retraso", 4 if ini else 8)
                if r >= 0:
                    e2 = tabla(TITULO_BACK10, r) if self.curva else 1.0
                    self._linea(c, t["l2"], self.y2 if t.get("l1") else self.y1, t.get("col2", "#35B3A4"), tabla(TITULO_ALFA, r) * sal, e2)
