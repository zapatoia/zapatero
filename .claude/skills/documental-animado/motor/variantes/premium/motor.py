#!/usr/bin/env python3
"""Motor del ESTILO PREMIUM (9:16, 1080×1920, 60 fps): mundo 3D continuo con «estaciones» (una por escena), la cámara vuela de una a otra
con desenfoque de movimiento; tarjetas y placas de cristal, profundidad de campo, reflejo, partículas, rótulo-karaoke arriba y posproceso.

  PY motor.py <proyecto> escenas | prueba t1 t2 … | secuencia t 12 | render [--procesos 4] | audio | qa
Voz: ../vertical/voz_eleven.py <proyecto> (misma voz y caché). Outro: ../vertical/outro.py <proyecto>.
Catálogo de escenas, cámaras, iconos y reglas: LEEME.md (en esta carpeta).
"""
import json, math, os, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MOTOR = AQUI.parents[1]
sys.path.insert(0, str(MOTOR)); sys.path.insert(0, str(AQUI))
from nucleo import tiempo as TI                                   # noqa: E402
TI.FPS = int(os.environ.get("DOC_FPS", "60"))
import numpy as np                                                # noqa: E402
import skia                                                       # noqa: E402
from nucleo import estilo as ES                                   # noqa: E402
from nucleo.texto import fuente, texto, ancho, color              # noqa: E402
from nucleo.lienzo import capa, relleno, trazo, rrc               # noqa: E402
for _n, _m in list(sys.modules.items()):
    if _n.startswith("nucleo") and hasattr(_m, "FPS"): _m.FPS = TI.FPS
from escena3d import Camara, Plano, dibujar_plano, suelo, particulas, Post, W, H   # noqa: E402
from piezas.tarjetas import tarjeta, placa_titulo, placa_contador, num_es, ORO, ORO2   # noqa: E402
from piezas.camaras import CAMARAS                               # noqa: E402
from piezas.iconos import ICONOS                                  # noqa: E402

FPS = TI.FPS
BG = "#06080D"; YS = -560                                          # fondo y altura del suelo
TR_A, TR_B = .28, .34                                              # transición: empieza antes y acaba después del corte
PASO = np.array([1750.0, 0, 1150.0])                               # separación entre estaciones
CAM_DEF = dict(titulo="entrada", tarjeta=["acercar", "orbita"], comparar="lateral", contador="acercar", apilado="grua")


def eexp(u):
    u = min(max(u, 0.0), 1.0)
    if u in (0, 1): return u
    return 2 ** (20 * u - 10) / 2 if u < .5 else (2 - 2 ** (-20 * u + 10)) / 2
def resorte(dt, k=9.0, w=13.0): return 0.0 if dt <= 0 else 1 - math.exp(-k * dt) * math.cos(w * dt)


class Premium(ES.Estilo):
    NOMBRE = "premium"
    COLA = .40
    ZONAS = dict(arriba=150, abajo=1536, derecha=950, der_y=(700, 1536))

    # ------------------------------------------------------------------ preparación
    def preparar(self):
        g = self.guion; pal = self.palabras; self.lineas = g["lineas"]
        self.idx_linea = {}
        for i, p in enumerate(pal): self.idx_linea.setdefault(p.get("linea", 1), []).append(i)
        self.escenas = []; nt = 0
        for n, ln in enumerate(self.lineas, 1):
            if ln.get("escena") and n in self.idx_linea:
                i0 = self.idx_linea[n][0]; t0 = 0.0 if not self.escenas else pal[i0]["s"] - .14
                s = ln["escena"]; tipo = s["tipo"]
                cam = s.get("cam") or CAM_DEF.get(tipo, "acercar")
                if isinstance(cam, list): cam = cam[nt % len(cam)]; nt += 1
                self.escenas.append(dict(spec=s, t0=t0, i0=i0, n=n, cam=cam, O=PASO * len(self.escenas)))
        for k, e in enumerate(self.escenas):
            e["t1"] = self.escenas[k + 1]["t0"] if k + 1 < len(self.escenas) else self.fin_s + .5
        self.F = dict(cap=fuente("Inter", 700, 62), et=fuente("Inter", 800, 30), et2=fuente("Inter", 600, 26))
        self._chunks(); self._pfx = Post()
        rng = np.random.default_rng(5); ext = PASO * max(1, len(self.escenas))
        self.polvo = np.c_[rng.uniform(-2600, ext[0] + 2600, 420), rng.uniform(-450, 2100, 420), rng.uniform(-2600, ext[2] + 2600, 420)]
        self.efectos()

    def ta(self, ref, e):
        if isinstance(ref, str) and ref.startswith("@"): return e["t0"] + float(ref[1:] or 0)
        return self.tl.t(ref, desde=e["i0"])

    def _chunks(self):
        """Rótulo-karaoke: cada línea se parte en trozos de ≤ 4 palabras que caben en 840 px."""
        P = self.palabras; self.ch = []
        for n in sorted(self.idx_linea):
            ids = self.idx_linea[n]; m = 1
            while True:                                                          # trozos equilibrados (nunca una palabra suelta al final)
                tam = math.ceil(len(ids) / m); trozos = [ids[i:i + tam] for i in range(0, len(ids), tam)]
                if all(len(x) <= 4 and ancho(" ".join(P[j]["w"] for j in x), self.F["cap"]) <= 840 for x in trozos) or m > len(ids): break
                m += 1
            self.ch += trozos
        for k, c in enumerate(self.ch):
            nxt = self.ch[k + 1][0] if k + 1 < len(self.ch) else None
            fin = P[nxt]["s"] - .04 if nxt is not None else self.fin_s + 1
            self.ch[k] = dict(ids=c, t0=P[c[0]]["s"] - .05, t1=min(fin, P[c[-1]]["e"] + 1.6))

    # ------------------------------------------------------------------ cámara
    def pose(self, k, t):
        e = self.escenas[k]; a = e["t0"] + (TR_B if k else 0); u = (t - a) / max(.3, e["t1"] - a)
        ojo, mira, roll = CAMARAS[e["cam"]](min(max(u, 0), 1), e["spec"])
        return ojo + e["O"], mira + e["O"], roll

    def camara(self, t):
        for j in range(1, len(self.escenas)):
            t0 = self.escenas[j]["t0"]
            if t0 - TR_A <= t < t0 + TR_B:
                w = eexp((t - (t0 - TR_A)) / (TR_A + TR_B)); a, b = self.pose(j - 1, t), self.pose(j, t0 + TR_B)
                ojo = a[0] + (b[0] - a[0]) * w; mira = a[1] + (b[1] - a[1]) * w
                ojo = ojo + np.array([0, 160, 0]) * math.sin(math.pi * w)                # arco: la cámara sube un poco al volar
                return Camara(ojo, mira, roll=a[2] + (b[2] - a[2]) * w + 6 * math.sin(math.pi * w), cy=1000), .12 < w < .88
        k = max(i for i, e in enumerate(self.escenas) if e["t0"] <= t or i == 0)
        o, m, r = self.pose(k, t); return Camara(o, m, roll=r, cy=1000), False

    # ------------------------------------------------------------------ contenido de cada estación
    def u_de(self, e, w, t, dur=1.1):
        return eexp((t - self.ta(w, e)) / dur) if w else 1.0

    def planos(self, k, t):
        e = self.escenas[k]; s = e["spec"]; O = e["O"]; tipo = s["tipo"]; out = []
        if tipo == "titulo":
            out.append(Plano(placa_titulo(s, t), O, 900, 620, nombre="titulo"))
        elif tipo == "tarjeta":
            out.append(Plano(tarjeta(s, t, self.u_de(e, s.get("word"), t)), O, 700, 920, nombre=s.get("titulo", "")))
        elif tipo == "comparar":
            ts = s["tarjetas"]; sep = s.get("sep", 400); n = len(ts)
            for i, d in enumerate(ts):
                x = (i - (n - 1) / 2) * 2 * sep / max(1, n - 1) if n > 1 else 0
                out.append(Plano(tarjeta(d, t, self.u_de(e, d.get("word"), t)), O + np.array([x * 1.0, 0, abs(x) * .6]), 700, 920,
                                 rot=(0, 12 * np.sign(x), 0), nombre=d.get("titulo", "")))
        elif tipo == "contador":
            img = placa_contador(s, t, self.u_de(e, s.get("word"), t, s.get("dur", 2.2)))
            out.append(Plano(img, O, img.width(), img.height(), nombre="contador"))
        elif tipo == "apilado":
            prev = [x for x in self.escenas[:k] if x["spec"]["tipo"] in ("tarjeta", "comparar")]
            ds = []
            for x in prev: ds += [x["spec"]] if x["spec"]["tipo"] == "tarjeta" else x["spec"]["tarjetas"]
            ds = ds[:s.get("max", 6)]; n = len(ds); sep = s.get("sep_capas", 260)
            up = eexp((t - e["t0"] - .2) / 1.4)
            for i, d in enumerate(ds):
                yy = (n - 1 - i) * sep * up - (n - 1) * sep / 2 * up
                out.append(Plano(tarjeta(d, t, 1.0), O + np.array([0, yy, 0]), 700, 920, rot=(90 * up, 0, -18 * up), reflejo=False, nombre=d.get("titulo", "")))
                out[-1].dato = d
        return out

    # ------------------------------------------------------------------ dibujo
    def escena(self, c, t):
        cam, rapido = self.camara(t); foco = float(np.linalg.norm(cam.mira - cam.ojo))
        c.clear(color(BG))
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial((520, 760), 1500, [color("#151B2C"), color(BG)], [0, 1])))
        suelo(c, cam, YS)
        k = max(i for i, e in enumerate(self.escenas) if e["t0"] - TR_A <= t or i == 0)
        vis = [j for j in (k - 1, k, k + 1) if 0 <= j < len(self.escenas)]
        pls = [p for j in vis for p in self.planos(j, t)]
        for pl in pls:                                                           # reflejos
            if pl.reflejo and abs(pl.rot[0]) < 5: dibujar_plano(c, cam, pl, foco, espejo_y=YS, alfa_extra=.15)
        O = self.escenas[k]["O"]; q, z = cam.pantalla(O[None, :])               # halo dorado de la estación actual
        if z[0] > 60:
            rr = 1100 * cam.f / z[0] * .6
            c.drawCircle(float(q[0, 0]), float(q[0, 1]), rr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (float(q[0, 0]), float(q[0, 1])), rr, [color(ORO, .16), color(ORO, 0)], [0, 1])))
        ek = self.escenas[k]
        if ek["spec"]["tipo"] == "contador" and ek["spec"].get("enjambre"):   # enjambre de iconos (detrás de la placa)
            self.enjambre(c, cam, ek, t, foco)
        barr = (t * .45) % 1.5; etq = []
        for pl in sorted(pls, key=lambda p: -float(cam.vista(p.c[None, :])[0, 2])):
            r = dibujar_plano(c, cam, pl, foco, barrido=barr if barr <= 1 else None)
            if r is not None and hasattr(pl, "dato"): etq.append((pl, r))
        e = self.escenas[k]
        if e["spec"]["tipo"] == "apilado":                                       # etiquetas con línea guía
            a = min(1, max(0, (t - e["t0"] - 1.3) / .4))
            for pl, (q, _) in etq:
                if a <= 0: break
                xr, yr = float(q[1, 0]), float(q[1, 1]); d = pl.dato
                wt = max(ancho(d.get("titulo", ""), self.F["et"]) * 1.2, 120); xt = min(xr + 60, 935 - wt)
                c.drawLine(xr, yr, xt - 8, yr - 50, trazo(ORO, 2, .9 * a)); c.drawCircle(xr, yr, 5, relleno(ORO2, a))
                texto(c, d.get("titulo", ""), xt, yr - 64, self.F["et"], "#FFFFFF", alinear="i", tracking=.2, alfa=a)
                texto(c, f"{d.get('prefijo', '')}{num_es(d.get('valor', 0), d.get('dec', 0))}{d.get('sufijo', '')}", xt, yr - 28, self.F["et2"], ORO, alinear="i", alfa=a)
        particulas(c, cam, self.polvo, foco, t)
        self.rotulo(c, t)
        return rapido

    def enjambre(self, c, cam, e, t, foco):
        s = e["spec"]; fn = ICONOS.get(s.get("icono", "globulo")); rng = np.random.default_rng(17); a0 = min(1, max(0, (t - self.ta(s.get("word", "@0"), e)) / .6))
        pts = []
        for i in range(34):
            r = 760 + 520 * rng.random(); w = .25 + .35 * rng.random(); ph = rng.random() * 6.28; yy = -380 + 760 * rng.random()
            P = e["O"] + np.array([r * math.cos(ph + w * t), yy + 30 * math.sin(t + i), 350 + r * abs(math.sin(ph + w * t)) * .9])
            q, z = cam.pantalla(P[None, :]); pts.append((z[0], q[0], i))
        if a0 <= 0: return
        spr = self._sprite(s.get("icono", "globulo"))                            # el icono se dibuja UNA vez y se reutiliza (rápido)
        for z, q, i in sorted(pts, key=lambda x: -x[0]):
            if z < 80: continue
            sz = 46 * cam.f / z; bl = min(10, abs(z - foco) * .004); r = sz * 1.6
            p = skia.Paint(Alphaf=a0, AntiAlias=True)
            if bl > .8: p.setImageFilter(skia.ImageFilters.Blur(bl, bl))
            c.drawImageRect(spr, skia.Rect.MakeXYWH(float(q[0]) - r, float(q[1]) - r, 2 * r, 2 * r), skia.SamplingOptions(skia.FilterMode.kLinear), p)

    def _sprite(self, nombre):
        cache = self.__dict__.setdefault("_spr", {})
        if nombre not in cache:
            sf_ = skia.Surface(160, 160); cc = sf_.getCanvas(); cc.clear(skia.ColorTRANSPARENT)
            ICONOS[nombre](cc, 80, 80, 50, 0.0); cache[nombre] = sf_.makeImageSnapshot()
        return cache[nombre]

    def rotulo(self, c, t):
        P = self.palabras; ch = next((x for x in self.ch if x["t0"] <= t < x["t1"]), None)
        if not ch: return
        sal = min(1, max(0, (ch["t1"] - t) / .12)); f = self.F["cap"]; esp = ancho(" ", f)
        ws = [P[i]["w"] for i in ch["ids"]]; tot = sum(ancho(w, f) for w in ws) + esp * (len(ws) - 1); x = 520 - tot / 2
        hablados = [i for i in ch["ids"] if P[i]["s"] - .03 <= t]; act = hablados[-1] if hablados else None
        for i, w in zip(ch["ids"], ws):
            dt = t - P[i]["s"] + .03; ww = ancho(w, f)
            if dt > 0:
                a = min(1, dt / .1) * sal; y = 300 + 18 * (1 - resorte(dt, 12, 13)); bl = max(.01, 8 * (1 - min(1, dt / .12)))
                col = "#FFFFFF" if i == act else "#7D8597"
                caja = skia.Rect.MakeLTRB(x - 40, y - 90, x + ww + 40, y + 70)          # capa acotada a la palabra (rápido)
                c.saveLayer(caja, skia.Paint(Alphaf=a, ImageFilter=skia.ImageFilters.Blur(bl, bl)))
                if i == act:
                    c.saveLayer(caja, skia.Paint(Alphaf=.35, ImageFilter=skia.ImageFilters.Blur(16, 16))); texto(c, w, x, y, f, ORO2, alinear="i"); c.restore()
                texto(c, w, x, y, f, col, alinear="i", sombra=(3, 10, .5)); c.restore()
            x += ww + esp

    def dibujar(self, L, f):
        t = f / FPS; rapido = self.escena(L.canvas, t)
        if rapido:                                                               # desenfoque de movimiento real: 4 subcuadros
            acc = L.arr[..., :3].astype(np.float32)
            for k in range(1, 4): self.escena(L.canvas, t - k / (FPS * 4)); acc += L.arr[..., :3]
            L.arr[..., :3] = (acc / 4).astype(np.uint8)
        L.arr[..., 3] = 255

    def post(self, arr, f): return self._pfx(arr, f / FPS)

    # ------------------------------------------------------------------ efectos de sonido
    def efectos(self):
        P = self.palabras; spans = [(p["s"], p["e"]) for p in P]
        dur = dict(whoosh=.34, pop=.09, tic=.03, golpe=.32, destello=.7)
        def libre(a, b): return not any(s < b - .01 and e > a + .01 for s, e in spans)
        def pon(ta, nom, vol):
            d = dur[nom]
            for tt in (ta - d - .02, ta - d - .1, ta - d * .6):
                if tt >= 0 and libre(tt, tt + d): self.sfx(TI.f_de_t(tt), nom, vol); return
            self.sfx(TI.f_de_t(max(0, ta - d * .5)), nom, vol * .6)
        for k, e in enumerate(self.escenas):
            s = e["spec"]
            if k: self.sfx(TI.f_de_t(max(0, e["t0"] - TR_A)), "whoosh", .9)
            if s["tipo"] == "titulo": self.sfx(TI.f_de_t(e["t0"] + .45), "golpe", .5)
            ws = [s.get("word")] + [d.get("word") for d in s.get("tarjetas", [])]
            for w in ws:
                if not w: continue
                tw = self.ta(w, e); pon(tw, "pop", .4)
                for j in range(6 if s["tipo"] != "contador" else 12):
                    tt = tw + .04 + j * .15
                    if libre(tt, tt + .03): self.sfx(TI.f_de_t(tt), "tic", .45)
            if s["tipo"] == "apilado": self.sfx(TI.f_de_t(e["t0"] + 1.3), "destello", .7)


def escenas(e):
    for k, s in enumerate(e.escenas):
        print(f"{s['t0']:6.2f} s  {s['spec']['tipo']:9s} cam={s['cam']:8s} «{e.lineas[s['n'] - 1]['texto']}»")
    print(f"fin {e.fin_s:.2f} s · {e.nf} cuadros a {FPS} fps")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "escenas":
        escenas(Premium(sys.argv[1])); sys.exit()
    ES.principal(Premium, Path(__file__).resolve())
    if len(sys.argv) > 2 and sys.argv[2] in ("render", "audio"):        # el grano dispara el peso a crf 16: se recomprime a crf 23 (≈ 0,5 MB/s)
        import subprocess
        from nucleo.rutas import FF
        fin = Path(sys.argv[1]).resolve() / "final" / f"{Path(sys.argv[1]).resolve().name}.mp4"
        if fin.exists() and fin.stat().st_size > 40e6:
            tmp = fin.with_suffix(".tmp.mp4")
            subprocess.run([FF, "-v", "error", "-y", "-i", str(fin), "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-movflags", "+faststart", str(tmp)], check=True)
            tmp.replace(fin); print(f"recomprimido: {fin.stat().st_size / 1e6:.1f} MB")
