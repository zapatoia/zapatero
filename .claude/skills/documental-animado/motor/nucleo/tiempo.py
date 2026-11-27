"""Tiempo y animación del núcleo de reels animados. Todo es función pura del cuadro: nada guarda estado entre cuadros.

Solo depende de la biblioteca estándar (lo importa también voz.py, que corre en otro entorno).
Curvas: `u` normalizado 0–1 → 0–1. Tablas medidas de las fichas: valor por cuadro relativo, con `tabla(T, f)`.
"""
import json, math, re, unicodedata
from pathlib import Path

W, H, FPS = 1080, 1920, 30


def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, u): return a + (b - a) * u
def f_de_t(t): return int(round(t * FPS))
def t_de_f(f): return f / FPS
def prog(f, f0, dur): return clamp((f - f0) / max(dur, 1e-6))


# ------------------------------------------------------------------ curvas (u de 0 a 1)
def lineal(u): return clamp(u)
def quad_out(u): u = clamp(u); return 1 - (1 - u) ** 2
def quad_in(u): u = clamp(u); return u * u
def quad_inout(u): u = clamp(u); return 2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2     # cámara de diorama (20 f)
def cubic_out(u): u = clamp(u); return 1 - (1 - u) ** 3                                        # contadores, cámara de títeres (40 f)
def cubic_in(u): u = clamp(u); return u ** 3
def cubic_inout(u): u = clamp(u); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def seno_inout(u): u = clamp(u); return -(math.cos(math.pi * u) - 1) / 2                        # paneo de palitos, camara-viaja
def expo_out(u): u = clamp(u); return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)
def back_out(u, s=1.70158):
    """easeOutBack. s=1.70 ≈ +10 % (duelo); s≈2.5 para el título de palitos."""
    u = clamp(u) - 1; return u * u * ((s + 1) * u + s) + 1
def resorte(f, k=0.2, w=0.52, f0=1.3):
    """Pop de resorte de títeres medido: s(f) = 1 − e^(−k(f+f0))·cos(w(f+f0)). +29 % y rebote −8 % con los valores por defecto."""
    if f < 0: return 0.0
    return 1 - math.exp(-k * (f + f0)) * math.cos(w * (f + f0))
def gravedad(f, g=17.0, v0=0.0):
    """Px caídos tras f cuadros. diorama midió g≈17 px/f² (1080×1920)."""
    f = max(f, 0); return v0 * f + 0.5 * g * f * f


CURVAS = dict(lineal=lineal, quad_out=quad_out, quad_in=quad_in, quad_inout=quad_inout, cubic_out=cubic_out, cubic_in=cubic_in,
              cubic_inout=cubic_inout, seno_inout=seno_inout, expo_out=expo_out, back_out=back_out)


# ------------------------------------------------------------------ tablas medidas (valor por cuadro)
POP = (0, .56, .90, 1.11, 1.17, 1.15, 1.08, 1.02, .98, .96, .97, .98, .99, 1.0)          # tarjetas: +17 % en f4, −4 % en f9
POP_ALFA = (0, .4, .8, 1.0)                                                               # tarjetas: alfa en 3 cuadros
POP_BLUR = (6, 4, 2, 0)                                                                   # tarjetas: desenfoque 6→0 px
TITULO_BACK10 = (.38, .62, .95, 1.06, 1.10, 1.09, 1.05, 1.01, 1.0)                        # palitos línea 2 del título
TITULO_ALFA = (.05, .30, .60, 1.0)
FRASE_ALFA = (.25, .7, .9, 1.0)                                                           # tarjetas: frase de karaoke
FLASH_C = (.55, .49, .43, .37, .30, .22, .08, 0)                                          # tarjetas C: destello sobre corte
FLASH_AV = (.51, .42, .34, .26, .20, .14, .10, .06, .05, .03, 0)                          # expediente
SELLO_AV = (1.6, 1.3, 1.15, 1.0)                                                          # expediente: escala
SELLO_AV_ALFA = (.15, .3, .7, 1.0)
DIGITO_AV = (1.5, 1.25, 1.1, 1.05, 1.0)                                                   # expediente: conteo 3-2-1
TARJETA_AV_X = (-108, -36, 0, 15, 12, 3, 0)                                               # expediente: entrada de tarjeta
SELLO_DD = (1.174, 1.10, 1.045, 1.012, 1.0)                                               # diorama


def tabla(T, f, fuera=None):
    """Valor interpolado de una tabla por cuadro relativo. Antes de 0 da T[0] (o `fuera`); después del final da T[-1]."""
    if f < 0: return T[0] if fuera is None else fuera
    if f >= len(T) - 1: return T[-1]
    i = int(f); return T[i] + (T[i + 1] - T[i]) * (f - i)


def pop(f, deriva=0.0015, deriva_max=0.06):
    """Escala POP medido + deriva lenta (+0.15 %/cuadro) tras asentarse. f = cuadros desde la entrada; f<0 → 0."""
    if f < 0: return 0.0
    if f < len(POP) - 1: return tabla(POP, f)
    return 1.0 + min((f - (len(POP) - 1)) * deriva, deriva_max)


def contador(f, dur, valor, de=0.0):
    """Ease-out cúbico medido (medido): v = V·(1−(1−t)³). dur en cuadros (tarjetas 54; duelo 30)."""
    return de + (valor - de) * cubic_out(f / max(dur, 1))


# ------------------------------------------------------------------ anclas a palabras
def norm(w):
    w = unicodedata.normalize("NFD", str(w).lower().replace("ñ", "\0"))
    w = "".join(c for c in w if unicodedata.category(c) != "Mn").replace("\0", "ñ")
    return re.sub(r"[^a-z0-9ñ%]", "", w)


class LineaTiempo:
    """palabras = [{"w","s","e"}]. Resuelve anclas a segundos o a cuadros.

      12.3            segundos absolutos
      "palabra"       cuando EMPIEZA su siguiente aparición desde `desde`
      "palabra#2"     la 2.ª aparición desde `desde`
      "palabra>"      cuando TERMINA
      "palabra+0.2"   desplazamiento en s (también "palabra-0.1" y "palabra>+6f" en cuadros)
      "+0.2"          relativo a `base` (p. ej. el elemento anterior)
      "@0.4"          s desde el inicio del tramo (`t0`)
      "marca:climax"  marca con nombre (estilos sin voz): tl.marca("climax", 26.67)
    """

    def __init__(self, palabras=None, fin=None, alias=None):
        self.pal = palabras or []
        self.n = [norm(p["w"]) for p in self.pal]
        self.alias = {norm(k): norm(v) for k, v in (alias or {}).items()}
        self.marcas = {}
        self.fin = fin if fin is not None else (self.pal[-1]["e"] if self.pal else 0.0)

    @classmethod
    def de_proyecto(cls, proy, alias=None):
        return cls(json.loads((Path(proy) / "palabras.json").read_text(encoding="utf-8-sig")), alias=alias)

    def marca(self, nombre, t): self.marcas[nombre] = float(t); return self

    def indice(self, palabra, desde=0, n=1):
        q = norm(palabra); q = self.alias.get(q, q); k = 0
        for i in range(desde, len(self.n)):
            if self.n[i] == q:
                k += 1
                if k == n: return i
        k = 0
        for i in range(desde, len(self.n)):       # prefijo solo como respaldo: «cancion» → «canciones»
            if len(q) >= 4 and self.n[i].startswith(q):
                k += 1
                if k == n: return i
        raise ValueError(f"Ancla no encontrada: «{palabra}» (#{n}) desde la palabra {desde}: {' '.join(self.n[desde:desde + 12])}…")

    def t(self, ref, desde=0, t0=0.0, base=None):
        if ref is None: return None
        if isinstance(ref, (int, float)): return float(ref)
        s = str(ref).strip()
        m = re.match(r"^(.*?)([+-]\d+(?:\.\d+)?f?)?$", s); b, off = m.group(1), m.group(2)
        d = 0.0
        if off: d = float(off[:-1]) / FPS if off.endswith("f") else float(off)
        if b == "": return (base if base is not None else t0) + d
        if b.startswith("@"): return t0 + float(b[1:] or 0) + d
        if b.startswith("marca:"): return self.marcas[b[6:]] + d
        fin = b.endswith(">"); b = b.rstrip(">"); n = 1
        if "#" in b: b, k = b.rsplit("#", 1); n = int(k)
        i = self.indice(b, desde, n)
        return (self.pal[i]["e"] if fin else self.pal[i]["s"]) + d

    def f(self, ref, desde=0, t0=0.0, base=None): return f_de_t(self.t(ref, desde, t0, base))

    def indice_de_ancla(self, ref, desde=0):
        b = re.sub(r"[+-]\d+(\.\d+)?f?$", "", str(ref)).rstrip(">"); n = 1
        if "#" in b: b, k = b.rsplit("#", 1); n = int(k)
        return self.indice(b, desde, n)

    def palabra_en(self, t):
        for i, p in enumerate(self.pal):
            if p["s"] <= t < p["e"]: return i
        return None
