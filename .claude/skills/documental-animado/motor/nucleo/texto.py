"""Fuentes y texto con kerning real (HarfBuzz + skia). Skia solo no aplica kerning: sin esto Montserrat Black se ve «de plantilla».

  fnt = fuente("Montserrat", 800, 68)
  texto(c, "HOLA", 540, 300, fnt, "#FFFFFF", alinear="c", tracking=0, centro_v=True)

Familias en nucleo/fuentes/ (Google Fonts, licencia OFL en cada carpeta): Montserrat, Figtree, Inter, JetBrainsMono (variables);
BarlowCondensed, IBMPlexMono (estáticas). Respaldo para cifras tabulares: tnum=True.
"""
from functools import lru_cache
from pathlib import Path

import skia
import uharfbuzz as hb

DIR = Path(__file__).resolve().parent / "fuentes"
VARIABLES = {"Montserrat": "Montserrat[wght].ttf", "Figtree": "Figtree[wght].ttf", "Inter": "Inter[opsz,wght].ttf",
             "JetBrainsMono": "JetBrainsMono[wght].ttf"}
PESOS = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
_WGHT = 2003265652  # 'wght'
_VIVOS = []


def color(c, alfa=1.0):
    """'#RRGGBB' o int skia → int ARGB con alfa multiplicado."""
    if isinstance(c, str):
        h = c.lstrip("#"); r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16); a = int(h[6:8], 16) if len(h) == 8 else 255
    else:
        a, r, g, b = (c >> 24) & 255, (c >> 16) & 255, (c >> 8) & 255, c & 255
    return skia.Color(r, g, b, int(round(a * max(0.0, min(1.0, alfa)))))


@lru_cache(maxsize=64)
def _ruta(familia, peso):
    if familia in VARIABLES: return DIR / familia / VARIABLES[familia]
    p = peso
    while p not in PESOS or not (DIR / familia / f"{familia}-{PESOS[p]}.ttf").exists():
        p -= 100
        if p < 400: raise FileNotFoundError(f"{familia} {peso} no está en {DIR}")
    return DIR / familia / f"{familia}-{PESOS[p]}.ttf"


@lru_cache(maxsize=64)
def tipo(familia, peso=400):
    # Python lee el archivo y skia recibe los bytes: así una ruta con acentos («C:\Users\José\…») no depende de cómo abra archivos cada librería en Windows.
    tf = skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(_ruta(familia, peso).read_bytes()))
    if tf is None: raise RuntimeError(f"No se pudo abrir {familia}")
    if familia in VARIABLES:
        # Ojo: skia guarda punteros a estos objetos; si se liberan, la variación se pierde (sale Thin). Se mantienen vivos en _VIVOS.
        co = skia.FontArguments.VariationPosition.Coordinates([skia.FontArguments.VariationPosition.Coordinate(_WGHT, float(peso))])
        pos = skia.FontArguments.VariationPosition(co); arg = skia.FontArguments(); arg.setVariationDesignPosition(pos); _VIVOS.append((co, pos, arg))
        tf = tf.makeClone(arg)
    return tf


@lru_cache(maxsize=64)
def _hb(familia, peso):
    blob = hb.Blob(_ruta(familia, peso).read_bytes()); _VIVOS.append(blob)     # bytes leídos por Python (ver tipo); el blob se mantiene vivo
    face = hb.Face(blob)
    f = hb.Font(face); s = face.upem; f.scale = (s, s)
    if familia in VARIABLES: f.set_variations({"wght": float(peso)})
    return f, s


class Fuente:
    def __init__(self, familia, peso, px):
        self.familia, self.peso, self.px = familia, peso, px
        self.sk = skia.Font(tipo(familia, peso), px); self.sk.setSubpixel(True); self.sk.setEdging(skia.Font.Edging.kAntiAlias)
        self.sk.setHinting(skia.FontHinting.kNone); self.sk.setLinearMetrics(True)
        m = self.sk.getMetrics(); self.cap = m.fCapHeight or px * .7; self.asc = -m.fAscent; self.desc = m.fDescent

    def __hash__(self): return hash((self.familia, self.peso, self.px))
    def __eq__(self, o): return (self.familia, self.peso, self.px) == (o.familia, o.peso, o.px)


@lru_cache(maxsize=512)
def fuente(familia, peso, px): return Fuente(familia, peso, float(px))


@lru_cache(maxsize=4096)
def _forma(fnt, txt, tracking, tnum):
    """→ (glifos, xs, ancho). tracking en em."""
    if not txt: return (), (), 0.0
    f, upem = _hb(fnt.familia, fnt.peso); buf = hb.Buffer(); buf.add_str(txt); buf.guess_segment_properties()
    feats = {"kern": True, "liga": False}
    if tnum: feats["tnum"] = True
    hb.shape(f, buf, feats)
    k = fnt.px / upem; x = 0.0; gl, xs = [], []; extra = tracking * fnt.px
    for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gl.append(inf.codepoint); xs.append(x + pos.x_offset * k); x += pos.x_advance * k + extra
    return tuple(gl), tuple(xs), x - extra if gl else 0.0


def ancho(txt, fnt, tracking=0.0, tnum=False): return _forma(fnt, txt, tracking, tnum)[2]


@lru_cache(maxsize=4096)
def _blob(fnt, txt, tracking, tnum):
    gl, xs, w = _forma(fnt, txt, tracking, tnum)
    if not gl: return None, 0.0
    b = skia.TextBlobBuilder(); b.allocRunPos(fnt.sk, list(gl), [skia.Point(x, 0) for x in xs])
    return b.make(), w


def texto(c, txt, x, y, fnt, col="#FFFFFF", alinear="c", tracking=0.0, alfa=1.0, centro_v=True, tnum=False, paint=None, sombra=None):
    """y es el centro de la altura de mayúscula (centro_v=True) o la línea base. alinear: i / c / d. Devuelve el ancho.
    sombra=(dy, sigma, alfa): sombra suave negra (la del karaoke del estilo)."""
    blob, w = _blob(fnt, txt, tracking, tnum)
    if blob is None or alfa <= 0: return w
    bx = x - (w / 2 if alinear == "c" else w if alinear == "d" else 0); by = y + fnt.cap / 2 if centro_v else y
    if sombra:
        dy, sg, a = sombra
        c.drawTextBlob(blob, bx, by + dy, skia.Paint(AntiAlias=True, Color=color("#000000", a * alfa),
                                                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sg)))
    p = paint or skia.Paint(AntiAlias=True, Color=color(col, alfa))
    c.drawTextBlob(blob, bx, by, p)
    return w


def partir_lineas(palabras, fnt, ancho_max, esp=None, tracking=0.0):
    """Reparto voraz de una lista de palabras en líneas ≤ ancho_max. esp = ancho del espacio (px). → [[índices]]"""
    esp = ancho(" ", fnt, tracking) if esp is None else esp
    lineas, cur, w = [], [], 0.0
    for i, p in enumerate(palabras):
        a = ancho(p, fnt, tracking)
        if cur and w + esp + a > ancho_max: lineas.append(cur); cur, w = [], 0.0
        w += (esp if cur else 0) + a; cur.append(i)
    if cur: lineas.append(cur)
    return lineas
