#!/usr/bin/env python3
"""Variante VERTICAL del documental animado: 1080×1920 (TikTok / Reels / Shorts), 60 fps, dibujado con skia sobre el núcleo del kit.

  PY motor.py <proyecto> prueba 0.5 3.2 8.1      → revision/prueba.jpg
  PY motor.py <proyecto> secuencia 7.9 12        → revision/seq-7.9.jpg
  PY motor.py <proyecto> escenas                 → lista de escenas con su segundo
  PY motor.py <proyecto> render [--procesos 4]   → final/<proyecto>.mp4 + -hoja.jpg + qa.json
  PY motor.py <proyecto> audio | qa

Escenas (en guion.json → lineas[].escena): map (mapa en metros con cámara, anillos de radio, bola de fuego, pines),
radio (suelo 2.5D con anillos en metros y personas a escala), stat (cifra con odómetro + objeto), artico (globo polar + año).
Los datos de mapa salen de <proyecto>/datos/geo_utm.json y puntos_utm.json (metros, ETRS89 / UTM 30N).
Zonas seguras de TikTok: nada abajo de y=1536 (20 %) ni a la derecha de x=950 (12 %).
"""
import json, math, os, sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MOTOR))
from nucleo import tiempo as TI                                   # noqa: E402
TI.FPS = int(os.environ.get("DOC_FPS", "60"))                     # antes de importar el resto: todos toman este FPS
if "--fps" in sys.argv: TI.FPS = int(sys.argv[sys.argv.index("--fps") + 1]); os.environ["DOC_FPS"] = str(TI.FPS)
import numpy as np                                                # noqa: E402
import skia                                                       # noqa: E402
from nucleo import estilo as ES                                   # noqa: E402
from nucleo.texto import fuente, texto, ancho, color              # noqa: E402
from nucleo.lienzo import capa, relleno, trazo, rrc               # noqa: E402
from nucleo.compositor import tramar, hex_rgb                     # noqa: E402
TX = sys.modules["nucleo.texto"]
for _n, _m in list(sys.modules.items()):                         # el paquete nucleo ya importó sus módulos con FPS=30: se igualan
    if _n.startswith("nucleo") and hasattr(_m, "FPS"): _m.FPS = TI.FPS

_ruta_orig = TX._ruta
def _ruta_serif(familia, peso):                                   # la serif del kit solo existe en cursiva
    if familia == "InstrumentSerif": return TX.DIR / "InstrumentSerif" / "InstrumentSerif-Italic.ttf"
    return _ruta_orig(familia, peso)
TX._ruta = _ruta_serif

W, H, FPS = TI.W, TI.H, TI.FPS
CX, CY = 520, 700              # centro de la franja de gráficos (corrido a la izquierda por la columna de botones)
GW = 430                       # medio ancho útil de gráficos (px)
CAP_CTX_Y, CAP_KEY_Y = 1268, 1400

SUP = {
    "dark":  dict(a="#0B1530", b="#050A18", txt="#FFFFFF", sub="#AFC3EE", acc="#6EA0FF", tierra="#12244A", borde="#2D5BB8", grid=True),
    "blue":  dict(a="#2453D6", b="#0D2A86", txt="#FFFFFF", sub="#D6E2FF", acc="#FFFFFF", tierra="#1E47B8", borde="#9DB8FF", grid=False),
    "light": dict(a="#F4F7FD", b="#D9E4F7", txt="#0C1630", sub="#3D4C6E", acc="#2F6BFF", tierra="#E4EBF8", borde="#9AAFD6", grid=False),
    "clay":  dict(a="#3A1E14", b="#170A06", txt="#FFFFFF", sub="#F1C9A8", acc="#FFB45C", tierra="#4A2618", borde="#C9774A", grid=True),
}
TRANS = ["whip", "zoom", "mask", "card"]


def ease_io_expo(u):
    u = TI.clamp(u)
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 2 ** (20 * u - 10) / 2 if u < .5 else (2 - 2 ** (-20 * u + 10)) / 2


def resorte(dt, k=9.0, w=13.0):
    """0→1 con un pequeño rebote; dt en segundos."""
    if dt <= 0: return 0.0
    return 1 - math.exp(-k * dt) * math.cos(w * dt)


def aparece(dt, d=4 / 60):
    return TI.clamp(dt / d) if dt > 0 else 0.0


def path_de(rings, cerrar=True):
    p = skia.Path()
    for r in rings:
        if len(r) < 2: continue
        p.moveTo(*r[0])
        for x, y in r[1:]: p.lineTo(x, y)
        if cerrar: p.close()
    return p


class Vertical(ES.Estilo):
    NOMBRE = "documental-vertical"
    COLA = .40
    ZONAS = dict(arriba=150, abajo=1536, derecha=950, der_y=(700, 1536))

    # ------------------------------------------------------------------ preparación
    def preparar(self):
        g = self.guion; pal = self.palabras
        self.lineas = g["lineas"]
        self.idx_linea = {}
        for i, p in enumerate(pal): self.idx_linea.setdefault(p.get("linea", 1), []).append(i)
        # escenas
        self.escenas = []
        for n, ln in enumerate(self.lineas, 1):
            if ln.get("escena"):
                i0 = self.idx_linea[n][0]
                t0 = 0.0 if not self.escenas else pal[i0]["s"] - .14
                self.escenas.append(dict(spec=ln["escena"], t0=t0, i0=i0, n=n))
        for k, e in enumerate(self.escenas):
            e["t1"] = self.escenas[k + 1]["t0"] if k + 1 < len(self.escenas) else self.fin_s + 1
            e["trans"] = e["spec"].get("transicion", TRANS[k % len(TRANS)])
        # datos
        d = self.proy / "datos"
        if (d / "puntos_utm.json").exists(): self.datos_madrid(d)
        self._prep_fondos()
        self.mundo = None; self._geo = {}
        if g.get("sfx"): self.efectos()

    def datos_madrid(self, d):
        self.pts = {k: np.array(v) for k, v in json.loads((d / "puntos_utm.json").read_text()).items()}
        self.o = self.pts["sol"]
        geo = json.loads((d / "geo_utm.json").read_text())
        o = self.o
        loc = lambda rs: [np.array(r) - o for r in rs]
        self.P = dict(
            tracts=path_de([r for f in geo["tracts"] for r in loc(f)]),
            districts=path_de([r for f in geo["districts"] for r in loc(f)]),
            city=path_de(loc(geo["city"])),
            munis=path_de([r for m in geo["munis"] for r in loc(m["r"])]),
            provs=path_de([r for m in geo["provs"] for r in loc(m["r"])]),
            com=path_de([r for m in geo["provs"] if m["id"] == "28" for r in loc(m["r"])]),
        )
        self.pts = {k: v - o for k, v in self.pts.items()}

    def _prep_fondos(self):
        self.fondos = {}
        for k, s in SUP.items():
            u = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            base = hex_rgb(s["a"]) * (1 - u) + hex_rgb(s["b"]) * u
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            v = np.sqrt(((xx - CX) / (W * .75)) ** 2 + ((yy - CY) / (H * .62)) ** 2)
            vig = np.clip(1.12 - .55 * v ** 1.6, .45, 1.1)[..., None]
            arr = tramar(np.broadcast_to(base, (H, W, 3)) * vig, 3)
            self.fondos[k] = np.dstack([arr, np.full((H, W), 255, np.uint8)])
        self.F = dict(ctx=fuente("Inter", 600, 46), key=fuente("Inter", 800, 124), keyserif=fuente("InstrumentSerif", 400, 140),
                      pill=fuente("Inter", 600, 30), pillb=fuente("Inter", 700, 34), big=fuente("Inter", 800, 250),
                      unit=fuente("Inter", 700, 64), nota=fuente("Inter", 600, 40), lab=fuente("Inter", 700, 30),
                      item=fuente("Inter", 700, 44), rot=fuente("Inter", 600, 32))

    # ------------------------------------------------------------------ tiempo
    def ta(self, ref, e):
        if isinstance(ref, str) and ref.startswith("@"): return e["t0"] + float(ref[1:] or 0)
        return self.tl.t(ref, desde=e["i0"])

    # ------------------------------------------------------------------ dibujo general
    def dibujar(self, L, f):
        t = f / FPS; c = L.canvas
        k = max(i for i, e in enumerate(self.escenas) if e["t0"] <= t or i == 0)
        e = self.escenas[k]
        TD = .34
        if k > 0 and t < e["t0"] + TD:
            u = (t - e["t0"]) / TD; prev = self.escenas[k - 1]
            self.transicion(L, prev, e, t, ease_io_expo(u), e["trans"])
        else:
            self.escena_completa(L, e, t)
        self.tipografia(c, t, e)

    def escena_completa(self, L, e, t, img=False):
        s = e["spec"]; sup = s.get("surface", "dark")
        L.arr[:] = self.fondos[sup]; c = L.canvas
        if SUP[sup]["grid"]: self.rejilla(c, t, sup)
        # empuje con resorte en cada frase + deriva lenta
        z = 1 + .018 * min(1, (t - e["t0"]) / 4)
        for n in range(e["n"], len(self.lineas) + 1):
            if n in self.idx_linea and self.palabras[self.idx_linea[n][0]]["s"] <= t and (n == e["n"] or not self.lineas[n - 1].get("escena")):
                if n > e["n"] and self.lineas[n - 1].get("escena"): break
                z += .012 * (1 - math.exp(-6 * max(0, t - self.palabras[self.idx_linea[n][0]]["s"])))
        c.save(); c.translate(CX, CY); c.scale(z, z); c.translate(-CX, -CY)
        getattr(self, "e_" + s["tipo"])(c, e, t, SUP[sup])
        c.restore()

    def capa_escena(self, e, t):
        from nucleo.lienzo import Lienzo
        if not hasattr(self, "_L2"): self._L2 = Lienzo()
        self.escena_completa(self._L2, e, t)
        return skia.Image.fromarray(self._L2.arr.copy(), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)

    def transicion(self, L, a, b, t, u, tipo):
        A = self.capa_escena(a, t); B = self.capa_escena(b, t); c = L.canvas
        c.clear(skia.ColorBLACK)
        if tipo == "whip":
            bl = 60 * math.sin(math.pi * u)
            p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(bl + .01, .01))
            c.drawImage(A, -W * u, 0, skia.SamplingOptions(), p); c.drawImage(B, W * (1 - u), 0, skia.SamplingOptions(), p)
        elif tipo == "zoom":
            bl = 14 * math.sin(math.pi * u)
            c.save(); s = 1 + 1.2 * u; c.translate(CX, CY); c.scale(s, s); c.translate(-CX, -CY)
            c.drawImage(A, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=1 - u, ImageFilter=skia.ImageFilters.Blur(bl + .01, bl + .01)))
            c.restore(); c.save(); s = 1.3 - .3 * u; c.translate(CX, CY); c.scale(s, s); c.translate(-CX, -CY)
            c.drawImage(B, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=u, ImageFilter=skia.ImageFilters.Blur(bl + .01, bl + .01)))
            c.restore()
        elif tipo == "mask":
            c.drawImage(A, 0, 0); r = 1.25 * math.hypot(W, H) * u
            c.save(); pth = skia.Path(); pth.addCircle(CX, CY, r); c.clipPath(pth, doAntiAlias=True); c.drawImage(B, 0, 0); c.restore()
            c.drawCircle(CX, CY, r, trazo("#FFFFFF", 6, .8 * (1 - u)))
        else:  # card
            c.save(); s = 1 - .06 * u; c.translate(CX, CY); c.scale(s, s); c.translate(-CX, -CY)
            c.drawImage(A, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=1 - .6 * u)); c.restore()
            y = H * (1 - u); bl = 18 * math.sin(math.pi * u)
            c.drawImage(B, 0, y, skia.SamplingOptions(), skia.Paint(ImageFilter=skia.ImageFilters.Blur(.01, bl + .01)))
        L.arr[..., 3] = 255

    def rejilla(self, c, t, sup):
        col = SUP[sup]["borde"]
        hy = 1180; n = 14; off = (t * 18) % 60
        for i in range(-n, n + 1):
            x0 = CX + i * 40; x1 = CX + i * 260
            c.drawLine(x0, hy, x1, H, trazo(col, 1.2, .10))
        y = hy
        k = 0
        while y < H:
            yy = hy + ((k * 60 + off) / 60) ** 1.7 * 9
            if yy > H: break
            c.drawLine(0, yy, W, yy, trazo(col, 1.0, .08 * min(1, (yy - hy) / 80)))
            k += 1; y = yy
        rng = np.random.default_rng(5)
        for i in range(36):
            x = (rng.random() * W + t * (6 + 10 * rng.random())) % W; y = (rng.random() * 1150 + 60 - t * 4 * rng.random()) % 1200
            c.drawCircle(x, y, 1.2 + 2 * rng.random(), relleno(col, .18 + .2 * rng.random()))

    # ------------------------------------------------------------------ piezas
    def pildora(self, c, txt, x, y, s, a=1.0, fnt=None, fondo=None, col=None, alinear="c"):
        fnt = fnt or self.F["pill"]; w = ancho(txt, fnt) + 44; h = fnt.px * 1.7
        if alinear == "i": x = x + w / 2
        elif alinear == "d": x = x - w / 2
        x = min(max(x, 40 + w / 2), 950 - w / 2)
        r = rrc(x, y, w, h, h / 2)
        c.drawRRect(r.makeOffset(0, 6) if hasattr(r, "makeOffset") else r, skia.Paint(AntiAlias=True, Color=color("#000000", .25 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        c.drawRRect(r, relleno(fondo or "#0B1430", .72 * a))
        c.drawRRect(r, trazo("#FFFFFF", 1.5, .22 * a))
        texto(c, txt, x, y, fnt, col or "#FFFFFF", alfa=a)
        return x, w

    def camara(self, e, t):
        ks = e["spec"]["cam"]; prev = None
        def cen(k):
            cc = k.get("c", "sol"); return self.pts[cc] if isinstance(cc, str) else np.array(cc, float)
        c0, r0 = cen(ks[0]), ks[0]["r"]
        for k in ks[1:]:
            ta = self.ta(k["t"], e); u = ease_io_expo((t - ta) / k.get("dur", 1.0))
            c1, r1 = cen(k), k["r"]
            r0 = math.exp(math.log(r0) + (math.log(r1) - math.log(r0)) * u); c0 = c0 + (c1 - c0) * u
        return c0, GW / r0

    def e_map(self, c, e, t, S):
        s = e["spec"]; cen, k = self.camara(e, t); r_m = GW / k
        c.save(); c.translate(CX, CY); c.scale(k, -k); c.translate(-cen[0], -cen[1])
        lw = lambda px: px / k
        reg = s.get("capas") == "region"
        if reg or r_m > 4000:
            a = TI.clamp((r_m - 4000) / 6000) if not reg else 1
            c.drawPath(self.P["com"], relleno(S["tierra"], .35 * a))
            c.drawPath(self.P["munis"], trazo(S["borde"], lw(1), .22 * a))
            c.drawPath(self.P["provs"], trazo(S["borde"], lw(2.2), .55 * a))
        c.drawPath(self.P["com"], relleno(S["tierra"], .6 if r_m < 9000 else .0))      # tapa huecos del mapa municipal
        c.drawPath(self.P["districts"], relleno(S["tierra"], .95))
        ta = TI.clamp(1 - (r_m - 4000) / 9000)
        if ta > 0: c.drawPath(self.P["tracts"], trazo(S["borde"], lw(1.0), .38 * ta))
        c.drawPath(self.P["districts"], trazo(S["borde"], lw(1.8), .55))
        cw = s.get("ciudad_word")
        ca = .9 * aparece(t - self.ta(cw, e), .25) if cw else 0
        c.drawPath(self.P["city"], trazo("#FF5A4E" if cw else S["borde"], lw(3 if cw else 2.2), ca if cw else .8))
        if ca: c.drawPath(self.P["districts"], relleno("#FF5A4E", .18 * ca))
        c.restore()
        P = lambda m: (CX + (m[0] - cen[0]) * k, CY - (m[1] - cen[1]) * k)
        # bola de fuego
        fb = s.get("fuego")
        if fb:
            dt = t - self.ta(fb["word"], e)
            if dt > 0:
                x, y = P(self.pts["sol"]); R = fb["r"] * k * (.2 + .8 * resorte(dt, 7, 9)); fl = 1 + .04 * math.sin(t * 31) * math.exp(-dt)
                with capa(c, modo=skia.BlendMode.kPlus):
                    c.drawCircle(x, y, R * 2.6 * fl, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), R * 2.6 * fl, [color("#FF7A1A", .55), color("#FF3D00", .18), color("#000000", 0)])))
                c.drawCircle(x, y, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - R * .25, y - R * .25), R * 1.2, [color("#FFFFFF"), color("#FFE27A"), color("#FF8A1C"), color("#E0360F")], [0, .35, .75, 1])))
                if fb.get("label"):
                    a = aparece(dt - .25, .2); self.pildora(c, fb["label"], x, y + max(R * 2.6, 60) + 10, S, a, fondo="#3A1405")
        # anillos
        for ri in s.get("rings", []): self.anillo(c, e, t, ri, P(self.pts["sol"]), ri["r"] * k, S)
        # pines
        for pi in s.get("pins", []):
            dt = t - self.ta(pi["word"], e)
            if dt <= 0: continue
            x, y = P(self.pts[pi["p"]]); a = aparece(dt, .12); sc = resorte(dt, 10, 14)
            for q in range(2):
                ph = ((t * .9 + q * .5) % 1)
                c.drawCircle(x, y, 10 + 40 * ph, trazo("#FFFFFF", 2.5, .5 * (1 - ph) * a))
            c.drawCircle(x, y, 13 * sc, relleno("#FFFFFF", a)); c.drawCircle(x, y, 6.5 * sc, relleno("#0B1430", a))
            big = pi.get("big"); fnt = self.F["pillb"] if big else self.F["pill"]
            lado = pi.get("lado", "c")
            if lado == "c": self.pildora(c, pi["label"], x, y - 58 * sc, S, a, fnt=fnt)
            elif lado == "d": self.pildora(c, pi["label"], x + 26, y, S, a, fnt=fnt, alinear="i")
            else: self.pildora(c, pi["label"], x - 26, y, S, a, fnt=fnt, alinear="d")
        # escala
        self.barra_escala(c, r_m, S)

    def anillo(self, c, e, t, ri, cen, R, S):
        dt = t - self.ta(ri["word"], e)
        if dt <= 0: return
        x, y = cen; g = R * (.15 + .85 * resorte(dt, 6.5, 8)); col = ri["col"]; a = aparece(dt, .1)
        c.drawCircle(x, y, g, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), max(g, 1), [color(col, .05 * a), color(col, .30 * a)], [0, 1])))
        p = trazo(col, 5, a)
        if ri.get("dash"): p.setPathEffect(skia.DashPathEffect.Make([22, 14], -t * 40))
        c.drawCircle(x, y, g, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=16, Color=color(col, .25 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        c.drawCircle(x, y, g, p)
        if ri.get("label") and g > 70:
            an = math.radians(ri.get("ang", -45)); lx, ly = x + g * math.cos(an), y + g * math.sin(an)
            la = aparece(dt - .3, .15) * TI.clamp((g - 70) / 40)
            if la > 0:
                c.drawCircle(lx, ly, 7, relleno(col, la))
                self.pildora(c, ri["label"], lx, ly - 34, S, la, fondo=col, fnt=self.F["lab"])

    def barra_escala(self, c, r_m, S):
        mpp = r_m / GW; obj = mpp * 180
        paso = 10 ** math.floor(math.log10(obj)); paso = next(m * paso for m in (5, 2, 1) if m * paso <= obj)
        L = paso / mpp; x0, y0 = 80, 1140
        txt = f"{paso / 1000:g} km" if paso >= 1000 else f"{paso:g} m"
        c.drawLine(x0, y0, x0 + L, y0, trazo(S["sub"], 3, .8))
        for xx in (x0, x0 + L): c.drawLine(xx, y0 - 10, xx, y0 + 10, trazo(S["sub"], 3, .8))
        texto(c, txt, x0 + L + 16, y0, self.F["pill"], S["sub"], alinear="i", alfa=.9)

    # ------------------------------------------------------------------ escena radio (suelo 2.5D)
    def e_radio(self, c, e, t, S):
        s = e["spec"]; _, k = self.camara(e, t); TY = .46
        oy = CY + 60
        P = lambda X, Z: (CX + X * k, oy + Z * k * TY)
        # suelo: baldosas de 1 m que se desvanecen
        lim = GW / k * 1.25; n = int(lim) + 2
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                if (i + j) % 2: continue
                d = math.hypot(i + .5, j + .5) / lim; a = .16 * TI.clamp(1.2 - d)
                if a <= 0: continue
                x0, y0 = P(i, j); x1, y1 = P(i + 1, j + 1)
                c.drawRect(skia.Rect(x0, y0, x1, y1), relleno("#9FB2D8", a))
        # anillos (elipses)
        for ri in s.get("rings", []):
            dt = t - self.ta(ri["word"], e)
            if dt <= 0: continue
            g = ri["r"] * k * (.15 + .85 * resorte(dt, 6.5, 8)); a = aparece(dt, .1); x, y = P(0, 0)
            rect = skia.Rect(x - g, y - g * TY, x + g, y + g * TY)
            c.drawOval(rect, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), max(g, 1), [color(ri["col"], .04 * a), color(ri["col"], .26 * a)], [0, 1], skia.TileMode.kClamp, 0, skia.Matrix.Scale(1, TY).postTranslate(0, y * (1 - TY)))))
            c.drawOval(rect, trazo(ri["col"], 5, a))
        # personas, de atrás hacia delante
        per = sorted(s.get("personas", []), key=lambda q: q[1])
        for X, Z in per:
            d = math.hypot(X, Z); x, y = P(X, Z)
            if not (40 < x < 960): continue
            col = "#22304F"; tint = None
            for ri in s.get("rings", []):
                if d <= ri["r"] and t > self.ta(ri["word"], e) + .15: tint = ri["col"]; break
            self.persona(c, x, y, k, tint or col, tint is not None)
        # objeto en el centro (fuera de escala, flota encima)
        x, y = P(0, 0); fl = 6 * math.sin(t * 3)
        c.drawOval(skia.Rect(x - 26, y - 8, x + 26, y + 8), relleno("#000000", .25))
        self.granada(c, x, y - 70 + fl, 1.0)
        self.pildora(c, s.get("objeto_label", ""), x, y - 160 + fl, S, 1.0, fondo="#0C1630")
        for ri in s.get("rings", []):
            dt = t - self.ta(ri["word"], e) - .3
            if dt <= 0: continue
            g = ri["r"] * k; an = math.radians(ri.get("ang", -40)); lx, ly = P(ri["r"] * math.cos(an), ri["r"] * math.sin(an))
            ly = oy + (ly - oy); a = aparece(dt, .15)
            lx2, ly2 = CX + g * math.cos(an) * .0 + (lx - CX), ly
            self.pildora(c, ri["label"], lx2, ly2 - 30, S, a, fondo=ri["col"], fnt=self.F["lab"])
        self.barra_escala(c, GW / k, S)

    def persona(self, c, x, y, k, col, marcado):
        h = 1.75 * k; w = .5 * k
        c.drawOval(skia.Rect(x - w * .8, y - w * .22, x + w * .8, y + w * .22), relleno("#000000", .18))
        c.drawRRect(rrc(x, y - h * .42, w, h * .56, w * .45), relleno(col))
        c.drawCircle(x, y - h * .84, w * .36, relleno(col))
        if marcado: c.drawCircle(x, y - h * .84, w * .36, trazo("#FFFFFF", 1.5, .6))

    def granada(self, c, x, y, s):
        r = 34 * s
        c.drawRRect(rrc(x, y - r * 1.05, r * .55, r * .4, 6), relleno("#5B6470"))
        c.drawRect(skia.Rect(x + r * .25, y - r * 1.2, x + r * .75, y - r * 1.02), relleno("#8C95A3"))
        c.drawCircle(x + r * .85, y - r * 1.1, r * .2, trazo("#C2CAD6", 3))
        c.drawOval(skia.Rect(x - r, y - r * .9, x + r, y + r), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - r * .35, y - r * .4), r * 1.6, [color("#8FA06A"), color("#4E5E32"), color("#2A3418")], [0, .55, 1])))
        for i in (-1, 0, 1):
            c.drawLine(x - r * .9, y + i * r * .45, x + r * .9, y + i * r * .45, trazo("#26301A", 2, .5))
        c.drawCircle(x - r * .4, y - r * .45, r * .18, relleno("#FFFFFF", .35))

    # ------------------------------------------------------------------ escena stat
    def e_stat(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ox, oy = CX, 520
        obj = s.get("objeto")
        if obj == "moab": self.moab(c, ox, oy + 10, dt0, S)
        elif obj == "nuclear": self.nuclear(c, ox, oy + 20, dt0, s.get("tam", .5), t)
        elif obj: getattr(self, "obj_" + obj)(c, ox, oy, dt0, t, S, e)
        if s.get("pill"):
            a = aparece(dt0 - .05, .15); self.pildora(c, s["pill"], CX, 245 - 20 * (1 - resorte(dt0, 9, 12)), S, a, fnt=self.F["pillb"])
        tw = self.ta(s["word"], e); dt = t - tw
        de = s.get("desde", 0); v = de + (s["valor"] - de) * TI.cubic_out(TI.clamp(dt / .9)) if dt > 0 else de
        a = aparece(dt + .25, .2)
        if a > 0:
            dec = s.get("decimales", 0); txt = f"{v:.{dec}f}".replace(".", ",") if dec else (f"{int(round(v)):,}".replace(",", ".") if s.get("miles", True) else str(int(round(v))))
            fnt = self.F["big"]; yb = 850 if self.guion.get("stat_alto") else 905
            if ancho(txt, fnt) > 860: fnt = fuente("Inter", 800, int(250 * 860 / ancho(txt, fnt)))
            sc = .9 + .1 * resorte(dt + .25, 8, 11)
            vel = abs(s["valor"] / .9 * 3 * (1 - TI.clamp(dt / .9)) ** 2) if 0 < dt < .9 else 0
            c.save(); c.translate(CX, yb); c.scale(sc, sc)
            with capa(c, alfa=a, blur=min(6, vel * .4)):
                texto(c, txt, 0, 0, fnt, S["txt"], tnum=True)
            c.restore()
            texto(c, s["unidad"], CX, yb + 150, self.F["unit"], S["acc"], alfa=a)
        if s.get("nota"):
            dn = t - self.ta(s.get("nota_word", s["word"]), e) - .15
            if dn > 0: self.pildora(c, s["nota"], CX, 1085 if self.guion.get("stat_alto") else 1150, S, aparece(dn, .15), fnt=self.F["nota"])

    def moab(self, c, x, y, dt, S):
        u = resorte(dt, 6, 7); x = x - 600 * (1 - u)
        L, R = 640, 62
        c.save(); c.translate(x, y); c.rotate(-8)
        c.drawOval(skia.Rect(-L * .55, R * 2.4, L * .55, R * 2.9), relleno("#000000", .3))
        # aletas reticuladas
        for s_ in (-1, 1):
            c.drawRect(skia.Rect(-L * .52, s_ * R * .2 if s_ > 0 else -R * 1.9, -L * .38, s_ * R * 1.9 if s_ > 0 else -R * .2), trazo("#D7DCE3", 3, .9))
            for i in range(4):
                yy = s_ * (R * .2 + i * R * .45)
                c.drawLine(-L * .52, yy, -L * .38, yy, trazo("#D7DCE3", 2, .7))
        body = skia.Path(); body.moveTo(-L * .5, -R); body.lineTo(L * .3, -R); body.cubicTo(L * .48, -R, L * .5, -R * .4, L * .5, 0)
        body.cubicTo(L * .5, R * .4, L * .48, R, L * .3, R); body.lineTo(-L * .5, R * .8); body.close()
        c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -R), (0, R)], [color("#E9C9A0"), color("#B98E5E"), color("#6E4F31")], [0, .45, 1])))
        c.drawPath(body, trazo("#2A1A0E", 2, .5))
        for xx in (-L * .25, L * .05):
            c.drawLine(xx, -R * .98, xx, R * .95, trazo("#5A3D22", 2.5, .6))
        c.drawRRect(rrc(L * .12, -R * .55, L * .3, R * .22, 6), relleno("#FFFFFF", .25))
        c.restore()

    def nuclear(self, c, x, y, dt, tam, t):
        u = resorte(dt, 5, 6); R = 300 * tam * (.3 + .7 * u)
        fl = 1 + .02 * math.sin(t * 23)
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(x, y, R * 1.9 * fl, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), R * 1.9 * fl, [color("#FF8A2A", .55), color("#FF3D00", .15), color("#000000", 0)])))
        c.drawCircle(x, y, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - R * .3, y - R * .3), R * 1.3, [color("#FFFFFF"), color("#FFE68A"), color("#FF9A2A"), color("#C9300C")], [0, .3, .72, 1])))
        rng = np.random.default_rng(2)
        for i in range(10):
            an = rng.random() * 6.28 + t * (.2 + .3 * rng.random()); rr_ = R * (.35 + .5 * rng.random())
            c.drawCircle(x + rr_ * math.cos(an), y + rr_ * math.sin(an) * .9, R * (.12 + .1 * rng.random()), relleno("#FFF3B0", .18))

    # ------------------------------------------------------------------ escena ártico
    def e_artico(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        if self.mundo is None: self.mundo = self.carga_mundo()
        lon0, lat0 = 40.0, 62.0; rot = 6 * dt0
        R = 380 * (.92 + .08 * resorte(dt0, 6, 8)); gx, gy = CX, 600
        def pr(lon, lat):
            l = np.radians(lon - lon0 - rot * 0); p = np.radians(lat); p0 = np.radians(lat0)
            x = np.cos(p) * np.sin(l); y = np.cos(p0) * np.sin(p) - np.sin(p0) * np.cos(p) * np.cos(l)
            vis = np.sin(p0) * np.sin(p) + np.cos(p0) * np.cos(p) * np.cos(l) > 0
            return gx + R * x, gy - R * y, vis
        c.drawCircle(gx, gy, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx - R * .3, gy - R * .4), R * 1.5, [color("#3A6FD8"), color("#17357F"), color("#0A1638")], [0, .6, 1])))
        pth = skia.Path()
        for ring in self.mundo:
            X, Y, V = pr(ring[:, 0], ring[:, 1])
            if V.mean() < .02: continue
            pen = False
            for xx, yy, vv in zip(X, Y, V):
                if vv:
                    (pth.lineTo if pen else pth.moveTo)(xx, yy); pen = True
                else: pen = False
        c.save(); cl = skia.Path(); cl.addCircle(gx, gy, R); c.clipPath(cl, doAntiAlias=True)
        c.drawPath(pth, trazo("#CFE0FF", 1.6, .75))
        c.restore()
        c.drawCircle(gx, gy, R, trazo("#FFFFFF", 2, .35))
        pi = s["pin"]; dt = t - self.ta(pi["word"], e)
        if dt > 0:
            x, y, _ = pr(np.array([pi["lon"]]), np.array([pi["lat"]])); x, y = float(x[0]), float(y[0]); a = aparece(dt, .12)
            for q in range(2):
                ph = ((t * .9 + q * .5) % 1); c.drawCircle(x, y, 10 + 46 * ph, trazo("#FFB45C", 3, .6 * (1 - ph) * a))
            c.drawCircle(x, y, 13, relleno("#FFB45C", a)); c.drawCircle(x, y, 6, relleno("#3A1E14", a))
            self.pildora(c, pi["label"], x, y - 56, S, a, fnt=self.F["pillb"])
        da = t - self.ta(s["anio_word"], e)
        if da > -.3:
            a = aparece(da + .3, .2); yv = 1170
            prog_ = TI.cubic_out(TI.clamp((da + .3) / .9)); v = int(round(1900 + (s["anio"] - 1900) * prog_))
            with capa(c, alfa=a):
                texto(c, str(v), CX, yv, self.F["big"], S["txt"], tnum=True)
        if s.get("pill"):
            self.pildora(c, s["pill"], CX, 150 + 40, S, aparece(dt0 - .1, .2), fnt=self.F["pill"])

    def carga_mundo(self):
        topo = json.loads((MOTOR / "variantes/documental/vendor/countries-50m.json").read_text())
        tr = topo["transform"]; arcs = [np.cumsum(np.array(a, float), 0) * tr["scale"] + tr["translate"] for a in topo["arcs"]]
        return [a for a in arcs if a[:, 1].max() > 45]

    # ------------------------------------------------------------------ tipografía cinética
    def tipografia(self, c, t, e):
        pal = self.palabras
        for n, ln in enumerate(self.lineas, 1):
            ids = self.idx_linea.get(n)
            if not ids or ln.get("cap", True) is False: continue
            s0 = pal[ids[0]]["s"] - .05
            nxt = self.idx_linea.get(n + 1); fin = (pal[nxt[0]]["s"] - 3 / FPS - .05) if nxt else self.fin_s + 1
            if not (s0 <= t < fin): continue
            sc = next((es for es in reversed(self.escenas) if es["t0"] <= max(t, s0)), self.escenas[0])
            S = SUP[sc["spec"].get("surface", "dark")]
            salida = TI.clamp((fin - t) / .1)
            key = ln.get("key", ""); serif = key.startswith("*"); key = key.lstrip("*")
            words = [p["w"] for p in (pal[i] for i in ids)]
            kw = key.split(); nk = len(kw)
            # posición de la clave dentro de la línea
            norm = lambda w: TI.norm(w)
            kpos = next((i for i in range(len(words) - nk + 1) if [norm(w) for w in words[i:i + nk]] == [norm(w) for w in kw]), None)
            enlinea = set()
            if kpos is not None and kpos + nk < len(words) and self.guion.get("clave_en_linea", False):
                enlinea = set(ids[kpos:kpos + nk]); kpos = None          # clave en medio de la frase: va resaltada dentro de la línea
            ctx_ids = [i for j, i in enumerate(ids) if kpos is None or not (kpos <= j < kpos + nk)]
            key_ids = [] if kpos is None else ids[kpos:kpos + nk]
            fc = self.F["ctx"]; esp = ancho(" ", fc)
            ctxw = [pal[i]["w"] for i in ctx_ids]
            if kpos is not None:   # quita la puntuación que queda colgando
                ctxw = [w.rstrip(":,.") if j == len(ctxw) - 1 else w for j, w in enumerate(ctxw)]
            filas = TX.partir_lineas(ctxw, fc, 820, esp)
            for fi, fila in enumerate(filas):
                tot = sum(ancho(ctxw[j], fc) for j in fila) + esp * max(0, len(fila) - 1)
                x = CX - tot / 2; ybase = CAP_CTX_Y - 62 * (len(filas) - 1 - fi)
                for j in fila:
                    i, w = ctx_ids[j], ctxw[j]
                    dt = t - pal[i]["s"] + .02; a = aparece(dt) * salida; wd = ancho(w, fc)
                    if a > 0:
                        yy = ybase + 18 * (1 - resorte(dt, 12, 14))
                        texto(c, w, x, yy, fc, S["acc"] if i in enlinea else S["txt"], alinear="i", alfa=(1 if i in enlinea else .88) * a, sombra=(3, 8, .35))
                    x += wd + esp
            if key_ids:
                dt = t - pal[key_ids[0]]["s"] + .02; a = aparece(dt) * salida
                if a > 0:
                    fk = self.F["keyserif"] if serif else self.F["key"]; kt = key.rstrip(".,:")
                    wk = ancho(kt, fk); esc = min(1.0, 860 / wk)
                    s_ = (.94 + .06 * resorte(dt, 8, 10)) * esc
                    c.save(); c.translate(CX, CAP_KEY_Y + 26 * (1 - resorte(dt, 8, 10))); c.scale(s_, s_)
                    if S["grid"]:
                        with capa(c, alfa=.55 * a, blur=22):
                            texto(c, kt, 0, 0, fk, S["acc"])
                    texto(c, kt, 0, 0, fk, S["acc"] if not S["grid"] or True else S["txt"], alfa=a, sombra=(4, 12, .35))
                    c.restore()


    # ------------------------------------------------------------------ efectos de sonido (guion.json → "sfx": true)
    def efectos(self):
        """SFX suaves: whoosh en cada transición, pop al aparecer pines/rótulos/notas, tic en contadores, golpe en el hueco,
        sello en cada ✕. Se colocan en el hueco de voz justo ANTES del ancla; si no cabe, a −40 % (la mezcla además baja 5 dB sobre la voz)."""
        P = self.palabras
        spans = [(p["s"], p["e"]) for p in P]
        dur = dict(whoosh=.34, pop=.09, tic=.03, golpe=.32, sello=.22, destello=.7)
        def libre(a, b): return not any(s < b - .01 and e > a + .01 for s, e in spans)
        def pon(t_ancla, nombre, vol):
            d = dur[nombre]
            for t in (t_ancla - d - .02, t_ancla - d - .1, t_ancla - d * .6):
                if t >= 0 and libre(t, t + d): self.sfx(TI.f_de_t(t), nombre, vol); return
            self.sfx(TI.f_de_t(max(0, t_ancla - d * .5)), nombre, vol * .6)
        for k, e in enumerate(self.escenas):
            s = e["spec"]
            if k: pon(e["t0"] + .17, "whoosh", .55)
            for key in ("pins", "rotulos"):
                for q in s.get(key, []):
                    w = q.get("word")
                    if w and not str(w).startswith("@"): pon(self.ta(w, e), "pop", .35)
            if s.get("tipo") == "stat":
                tw = self.ta(s["word"], e)
                for j in range(4):
                    tt = tw + .05 + j * .2
                    if libre(tt, tt + .03): self.sfx(TI.f_de_t(tt), "tic", .35)
                if s.get("nota_word"): pon(self.ta(s["nota_word"], e) + .15, "pop", .3)
            if s.get("tipo") == "fecha":
                tw = self.ta(s["word"], e)
                for j in range(5):
                    tt = tw + .05 + j * .18
                    if libre(tt, tt + .03): self.sfx(TI.f_de_t(tt), "tic", .35)
            if s.get("hueco"): pon(self.ta(s["hueco"]["word"], e), "golpe", .55)
            for it in s.get("items", []): pon(self.ta(it["word"], e) + .55, "sello", .3)
        vistos = set(); ev = []
        for x in sorted(self.ev, key=lambda x: x["f"]):
            if (x["f"] // 6, x["sfx"]) not in vistos: vistos.add((x["f"] // 6, x["sfx"])); ev.append(x)
        self.ev = ev

    # ------------------------------------------------------------------ mapas del mundo (lon/lat, Lambert azimutal)
    def _mundo_rings(self):
        if getattr(self, "_rings", None) is not None: return self._rings
        topo = json.loads((MOTOR / "variantes/documental/vendor/countries-50m.json").read_text())
        tr = topo["transform"]; arcs = [np.cumsum(np.array(a, float), 0) * tr["scale"] + tr["translate"] for a in topo["arcs"]]
        def ring(idx):
            pts = []
            for i in idx:
                a = arcs[i] if i >= 0 else arcs[~i][::-1]; pts.extend(a[1:] if pts else a)
            return np.array(pts)
        out = {}
        for g in topo["objects"]["countries"]["geometries"]:
            if g["type"] not in ("Polygon", "MultiPolygon"): continue
            polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
            out.setdefault(g.get("id") or g["properties"]["name"], []).extend(ring(r) for p in polys for r in p)
        self._rings = out; return out

    def geo(self, proj):
        key = tuple(proj)
        if key in self._geo: return self._geo[key]
        l0, p0 = np.radians(proj[0]), np.radians(proj[1]); R = 6371.0
        def pr(r):
            l = np.radians(r[:, 0]) - l0; p = np.radians(r[:, 1])
            cc = np.sin(p0) * np.sin(p) + np.cos(p0) * np.cos(p) * np.cos(l)
            if cc.min() < -0.2: return None
            k = R * np.sqrt(2 / (1 + cc))
            return np.c_[k * np.cos(p) * np.sin(l), k * (np.cos(p0) * np.sin(p) - np.sin(p0) * np.cos(p) * np.cos(l))]
        rings = self._mundo_rings(); por = {}
        for cid, rs in rings.items():
            q = [x for x in (pr(r) for r in rs) if x is not None and len(x) > 2]
            if q: por[cid] = q
        G = dict(pr=lambda lon, lat: pr(np.array([[lon, lat]]))[0],
                 tierra=path_de([r for cid, rs in por.items() if cid != "250" for r in rs]),
                 francia=path_de(por.get("250", [])),
                 ids={cid: path_de(rs) for cid, rs in por.items()})
        self._geo[key] = G; return G

    def cam_geo(self, e, t, G):
        ks = e["spec"]["cam"]
        c0, r0 = np.array(G["pr"](*ks[0]["c"])), ks[0]["r"]
        for k in ks[1:]:
            ta = self.ta(k["t"], e); u = ease_io_expo((t - ta) / k.get("dur", 1.0))
            c1, r1 = np.array(G["pr"](*k["c"])), k["r"]
            r0 = math.exp(math.log(r0) + (math.log(r1) - math.log(r0)) * u); c0 = c0 + (c1 - c0) * u
        return c0, GW / r0

    def e_geo(self, c, e, t, S):
        s = e["spec"]; G = self.geo(s["proj"]); cen, k = self.cam_geo(e, t, G); lw = lambda px: px / k
        # temblor breve al abrirse el hueco
        hw = s.get("hueco"); th = self.ta(hw["word"], e) if hw else None
        if th is not None and 0 < t - th < .45:
            a = (1 - (t - th) / .45) * 7; c.translate(a * math.sin(t * 90), a * math.cos(t * 70))
        c.save(); c.translate(CX, CY); c.scale(k, -k); c.translate(-cen[0], -cen[1])
        c.drawPath(G["tierra"], relleno(S["tierra"], .95))
        for r in s.get("resaltar", []):
            a = aparece(t - self.ta(r["word"], e), .3)
            if a <= 0: continue
            for cid in r["ids"]:
                if cid in G["ids"]: c.drawPath(G["ids"][cid], relleno(r["col"], r.get("alfa", .45) * a)); c.drawPath(G["ids"][cid], trazo(r["col"], lw(2.5), .9 * a))
        c.drawPath(G["tierra"], trazo(S["borde"], lw(1.4), .7))
        # Francia → hueco
        if hw or s.get("hueco_ya"):
            u = 1.0 if s.get("hueco_ya") else TI.clamp((t - th) / .7)
            if u < 1: c.drawPath(G["francia"], relleno(S["tierra"], .95)); c.drawPath(G["francia"], trazo(S["borde"], lw(1.4), .7))
            if u > 0: self.hueco(c, G, k, ease_io_expo(u) if u < 1 else 1, t)
        else:
            c.drawPath(G["francia"], relleno(S["tierra"], .95)); c.drawPath(G["francia"], trazo(S["borde"], lw(1.4), .7))
        c.restore()
        P = lambda lon, lat: (lambda q: (CX + (q[0] - cen[0]) * k, CY - (q[1] - cen[1]) * k))(G["pr"](lon, lat))
        for ro in s.get("rotulos", []):
            dt = t - self.ta(ro["word"], e)
            if dt <= 0: continue
            x, y = P(ro["lon"], ro["lat"]); a = aparece(dt, .2)
            if ro.get("grande"): self.pildora(c, ro["txt"], x, y - 10 * (1 - resorte(dt, 9, 12)), S, a, fnt=self.F["pillb"])
            elif 40 < x < 950 and 120 < y < 1180: texto(c, ro["txt"], x, y, self.F["rot"], S["sub"], alfa=.85 * a, sombra=(2, 6, .4))
        for pi in s.get("pins", []):
            dt = t - self.ta(pi["word"], e)
            if dt <= 0: continue
            x, y = P(pi["lon"], pi["lat"]); self.pin(c, x, y, pi, dt, t, S)

    def pin(self, c, x, y, pi, dt, t, S):
        a = aparece(dt, .12); sc = resorte(dt, 10, 14)
        for q in range(2):
            ph = ((t * .9 + q * .5) % 1); c.drawCircle(x, y, 10 + 40 * ph, trazo("#FFFFFF", 2.5, .5 * (1 - ph) * a))
        c.drawCircle(x, y, 13 * sc, relleno("#FFFFFF", a)); c.drawCircle(x, y, 6.5 * sc, relleno("#0B1430", a))
        lado = pi.get("lado", "c")
        if lado == "c": self.pildora(c, pi["label"], x, y - 58 * sc, S, a)
        elif lado == "d": self.pildora(c, pi["label"], x + 26, y, S, a, alinear="i")
        else: self.pildora(c, pi["label"], x - 26, y, S, a, alinear="d")

    def hueco(self, c, G, k, u, t):
        """El hueco: abismo negro con paredes de roca (la tierra vecina desplazada), sombra interior y polvo que cae."""
        fr = G["francia"]; b = fr.getBounds(); cx, cy = b.centerX(), b.centerY(); rmax = max(b.width(), b.height()) * .75
        c.save(); c.clipPath(fr, doAntiAlias=True)
        if u < 1:
            m = skia.Path(); m.addCircle(cx, cy, rmax * u); c.clipPath(m, doAntiAlias=True)
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial((cx, cy), rmax, [color("#000000"), color("#05070D"), color("#14100C")], [0, .7, 1])))
        for dy, col, a in ((54, "#0B0705", .95), (36, "#24170F", .95), (22, "#47301F", .95), (11, "#6B4A33", .95), (4, "#8C6446", .9)):        # paredes: la tierra de alrededor, más oscura y más abajo
            c.save(); c.translate(0, -dy / k); c.drawPath(G["tierra"], relleno(col, a)); c.restore()
        c.drawPath(fr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=40 / k, Color=color("#000000", .9),
                                  MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14 / k)))
        rng = np.random.default_rng(4)
        for i in range(70):
            x = b.left() + rng.random() * b.width(); y0 = b.bottom() - rng.random() * b.height()
            y = y0 - ((t * (40 + 60 * rng.random()) + rng.random() * 300) % 300) / k
            c.drawCircle(x, y, (1 + 1.5 * rng.random()) / k, relleno("#C9A27E", .35 * rng.random()))
        c.restore()
        c.drawPath(fr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7 / k, Color=color("#FF6A3D", .25 * u),
                                  MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6 / k)))
        c.drawPath(fr, trazo("#E8B48A", 1.6 / k, .55 * u))

    # ------------------------------------------------------------------ fecha (año que rueda sobre una regla)
    def e_fecha(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tw = self.ta(s["word"], e); dt = t - tw
        de = s.get("desde", s["anio"] - 100)
        v = de + (s["anio"] - de) * TI.cubic_out(TI.clamp(dt / 1.0)) if dt > 0 else de
        if s.get("pill"): self.pildora(c, s["pill"], CX, 330 - 20 * (1 - resorte(dt0, 9, 12)), S, aparece(dt0, .15), fnt=self.F["pillb"])
        yb = 700; a = aparece(dt0, .2)
        txt = str(int(round(v)))
        vel = (1 - TI.clamp(dt / 1.0)) ** 2 if 0 < dt < 1 else 0
        c.save(); c.translate(CX, yb); sc = .92 + .08 * resorte(dt0, 8, 10); c.scale(sc, sc)
        with capa(c, alfa=a, blur=min(5, vel * 8)): texto(c, txt, 0, 0, self.F["big"], S["txt"], tnum=True)
        c.restore()
        # regla de años
        y0 = 930; px = 9.0
        c.drawLine(40, y0, 950, y0, trazo(S["sub"], 2, .5))
        for yr in range(int(v) - 60, int(v) + 61):
            x = CX + (yr - v) * px
            if not 40 < x < 950: continue
            big = yr % 10 == 0; al = .9 * (1 - abs(x - CX) / 480)
            c.drawLine(x, y0, x, y0 - (34 if big else 14), trazo(S["sub"], 3 if big else 1.5, al))
            if big: texto(c, str(yr), x, y0 + 36, self.F["pill"], S["sub"], alfa=al)
        c.drawPath(skia.Path.Polygon([(CX - 14, y0 - 56), (CX + 14, y0 - 56), (CX, y0 - 38)], True), relleno(S["acc"], a))
        tx = s.get("tachar_word")
        if tx:
            u = TI.clamp((t - self.ta(tx, e)) / .35)
            if u > 0:
                w = ancho(txt, self.F["big"]) * sc / 2 + 30
                c.drawLine(CX - w, yb + 10, CX - w + 2 * w * TI.cubic_out(u), yb - 10, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                                                                                StrokeWidth=16, Color=color("#E5322D"), StrokeCap=skia.Paint.kRound_Cap))

    # ------------------------------------------------------------------ lista con ✕ que se trazan
    def e_lista(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        if s.get("pill"): self.pildora(c, s["pill"], CX, 330, S, aparece(dt0, .15), fnt=self.F["pillb"], fondo="#0C1630")
        its = s["items"]; hh = 150; y0 = 700 - (len(its) - 1) * hh / 2
        for i, it in enumerate(its):
            dt = t - self.ta(it["word"], e)
            if dt <= -.05: continue
            a = aparece(dt + .05, .15); sl = 1 - resorte(dt + .05, 8, 11); y = y0 + i * hh; x = CX + 60 * sl
            r = rrc(x, y, 860, 118, 28)
            c.drawRRect(r.makeOffset(0, 10) if hasattr(r, "makeOffset") else r, skia.Paint(AntiAlias=True, Color=color("#0C1630", .18 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
            c.drawRRect(r, relleno("#FFFFFF", .92 * a)); c.drawRRect(r, trazo("#9AAFD6", 2, .6 * a))
            fnt = self.F["item"]; tw_ = ancho(it["txt"], fnt); f2 = fnt if tw_ < 700 else fuente("Inter", 700, int(44 * 700 / tw_))
            texto(c, it["txt"], x - 330, y, f2, "#0C1630", alinear="i", alfa=a)
            # ✕
            u = TI.clamp((dt - .55) / .3)
            cx_, cy_ = x - 375, y; L = 22
            c.drawCircle(cx_, cy_, 30, relleno("#E5322D", .15 * a))
            if u > 0:
                p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Color=color("#E5322D"), StrokeCap=skia.Paint.kRound_Cap)
                u1 = TI.clamp(u * 2); u2 = TI.clamp(u * 2 - 1)
                c.drawLine(cx_ - L, cy_ - L, cx_ - L + 2 * L * u1, cy_ - L + 2 * L * u1, p)
                if u2 > 0: c.drawLine(cx_ + L, cy_ - L, cx_ + L - 2 * L * u2, cy_ - L + 2 * L * u2, p)
                ul = TI.clamp((dt - .8) / .35)
                if ul > 0: c.drawLine(x - 330, y + 2, x - 330 + min(tw_, 700) * TI.cubic_out(ul), y + 2, trazo("#E5322D", 5, .85))

    # ------------------------------------------------------------------ objetos de las cifras
    def obj_hueco(self, c, x, y, dt, t, S, e):
        u = resorte(dt, 6, 8); rx, ry = 330 * u, 120 * u; y += 20
        if rx < 2: return
        c.drawOval(skia.Rect(x - rx - 30, y - ry - 14, x + rx + 30, y + ry + 18), relleno("#6E4A32", .9))
        c.drawOval(skia.Rect(x - rx - 30, y - ry - 14, x + rx + 30, y + ry + 18), trazo("#C9774A", 3, .6))
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y - ry), (0, y + ry)], [color("#2A1A10"), color("#000000")], [0, .6])))
        rng = np.random.default_rng(1)
        for i in range(26):
            px_ = x + (rng.random() - .5) * rx * 1.6; py = y - ry * .4 + ((t * 120 * (.5 + rng.random()) + rng.random() * 200) % (ry * 1.3))
            c.drawCircle(px_, py, 2 + 2 * rng.random(), relleno("#C9A27E", .5 * (1 - (py - y + ry * .4) / (ry * 1.3))))

    def obj_mapa_x2(self, c, x, y, dt, t, S, e):
        w, h = 300, 240; a = aparece(dt, .2); u = resorte(dt - .9, 7, 9)
        c.drawRRect(rrc(x - w / 2 - 6, y, w, h, 18), relleno("#FFFFFF", .22 * a)); c.drawRRect(rrc(x - w / 2 - 6, y, w, h, 18), trazo("#FFFFFF", 3, .8 * a))
        texto(c, "EE. UU.", x - w / 2 - 6, y, self.F["pillb"], "#FFFFFF", alfa=a)
        if u > 0:
            xx = x + w / 2 + 6 + 200 * (1 - u)
            c.drawRRect(rrc(xx, y, w, h, 18), relleno("#FFD34D", .55 * min(1, u))); c.drawRRect(rrc(xx, y, w, h, 18), trazo("#FFD34D", 3, min(1, u)))
            texto(c, "+ Luisiana", xx, y, self.F["pillb"], "#0C1630", alfa=min(1, u))

    def obj_regla(self, c, x, y, dt, t, S, e):
        u = resorte(dt, 6, 8); L = 820; x0 = x - L / 2 + 700 * (1 - u); y0 = y - 50
        r = skia.Rect(x0, y0, x0 + L, y0 + 110)
        c.drawRect(r.makeOffset(0, 14) if hasattr(r, "makeOffset") else r, skia.Paint(AntiAlias=True, Color=color("#000000", .3), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        c.drawRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y0), (0, y0 + 110)], [color("#F3D58A"), color("#D9AE55")])))
        c.drawRect(r, trazo("#8A6420", 2))
        for i in range(101):
            xx = x0 + 10 + i * (L - 20) / 100; hgt = 42 if i % 10 == 0 else 26 if i % 5 == 0 else 14
            c.drawLine(xx, y0, xx, y0 + hgt, trazo("#4A3510", 2 if i % 10 == 0 else 1.2))
            if i % 10 == 0 and 0 < i < 100: texto(c, str(i), xx, y0 + 66, self.F["pill"], "#4A3510")
        texto(c, "1 m", x0 + L - 60, y0 + 82, self.F["pillb"], "#4A3510")

    def obj_euros(self, c, x, y, dt, t, S, e):
        tw = self.ta(e["spec"]["word"], e); n = int(1 + 9 * TI.clamp((t - tw) / .9)) if t > tw else 1
        for col_ in (-1, 0, 1):
            m = max(1, n - abs(col_) * 2)
            for i in range(m):
                cx_, cy_ = x + col_ * 170, y + 120 - i * 24
                c.drawOval(skia.Rect(cx_ - 72, cy_ - 22, cx_ + 72, cy_ + 22), relleno("#8A6420"))
                c.drawOval(skia.Rect(cx_ - 72, cy_ - 30, cx_ + 72, cy_ + 14), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(cx_ - 72, 0), (cx_ + 72, 0)], [color("#FFE28A"), color("#D9A53A"), color("#FFE28A")])))
                c.drawOval(skia.Rect(cx_ - 50, cy_ - 23, cx_ + 50, cy_ + 7), trazo("#B9852A", 2, .8))
            texto(c, "€", cx_, cy_ - 8, self.F["pillb"], "#8A6420")

    def obj_avion(self, c, x, y, dt, t, S, e):
        u = TI.clamp(dt / 2.2); px_ = x - 420 + 840 * TI.cubic_out(u) ; py = y + 60 - 120 * TI.cubic_out(u)
        for i in range(30):
            q = i / 30; tx = px_ - 30 - q * 360; ty = py + 8 + q * 52
            if tx > 40: c.drawCircle(tx, ty, 5 * (1 - q), relleno("#FFFFFF", .35 * (1 - q)))
        c.save(); c.translate(px_, py); c.rotate(-8); s = 1.6
        b = skia.Path(); b.moveTo(70 * s, 0); b.cubicTo(60 * s, -9 * s, 30 * s, -9 * s, -60 * s, -7 * s); b.lineTo(-72 * s, -26 * s); b.lineTo(-80 * s, -26 * s)
        b.lineTo(-74 * s, 0); b.lineTo(-80 * s, 8 * s); b.lineTo(-60 * s, 8 * s); b.cubicTo(30 * s, 9 * s, 60 * s, 9 * s, 70 * s, 0); b.close()
        wg = skia.Path(); wg.moveTo(10 * s, 2 * s); wg.lineTo(-25 * s, 48 * s); wg.lineTo(-38 * s, 48 * s); wg.lineTo(-18 * s, 3 * s); wg.close()
        wg2 = skia.Path(); wg2.moveTo(10 * s, -2 * s); wg2.lineTo(-20 * s, -30 * s); wg2.lineTo(-30 * s, -30 * s); wg2.lineTo(-16 * s, -3 * s); wg2.close()
        c.drawPath(wg2, relleno("#B9C6DE")); c.drawPath(b, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -9 * s), (0, 9 * s)], [color("#FFFFFF"), color("#C4CFE3")])))
        c.drawPath(wg, relleno("#E3E9F5")); c.restore()


def escenas(e):
    for k, s in enumerate(e.escenas):
        print(f"{s['t0']:6.2f} s  {s['spec']['tipo']:7s} {s['spec'].get('surface', 'dark'):6s} {s['trans']:6s} «{e.lineas[s['n'] - 1]['texto']}»")
    print(f"fin {e.fin_s:.2f} s · {e.nf} cuadros a {FPS} fps")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "escenas":
        escenas(Vertical(sys.argv[1])); sys.exit()
    ES.principal(Vertical, Path(__file__).resolve())
