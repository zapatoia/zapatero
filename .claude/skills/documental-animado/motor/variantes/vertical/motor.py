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

# ---- efectos de sonido extra (se registran en el núcleo; los existentes no cambian)
from nucleo import audio as AU                                     # noqa: E402
def _s_silbato():
    """Silbato de árbitro: tono ~3 kHz con el trino de la bolita (FM ~32 Hz) y algo de soplido."""
    d = .55; n = int(d * AU.SR); t = np.arange(n) / AU.SR
    f = 3050 + 220 * np.sign(np.sin(2 * np.pi * 32 * t)) * .5 + 90 * np.sin(2 * np.pi * 32 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / AU.SR) + .25 * np.sin(4 * np.pi * np.cumsum(f) / AU.SR)
    x = x * (.8 + .2 * np.sin(2 * np.pi * 32 * t)) + .18 * AU._banda(AU._ruido(n, 9), 2000, 6000)
    env = np.minimum(1, t / .015) * np.minimum(1, (d - t) / .08) * (1 - .15 * t / d)
    return x * env
def _s_latido():
    """Latido (lub-dub) grave y suave."""
    d = .5; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
    for t0, a in ((0.0, 1.0), (.19, .7)):
        k = int(t0 * AU.SR); tt = t[:n - k]
        x[k:] += a * (np.sin(2 * np.pi * (58 - 12 * tt / .12) * tt) * np.exp(-tt / .055) * np.minimum(1, tt / .004))
    return np.tanh(1.6 * AU._bajos(x, 180))
def _s_estadio():
    """Rumor de estadio que crece y se apaga (un solo golpe de 2 s, sin bucle)."""
    d = 2.0; n = int(d * AU.SR); u = np.linspace(0, 1, n)
    x = AU._banda(AU._ruido(n, 21), 250, 2400) + .5 * AU._banda(AU._ruido(n, 22), 900, 3500) * (1 + .3 * np.sin(2 * np.pi * 3.1 * u * d))
    return x * np.sin(np.pi * u) ** 1.5
AU.SFX.setdefault("silbato", (_s_silbato, -21)); AU.SFX.setdefault("latido", (_s_latido, -21)); AU.SFX.setdefault("estadio", (_s_estadio, -33))
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
        g = self.guion
        if not (self.proy / "palabras.json").exists() and any(l.get("silencio") for l in g["lineas"]):   # prueba sin voz: respeta los silencios
            from nucleo.tiempo import LineaTiempo
            extra = 0.0; ult = {}
            for k, p in enumerate(self.palabras): ult[p.get("linea", 1)] = k
            add = {ult[n]: float(l.get("silencio", 0) or 0) for n, l in enumerate(g["lineas"], 1) if n in ult}
            for k, p in enumerate(self.palabras):
                p["s"] += extra; p["e"] += extra; extra += add.get(k, 0)
            self.tl = LineaTiempo(self.palabras, alias=g.get("alias")); self.fin_s = self.palabras[-1]["e"] + self.COLA; self.nf = TI.f_de_t(self.fin_s)
        pal = self.palabras
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
                      item=fuente("Inter", 700, 44), rot=fuente("Inter", 600, 32), cron=fuente("Inter", 800, 128),
                      etq=fuente("Inter", 800, 46), mini=fuente("Inter", 700, 25), mini2=fuente("Inter", 700, 29))

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
        if s["tipo"] in ("bolas", "penalti") or s.get("camara_fija"): z = 1.0                                  # juego continuo: la cámara no se mueve
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
        if s.get("valor") is None: return
        tw = self.ta(s["word"], e); dt = t - tw
        de = s.get("desde", 0); v = de + (s["valor"] - de) * TI.cubic_out(TI.clamp(dt / .9)) if dt > 0 else de
        a = aparece(dt + .25, .2) if not s.get("ver_desde") else aparece(dt0 - .1, .2)
        if a > 0:
            dec = s.get("decimales", 0); txt = s.get("prefijo", "") + (f"{v:.{dec}f}".replace(".", ",") if dec else (f"{int(round(v)):,}".replace(",", ".") if s.get("miles", True) else str(int(round(v)))))
            fnt = self.F["big"]; yb = 850 if self.guion.get("stat_alto") else 905
            if ancho(txt, fnt) > 860: fnt = fuente("Inter", 800, int(250 * 860 / ancho(txt, fnt)))
            sc = .9 + .1 * resorte(dt + .25, 8, 11)
            vel = abs((s["valor"] - s.get("desde", 0)) / .9 * 3 * (1 - TI.clamp(dt / .9)) ** 2) if 0 < dt < .9 else 0
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
            nxt = next((self.idx_linea[m] for m in range(n + 1, len(self.lineas) + 1) if m in self.idx_linea), None); fin = (pal[nxt[0]]["s"] - 3 / FPS - .05) if nxt else self.fin_s + 1
            if not (s0 <= t < fin): continue
            sc = next((es for es in reversed(self.escenas) if es["t0"] <= max(t, s0)), self.escenas[0])
            S = SUP[sc["spec"].get("surface", "dark")]
            salida = TI.clamp((fin - t) / .1)
            key = ln.get("key", ""); serif = key.startswith("*"); key = key.lstrip("*")
            words = [p["w"] for p in (pal[i] for i in ids)]
            kw = key.split(); nk = len(kw)
            # posición de la clave dentro de la línea
            norm = lambda w: TI.norm(w)
            kpos = next((i for i in reversed(range(len(words) - nk + 1)) if [norm(w) for w in words[i:i + nk]] == [norm(w) for w in kw]), None)
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
            if s.get("tipo") == "penalti":
                for r in self._pen_rondas(e):
                    self.sfx(TI.f_de_t(r["t0"] + .05), "silbato", 1.0)                                    # silbato: empieza la ronda
                    k = 0
                    while r["t0"] + .8 + k * .78 < r["td"] + .5:                                         # latido de espera (ritmo fijo: no avisa)
                        tl_ = r["t0"] + .8 + k * .78
                        if libre(tl_, tl_ + .4): self.sfx(TI.f_de_t(tl_), "latido", 1.0)
                        k += 1
                    if libre(r["td"] + .45, r["td"] + .8): self.sfx(TI.f_de_t(r["td"] + .45), "golpe", .35)   # cae el portero (después: el sonido no avisa)
                    tch = s.get("chut_s", .75)
                    if libre(r["td"] + tch - .02, r["td"] + tch + .32): self.sfx(TI.f_de_t(r["td"] + tch - .02), "whoosh", 1.0)   # chut
                    if libre(r["td"] + tch + .34, r["td"] + tch + .45): self.sfx(TI.f_de_t(r["td"] + tch + .34), "pop", .4)       # red
                # gancho: estadio, portero que cae, estirada de ejemplo, marcador que aparece
                self.sfx(0, "estadio", 1.0)
                if s.get("portero_word"):
                    tp = self.ta(s["portero_word"], e); pon(tp, "whoosh", .4); self.sfx(TI.f_de_t(tp + .32), "golpe", .45)
                if s.get("demo_tiro"):
                    tt_ = self.ta(s["demo_tiro"], e); pon(tt_, "whoosh", .55); self.sfx(TI.f_de_t(tt_ + .45), "golpe", .4)
                if s.get("demo_word"):
                    td_ = self.ta(s["demo_word"], e); pon(td_, "pop", .45)
                    for j in range(8): self.sfx(TI.f_de_t(td_ + .1 + j * .22), "tic", .5)
            if s.get("tipo") == "bolas":
                for nv in s.get("niveles", [])[1:]: pon(self.ta(nv["word"], e), "pop", .35)
                pon(self.ta(s["blanco_word"], e), "destello", .6)
                if s.get("ciclo"):
                    tb, tn, per = self.ta(s["blanco_word"], e), self.ta(s["numeros_word"], e), s.get("ciclo_s", 1.5)
                    tt = tb + per
                    while tt < tn - .2:
                        if libre(tt, tt + .03): self.sfx(TI.f_de_t(tt), "tic", .3)
                        tt += per
                for x in s.get("extra", []): pon(self.ta(x["word"], e), "pop", .4)
                pon(self.ta(s["parar_word"], e) + .1, "golpe", .5)
                pon(self.ta(s["numeros_word"], e), "pop", .35)
                pon(self.ta(s["revelar_word"], e), "golpe", .55)
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
            cx_, cy_ = x - 375, y; L = 22
            if s.get("marca") == "mas":
                u = TI.clamp((dt - .3) / .25)
                c.drawCircle(cx_, cy_, 30, relleno("#2FBF71", .18 * a))
                if u > 0:
                    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Color=color("#2FBF71"), StrokeCap=skia.Paint.kRound_Cap)
                    c.drawLine(cx_ - L * u, cy_, cx_ + L * u, cy_, p); c.drawLine(cx_, cy_ - L * u, cx_, cy_ + L * u, p)
                continue
            # ✕
            u = TI.clamp((dt - .55) / .3)
            c.drawCircle(cx_, cy_, 30, relleno("#E5322D", .15 * a))
            if u > 0:
                p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Color=color("#E5322D"), StrokeCap=skia.Paint.kRound_Cap)
                u1 = TI.clamp(u * 2); u2 = TI.clamp(u * 2 - 1)
                c.drawLine(cx_ - L, cy_ - L, cx_ - L + 2 * L * u1, cy_ - L + 2 * L * u1, p)
                if u2 > 0: c.drawLine(cx_ + L, cy_ - L, cx_ + L - 2 * L * u2, cy_ - L + 2 * L * u2, p)
                ul = TI.clamp((dt - .8) / .35)
                if ul > 0: c.drawLine(x - 330, y + 2, x - 330 + min(tw_, 700) * TI.cubic_out(ul), y + 2, trazo("#E5322D", 5, .85))

    # ------------------------------------------------------------------ objetos de las cifras
    def obj_humo(self, c, x, y, dt, t, S, e):
        """Fábrica con chimeneas; el humo adelgaza tras la palabra de la cifra."""
        tw = self.ta(e["spec"]["word"], e); baja = 1 - .75 * TI.clamp((t - tw) / 1.2) if t > tw else 1
        a = aparece(dt, .2); yb = y + 190
        c.drawRect(skia.Rect(x - 300, yb - 120, x + 300, yb), relleno("#5A3A2A", a))
        for i in range(4):
            xx = x - 300 + i * 150; tri = skia.Path.Polygon([(xx, yb - 120), (xx + 150, yb - 120), (xx + 150, yb - 190)], True); c.drawPath(tri, relleno("#6E4A36", a))
        for k, cx_ in enumerate((x - 210, x + 30, x + 230)):
            c.drawRect(skia.Rect(cx_ - 26, yb - 280, cx_ + 26, yb - 120), relleno("#7A5240", a)); c.drawRect(skia.Rect(cx_ - 30, yb - 295, cx_ + 30, yb - 275), relleno("#94664F", a))
            for q in range(7):
                ph = ((t * .45 + q / 7 + k * .13) % 1); r = (14 + 26 * ph) * baja
                c.drawCircle(cx_ + 40 * ph + 10 * math.sin(t * 2 + q), yb - 305 - 95 * ph, r, relleno("#B9A99C", .42 * (1 - ph) * a * (.4 + .6 * baja)))
        for i in range(6):
            c.drawRect(skia.Rect(x - 270 + i * 95, yb - 80, x - 230 + i * 95, yb - 40), relleno("#FFC46B", .55 * a))

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


    # ------------------------------------------------------------------ mapamundi Equal Earth con meridiano central móvil y giro
    def _ee(self):
        if getattr(self, "_eeR", None) is not None: return self._eeR
        A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796; M = np.sqrt(3) / 2
        def fac(lat):
            th = np.arcsin(M * np.sin(np.radians(lat)))
            y = th * (A1 + A2 * th ** 2 + th ** 6 * (A3 + A4 * th ** 2))
            gx = 2 * np.sqrt(3) * np.cos(th) / (3 * (A1 + 3 * A2 * th ** 2 + th ** 6 * (7 * A3 + 9 * A4 * th ** 2)))
            return gx * 6371.0, y * 6371.0
        rs = []
        for cid, rings in self._mundo_rings().items():
            for r in rings:
                if len(r) < 4: continue
                r = r[::2] if len(r) > 60 else r
                lon = np.degrees(np.unwrap(np.radians(r[:, 0])))          # anillos que cruzan los 180°: longitud continua
                gx, y = fac(r[:, 1]); rs.append((cid, lon, gx, y))
        la = np.linspace(-90, 90, 181); gxo, yo = fac(la)
        self._eeR = dict(fac=fac, rings=rs, borde=(gxo, yo)); return self._eeR

    def _key(self, ks, e, t, campo="v", ease=True):
        v = ks[0][campo]
        for k in ks[1:]:
            u = (t - self.ta(k["t"], e)) / k.get("dur", 1.0); u = ease_io_expo(u) if ease else TI.clamp(u)
            v = v + (k[campo] - v) * u if not isinstance(v, list) else [a + (b - a) * u for a, b in zip(v, k[campo])]
        return v

    def e_mundo(self, c, e, t, S):
        s = e["spec"]; E = self._ee(); fac = E["fac"]
        lam = self._key(s.get("lam", [{"t": "@0", "v": 0}]), e, t)
        rot = self._key(s.get("rot", [{"t": "@0", "v": 0}]), e, t)
        def pr(lon, lat):
            gx, y = fac(np.array([lat], float)); d = ((lon - lam + 180) % 360) - 180
            return float(np.radians(d) * gx[0]), float(y[0])
        cams = s.get("cam", [{"t": "@0", "c": [None, 0], "r": 17600}])
        def cen_of(k):
            cc = k["c"]; return np.array(pr(lam if cc[0] is None else cc[0], cc[1]))
        cen = cen_of(cams[0]); r0 = cams[0]["r"]
        for k in cams[1:]:
            u = ease_io_expo((t - self.ta(k["t"], e)) / k.get("dur", 1.0)); c1 = cen_of(k)
            r0 = math.exp(math.log(r0) + (math.log(k["r"]) - math.log(r0)) * u); cen = cen + (c1 - cen) * u
        k_ = GW / r0; lw = lambda px: px / k_
        c.save(); c.translate(CX, CY); c.rotate(rot); c.scale(k_, -k_); c.translate(-cen[0], -cen[1])
        gxo, yo = E["borde"]; ol = skia.Path(); ol.moveTo(-math.pi * gxo[0], yo[0])
        for g_, y_ in zip(gxo, yo): ol.lineTo(-math.pi * g_, y_)
        for g_, y_ in zip(gxo[::-1], yo[::-1]): ol.lineTo(math.pi * g_, y_)
        ol.close()
        c.drawPath(ol, relleno("#0E2350", .95)); c.save(); c.clipPath(ol, doAntiAlias=True)
        # retícula
        gw = s.get("reticula_word"); ga = aparece(t - self.ta(gw, e), .4) if gw else (.35 if s.get("reticula") else 0)
        if ga > 0:
            for lo in range(-180, 181, 30):
                p = skia.Path(); la_ = np.linspace(-90, 90, 61); g2, y2 = fac(la_); d = ((lo - lam + 180) % 360) - 180
                p.moveTo(math.radians(d) * g2[0], y2[0])
                for a_, b_ in zip(g2, y2): p.lineTo(math.radians(d) * a_, b_)
                c.drawPath(p, trazo(S["borde"], lw(1.2), .5 * ga))
            for la_ in range(-60, 61, 30):
                g2, y2 = fac(np.array([la_], float)); c.drawLine(-math.pi * g2[0], y2[0], math.pi * g2[0], y2[0], trazo(S["borde"], lw(1.2), .5 * ga))
        hl = {}
        for h in s.get("resaltar", []):
            a = aparece(t - self.ta(h["word"], e), .3)
            for cid in h["ids"]: hl[cid] = (h["col"], a)
        tierra = skia.Path(); extra = {}
        for cid, lon, gx, y in E["rings"]:
            for sh in (-720, -360, 0, 360, 720):
                d = lon - lam + sh
                if d.max() < -182 or d.min() > 182: continue
                x = np.radians(d) * gx; pth = extra.setdefault(cid, skia.Path()) if cid in hl else tierra
                pth.moveTo(x[0], y[0])
                for xx, yy in zip(x[1:], y[1:]): pth.lineTo(xx, yy)
                pth.close()
        c.drawPath(tierra, relleno(S["tierra"] if S["tierra"] != "#12244A" else "#2A4F9A", 1)); c.drawPath(tierra, trazo("#0E2350", lw(1), .8))
        for cid, pth in extra.items():
            col, a = hl[cid]; c.drawPath(pth, relleno("#2A4F9A")); c.drawPath(pth, relleno(col, a)); c.drawPath(pth, trazo("#0E2350", lw(1), .8))
        # meridiano cero
        mw = s.get("meridiano_word")
        if mw:
            u = TI.clamp((t - self.ta(mw, e)) / .8)
            if u > 0:
                la_ = np.linspace(85, 85 - 170 * TI.cubic_out(u), 80); g2, y2 = fac(la_); d = ((0 - lam + 180) % 360) - 180
                p = skia.Path(); p.moveTo(math.radians(d) * g2[0], y2[0])
                for a_, b_ in zip(g2, y2): p.lineTo(math.radians(d) * a_, b_)
                c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=lw(12), Color=color("#FFD34D", .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, lw(6))))
                c.drawPath(p, trazo("#FFD34D", lw(4)))
        c.restore()
        c.drawPath(ol, trazo("#7FA6F0", lw(2), .6))
        # línea del centro del mapa (la que «engaña»)
        cw = s.get("centro_word")
        if cw:
            a = aparece(t - self.ta(cw, e), .3)
            if a > 0:
                g2, y2 = fac(np.array([-75.0, 75.0])); p = trazo("#FFFFFF", lw(3), .75 * a); p.setPathEffect(skia.DashPathEffect.Make([lw(18), lw(12)], 0))
                c.drawLine(0, y2[0], 0, y2[1], p)
        c.restore()
        def scr(lon, lat):
            x, y = pr(lon, lat); x, y = (x - cen[0]) * k_, -(y - cen[1]) * k_
            ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            return CX + x * ca - y * sa, CY + x * sa + y * ca
        if cw:
            a = aparece(t - self.ta(cw, e) - .15, .2)
            if a > 0:
                xx, yy = scr(lam, 0); g2, y2 = fac(np.array([75.0]))
                self.pildora(c, s.get("centro_label", "centro del mapa"), xx, CY - (y2[0] - cen[1]) * k_ - 30, S, a, fnt=self.F["pill"])
        for pi in s.get("pins", []):
            dt = t - self.ta(pi["word"], e)
            if dt > 0:
                x, y = scr(pi["lon"], pi["lat"]); self.pin(c, x, y, pi, dt, t, S)
        if s.get("pill"):
            a = aparece(t - self.ta(s.get("pill_word", "@0"), e), .2)
            if a > 0: self.pildora(c, s["pill"], CX, 330, S, a, fnt=self.F["pillb"])

    # ------------------------------------------------------------------ globo que gira (ortográfica)
    def e_globo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        lon0 = self._key(s["lon"], e, t) + s.get("vel", 0) * dt0 if "lon" in s else s.get("lon0", 0) + s.get("vel", 25) * dt0
        lat0 = self._key(s["lat"], e, t) if "lat" in s else s.get("lat0", 20)
        R = 400 * (.9 + .1 * resorte(dt0, 6, 8)); gx, gy = CX, 640
        def pr(lon, lat):
            l = np.radians(np.asarray(lon) - lon0); p = np.radians(np.asarray(lat)); p0 = np.radians(lat0)
            x = np.cos(p) * np.sin(l); y = np.cos(p0) * np.sin(p) - np.sin(p0) * np.cos(p) * np.cos(l)
            vis = np.sin(p0) * np.sin(p) + np.cos(p0) * np.cos(p) * np.cos(l) > 0
            return gx + R * x, gy - R * y, vis
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(gx, gy, R * 1.25, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx, gy), R * 1.25, [color("#3A6FD8", .0), color("#3A6FD8", .0), color("#3A6FD8", .35), color("#000000", 0)], [0, .78, .8, 1])))
        c.drawCircle(gx, gy, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx - R * .35, gy - R * .4), R * 1.6, [color("#2D63D0"), color("#163A8C"), color("#081436")], [0, .55, 1])))
        land = skia.Path()
        for cid, rings in self._mundo_rings().items():
            for r in rings:
                if len(r) < 4: continue
                r = r[::2] if len(r) > 60 else r
                X, Y, V = pr(r[:, 0], r[:, 1])
                if V.mean() < .999: continue                      # solo anillos enteros a la vista (sin cortes raros en el borde)
                land.moveTo(X[0], Y[0])
                for xx, yy in zip(X[1:], Y[1:]): land.lineTo(xx, yy)
                land.close()
        c.drawPath(land, relleno("#5C8DF0", .95)); c.drawPath(land, trazo("#0E2350", 1, .6))
        c.drawCircle(gx, gy, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx + R * .3, gy + R * .35), R * 1.3, [color("#000000", 0), color("#000000", .0), color("#000000", .45)], [0, .5, 1])))
        c.drawCircle(gx, gy, R, trazo("#BFD4FF", 2, .5))
        for pi in s.get("pins", []):
            dt = t - self.ta(pi["word"], e)
            if dt <= 0: continue
            X, Y, V = pr([pi["lon"]], [pi["lat"]])
            if V[0]: self.pin(c, float(X[0]), float(Y[0]), pi, dt, t, S)
        if s.get("pill"):
            self.pildora(c, s["pill"], CX, 170, S, aparece(t - self.ta(s.get("pill_word", "@0"), e), .2), fnt=self.F["pillb"])


    # ------------------------------------------------------------------ gente: rejilla de personas que desaparecen (o grupos con huecos)
    def figura(self, c, x, y, h, col, a=1.0, hueco=False):
        w = h * .42
        if hueco:
            p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5, Color=color(col, .7 * a))
            p.setPathEffect(skia.DashPathEffect.Make([7, 6], 0))
            c.drawRRect(rrc(x, y - h * .3, w, h * .56, w * .45), p); c.drawCircle(x, y - h * .74, w * .36, p); return
        c.drawRRect(rrc(x, y - h * .3, w, h * .56, w * .45), relleno(col, a))
        c.drawCircle(x, y - h * .74, w * .36, relleno(col, a))

    def e_gente(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        if s.get("pill"): self.pildora(c, s["pill"], CX, 220, S, aparece(dt0 - .05, .15), fnt=self.F["pillb"])
        if s.get("grupos"):
            gs = s["grupos"]; hh = min(230, 820 / len(gs)); y0 = 680 - (len(gs) - 1) * hh / 2; ch = min(200, hh - 24); fh = ch * .55
            for i, gr in enumerate(gs):
                dt = t - self.ta(gr["word"], e)
                if dt <= -.05: continue
                a = aparece(dt + .05, .15); sl = 1 - resorte(dt + .05, 8, 11); y = y0 + i * hh; x = CX + 60 * sl
                r = rrc(x, y, 880, ch, 30)
                c.drawRRect(r, relleno("#FFFFFF", .10 * a)); c.drawRRect(r, trazo("#FFFFFF", 2, .25 * a))
                texto(c, gr["label"], x - 410, y - ch * .31, self.F["pillb"], S["txt"], alinear="i", alfa=a)
                ic = gr.get("icono")
                if ic: self.vehiculo(c, ic, x - 300, y + ch * .12, ch * .5, a)
                n = gr.get("n", 8); pat = gr.get("patron"); paso = 104 if n > 4 else 150; fx0 = x - (n - 1) * paso / 2 + (110 if n <= 4 else 0)
                if gr.get("alerta") and dt > .35:
                    c.drawRRect(r, trazo("#E5322D", 5, aparece(dt - .35, .15)))
                for j in range(n):
                    fx = fx0 + j * paso if n <= 4 else x - 380 + j * 104; hueco = (j % 2 == 1) if pat is None else not pat[j]
                    fa = a * (1 if not hueco else TI.clamp((dt - .35) / .25) if dt > .35 else 0)
                    if hueco: self.figura(c, fx, y + ch * .4, fh, "#FF6A5C", fa, True)
                    else: self.figura(c, fx, y + ch * .4, fh, "#CFE0FF", a)
            return
        cols, rows = s.get("cols", 10), s.get("rows", 10); h = 62; gx, gy = 84, 78
        x0 = CX - (cols - 1) * gx / 2; y0 = 300 + h
        tq = self.ta(s["quitar_word"], e) if s.get("quitar_word") else (e["t0"] - 9 if s.get("ya_quitados") else None)
        tr = self.ta(s["rellenar_word"], e) if s.get("rellenar_word") else None
        rng = np.random.default_rng(11); orden = rng.permutation(cols * rows); quita = set(orden[:cols * rows // 2].tolist())
        retraso = {k: .5 * rng.random() for k in quita}
        for i in range(rows):
            for j in range(cols):
                k = i * cols + j; x = x0 + j * gx; y = y0 + i * gy
                ap = aparece(dt0 - .02 * k / 3, .15)
                if ap <= 0: continue
                if tr is not None and k in quita and list(sorted(quita)).index(k) % 7 == 0 and t > tr + 1.2 * (list(sorted(quita)).index(k) // 7) / 8:
                    u = aparece(t - tr - 1.2 * (list(sorted(quita)).index(k) // 7) / 8, .3); self.figura(c, x, y, h, "#8FE3A8", ap * u)
                    if u < 1: self.figura(c, x, y, h, "#CFE0FF", .35 * ap * (1 - u), True)
                elif tq is not None and k in quita and t > tq + retraso[k]:
                    u = TI.clamp((t - tq - retraso[k]) / .6)
                    if u < 1:
                        self.figura(c, x, y, h, "#CFE0FF", (1 - u) * ap)
                        r2 = np.random.default_rng(k)
                        for q in range(9):
                            px = x + (r2.random() - .5) * 26 + 70 * u * r2.random(); py = y - h * r2.random() - 60 * u * r2.random()
                            c.drawCircle(px, py, 2.5 * (1 - u) + .5, relleno("#FFD9A0", .8 * (1 - u)))
                    else:
                        self.figura(c, x, y, h, "#CFE0FF", .35 * ap, True)
                else:
                    self.figura(c, x, y, h, "#CFE0FF", ap)


    def obj_ciudad(self, c, x, y, dt, t, S, e):
        """Perfil de ciudad de noche; tras la palabra se apaga la mitad de las ventanas (con parpadeo)."""
        tw = self.ta(e["spec"]["word"], e); a = aparece(dt, .2); yb = y + 260
        rng = np.random.default_rng(3); xs = x - 420
        while xs < x + 420:
            w = 70 + 60 * rng.random(); hgt = 180 + 280 * rng.random()
            c.drawRect(skia.Rect(xs, yb - hgt, xs + w - 8, yb), relleno("#152B5C", a))
            for wy in np.arange(yb - hgt + 18, yb - 20, 30):
                for wx in np.arange(xs + 12, xs + w - 22, 22):
                    k = rng.random(); apaga = k < .5
                    on = 1.0
                    if apaga and t > tw - .35:
                        ph = t - tw + .35 - k * .6
                        on = 0 if ph > .25 else (1 if ph < 0 else (1 if int(ph * 40) % 2 else .2))
                    if rng.random() < .85: c.drawRect(skia.Rect(wx, wy, wx + 11, wy + 14), relleno("#FFD98A", .9 * a * on + .06))
            xs += w
        c.drawRect(skia.Rect(x - 440, yb, x + 440, yb + 6), relleno("#0B1530", a))

    def e_barras(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        if s.get("pill"): self.pildora(c, s["pill"], CX, 330, S, aparece(t - self.ta(s.get("pill_word", "@0"), e), .15), fnt=self.F["pillb"], fondo="#0C1630")
        bs = s["barras"]; mx = s.get("max", max(b["valor"] for b in bs)); hh = 210; y0 = 640 - (len(bs) - 1) * hh / 2; W_ = 640
        for i, b in enumerate(bs):
            dt = t - self.ta(b["word"], e)
            if dt <= -.05: continue
            a = aparece(dt + .05, .15); u = TI.cubic_out(TI.clamp(dt / .8)); y = y0 + i * hh
            texto(c, b["label"], 110, y - 62, self.F["pillb"], "#0C1630", alinear="i", alfa=a)
            c.drawRRect(rrc(110 + W_ / 2, y + 10, W_, 70, 35), relleno("#C9D6EE", .5 * a))
            w = max(70, W_ * b["valor"] / mx * u)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, y - 25, 110 + w, y + 45), 35, 35), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(110, 0), (110 + W_, 0)], [color(b.get("col", "#2F6BFF")), color("#6EA0FF")])))
            texto(c, b["txt"], 110 + w + 24, y + 10, self.F["item"], "#0C1630", alinear="i", alfa=aparece(dt - .5, .2))


    def vehiculo(self, c, tipo, x, y, h, a):
        col = color("#9DB8FF", a)
        if tipo == "coche":
            w = h * 2.2
            b = skia.Path(); b.moveTo(x - w / 2, y + h * .2); b.lineTo(x - w / 2, y - h * .05); b.lineTo(x - w * .28, y - h * .1); b.lineTo(x - w * .15, y - h * .45)
            b.lineTo(x + w * .2, y - h * .45); b.lineTo(x + w * .33, y - h * .1); b.lineTo(x + w / 2, y - h * .02); b.lineTo(x + w / 2, y + h * .2); b.close()
            c.drawPath(b, skia.Paint(AntiAlias=True, Color=col))
            for wx in (x - w * .28, x + w * .28): c.drawCircle(wx, y + h * .22, h * .17, relleno("#0B1530", a)); c.drawCircle(wx, y + h * .22, h * .09, relleno("#9DB8FF", a))
            c.drawRect(skia.Rect(x - w * .1, y - h * .38, x + w * .15, y - h * .12), relleno("#0B1530", .7 * a))
        else:
            s_ = h / 75; x += 20
            b = skia.Path(); b.moveTo(70 * s_ + x, y); b.cubicTo(60 * s_ + x, y - 9 * s_, 30 * s_ + x, y - 9 * s_, x - 60 * s_, y - 7 * s_); b.lineTo(x - 72 * s_, y - 26 * s_)
            b.lineTo(x - 80 * s_, y - 26 * s_); b.lineTo(x - 74 * s_, y); b.lineTo(x - 60 * s_, y + 8 * s_); b.cubicTo(30 * s_ + x, y + 9 * s_, 60 * s_ + x, y + 9 * s_, 70 * s_ + x, y); b.close()
            wg = skia.Path(); wg.moveTo(x + 10 * s_, y + 2 * s_); wg.lineTo(x - 25 * s_, y + 40 * s_); wg.lineTo(x - 38 * s_, y + 40 * s_); wg.lineTo(x - 18 * s_, y + 3 * s_); wg.close()
            c.drawPath(b, skia.Paint(AntiAlias=True, Color=col)); c.drawPath(wg, skia.Paint(AntiAlias=True, Color=col))

    def obj_familias(self, c, x, y, dt, t, S, e):
        """Las 16 combinaciones posibles de 4 abuelos (cada uno sigue o no): solo una conserva a los cuatro."""
        tw = self.ta(e["spec"]["word"], e); a = aparece(dt, .2)
        for k in range(16):
            i, j = divmod(k, 4); cx_ = x - 330 + j * 220; cy_ = y - 185 + i * 115
            ak = a * aparece(dt - .04 * k, .12)
            if ak <= 0: continue
            todos = k == 15; on = todos and t > tw - .1
            c.drawRRect(rrc(cx_, cy_, 200, 100, 22), relleno("#2FBF71" if on else "#FFFFFF", (.35 if on else .08) * ak))
            if on: c.drawRRect(rrc(cx_, cy_, 200, 100, 22), trazo("#2FBF71", 4, ak))
            for q in range(4):
                vivo = (k >> q) & 1; fx = cx_ - 66 + q * 44
                if vivo: self.figura(c, fx, cy_ + 34, 58, "#CFE0FF", ak)
                else: self.figura(c, fx, cy_ + 34, 58, "#FF6A5C", .8 * ak, True)

    # ------------------------------------------------------------------ bolas (juego «sigue la pelota roja» sobre una silueta de neón)
    def _bolas_prep(self, e):
        """Simulación determinista (120 Hz, independiente del FPS): pelotas que rebotan en el borde de la silueta y entre sí.
        La semilla se elige para que, al pararse, la roja quede en la posición `respuesta` (contando de izquierda a derecha)."""
        if getattr(self, "_B", None) is not None: return self._B
        from scipy import ndimage
        s = e["spec"]; R = s.get("radio", 30)
        # silueta: países (ids ISO numéricos) con los anillos dentro de `lon_min..lon_max` / `lat_min..lat_max`
        sil = s.get("silueta", {}); rings = self._mundo_rings()
        lo0, lo1 = sil.get("lon", [-180, 180]); la0, la1 = sil.get("lat", [-90, 90])
        rs = [r for cid in sil.get("ids", ["724"]) for r in rings.get(cid, [])
              if lo0 <= r[:, 0].mean() <= lo1 and la0 <= r[:, 1].mean() <= la1 and len(r) > 8]
        l0 = np.radians(np.mean([r[:, 0].mean() for r in rs])); p0 = np.radians(np.mean([r[:, 1].mean() for r in rs]))
        def pr(r):
            l = np.radians(r[:, 0]) - l0; p = np.radians(r[:, 1])
            cc = np.sin(p0) * np.sin(p) + np.cos(p0) * np.cos(p) * np.cos(l); k = np.sqrt(2 / (1 + cc))
            return np.c_[k * np.cos(p) * np.sin(l), -k * (np.cos(p0) * np.sin(p) - np.sin(p0) * np.cos(p) * np.cos(l))]
        q = [pr(r) for r in rs]; allp = np.vstack(q); mn, mx = allp.min(0), allp.max(0)
        ancho_px = sil.get("ancho", 820); esc = ancho_px / (mx[0] - mx[0] + mx[0] - mn[0])
        cy = sil.get("cy", 760); off = np.array([CX, cy]) - (mn + mx) / 2 * esc
        q = [p * esc + off for p in q]
        grande = max(range(len(q)), key=lambda i: len(q[i]))                 # el contorno principal es el campo de juego
        path = path_de(q); campo = path_de([q[grande]])
        # máscara y distancia al borde (a 1/2 de resolución)
        ds = 2; mw, mh = W // ds, H // ds
        from nucleo.lienzo import Lienzo
        Lm = Lienzo(mw, mh); Lm.canvas.clear(skia.ColorBLACK); Lm.canvas.scale(1 / ds, 1 / ds)
        Lm.canvas.drawPath(campo, relleno("#FFFFFF")); m = Lm.arr[..., 0] > 127
        dist = ndimage.gaussian_filter(ndimage.distance_transform_edt(m) * ds, 2.0)
        gy, gx = np.gradient(dist)
        def D(x, y):
            i = int(min(max(y / ds, 0), mh - 1)); j = int(min(max(x / ds, 0), mw - 1)); return dist[i, j], gx[i, j], gy[i, j]
        # tiempos
        ta = lambda w: self.ta(w, e)
        niv = sorted((ta(n["word"]), n["v"]) for n in s["niveles"])
        t_stop = ta(s["parar_word"]); extra = [(ta(x["word"]), x) for x in s.get("extra", [])]
        def vel(t):
            v = niv[0][1]
            for tt, vv in niv:
                if t >= tt: v = v + (vv - v) * 1  # escalón suavizado abajo
            vs = niv[0][1]
            for k, (tt, vv) in enumerate(niv):
                u = TI.clamp((t - tt) / .6); u = u * u * (3 - 2 * u); vs = vs + (vv - vs) * u
            if t > t_stop: vs *= max(0.0, 1 - (t - t_stop) / .35) ** 2
            return vs
        n0 = s.get("n", 3); DT = 1 / 120; T = self.fin_s + 1; N = int(T / DT) + 2
        cand = [(x, y) for y in range(0, H, 12) for x in range(0, W, 12) if D(x, y)[0] > R + 30]
        def simular(seed):
            rng = np.random.default_rng(seed)
            nb = n0 + sum(x["n"] if "n" in x else 1 for _, x in extra)
            P = np.full((N, nb, 2), np.nan, np.float32)
            pos = []; head = []; activo = []
            for i in range(n0):
                for _ in range(400):
                    x, y = cand[rng.integers(len(cand))]
                    if all(math.hypot(x - a, y - b) > 6 * R for a, b in pos): break
                pos.append([float(x), float(y)]); head.append(rng.random() * 2 * math.pi); activo.append(True)
            pend = sorted([tt for tt, x in extra for _ in range(x.get("n", 1))])
            for k in range(N):
                t = k * DT
                while pend and t >= pend[0]:
                    pend.pop(0)
                    best = max(cand[::7], key=lambda c: min(math.hypot(c[0] - a, c[1] - b) for a, b in pos) + rng.random() * 30)
                    pos.append([float(best[0]), float(best[1])]); head.append(rng.random() * 2 * math.pi)
                v = vel(t)
                for i in range(len(pos)):
                    head[i] += rng.normal(0, 1.6) * math.sqrt(DT)
                    pos[i][0] += math.cos(head[i]) * v * DT; pos[i][1] += math.sin(head[i]) * v * DT
                    d, nx, ny = D(*pos[i]); nn = math.hypot(nx, ny) + 1e-9; nx /= nn; ny /= nn
                    if d < R + 8:
                        vx, vy = math.cos(head[i]), math.sin(head[i]); dot = vx * nx + vy * ny
                        if dot < 0: vx -= 2 * dot * nx; vy -= 2 * dot * ny; head[i] = math.atan2(vy, vx)
                        pos[i][0] += nx * (R + 8 - d); pos[i][1] += ny * (R + 8 - d)
                for i in range(len(pos)):
                    for j in range(i + 1, len(pos)):
                        dx = pos[j][0] - pos[i][0]; dy = pos[j][1] - pos[i][1]; dd = math.hypot(dx, dy)
                        if dd < 2 * R + 6 and dd > 1e-6:
                            ux, uy = dx / dd, dy / dd
                            ai = math.cos(head[i]) * ux + math.sin(head[i]) * uy; aj = math.cos(head[j]) * ux + math.sin(head[j]) * uy
                            if ai - aj > 0:          # se acercan: intercambian la componente normal (choque elástico)
                                vi = (math.cos(head[i]) + (aj - ai) * ux, math.sin(head[i]) + (aj - ai) * uy)
                                vj = (math.cos(head[j]) + (ai - aj) * ux, math.sin(head[j]) + (ai - aj) * uy)
                                head[i] = math.atan2(vi[1], vi[0]); head[j] = math.atan2(vj[1], vj[0])
                            sep = (2 * R + 6 - dd) / 2
                            pos[i][0] -= ux * sep; pos[i][1] -= uy * sep; pos[j][0] += ux * sep; pos[j][1] += uy * sep
                for i in range(len(pos)): P[k, i] = pos[i]
            return P
        resp = s.get("respuesta"); ks = min(N - 1, int((t_stop + .6) / DT)); P = None
        for seed in range(s.get("semilla", 1), s.get("semilla", 1) + 300):
            P = simular(seed)
            fin = P[ks]; xs = fin[:, 0]; orden = list(np.argsort(xs))
            gap = np.diff(np.sort(xs)).min() if len(xs) > 1 else 999
            if resp is None or (orden.index(0) + 1 == resp and gap > 100 and fin[:, 1].min() > 430): break
        self._B = dict(P=P, DT=DT, R=R, path=path, campo=campo, orden=orden, t_stop=t_stop, niv=niv, seed=seed,
                       nac={i: (0.0 if i < n0 else None) for i in range(P.shape[1])})
        for i in range(P.shape[1]):
            if self._B["nac"][i] is None: self._B["nac"][i] = np.argmax(~np.isnan(P[:, i, 0])) * DT
        return self._B

    def _bolas_color(self, s, tb, t, base):
        cic = s["ciclo"]; per = s.get("ciclo_s", 1.5); kc = int((t - tb) // per); uc = TI.clamp(((t - tb) - kc * per) / .3)
        prev = base if kc == 0 else __import__("nucleo.compositor", fromlist=["hex_rgb"]).hex_rgb(cic[(kc - 1) % len(cic)])
        now = hex_rgb(cic[kc % len(cic)])
        return "#%02X%02X%02X" % tuple(int(round(x)) for x in (prev * (1 - uc) + now * uc))

    def e_bolas(self, c, e, t, S):
        s = e["spec"]; B = self._bolas_prep(e); R = B["R"]; P = B["P"]; DT = B["DT"]
        ta = lambda w: self.ta(w, e)
        NEON = s.get("neon", "#8F7CFF")
        # halo de fondo
        c.drawCircle(CX, 760, 620, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX, 760), 620, [color(NEON, .22), color(NEON, .06), color(NEON, 0)], [0, .55, 1])))
        # silueta de neón
        pulso = .85 + .15 * math.sin(t * 2.2)
        c.drawPath(B["path"], skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, 420), (0, 1110)], [color("#151B45", .96), color("#0A0F2C", .96)])))
        c.drawPath(B["path"], skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26, Color=color(NEON, .30 * pulso),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
        c.save(); c.clipPath(B["path"], doAntiAlias=True)
        c.drawPath(B["path"], skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=40, Color=color(NEON, .22),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        rng = np.random.default_rng(3)
        for i in range(60):                                                      # polvo de luz dentro de la silueta
            x = 110 + rng.random() * 820; y = 420 + ((rng.random() * 700 - t * (5 + 8 * rng.random())) % 700)
            c.drawCircle(x, y, 1 + 1.6 * rng.random(), relleno("#C9C0FF", .10 + .18 * rng.random()))
        c.restore()
        c.drawPath(B["path"], trazo("#B7ACFF", 5, .55 * pulso))
        c.drawPath(B["path"], trazo("#EEEAFF", 2, .95))
        # dificultad
        dt0 = t - e["t0"]; a0 = aparece(dt0, .25)
        texto(c, s.get("dificultad", "DIFICULTAD"), CX, 178, self.F["lab"], "#C9C3EE", alfa=.9 * a0, tracking=.32)
        nv = sum(1 for tt, _ in B["niv"] if t >= tt); nseg = len(B["niv"]); bw = 560; seg = bw / nseg
        cols = ["#7CFF4F", "#B6F23F", "#FFD24A", "#FF8A3D", "#FF3B4A"]
        for k in range(nseg):
            x = CX - bw / 2 + k * seg
            c.drawRRect(rrc(x + seg / 2, 224, seg - 6, 14, 7), relleno("#FFFFFF", .10 * a0))
            if k < nv:
                u = resorte(t - B["niv"][k][0], 9, 12); col = cols[min(nv - 1, len(cols) - 1)]
                w_ = (seg - 6) * min(1, u)
                with capa(c, alfa=.8 * a0, blur=8): c.drawRRect(rrc(x + 3 + w_ / 2, 224, w_, 14, 7), relleno(col))
                c.drawRRect(rrc(x + 3 + w_ / 2, 224, w_, 14, 7), relleno(col, a0))
        # rótulo (píldora) que cambia por fases
        rot = [r for r in s.get("rotulos", []) if t >= ta(r["word"]) - .05]
        if rot:
            r = rot[-1]; dt = t - ta(r["word"]) + .05; a = aparece(dt, .15)
            fin = r.get("hasta"); a *= 1 if not fin else TI.clamp((ta(fin) - t) / .15)
            if a > 0: self.pildora(c, r["txt"], CX, 312 - 12 * (1 - resorte(dt, 9, 12)), S, a, fnt=self.F["pillb"],
                                   col="#FFFFFF" if not r.get("acento") else r["acento"])
        # pelotas
        k = t / DT; k0 = int(min(max(k, 0), P.shape[0] - 2)); fr = TI.clamp(k - k0)
        pos = P[k0] * (1 - fr) + P[k0 + 1] * fr
        tb = ta(s["blanco_word"]); tn = ta(s["numeros_word"]); tr = ta(s["revelar_word"])
        ub = TI.clamp((t - tb) / .45); ur = TI.clamp((t - tr) / .3)
        ROJO, VERDE, BLANCO = hex_rgb("#FF3B4A"), hex_rgb(s.get("otras", "#2ED47A")), hex_rgb("#F2EEFF")
        mezc = lambda a, b, u: "#%02X%02X%02X" % tuple(int(round(x)) for x in (a * (1 - u) + b * u))
        orden = B["orden"]
        for i in range(P.shape[1]):
            if np.isnan(pos[i, 0]): continue
            dtn = t - B["nac"][i]; sc = resorte(dtn, 9, 13) if dtn < 1.2 else 1.0
            base = ROJO if i == 0 else VERDE
            col = mezc(base, BLANCO, ub)
            if s.get("ciclo") and t >= tb:                                   # todas a la vez cambian de color cada `ciclo_s`
                c_t = lambda tt: self._bolas_color(s, tb, tt, base)
                col = c_t(t) if t < tn else mezc(hex_rgb(c_t(tn)), BLANCO, TI.clamp((t - tn) / .3))
            if i == 0 and ur > 0: col = mezc(BLANCO, ROJO, ur)
            dim = 1 - .6 * ur if i != 0 else 1.0
            x, y = float(pos[i, 0]), float(pos[i, 1])
            # estela
            for j in range(1, 9):
                kk = k0 - j * 2
                if kk < 0 or np.isnan(P[kk, i, 0]): break
                c.drawCircle(float(P[kk, i, 0]), float(P[kk, i, 1]), R * (1 - j * .09) * sc, relleno(col, .10 * (1 - j / 9) * dim))
            # anillo de suelo tras parar
            if t > tn:
                ua = aparece(t - tn - .05 * orden.index(i), .2)
                c.drawOval(skia.Rect.MakeXYWH(x - R * 2, y + R * .85, R * 4, R * .9), trazo("#C9C0FF", 2.2, .5 * ua * dim))
            with capa(c, alfa=.55 * dim, blur=18): c.drawCircle(x, y, R * 1.15 * sc, relleno(col))
            c.drawCircle(x, y + R * .35, R * .95 * sc, skia.Paint(AntiAlias=True, Color=color("#000000", .35 * dim),
                                                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
            hl = mezc(hex_rgb(col), np.array([255., 255, 255]), .65); sh = mezc(hex_rgb(col), np.array([10., 10, 30]), .45)
            c.drawCircle(x, y, R * sc, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (x - R * .35, y - R * .4), R * 1.5 * max(sc, .01), [color(hl, dim), color(col, dim), color(sh, dim)], [0, .45, 1])))
            c.drawOval(skia.Rect.MakeXYWH(x - R * .55, y - R * .72, R * .5, R * .3), relleno("#FFFFFF", .55 * dim * sc))
            c.drawCircle(x, y, R * sc, trazo("#FFFFFF", 1.2, .25 * dim))
            # destello al cambiar de color
            if 0 < t - tb < .6:
                u = (t - tb) / .6; c.drawCircle(x, y, R * (1 + 1.4 * u), trazo("#FFFFFF", 3, .7 * (1 - u)))
            elif s.get("ciclo") and tb < t < tn:
                per = s.get("ciclo_s", 1.5); dc = (t - tb) % per
                if (t - tb) >= per and dc < .45:
                    u = dc / .45; c.drawCircle(x, y, R * (1 + .8 * u), trazo(col, 2.5, .6 * (1 - u)))
            # marcador de la roja (antes del cambio)
            if i == 0 and t < tb + .3:
                am = TI.clamp((tb + .3 - t) / .3) * aparece(dtn, .2); yy = y - R - 26 + 5 * math.sin(t * 6)
                tri = skia.Path(); tri.moveTo(x - 11, yy - 9); tri.lineTo(x + 11, yy - 9); tri.lineTo(x, yy + 7); tri.close()
                c.drawPath(tri, relleno("#FFFFFF", am))
            # revelado: pulsos rojos
            if i == 0 and ur > 0:
                for qn in range(2):
                    ph = ((t - tr) * .9 + qn * .5) % 1; c.drawCircle(x, y, R * (1.1 + 1.6 * ph), trazo("#FF3B4A", 3, .7 * (1 - ph)))
            # número
            if t > tn:
                n = orden.index(i) + 1; dtq = t - tn - .08 * (n - 1)
                if dtq > 0:
                    aq = aparece(dtq, .15); yq = y - R - 52 - 14 * (1 - resorte(dtq, 9, 12))
                    fq = self.F["unit"]; colq = "#FF3B4A" if (i == 0 and ur > 0) else "#FFFFFF"
                    texto(c, str(n), x, yq, fq, colq, alfa=aq * (dim if i else 1), sombra=(4, 10, .5))

    # ------------------------------------------------------------------ penalti (juego: pausa el vídeo cuando el portero se tire)
    ESCALA_PEN = [(0.00, .10, "#8A93A6", "Te adelantaste", "TE ADELANTASTE"), (.10, .20, "#2ED47A", "Golazo", "¡GOLAZO!"),
                  (.20, .30, "#B6F23F", "Gol", "¡GOL!"), (.30, .45, "#FF9A3D", "Al palo", "AL PALO"), (.45, 9.9, "#FF3B4A", "Parada", "PARADA")]

    def _pen_rondas(self, e):
        if getattr(self, "_PR", None) is not None: return self._PR
        s = e["spec"]; out = []
        for k, r in enumerate(s["rondas"]):
            t0 = self.ta(r["word"], e)
            out.append(dict(n=k + 1, t0=t0, td=t0 + r["espera"], lado=r.get("lado", 1 if k % 2 == 0 else -1),
                            amagos=[(t0 + a, (-1 if k % 2 == 0 else 1) * (1 if j % 2 == 0 else -1)) for j, a in enumerate(r.get("amagos", []))],
                            vel=r.get("vel", 1.0)))
        for k, r in enumerate(out): r["t1"] = out[k + 1]["t0"] - .25 if k + 1 < len(out) else self.ta(s["fin_word"], e)
        self._PR = out; return out

    def portero(self, c, x, y, lean, rot, brazos, a=1.0):
        """Portero de frente. (x, y) = caderas. lean/rot en grados; brazos 0 = abiertos a los lados, 1 = estirados por encima."""
        c.save(); c.translate(x, y); c.rotate(rot + lean); c.scale(1.22, 1.22)
        cam, cam2, pant, piel = "#D7FF3A", "#8DB81A", "#1C2340", "#F0C3A0"
        # sombra en el suelo se dibuja fuera
        for sx in (-1, 1):                                                       # piernas
            c.save(); c.translate(sx * 17, 8); c.rotate(-sx * (8 + 10 * brazos))
            c.drawRRect(rrc(0, 46, 24, 92, 11), skia.Paint(AntiAlias=True, Alphaf=a, Shader=skia.GradientShader.MakeLinear([(-12, 0), (12, 0)], [color("#2A3360"), color(pant)])))
            c.drawRRect(rrc(0, 70, 25, 42, 10), relleno("#E9ECF5", .95 * a))   # medias
            c.drawRRect(rrc(sx * 6, 96, 36, 16, 8), relleno("#111522", a))      # botas
            c.restore()
        c.drawRRect(rrc(0, 6, 64, 30, 12), relleno(pant, a))                     # pantalón
        for sx in (-1, 1):                                                       # brazos
            ang = sx * (100 - 70 * brazos) if brazos < 1 else sx * 30
            ang = sx * (105 * (1 - brazos) + 165 * brazos)
            c.save(); c.translate(sx * 30, -78); c.rotate(-ang)
            c.drawRRect(rrc(0, 40, 20, 80, 10), skia.Paint(AntiAlias=True, Alphaf=a, Shader=skia.GradientShader.MakeLinear([(-10, 0), (10, 0)], [color(cam), color(cam2)])))
            c.drawCircle(0, 86, 15, relleno("#FFFFFF", a)); c.drawCircle(0, 86, 15, trazo("#B9C2DA", 2, a))   # guantes
            c.restore()
        c.drawRRect(rrc(0, -44, 70, 92, 22), skia.Paint(AntiAlias=True, Alphaf=a, Shader=skia.GradientShader.MakeLinear([(-35, -90), (35, 0)], [color("#F2FF8A"), color(cam), color(cam2)], [0, .45, 1])))
        texto(c, "1", 0, -48, self.F["lab"], "#1C2340", alfa=.85 * a)
        c.drawRRect(rrc(0, -94, 18, 14, 6), relleno(piel, a))                    # cuello
        c.drawCircle(0, -114, 24, skia.Paint(AntiAlias=True, Alphaf=a, Shader=skia.GradientShader.MakeRadial((-8, -122), 30, [color("#FFD9BE"), color(piel), color("#C9906C")], [0, .6, 1])))
        c.drawArc(skia.Rect.MakeXYWH(-25, -140, 50, 34), 180, 180, True, relleno("#2B1A10", a))   # pelo
        c.restore()

    def balon(self, c, x, y, r):
        c.drawOval(skia.Rect.MakeXYWH(x - r * 1.1, y + r * .7, r * 2.2, r * .55), skia.Paint(AntiAlias=True, Color=color("#000000", .45),
                                                                                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - r * .35, y - r * .4), r * 1.6,
                                                                                              [color("#FFFFFF"), color("#E6EAF2"), color("#8D96AE")], [0, .5, 1])))
        def pent(cx, cy, rr, rot):
            p = skia.Path()
            for i in range(5):
                a_ = math.radians(rot + 72 * i - 90); (p.moveTo if i == 0 else p.lineTo)(cx + rr * math.cos(a_), cy + rr * math.sin(a_))
            p.close(); return p
        c.save(); pc = skia.Path(); pc.addCircle(x, y, r); c.clipPath(pc, doAntiAlias=True)
        c.drawPath(pent(x, y, r * .32, 0), relleno("#1A1F2E"))
        for i in range(5):
            a_ = math.radians(72 * i - 90); c.drawPath(pent(x + r * .82 * math.cos(a_), y + r * .82 * math.sin(a_), r * .3, 36), relleno("#1A1F2E"))
        c.restore()
        c.drawCircle(x, y, r, trazo("#FFFFFF", 1.2, .4))

    def e_penalti(self, c, e, t, S):
        s = e["spec"]; R = self._pen_rondas(e); ta = lambda w: self.ta(w, e)
        GY, PL, PR_, TY = 650, 92, 948, 300                                    # línea de gol, postes, larguero
        # estadio: focos y grada
        for fx in (130, 910):
            c.drawCircle(fx, 90, 330, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((fx, 90), 330, [color("#CFE0FF", .30), color("#6EA0FF", .08), color("#6EA0FF", 0)], [0, .4, 1])))
            for i in range(3):
                for j in range(4): c.drawCircle(fx - 45 + j * 30, 70 + i * 26, 9, relleno("#FFFFFF", .9))
        rng = np.random.default_rng(8)
        for i in range(260):                                                     # público desenfocado
            x = rng.random() * W; y = 360 + rng.random() * 250
            c.drawCircle(x, y, 5 + 5 * rng.random(), relleno(["#2A3A6E", "#3B2A6E", "#6E2A3B", "#2A5A6E"][i % 4], .35 + .2 * math.sin(t * 2 + i)))
        # césped con franjas en perspectiva
        c.drawRect(skia.Rect.MakeXYWH(0, GY - 40, W, H - GY + 40), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, GY - 40), (0, 1250)], [color("#0F4A2A"), color("#072012")])))
        y = GY - 40; k = 0
        while y < 1240:
            hgt = 22 + (y - GY + 40) * .35
            if k % 2 == 0: c.drawRect(skia.Rect.MakeXYWH(0, y, W, hgt), relleno("#FFFFFF", .035))
            y += hgt; k += 1
        c.drawRect(skia.Rect.MakeXYWH(0, 1100, W, H - 1100), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1100), (0, 1320)], [color("#04120A", 0), color("#04120A", .9)])))
        ln = trazo("#FFFFFF", 4, .55)
        c.drawLine(0, GY, W, GY, ln)
        ar = skia.Path(); ar.moveTo(240, GY); ar.lineTo(190, 745); ar.lineTo(850, 745); ar.lineTo(800, GY); c.drawPath(ar, ln)
        # red y portería
        c.save()
        red = trazo("#FFFFFF", 1.4, .22)
        bl, br, bt, bb = PL + 50, PR_ - 50, TY + 34, GY - 30
        for i in range(0, 26):
            x = bl + (br - bl) * i / 25; c.drawLine(x, bt, x, bb, red)
        for j in range(0, 10):
            yy = bt + (bb - bt) * j / 9; c.drawLine(bl, yy, br, yy, red)
        for (x0, y0), (x1, y1) in (((PL, TY), (bl, bt)), ((PR_, TY), (br, bt)), ((PL, GY), (bl, bb)), ((PR_, GY), (br, bb))): c.drawLine(x0, y0, x1, y1, trazo("#FFFFFF", 2, .35))
        for j in range(1, 6):
            yy = TY + (GY - TY) * j / 6; c.drawLine(PL, yy, bl, bt + (bb - bt) * j / 6, red); c.drawLine(PR_, yy, br, bt + (bb - bt) * j / 6, red)
        c.restore()
        # portero (según la ronda)
        act = next((r for r in reversed(R) if t >= r["t0"] - .25), None)
        x0, y0, lean, rot, brz, sh = CX, GY - 144, 0.0, 0.0, 0.0, 1.0      # quieto del todo hasta que se tira
        ap_p, ycae = 1.0, 0.0
        pw = s.get("portero_word"); dtw = s.get("demo_tiro"); dw_ = s.get("demo_word")
        if pw and not act:                                                       # el portero entra al nombrarlo (cae desde arriba)
            dp = t - ta(pw) + .05; ap_p = min(1.0, max(0.0, dp / .15)); ycae = -260 * (1 - resorte(dp, 8, 11)) if dp > 0 else 0
        if act: ap_p = min(1.0, max(0.0, (t - act["t0"] + .25) / .2)) if act["n"] > 1 else 1.0
        demo = (not act) and dtw and ta(dtw) <= t < (ta(dw_) if dw_ else 1e9)
        if dw_ and not act and t >= ta(dw_): ap_p = min(ap_p, max(0.0, (t - ta(dw_)) / .2))
        if demo:                                                                 # estirada de ejemplo
            u = (t - ta(dtw)) / .5; v = min(u, 1.0); ev = 1 - (1 - v) ** 2
            rot = 78 * ev; x0 += 270 * ev; y0 += -110 * math.sin(math.pi * v) + 92 * ev; brz = ev; sh = 1 - .5 * math.sin(math.pi * v)
        y0 += ycae
        if act:
            for ta_, sd in act["amagos"]:
                u = (t - ta_) / .5
                if 0 < u < 1: lean += sd * 16 * math.sin(math.pi * u); x0 += sd * 46 * math.sin(math.pi * u)
            u = (t - act["td"]) / (.5 / act["vel"])
            if u > 0:
                v = min(u, 1.0); ev = 1 - (1 - v) ** 2; sd = act["lado"]
                rot = sd * 78 * ev; x0 += sd * 270 * ev; y0 += -110 * math.sin(math.pi * v) + 92 * ev; brz = ev
                sh = 1 - .5 * math.sin(math.pi * v)
        if ap_p > 0:
            c.drawOval(skia.Rect.MakeXYWH(x0 - 70 * sh, GY + 4, 140 * sh, 22), skia.Paint(AntiAlias=True, Color=color("#000000", .45 * ap_p), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
            self.portero(c, x0, y0, lean, rot, brz, ap_p)
        if demo and t - ta(dtw) > .1: self.pildora(c, s.get("demo_txt", "ASÍ"), x0 - 40, GY + 70, S, min(1, (t - ta(dtw) - .1) / .15), fnt=self.F["pillb"])
        # balón: tras la estirada sale disparado a la escuadra contraria (después del momento de pausar: no avisa)
        bx, by, br, en_red, ur = CX, 800.0, 36.0, False, 0.0
        tch = s.get("chut_s", .75)
        if act and t >= act["td"] + tch:
            u = min(1.0, (t - act["td"] - tch) / .34); ue = 1 - (1 - u) ** 2; tx_, ty_ = CX - act["lado"] * 300, TY + 78
            bx = CX + (tx_ - CX) * ue; by = 800 + (ty_ - 800) * ue - 90 * math.sin(math.pi * u); br = 36 - 17 * ue; en_red = u >= 1
            ur = (t - act["td"] - tch - .34) / .5
            for k in range(1, 6):                                                # estela
                uk = max(0.0, u - k * .05); uke = 1 - (1 - uk) ** 2
                c.drawCircle(CX + (tx_ - CX) * uke, 800 + (ty_ - 800) * uke - 90 * math.sin(math.pi * uk), br * (1 - k * .12), relleno("#FFFFFF", .12 * (1 - k / 6) * (u < 1)))
        if en_red:
            if 0 < ur < 1:                                                       # la red se hincha
                for q in range(3): c.drawCircle(bx, by, 30 + 70 * ur + q * 18, trazo("#FFFFFF", 2, .35 * (1 - ur)))
            self.balon(c, bx, by, br)
        # postes y larguero encima del portero
        for p in (skia.Rect.MakeLTRB(PL - 9, TY - 9, PL + 9, GY), skia.Rect.MakeLTRB(PR_ - 9, TY - 9, PR_ + 9, GY), skia.Rect.MakeLTRB(PL - 9, TY - 9, PR_ + 9, TY + 9)):
            c.drawRect(p.makeOffset(4, 6), relleno("#000000", .3))
            c.drawRect(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(p.left(), p.top()), (p.right(), p.bottom())], [color("#FFFFFF"), color("#C9D3EA")])))
        if not en_red: self.balon(c, bx, by, br)
        # rótulos arriba
        dt0 = t - e["t0"]
        rot_ = [r for r in s.get("rotulos", []) if t >= ta(r["word"]) - .05]
        lab = None
        if act and t < act["t1"]: lab = s.get("ronda_txt", "RONDA {n} DE {N}").format(n=act["n"], N=len(R))
        elif rot_: lab = rot_[-1]["txt"]
        if lab:
            dl = (t - act["t0"] + .3) if (act and t < act["t1"]) else (t - ta(rot_[-1]["word"]) + .05)
            c.save(); sc_ = .9 + .1 * resorte(dl, 9, 12); c.translate(CX, 200); c.scale(sc_, sc_); c.translate(-CX, -200)
            self.pildora(c, lab, CX, 200, S, aparece(dl, .15), fnt=self.F["pillb"]); c.restore()
        # marcador: solo en la demo y en cada ronda; sale mientras se explica otra cosa
        tramos = []
        if s.get("demo_word") and R: tramos.append((ta(s["demo_word"]), R[0]["t0"] - .3))
        for r in R: tramos.append((r["t0"] - .3, min(r["td"] + s.get("ver_s", 1.75), r["t1"])))
        un = []
        for a0, a1 in sorted(tramos):
            if un and a0 <= un[-1][1] + .5: un[-1][1] = max(un[-1][1], a1)
            else: un.append([a0, a1])
        tramos = un
        pv = max([min(1.0, max(0.0, (t - a0) / .3)) * min(1.0, max(0.0, (a1 - t) / .25)) for a0, a1 in tramos] + [0.0])
        if pv <= 0: return
        pe = 1 - (1 - pv) ** 3
        c.save(); c.translate(0, 70 * (1 - pe)); c.saveLayer(None, skia.Paint(Alphaf=pv))
        val = 0.0; estado = "espera"
        dw = s.get("demo_word")
        if act and t >= act["t0"] - .25:
            if t >= act["td"]: val = min(t, act["t1"], act["td"] + 1.5) - act["td"]; estado = "corre"
        elif dw and t >= ta(dw):
            val = min(.62, (t - ta(dw)) * .3); estado = "demo"
        PY = 920
        r_ = rrc(CX, PY, 700, 150, 34)
        c.drawRRect(r_.makeOffset(0, 10), skia.Paint(AntiAlias=True, Color=color("#000000", .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
        c.drawRRect(r_, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, PY - 75), (0, PY + 75)], [color("#1C2340", .92), color("#070B1A", .95)])))
        c.drawRRect(r_, trazo("#FFFFFF", 2.5, .35))
        txt = f"{val:.3f}".replace(".", ",")
        texto(c, txt, CX - 20, PY, self.F["cron"], "#FFFFFF", tnum=True, sombra=(4, 10, .4))
        texto(c, "s", CX + 268, PY + 30, self.F["unit"], "#AFC3EE")
        seg = next(sg for sg in self.ESCALA_PEN if sg[0] <= val < sg[1]) if val > 0 else self.ESCALA_PEN[0]
        etq = s.get("espera_txt", "AÚN NO") if estado == "espera" else seg[4]
        colp = "#3A4462" if estado == "espera" else seg[2]
        fp = self.F["etq"]; wq = ancho(etq, fp) + 70
        rq = rrc(CX, 1042, wq, 76, 22); c.drawRRect(rq, relleno(colp, .95)); c.drawRRect(rq, trazo("#FFFFFF", 2, .25))
        texto(c, etq, CX, 1042, fp, "#0B1020" if estado != "espera" else "#FFFFFF")
        # escala
        x0e, wt = 82, 860; ws = wt / 5; ye = 1122
        for i, (a_, b_, col, nom, _) in enumerate(self.ESCALA_PEN):
            xx = x0e + i * ws; on = seg is self.ESCALA_PEN[i] and estado != "espera"
            c.drawRRect(rrc(xx + ws / 2, ye, ws - 6, 40, 8), relleno(col, .95 if on else .45))
            rango = (f"{a_:.2f}–{b_:.2f}" if b_ < 9 else f"+{a_:.2f}").replace(".", ",")
            texto(c, rango, xx + ws / 2, ye, self.F["mini"], "#0B1020", alfa=.95 if on else .7, tnum=True)
            texto(c, nom, xx + ws / 2, ye + 46, self.F["mini2"], "#FFFFFF", alfa=1 if on else .6)
        # puntero
        def pos_val(v):
            for i, (a_, b_, *_r) in enumerate(self.ESCALA_PEN):
                if v < b_: return x0e + i * ws + ws * (v - a_) / ((b_ if b_ < 9 else .80) - a_) if v < (b_ if b_ < 9 else .80) else x0e + wt - 4
            return x0e + wt - 4
        px = min(pos_val(val), x0e + wt - 6)
        tri = skia.Path(); tri.moveTo(px - 13, ye - 46); tri.lineTo(px + 13, ye - 46); tri.lineTo(px, ye - 26); tri.close()
        c.drawPath(tri, relleno("#FFFFFF"))
        c.restore(); c.restore()


def escenas(e):
    for k, s in enumerate(e.escenas):
        print(f"{s['t0']:6.2f} s  {s['spec']['tipo']:7s} {s['spec'].get('surface', 'dark'):6s} {s['trans']:6s} «{e.lineas[s['n'] - 1]['texto']}»")
    print(f"fin {e.fin_s:.2f} s · {e.nf} cuadros a {FPS} fps")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "escenas":
        escenas(Vertical(sys.argv[1])); sys.exit()
    ES.principal(Vertical, Path(__file__).resolve())
