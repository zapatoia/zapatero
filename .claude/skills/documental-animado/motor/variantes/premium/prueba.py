#!/usr/bin/env python3
"""Prueba muda del estilo «premium» (oscuro + dorado, 2.5D con planos en perspectiva), 1080×1920 a 60 fps.

  PY prueba.py <carpeta_prueba> <proyecto_fuente>     → <carpeta_prueba>/prueba-premium.mp4 + hoja.jpg

Planos: A) móvil con el vídeo dentro que se abre en capas de cristal; B) contador dorado de fotogramas;
C) línea de tiempo «detrás de las cámaras» (fotogramas, onda de la voz, palabras con su segundo) que se inclina.
Usa material real del proyecto fuente: thumbs/fNN.png, pantalla.png (en la carpeta de prueba), voz.wav y palabras.json.
"""
import json, math, subprocess, sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MOTOR))
import numpy as np                                                # noqa: E402
import skia                                                       # noqa: E402
import soundfile as sf                                            # noqa: E402
from nucleo.texto import fuente, texto, ancho, color              # noqa: E402
from nucleo.lienzo import Lienzo, capa, relleno, trazo, rrc       # noqa: E402
from nucleo.rutas import FF                                       # noqa: E402
from nucleo.render import ENC                                     # noqa: E402

W, H, FPS = 1080, 1920, 60
CX, CY = 520, 860
ORO, ORO2, BG = "#E8B04A", "#FFD98A", "#07090E"
TA, TB, TC = 2.7, 4.7, 8.0            # fin de cada plano


def ease(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def eexp(u):
    u = min(max(u, 0.0), 1.0)
    if u in (0, 1): return u
    return 2 ** (20 * u - 10) / 2 if u < .5 else (2 - 2 ** (-20 * u + 10)) / 2
def resorte(dt, k=9.0, w=13.0): return 0.0 if dt <= 0 else 1 - math.exp(-k * dt) * math.cos(w * dt)


def rot(rx, ry, rz):
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def proyectar(P, R, cx=CX, cy=CY, dist=2400.0, esc=1.0):
    Q = (R @ np.asarray(P, float).T).T * esc
    f = dist / (dist + Q[:, 2]); return np.c_[cx + Q[:, 0] * f, cy + Q[:, 1] * f], Q[:, 2]


def plano(c, img, w, h, z, R, alfa=1.0, esc=1.0, cx=CX, cy=CY):
    """Dibuja la imagen `img` (w×h, centrada) como un plano en z, rotado por R y en perspectiva."""
    P = [(-w / 2, -h / 2, z), (w / 2, -h / 2, z), (w / 2, h / 2, z), (-w / 2, h / 2, z)]
    q, zz = proyectar(P, R, cx, cy, esc=esc)
    m = skia.Matrix()
    m.setPolyToPoly([skia.Point(0, 0), skia.Point(img.width(), 0), skia.Point(img.width(), img.height()), skia.Point(0, img.height())],
                    [skia.Point(*map(float, p)) for p in q])
    c.save(); c.concat(m)
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), skia.Paint(Alphaf=alfa))
    c.restore(); return q


def superficie(w, h):
    s = skia.Surface(int(w), int(h)); return s, s.getCanvas()


def cargar(p): return skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(Path(p).read_bytes()))


class Prueba:
    def __init__(self, dirp, proy):
        self.dir = Path(dirp); self.proy = Path(proy)
        self.F = dict(lab=fuente("Inter", 800, 30), lab2=fuente("Inter", 700, 26), big=fuente("Inter", 800, 230), cap=fuente("Inter", 700, 66),
                      capl=fuente("Inter", 400, 66), word=fuente("Inter", 600, 40), wordb=fuente("Inter", 800, 46), ts=fuente("Inter", 600, 28),
                      tick=fuente("Inter", 500, 26), mini=fuente("Inter", 700, 22))
        self.pantalla = cargar(self.dir / "pantalla.png")
        self.thumbs = [cargar(p) for p in sorted((self.dir / "thumbs").glob("f*.png"))]
        x, sr = sf.read(str(self.proy / "voz.wav"), dtype="float32")
        if x.ndim > 1: x = x.mean(1)
        hop = sr // 100; n = len(x) // hop
        self.env = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, 1)); self.env /= self.env.max() + 1e-9
        self.pal = json.loads((self.proy / "palabras.json").read_text())
        self.movil = self._movil(); self.capas = self._capas()
        rng = np.random.default_rng(3); self.polvo = rng.random((90, 4))

    # ---------------------------------------------------------------- piezas planas (luego se proyectan)
    def _movil(self):
        w, h = 620, 1280; s, c = superficie(w, h); c.clear(skia.ColorTRANSPARENT)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(6, 6, w - 12, h - 12), 92, 92)
        c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (w, h)], [color("#3A3F4A"), color("#0E1016"), color("#2A2E38")], [0, .5, 1])))
        c.drawRRect(r, trazo("#9AA3B5", 3, .8))
        sc = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(26, 26, w - 52, h - 52), 74, 74)
        c.save(); c.clipRRect(sc, doAntiAlias=True)
        c.drawImageRect(self.pantalla, skia.Rect.MakeXYWH(26, 26, w - 52, h - 52), skia.SamplingOptions(skia.FilterMode.kLinear))
        c.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (w, h * .6)], [color("#FFFFFF", .16), color("#FFFFFF", 0)])))
        c.restore()
        c.drawRRect(rrc(w / 2, 62, 170, 46, 23), relleno("#000000"))                   # isla
        texto(c, "9:41", 110, 64, self.F["lab2"], "#FFFFFF")
        return s.makeImageSnapshot()

    def _vidrio(self, w, h, contenido=None):
        s, c = superficie(w, h); c.clear(skia.ColorTRANSPARENT)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(4, 4, w - 8, h - 8), 70, 70)
        c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (w, h)], [color("#FFFFFF", .10), color("#FFFFFF", .02), color("#FFFFFF", .07)], [0, .6, 1])))
        c.drawRRect(r, trazo("#FFFFFF", 2.5, .45))
        c.drawLine(80, 6, w - 80, 6, trazo("#FFFFFF", 3, .55))
        if contenido: contenido(c, w, h)
        return s.makeImageSnapshot()

    def _capas(self):
        w, h = 620, 1280
        def subt(c, w, h):
            texto(c, "Pausa justo cuando", w / 2, 300, self.F["lab2"], "#FFFFFF", alfa=.9)
            texto(c, "se tire", w / 2, 380, self.F["cap"], "#6EA0FF")
        def marcador(c, w, h):
            c.drawRRect(rrc(w / 2, 840, 470, 120, 30), relleno("#0B1020", .9)); c.drawRRect(rrc(w / 2, 840, 470, 120, 30), trazo("#FFFFFF", 2, .4))
            texto(c, "0,186 s", w / 2, 840, self.F["cap"], "#FFFFFF", tnum=True)
            c.drawRRect(rrc(w / 2, 950, 220, 56, 16), relleno("#2ED47A")); texto(c, "¡GOLAZO!", w / 2, 950, self.F["lab2"], "#0B1020")
        def etiquetas(c, w, h):
            for (x, y, t_) in ((150, 600, "PORTERO"), (420, 700, "BALÓN"), (330, 1040, "ESCALA")):
                c.drawLine(x, y + 20, x, y + 120, trazo("#FFFFFF", 1.5, .6)); texto(c, t_, x, y, self.F["mini"], "#FFFFFF", tracking=.2)
        return [self.movil, self._vidrio(w, h, etiquetas), self._vidrio(w, h, marcador), self._vidrio(w, h, subt)]

    # ---------------------------------------------------------------- fondo
    def fondo(self, c, t, tono=1.0):
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial((CX, 760), 1300, [color("#141A2A"), color(BG)], [0, 1])))
        for i in range(0, W, 90): c.drawLine(i, 0, i, H, trazo("#FFFFFF", 1, .025))
        for j in range(0, H, 90): c.drawLine(0, j, W, j, trazo("#FFFFFF", 1, .025))
        for x, y, r, v in self.polvo:
            c.drawCircle((x * W + t * 8 * v) % W, (y * H - t * 14 * v) % H, 1 + 1.8 * r, relleno("#FFFFFF", (.12 + .3 * v) * tono))

    def rotulo(self, c, t, t0, ctx, clave):
        dt = t - t0
        if dt < 0: return
        a = min(1, dt / .12); y = 330 + 20 * (1 - resorte(dt, 10, 12))
        wc = ancho(ctx + " ", self.F["capl"]); wk = ancho(clave, self.F["cap"]); x0 = CX - (wc + wk) / 2
        texto(c, ctx, x0, y, self.F["capl"], "#8C93A6", alinear="i", alfa=a)
        texto(c, clave, x0 + wc, y, self.F["cap"], "#FFFFFF", alinear="i", alfa=min(1, max(0, (dt - .15) / .1)))

    # ---------------------------------------------------------------- planos
    def plano_a(self, c, t):
        self.fondo(c, t)
        u1 = ease(t / 1.1); u2 = eexp((t - 1.0) / 1.2)
        rx = 6 * (1 - u1) + 52 * u2; ry = -16 * (1 - u1); rz = -32 * u2
        esc = .74 + .06 * u1 - .08 * u2; R = rot(rx, ry, rz)
        sep = 260 * u2; orden = range(len(self.capas))
        # sombra en el «suelo»
        c.drawOval(skia.Rect.MakeXYWH(CX - 330, CY + 560 - 180 * u2, 660, 120), skia.Paint(AntiAlias=True, Color=color("#000000", .55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
        with capa(c, alfa=.35 * u2, blur=60): c.drawCircle(CX, CY + 120, 360, relleno(ORO))
        for k in orden:
            img = self.capas[k]; a = 1.0 if k == 0 else min(1, u2 * 1.6)
            if a <= 0: continue
            q = plano(c, img, 620, 1280, -sep * k, R, a, esc, cy=CY + 120)
            if k > 0 and u2 > .2:
                for p in q: c.drawCircle(float(p[0]), float(p[1]), 3, relleno(ORO2, .7 * a))
        self.rotulo(c, t, .15, "con un vídeo", "que")

    def plano_b(self, c, t):
        self.fondo(c, t + TA); dt = t
        objetivo = "3.051"; u = eexp(dt / 1.3)
        val = int(round(3051 * u)); s = f"{val:,}".replace(",", ".").rjust(5)
        cw, ch, gap = 150, 230, 18; n = len(s); x0 = CX - (n * cw + (n - 1) * gap) / 2; y = 900
        ap = resorte(dt, 8, 11); c.save(); c.translate(CX, y); c.scale(.85 + .15 * ap, .85 + .15 * ap); c.translate(-CX, -y)
        marco = rrc(CX, y, n * cw + (n - 1) * gap + 70, ch + 70, 40)
        c.drawRRect(marco, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y - 150), (0, y + 150)], [color("#2A2F3C"), color("#0A0C12")])))
        c.drawRRect(marco, trazo("#E9ECF3", 5, .85))
        for i, ch_ in enumerate(s):
            x = x0 + i * (cw + gap) + cw / 2
            if ch_ == ".": texto(c, ".", x, y + 40, self.F["big"], "#FFFFFF"); continue
            if ch_ == " ": continue
            card = rrc(x, y, cw, ch, 18)
            c.drawRRect(card, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y - ch / 2), (0, y + ch / 2)], [color("#2B2F3A"), color("#14161D"), color("#05060A")], [0, .5, 1])))
            velo = (1 - u) * 26                                                 # desenfoque vertical mientras rueda
            c.save(); c.clipRRect(card, doAntiAlias=True)
            if velo > .5:
                c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(.01, velo))); texto(c, ch_, x, y, self.F["big"], "#FFFFFF"); c.restore()
            else: texto(c, ch_, x, y, self.F["big"], "#FFFFFF")
            c.drawLine(x - cw / 2, y, x + cw / 2, y, trazo("#000000", 4, .8))
            c.drawRect(skia.Rect.MakeXYWH(x - cw / 2, y - ch / 2, cw, ch / 2), relleno("#FFFFFF", .05))
            c.restore()
        c.restore()
        # icono de película + etiqueta
        a = min(1, max(0, (dt - .3) / .2))
        texto(c, "FOTOGRAMAS", CX, y + 230, self.F["lab"], ORO, tracking=.35, alfa=a)
        texto(c, "60 por segundo · 50,9 s", CX, y + 285, self.F["lab2"], "#8C93A6", alfa=a)
        if u >= 1:
            for q in range(2):
                ph = ((dt - 1.3) * 1.2 + q * .5) % 1
                c.drawRRect(rrc(CX, y, (n * cw + 200) * (1 + .15 * ph), (ch + 70) * (1 + .3 * ph), 40), trazo(ORO, 3, .6 * (1 - ph)))
        self.rotulo(c, t, .05, "el vídeo tiene", "fotogramas")

    def linea_tiempo(self, tv, tono=1.0):
        """Capa plana de la línea de tiempo con el cabezal en el segundo de voz tv."""
        s, c = superficie(W, 1500); c.clear(skia.ColorTRANSPARENT)
        PX = 640.0; cab = 540                                                     # px por segundo; x del cabezal
        X = lambda tt: cab + (tt - tv) * PX
        # fotogramas
        texto(c, "FOTOGRAMAS", 40, 60, self.F["lab"], "#FFFFFF", alinear="i", tracking=.3)
        for i, im in enumerate(self.thumbs):
            tt = .25 + i * .5; x = X(tt)
            if -200 < x < W + 200:
                act = abs(tt - tv) < .25; wv, hv = (220, 390) if act else (170, 302)
                yv = 300 if act else 290
                r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - wv / 2, yv - hv / 2, wv, hv), 22, 22)
                c.save(); c.clipRRect(r, doAntiAlias=True)
                c.drawImageRect(im, r.rect(), skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=1 if act else .55)); c.restore()
                c.drawRRect(r, trazo(ORO if act else "#FFFFFF", 4 if act else 1.5, .95 if act else .2))
        # voz
        texto(c, "VOZ", 40, 560, self.F["lab"], "#FFFFFF", alinear="i", tracking=.3)
        ym = 700
        for k in range(0, W, 7):
            tt = tv + (k - cab) / PX
            if tt < 0: continue
            i = int(tt * 100)
            if i >= len(self.env): break
            a_ = float(self.env[i]); hb = 6 + 170 * a_ ** .8
            col = ORO if tt <= tv else "#C9A55A"
            c.drawLine(k, ym - hb / 2, k, ym + hb / 2, trazo(col, 3.2, .95 if tt <= tv else .55))
        # palabras con su segundo
        texto(c, "PALABRAS", 40, 1010, self.F["lab"], "#FFFFFF", alinear="i", tracking=.3)
        ult_x = -1e9; ult_ts = -1e9
        for p in self.pal:
            x = X(p["s"])
            if not (-150 < x < W + 150): continue
            act = p["s"] <= tv < p["e"] + .08
            wq = ancho(p["w"], self.F["wordb" if act else "word"])
            if x < ult_x + 22 and not act: continue
            ult_x = x + wq
            c.drawLine(x, 860, x, 885, trazo("#FFFFFF", 2, .5))
            texto(c, p["w"], x, 920, self.F["wordb" if act else "word"], "#FFFFFF" if act else "#8C93A6", alinear="i")
            wts = ancho("0,00 s", self.F["ts"])
            if act or x > ult_ts + 24:
                ult_ts = x + wts
                texto(c, f"{p['s']:.2f} s".replace(".", ","), x, 970, self.F["ts"], ORO if act else "#8C93A6", alinear="i", tnum=True)
        # regla
        yr = 1080
        for k in range(int((tv - 2) * 10), int((tv + 2) * 10) + 1):
            x = X(k / 10); big = k % 10 == 0
            c.drawLine(x, yr, x, yr + (34 if big else 14), trazo("#FFFFFF", 2 if big else 1.2, .7 if big else .35))
            if big: texto(c, f"{k // 10} s", x + 10, yr + 40, self.F["tick"], "#FFFFFF", alinear="i", alfa=.8)
        texto(c, "60 FOTOGRAMAS POR SEGUNDO", 40, 1180, self.F["lab"], "#FFFFFF", alinear="i", tracking=.3)
        # cabezal con destello
        c.drawLine(cab, 120, cab, 1100, trazo("#FFFFFF", 3, .95))
        tri = skia.Path(); tri.moveTo(cab - 14, 112); tri.lineTo(cab + 14, 112); tri.lineTo(cab, 132); tri.close(); c.drawPath(tri, relleno("#FFFFFF"))
        for k in range(12):
            a_ = math.radians(k * 30 + tv * 40); r1 = 46 + 8 * math.sin(tv * 9 + k)
            c.drawLine(cab + 10 * math.cos(a_), 60 + 10 * math.sin(a_), cab + r1 * math.cos(a_), 60 + r1 * math.sin(a_), trazo("#FF8A5C", 4, .9))
        return s.makeImageSnapshot()

    def plano_c(self, c, t):
        self.fondo(c, t + TB)
        tv = 1.0 + t * 1.0
        img = self.linea_tiempo(tv)
        u = eexp((t - 2.2) / 1.0)
        R = rot(38 * u, 0, -14 * u); esc = 1 - .12 * u
        if u <= 0: c.drawImage(img, 0, 420)
        else:
            plano(c, img, W, 1500, 0, R, 1.0, esc, cx=W / 2, cy=1170)
            with capa(c, alfa=.6 * u):
                q, _ = proyectar([(-W / 2 + 20, -730, 0), (W / 2 - 20, -730, 0), (W / 2 - 20, 730, 0), (-W / 2 + 20, 730, 0)], R, W / 2, 1170, esc=esc)
                pth = skia.Path(); pth.addPoly([skia.Point(*map(float, p)) for p in q], True); c.drawPath(pth, trazo(ORO, 4, .9))
        self.rotulo(c, t, .05, "y el truco no es", "la")

    def cuadro(self, c, t):
        c.clear(color(BG))
        if t < TA: self.plano_a(c, t)
        elif t < TB: self.plano_b(c, t - TA)
        else: self.plano_c(c, t - TB)
        # transición: destello + desenfoque breve en los cortes
        for tc in (TA, TB):
            d = abs(t - tc)
            if d < .1: c.drawPaint(skia.Paint(Color=color("#FFFFFF", .035 * (1 - d / .1))))


def main(dirp, proy):
    P = Prueba(dirp, proy); nf = int(TC * FPS); L = Lienzo(); out = Path(dirp) / "prueba-premium.mp4"
    ff = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, str(out)], stdin=subprocess.PIPE)
    hoja = []
    for f in range(nf):
        t = f / FPS; P.cuadro(L.canvas, t); L.arr[..., 3] = 255; ff.stdin.write(L.arr.tobytes())
        if f % 30 == 15: hoja.append(L.arr[::4, ::4, :3].copy())
    ff.stdin.close(); ff.wait()
    subprocess.run([FF, "-v", "error", "-y", "-i", str(out), "-vf", "fps=2,scale=270:-1,tile=8x2", "-frames:v", "1", str(Path(dirp) / "hoja.jpg")], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
