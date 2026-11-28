"""Escenas del documental 18 («¿Cómo llega la música a tus auriculares si no hay ningún cable?»).

Reutiliza el protagonista en primer plano del 17 (`self.cara_b`, sin barba) con auriculares inalámbricos.
oreja      gancho: cable del móvil al auricular que se corta (corte_word, ¡CHAS!) y la música sigue volando por el aire (aire_word);
           cierre: la música llega saltando de canal en canal (saltos_word) y entra en la oreja (oreja_word).
bits       móvil con la canción: la onda se vuelve ceros y unos (numeros_word), la prensa la comprime (comprime_word) y sale por arriba.
ondas      la antena del móvil lanza la onda de radio; vibran_word: contador que rueda hasta `cifra` y la onda se aprieta;
           luz_word: el destello viaja a la velocidad de la luz; llega_word: llega en 0,000000001 s.
lleno      salón con router (wifi_word), móviles (moviles_word) y microondas (micro_word) que llenan la banda de 2,4 GHz.
saltos     79 canales; el paquete de música salta (salta_word), canales_word, veces_word (1.600/s), ocupado_word (canales en rojo
           que esquiva), pareja_word (móvil y auricular con el mismo baile).
auricular  corte del auricular: antena_word, chip_word, conversor_word, bobina_word, iman_word, vibra_word, timpano_word.
relevo     el móvil manda la música a un auricular (recibe_word) y este se la pasa al otro (pasa_word).
rey        el rey vikingo con el diente azul (rey_word, diente_word), Dinamarca y Noruega en el mapa (unio_word: dk / no, ids ISO),
           une_word: el rey junta un móvil y unos auriculares.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]
    FNT = {}
    def F(peso, px, fam="Inter"):
        k = (fam, peso, px)
        if k not in FNT: FNT[k] = fuente(fam, peso, px)
        return FNT[k]

    # ---------------------------------------------------------------- sonidos propios
    def s_tijera():
        d = .18; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 181), 2000, 9000) * np.exp(-t / .015) + .8 * np.sin(2 * np.pi * 2900 * t) * np.exp(-t / .02)
    def s_nota():
        d = .35; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 880 * t) + .4 * np.sin(2 * np.pi * 1760 * t) + .2 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-t / .09) * np.minimum(1, t / .004)
    def s_datos():
        d = .5; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n); rng = np.random.default_rng(182)
        for k in range(22):
            a = int(k * .022 * AU.SR); m = int(.012 * AU.SR); f = 1200 + 2400 * rng.random()
            x[a:a + m] += np.sign(np.sin(2 * np.pi * f * t[:m])) * .5
        return AU._bajos(x, 6000) * np.sin(np.pi * t / d)
    def s_prensa():
        d = .45; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.tanh(2.5 * (np.sin(2 * np.pi * (140 - 80 * t) * t) * np.exp(-t / .12) + .3 * AU._banda(AU._ruido(n, 183), 200, 2000) * np.exp(-t / .05)))
    def s_salto():
        d = .07; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * (1500 + 9000 * t) * t) * np.exp(-t / .02)
    def s_micro():
        d = .9; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        return (np.sin(2 * np.pi * 120 * t) + .5 * np.sin(2 * np.pi * 240 * t) + .2 * AU._banda(AU._ruido(n, 184), 300, 1500)) * np.sin(np.pi * u) ** .6
    def s_electrico():
        d = .5; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 100 * t) * .6 + .4 * AU._banda(AU._ruido(n, 185), 3000, 8000) * (np.sin(2 * np.pi * 50 * t) > .6)) * np.sin(np.pi * t / d)
    def s_corona():
        d = .9; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for k, f in enumerate((523, 659, 784, 1047)):
            a = int(k * .1 * AU.SR); tt = t[:n - a]; x[a:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / .25) * np.minimum(1, tt / .005)
        return x
    for nom, fn, db in (("tijera", s_tijera, -25), ("nota", s_nota, -30), ("datos", s_datos, -33), ("prensa", s_prensa, -25),
                        ("salto", s_salto, -36), ("micro", s_micro, -32), ("electrico", s_electrico, -31), ("corona", s_corona, -29)):
        AU.SFX.setdefault(nom, (fn, db))

    # ---------------------------------------------------------------- utilidades
    def _io(u): u = TI.clamp(u); return u * u * (3 - 2 * u)
    def _tw(self, e, k): return self.ta(e["spec"][k], e) if e["spec"].get(k) else 1e9
    def _lin(y0, y1, cols, a=1.0, x=0, pos=None):
        return skia.GradientShader.MakeLinear([(x, y0), (x, y1)], [color(k, a) for k in cols], pos)
    def _linx(x0, x1, cols, a=1.0, pos=None):
        return skia.GradientShader.MakeLinear([(x0, 0), (x1, 0)], [color(k, a) for k in cols], pos)
    def _rad(x, y, r, cols, pos=None, a=1.0):
        return skia.GradientShader.MakeRadial((x, y), max(r, .1), [color(k, a) for k in cols], pos)
    def _p(sh): return skia.Paint(AntiAlias=True, Shader=sh)
    def _mix(a, b, u):
        ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)], float); cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)], float)
        v = ca + (cb - ca) * TI.clamp(u); return "#" + "".join(f"{int(round(q)):02X}" for q in v)
    def _sombra(c, x, y, rx, ry, a):
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), skia.Paint(AntiAlias=True, Color=color("#000000", a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, ry * .7 + 4)))
    def _franja(c):
        c.drawRect(skia.Rect(-80, 1040, W + 80, H + 80), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1060), (0, 1300)], [color("#05060C", 0), color("#05060C", .72)])))
    def _pill(self, c, txt, x, y, S, a, fondo="#0B1430", grande=True):
        if a > 0 and txt: self.pildora(c, txt, x, y, S, a, fnt=self.F["pillb"] if grande else self.F["pill"], fondo=fondo)
    def _glow(c, x, y, r, col, a):
        if a <= 0: return
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(x, y, r, _p(_rad(x, y, r, [col, "#000000"], None, a)))
    def _bokeh(c, t, a=1.0, seed=3, cols=("#3A6AE0", "#7A4AE0", "#2AB0E0"), n=14, ymax=1150):
        rng = np.random.default_rng(seed)
        for k in range(n):
            x = (rng.random() * W + t * (5 + 8 * rng.random())) % (W + 200) - 100; y = 80 + rng.random() * ymax; r = 40 + 90 * rng.random()
            _glow(c, x, y, r, cols[k % len(cols)], .16 * a * (.6 + .4 * math.sin(t * .8 + k)))
    def _polvo(c, t, x0, x1, y0, y1, a, seed=5, n=40, col="#FFF6D0"):
        rng = np.random.default_rng(seed)
        for k in range(n):
            x = x0 + (x1 - x0) * ((rng.random() + .02 * t * (rng.random() - .5)) % 1); y = y0 + (y1 - y0) * ((rng.random() - .015 * t * (.5 + rng.random())) % 1)
            c.drawCircle(x, y, 1.2 + 2.4 * rng.random(), relleno(col, a * (.3 + .5 * rng.random()) * (.6 + .4 * math.sin(t * 2 + k))))
    def _nota(c, x, y, s, a=1.0, col="#FFFFFF", doble=False, rot=0.0):
        """Nota musical (corchea o semicorchea doble)."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
        c.drawOval(skia.Rect(-16, -10, 12, 12), relleno(col, a))
        c.drawLine(10, 0, 10, -54, trazo(col, 5, a))
        if doble:
            c.drawOval(skia.Rect(22, -18, 50, 4), relleno(col, a)); c.drawLine(48, -8, 48, -62, trazo(col, 5, a))
            c.drawLine(10, -54, 48, -62, trazo(col, 9, a))
        else:
            fl = skia.Path(); fl.moveTo(10, -54); fl.cubicTo(30, -44, 34, -28, 24, -16); fl.cubicTo(28, -30, 22, -38, 10, -40); c.drawPath(fl, relleno(col, a))
        c.restore()
    def _auri(c, x, y, s, rot=0.0, a=1.0, glow=0.0, lado=1):
        """Auricular inalámbrico blanco: cabeza redonda en (x, y), palito hacia abajo."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s * lado, s)
        if glow > 0: _glow(c, 0, 0, 120, "#7FD3FF", .6 * glow * a)
        _sombra(c, 6, 60, 40, 70, .25 * a)
        c.drawRRect(rrc(14, 70, 34, 130, 17), _p(_linx(-3, 31, ["#FFFFFF", "#E2E7F0", "#AEB8CA"], a)))
        c.drawCircle(14, 140, 6, relleno("#AEB8CA", a))
        c.drawCircle(0, 0, 50, _p(_rad(-16, -18, 70, ["#FFFFFF", "#EEF1F6", "#B9C2D2"], [0, .6, 1], a)))
        c.drawOval(skia.Rect(-46, -20, -14, 22), _p(_rad(-30, 0, 24, ["#3A4258", "#1A1F33"], None, a)))     # rejilla
        for k in range(4): c.drawCircle(-30 + 6 * (k % 2), -8 + 6 * k, 2.4, relleno("#5A6478", a))
        c.drawOval(skia.Rect(-22, -40, 6, -26), relleno("#FFFFFF", .8 * a))
        c.restore()
    def _movil(c, x, y, w, h, rot=0.0, a=1.0):
        """Carcasa de móvil; devuelve el rect de la pantalla en coordenadas locales (dibuja tú dentro con save/translate)."""
        c.save(); c.translate(x, y); c.rotate(rot)
        _sombra(c, 10, h / 2 + 10, w * .45, 24, .35 * a)
        c.drawRRect(rrc(0, 0, w, h, w * .14), _p(_linx(-w / 2, w / 2, ["#3A3F52", "#1A1D2A", "#2A2F40"], a)))
        c.drawRRect(rrc(0, 0, w - 18, h - 18, w * .12), relleno("#05060C", a))
        c.drawRRect(rrc(0, -h / 2 + 30, w * .28, 18, 9), relleno("#000000", a))
        c.restore()
        return skia.Rect(x - w / 2 + 14, y - h / 2 + 14, x + w / 2 - 14, y + h / 2 - 14)
    def _pantalla_musica(c, R, t, a=1.0, onda=1.0):
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(R, 30, 30), doAntiAlias=True)
        c.drawRect(R, _p(_lin(R.top(), R.bottom(), ["#2A1A5A", "#0E1430"], a)))
        cx = R.centerX(); w = R.width()
        cov = skia.Rect(cx - w * .36, R.top() + w * .16, cx + w * .36, R.top() + w * .16 + w * .72)
        c.drawRRect(skia.RRect.MakeRectXY(cov, 22, 22), _p(skia.GradientShader.MakeLinear([(cov.left(), cov.top()), (cov.right(), cov.bottom())], [color("#FF5A8A", a), color("#7A4AE0", a), color("#2AB0E0", a)])))
        c.drawCircle(cov.centerX(), cov.centerY(), w * .2, relleno("#FFFFFF", .18 * a)); c.drawCircle(cov.centerX(), cov.centerY(), w * .06, relleno("#FFFFFF", .5 * a))
        y0 = cov.bottom() + 50
        c.drawRRect(rrc(cx, y0, w * .6, 22, 11), relleno("#FFFFFF", .85 * a)); c.drawRRect(rrc(cx, y0 + 36, w * .4, 16, 8), relleno("#FFFFFF", .4 * a))
        if onda > 0:
            yw = y0 + 110
            for k in range(26):
                xx = R.left() + 30 + k * (w - 60) / 25; hh = (10 + 40 * abs(math.sin(k * .7 + t * 6) * math.sin(k * .23 + t * 2.3))) * onda
                c.drawLine(xx, yw - hh * w / 400, xx, yw + hh * w / 400, trazo("#7FD3FF", max(2.0, w * .016), .9 * a))
        yb = R.bottom() - 70
        c.drawLine(R.left() + 40, yb - 50, R.right() - 40, yb - 50, trazo("#FFFFFF", 4, .25 * a))
        pr = R.left() + 40 + (R.width() - 80) * ((t * .03) % 1); c.drawLine(R.left() + 40, yb - 50, pr, yb - 50, trazo("#FFFFFF", 4, .9 * a)); c.drawCircle(pr, yb - 50, 8, relleno("#FFFFFF", a))
        c.drawCircle(cx, yb + 10, 34, relleno("#FFFFFF", a))
        c.drawRect(skia.Rect(cx - 11, yb - 4, cx - 4, yb + 24), relleno("#0E1430", a)); c.drawRect(skia.Rect(cx + 4, yb - 4, cx + 11, yb + 24), relleno("#0E1430", a))
        c.restore()

    # ---------------------------------------------------------------- oreja (gancho y cierre)
    def e_oreja(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "gancho")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0E1640", "#0A0F2A", "#050816"])))
        _bokeh(c, t)
        fx, fy, fs = CX - 110, 600, 1.0
        ex, ey = fx + 196 * fs, fy - 5 * fs                                         # oreja derecha (de la imagen)
        mx, my = 820, 960                                                           # móvil
        if modo == "gancho":
            tc = _tw(self, e, "corte_word"); ta = _tw(self, e, "aire_word")
            expr = "o" if tc < t < ta + .4 else ("feliz" if t > ta + .4 else "neutral")
        else:
            ts = _tw(self, e, "saltos_word"); to = _tw(self, e, "oreja_word")
            expr = "feliz" if t > to - .2 else "neutral"
        self.cara_b(c, fx, fy, fs, t, cob=0.0, largo=0, expr=expr, mira=(.5, .2))
        _auri(c, ex + 6, ey + 4, .78, -10, 1.0, lado=1)
        _auri(c, fx - 196 * fs - 6, ey + 4, .78, 10, 1.0, lado=-1)
        R = _movil(c, mx, my, 250, 480, -8)
        c.save(); c.translate(mx, my); c.rotate(-8); c.translate(-mx, -my); _pantalla_musica(c, R, t, onda=.6); c.restore()
        # trayectoria del móvil a la oreja
        p0, p1 = (mx - 30, my - 240), (ex + 26, ey + 100)
        def bez(u):
            cx_, cy_ = (p0[0] + p1[0]) / 2 + 220, (p0[1] + p1[1]) / 2 - 60
            return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * cx_ + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * cy_ + u * u * p1[1])
        if modo == "gancho":
            ucorte = TI.clamp((t - tc) / .9)
            if t < tc:
                cab = skia.Path(); cab.moveTo(*bez(0))
                for k in range(1, 31): cab.lineTo(*bez(k / 30))
                c.drawPath(cab, trazo("#FFFFFF", 9, .95)); c.drawPath(cab, trazo("#C9D0DE", 3, .8))
                # tijeras que se acercan
                ux = _io((t - tc + .6) / .55); qx, qy = bez(.5); sx_ = qx + 400 * (1 - ux)
                if ux > 0: _tijeras(c, sx_, qy, 1.0, 22 * (1 - TI.clamp((t - tc + .12) / .1)), ux)
            else:
                d = t - tc
                for half, (u0, u1) in enumerate(((0, .48), (.52, 1))):              # las dos mitades caen
                    cab = skia.Path(); first = True
                    for k in range(16):
                        u = u0 + (u1 - u0) * k / 15; x, y = bez(u)
                        drop = 900 * d * d * (1 if half == 0 else .8) + (0 if half == 0 else 30 * d)
                        w_ = abs(u - .5) * 2; x += (60 if half == 0 else -40) * d * (1 - w_); y += drop * (1 - w_ * .9)
                        (cab.moveTo if first else cab.lineTo)(x, y); first = False
                    c.drawPath(cab, trazo("#FFFFFF", 9, .95 * TI.clamp(1.3 - d)))
                qx, qy = bez(.5)
                if d < .5: _tijeras(c, qx, qy, 1.0, 0, 1 - d * 2)
                if d < .9: self.comic_t(c, "¡CHAS!", qx - 120, qy - 140, 80, -8, .7 + .3 * resorte(d, 10, 14), 1 - TI.clamp((d - .65) / .25), "#FFE15A")
            # la música vuela por el aire
            if t > ta - .3:
                af = aparece(t - ta + .3, .3)
                for k in range(4):                                                   # arcos de onda
                    ph = ((t - ta) * .9 + k / 4) % 1; u = ph; x, y = bez(u)
                    c.drawArc(skia.Rect(x - 40, y - 40, x + 40, y + 40), -150, 120, False, trazo("#7FD3FF", 5, af * math.sin(math.pi * ph)))
                for k in range(7):
                    ph = ((t - ta) * .55 + k / 7) % 1; x, y = bez(ph)
                    _nota(c, x + 30 * math.sin(ph * 8 + k), y + 20 * math.cos(ph * 6 + k), 1.4 + .3 * math.sin(k), af * math.sin(math.pi * ph), ("#FFFFFF", "#FFE15A", "#7FD3FF")[k % 3], k % 2 == 1, 10 * math.sin(t * 3 + k))
                _glow(c, ex + 6, ey, 90, "#7FD3FF", .3 * af * (.6 + .4 * math.sin(t * 6)))
        else:
            # cierre: la música llega saltando de canal en canal (zigzag) y entra en la oreja
            au = aparece(dt0, .3)
            for k in range(9):
                ph = ((t - e["t0"]) * .7 + k / 9) % 1; x, y = bez(ph)
                salto = 40 * math.sin(math.floor(ph * 14 + k) * 2.3)
                _nota(c, x + salto, y + .6 * salto, 1.4, au * math.sin(math.pi * ph), ("#FFFFFF", "#FFE15A", "#7FD3FF")[k % 3], k % 2 == 1)
            if t > ts:
                a = aparece(t - ts, .15)
                c.drawRRect(rrc(mx - 20, 230, 400, 100, 50), relleno("#0B1430", .8 * a)); c.drawRRect(rrc(mx - 20, 230, 400, 100, 50), trazo("#7FD3FF", 3, .8 * a))
                v = int(1600 * TI.cubic_out(TI.clamp((t - ts) / .9)))
                with capa(c, alfa=a, blur=(1.5 if t - ts < .9 else 0)): texto(c, f"{v:,}".replace(",", ".") + " /s", mx - 20, 230, F(800, 56), "#FFFFFF", tnum=True)
            if t > to - .2:
                uo = aparece(t - to + .2, .2)
                for q in range(3):
                    ph = ((t - to) * 1.2 + q / 3) % 1; c.drawCircle(ex + 6, ey, 60 + 120 * ph, trazo("#FFE15A", 4, .6 * (1 - ph) * uo))
                _glow(c, ex + 6, ey, 140, "#FFE15A", .45 * uo)
        _franja(c)

    def _tijeras(c, x, y, s, ab, a):
        c.save(); c.translate(x, y); c.scale(s, s)
        for sg in (-1, 1):
            c.save(); c.rotate(sg * ab)
            c.drawPath(skia.Path.Polygon([(0, 0), (-120, sg * 10), (-130, sg * 4), (0, -sg * 8)], True), _p(_lin(-10, 10, ["#FFFFFF", "#AEB8CA"], a)))
            c.drawCircle(46, sg * 26, 24, trazo("#E5322D", 12, a))
            c.restore()
        c.drawCircle(0, 0, 7, relleno("#5A6478", a))
        c.restore()

    # ---------------------------------------------------------------- la canción en ceros y unos
    def e_bits(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tn = _tw(self, e, "numeros_word"); tc = _tw(self, e, "comprime_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#1A1440", "#0C0A22", "#05030E"])))
        _bokeh(c, t, .8, seed=9, cols=("#7A4AE0", "#FF5A8A", "#3A6AE0"))
        mx, my, mw, mh = CX, 640, 470, 900
        R = _movil(c, mx, my, mw, mh, 0)
        ub = _io((t - tn + .1) / .6)
        if ub < 1: _pantalla_musica(c, R, t, 1 - ub, onda=1.0)
        if ub > 0:
            c.save(); c.clipRRect(skia.RRect.MakeRectXY(R, 30, 30), doAntiAlias=True)
            c.drawRect(R, relleno("#05060C", ub))
            uc = _io((t - tc) / .6); top = R.top() + 40 + 330 * uc; bot = R.bottom() - 40 - 330 * uc
            fpx = int(30 - 8 * uc); rng = np.random.default_rng(int(t * 12))
            cols = int((R.width() - 40) // (fpx * .8)); filas = int((bot - top) // (fpx * 1.05))
            for i in range(cols):
                off = (t * (60 + 25 * (i % 5)) + i * 37) % (fpx * 1.05)
                for j in range(-1, filas + 1):
                    yy = top + j * fpx * 1.05 + off
                    if yy < top - 2 or yy > bot + 2: continue
                    bit = "1" if (math.sin(i * 12.9898 + (j - int(t * 3)) * 78.233) * 43758.5) % 1 > .5 else "0"
                    col = _mix("#7FD3FF", "#FFE15A", uc) if bit == "1" else _mix("#3A6AE0", "#E0902A", uc)
                    texto(c, bit, R.left() + 30 + i * fpx * .8, yy, F(800, fpx, "JetBrainsMono"), col, alfa=ub * (.55 + .45 * (bit == "1")))
            c.restore()
            if uc > 0:
                # prensa: dos placas que aprietan
                for sg, yy in ((-1, top - 30), (1, bot + 30)):
                    for k in range(6):                                                   # flechas de fuerza
                        c.drawLine(mx - 200 + k * 80, yy + sg * 120, mx - 200 + k * 80, yy + sg * 50, trazo("#FFE15A", 6, .7 * uc))
                    c.drawRRect(rrc(mx, yy, mw + 60, 44, 10), _p(_lin(yy - 22, yy + 22, ["#C9D0DE", "#6A7488"])))
                    ya_, yb_ = sorted((yy + sg * 22, yy + sg * 400)); c.drawRect(skia.Rect(mx - 22, ya_, mx + 22, yb_), _p(_linx(mx - 22, mx + 22, ["#AEB8CA", "#5A6478"])))
                if t > tc + .5:
                    _pill(self, c, s.get("comprime_txt", "COMPRIMIDA"), mx, my + 4 - 0, S, aparece(t - tc - .5, .15) * (1 - TI.clamp((t - tc - 2.2) / .2)), fondo="#8A5A0A")
                # sale volando hacia arriba
                if t > tc + 2.2:
                    for k in range(6):
                        ph = ((t - tc - 2.2) * .8 + k / 6) % 1; px = mx + 120 * math.sin(k * 2.1); py = top - 60 - 600 * ph
                        c.drawRRect(rrc(px, py, 70, 36, 8), relleno("#FFE15A", math.sin(math.pi * ph)))
                        c.drawRRect(rrc(px, py, 70, 36, 8), trazo("#FFFFFF", 2, math.sin(math.pi * ph)))
        if dt0 > .3 and t < tn: _pill(self, c, s.get("cancion_txt", "TU CANCIÓN"), mx, R.top() - 40, S, aparece(dt0 - .3, .15), fondo="#7A2A6A")
        _franja(c)

    # ---------------------------------------------------------------- ondas de radio
    def e_ondas(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tv = _tw(self, e, "vibran_word"); tl = _tw(self, e, "luz_word"); tg = _tw(self, e, "llega_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2E62E6", "#1A3FB0", "#0A1E60"])))
        for k in range(30): c.drawLine(-80, 300 + k * 30, W + 80, 300 + k * 30, trazo("#FFFFFF", 1, .04))
        mx, my = 200, 900
        R = _movil(c, mx, my, 230, 430, -6); c.save(); c.translate(mx, my); c.rotate(-6); c.translate(-mx, -my); _pantalla_musica(c, R, t, onda=.5); c.restore()
        _auri(c, 860, 540, 1.5, 0, 1.0, glow=(aparece(t - tg, .1) if t > tg else 0))
        # antena que emite
        ax, ay = mx + 50, my - 220
        c.drawLine(ax, ay, ax, ay - 50, trazo("#FFFFFF", 6)); c.drawCircle(ax, ay - 54, 9, relleno("#FFE15A"))
        for q in range(3):
            ph = ((t * 1.3) + q / 3) % 1; r = 20 + 80 * ph
            c.drawArc(skia.Rect(ax - r, ay - 54 - r, ax + r, ay - 54 + r), -60, 120, False, trazo("#FFFFFF", 4, .7 * (1 - ph)))
        # la onda: del móvil al auricular; se aprieta cuando rueda el contador
        uv = TI.cubic_out(TI.clamp((t - tv) / 1.6)) if t > tv else 0
        ciclos = 3 + 21 * uv; x0, y0, x1, y1 = ax + 30, ay - 54, 790, 540
        aw = aparece(t - (_tw(self, e, "ondas_word") - .1), .3) if t > _tw(self, e, "ondas_word") - .1 else aparece(dt0 - .2, .3) * .0
        if aw > 0:
            pth = skia.Path(); n = 260; reveal = TI.clamp((t - _tw(self, e, "ondas_word") + .1) / .7)
            for k in range(int(n * reveal) + 1):
                u = k / n; x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u
                nx, ny = -(y1 - y0), (x1 - x0); L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
                amp = 40 * math.sin(math.pi * u) ** .5
                off = amp * math.sin(2 * math.pi * (ciclos * u - t * 2))
                (pth.moveTo if k == 0 else pth.lineTo)(x + nx * off, y + ny * off)
            c.drawPath(pth, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=14, Color=color("#7FD3FF", .25 * aw), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
            c.drawPath(pth, trazo("#FFFFFF", 5, aw))
        # contador de vibraciones
        if t > tv - .1:
            a = aparece(t - tv + .1, .15); v = int(s.get("cifra", 2400000000) * uv)
            c.drawRRect(rrc(CX, 260, 900, 220, 40), _p(_lin(150, 370, ["#FFFFFF", "#DCE6F6"], a)))
            with capa(c, alfa=a, blur=(2 if 0 < uv < 1 else 0)):
                txt = f"{v:,}".replace(",", "."); f = F(800, 104); wv = ancho("2.400.000.000", f); sc = min(1.0, 820 / wv)
                c.save(); c.translate(CX, 236); c.scale(sc, sc); texto(c, txt, 0, 0, f, "#1A3FB0", tnum=True); c.restore()
            texto(c, s.get("cifra_txt", "VECES POR SEGUNDO"), CX, 330, F(800, 32), "#5A6A8A", alfa=a, tracking=.18)
        # destello a la velocidad de la luz
        if t > tl:
            u = TI.clamp((t - tl) / .35); x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u
            if u < 1:
                for j in range(12):
                    uu = max(0, u - j * .03); xx = x0 + (x1 - x0) * uu; yy = y0 + (y1 - y0) * uu
                    _glow(c, xx, yy, 60 - 4 * j, "#FFFFFF", .7 * (1 - j / 12))
            _pill(self, c, s.get("luz_txt", "300.000 KM/S"), 470, 830, S, aparece(t - tl - .1, .15), fondo="#0B1430")
        if t > tg:
            a = aparece(t - tg, .15)
            _pill(self, c, s.get("tiempo_txt", "0,000000001 S"), 760, 760, S, a, fondo="#8A5A0A")
            if t - tg < 1: self.comic_t(c, "¡YA!", 900, 400, 74, 8, .7 + .3 * resorte(t - tg, 10, 14), 1 - TI.clamp((t - tg - .7) / .3), "#FFE15A")
        _franja(c)

    # ---------------------------------------------------------------- el aire está lleno
    def _router(c, x, y, a=1.0):
        c.drawRRect(rrc(x, y, 220, 70, 20), _p(_lin(y - 35, y + 35, ["#F4F6FA", "#AEB8CA"], a)))
        for sx in (-70, 70): c.drawLine(x + sx, y - 30, x + sx * 1.15, y - 150, trazo("#2A2F44", 10, a))
        for k in range(4): c.drawCircle(x - 60 + k * 36, y + 6, 6, relleno("#2ED47A", a * (.5 + .5 * math.sin(k * 2 + y))))
    def _microondas(c, x, y, t, on, a=1.0):
        c.drawRRect(rrc(x, y, 330, 210, 18), _p(_lin(y - 105, y + 105, ["#F4F6FA", "#C9D0DE"], a)))
        c.drawRRect(rrc(x - 40, y, 220, 160, 12), relleno(_mix("#1A1F33", "#FFB45C", on * .8), a))
        if on > 0:
            c.save(); c.clipRRect(rrc(x - 40, y, 220, 160, 12), doAntiAlias=True)
            pa = t * 2; c.drawOval(skia.Rect(x - 40 - 70, y + 30, x - 40 + 70, y + 60), relleno("#FFFFFF", .4 * on))
            c.drawCircle(x - 40 + 30 * math.cos(pa), y + 30 + 6 * math.sin(pa), 26, relleno("#E5322D", on)); c.restore()
        c.drawRRect(rrc(x + 125, y, 60, 170, 10), relleno("#2A2F44", a))
        texto(c, "1:30" if on > 0 else "", x + 125, y - 50, F(800, 24), "#7CFF8A", alfa=a, tnum=True)
        for k in range(3): c.drawCircle(x + 125, y + k * 40 - 5, 10, relleno("#AEB8CA", a))
    def e_lleno(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tw_, tm_, to_ = _tw(self, e, "wifi_word"), _tw(self, e, "moviles_word"), _tw(self, e, "micro_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1000, ["#5A3A2A", "#3A2418"])))
        c.drawRect(skia.Rect(-80, 1000, W + 80, H + 80), _p(_lin(1000, H, ["#2A1A10", "#120A06"])))
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(780, 250, 500, _p(_rad(780, 250, 500, ["#FFD9A0", "#000000"], None, .18)))
        c.drawRect(skia.Rect(-80, 960, W + 80, 1000), _p(_lin(960, 1000, ["#8A5A32", "#5A3A20"])))            # encimera / mueble
        # banda de 2,4 GHz arriba: se va llenando
        bx0, bx1, by = 80, 940, 300
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx0, by - 70, bx1, by + 70), 30, 30), relleno("#0B0A14", .65))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx0, by - 70, bx1, by + 70), 30, 30), trazo("#FFB45C", 3, .7))
        texto(c, s.get("banda_txt", "2,4 GHz"), bx0 + 90, by - 100, F(800, 34), "#FFD9A0")
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(bx0, by - 70, bx1, by + 70), 30, 30), doAntiAlias=True)
        fuentes = [(tw_, "#5AC8FF", 21), (tm_, "#7CFF8A", 22), (tm_ + .2, "#7CFF8A", 23), (to_, "#FF8A3D", 24)]
        for tt, col, seed in fuentes:
            if t < tt: continue
            ua = aparece(t - tt, .4); rng = np.random.default_rng(seed)
            for k in range(10 if seed != 24 else 18):
                ph = (t * (.12 + .1 * rng.random()) + rng.random()) % 1; x = bx0 + (bx1 - bx0) * ph; y = by + 40 * (rng.random() - .5)
                _glow(c, x, y, 50 + 30 * rng.random() + (30 if seed == 24 else 0), col, .55 * ua)
        c.restore()
        # router, móviles, microondas
        rx, ry = 205, 900
        c.save(); c.translate(rx, ry); c.scale(1.5, 1.5); c.translate(-rx, -ry); _router(c, rx, ry, aparece(dt0 - .1, .2)); c.restore()
        if t > tw_:
            for q in range(3):
                ph = ((t - tw_) * 1.1 + q / 3) % 1; r = 40 + 200 * ph
                c.drawArc(skia.Rect(rx - r, ry - 60 - r, rx + r, ry - 60 + r), -140, 100, False, trazo("#5AC8FF", 6, .8 * (1 - ph)))
            _pill(self, c, s.get("wifi_txt", "WIFI"), rx, ry + 90, S, aparece(t - tw_, .15), fondo="#1C5A8A")
        for k, (px, py, rot) in enumerate(((470, 850, -12), (620, 870, 14))):
            if t < tm_ + .15 * k: continue
            u = resorte(t - tm_ - .15 * k, 9, 12); R = _movil(c, px, py - 30 * (1 - u), 150, 290, rot, aparece(t - tm_ - .15 * k, .1))
            c.save(); c.translate(px, py - 30 * (1 - u)); c.rotate(rot); c.drawRRect(rrc(0, 0, 116, 256, 16), _p(_lin(-128, 128, ["#7CFF8A", "#2E9A4A"], .8)))
            c.drawCircle(0, -40, 30, relleno("#FFFFFF", .8)); c.drawRRect(rrc(0, 30, 80, 14, 7), relleno("#FFFFFF", .6)); c.restore()
            for q in range(2):
                ph = ((t - tm_) * 1.3 + q / 2 + k * .3) % 1; r = 30 + 120 * ph
                c.drawArc(skia.Rect(px - r, py - 130 - r, px + r, py - 130 + r), -150, 120, False, trazo("#7CFF8A", 5, .7 * (1 - ph)))
        if t > tm_: _pill(self, c, s.get("moviles_txt", "OTROS MÓVILES"), 540, 960 + 40, S, aparece(t - tm_ - .2, .15), fondo="#1E6A3A")
        ox, oy = 740, 560
        on = _io((t - to_ + .1) / .3)
        c.save(); c.translate(ox, oy); c.scale(1.25, 1.25); c.translate(-ox, -oy); _microondas(c, ox, oy, t, on); c.restore()
        if on > 0:
            for q in range(3):
                ph = ((t - to_) * 1.0 + q / 3) % 1; r = 80 + 220 * ph
                c.drawArc(skia.Rect(ox - r, oy - r, ox + r, oy + r), -130, 80, False, trazo("#FF8A3D", 7, .8 * (1 - ph)))
            _pill(self, c, s.get("micro_txt", "MICROONDAS"), ox, oy + 175, S, aparece(t - to_, .15), fondo="#8A3A0A")
            if t - to_ < 1.2: self.comic_t(c, "¡MMMM!", 700, 440, 64, 8, .7 + .3 * resorte(t - to_, 10, 14), 1 - TI.clamp((t - to_ - .9) / .3), "#FFE15A")
        # tu nota, atascada en la banda
        if t > to_ + .8:
            a = aparece(t - to_ - .8, .15); jx = 6 * math.sin(t * 30)
            c.drawCircle(CX + jx + 16, by - 6, 52, relleno("#0B0A14", .75 * a)); c.drawCircle(CX + jx + 16, by - 6, 52, trazo("#FFFFFF", 3, a))
            _nota(c, CX + jx, by + 20, 1.2, a, "#FFFFFF", True)
            _pill(self, c, "¡ATASCO!", CX + 170, by - 105, S, a, fondo="#8A1A0A")
        _franja(c)

    # ---------------------------------------------------------------- 79 canales y saltos
    NCH = 79
    def _canal(k, seed=7):
        return int((math.sin(k * 12.9898 + seed * 78.233) * 43758.5453) % 1 * NCH)
    def e_saltos(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ts, tc, tv, to, tp = (_tw(self, e, k) for k in ("salta_word", "canales_word", "veces_word", "ocupado_word", "pareja_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0B1530", "#071026", "#050A18"])))
        _bokeh(c, t, .6, seed=13)
        X0, X1, Y0, Y1 = 70, 960, 360, 860
        dx = (X1 - X0) / NCH
        ua = aparece(dt0 - .05, .3)
        busy = set()
        if t > to: busy = {k for k in range(NCH) if 20 <= k <= 31 or 52 <= k <= 60}
        sweep = TI.clamp((t - tc) / .8) if t > tc else 0
        for k in range(NCH):
            x = X0 + (k + .5) * dx
            lit = 1.0 if sweep * NCH > k else 0
            col = "#E5322D" if k in busy else _mix("#2D5BB8", "#6EA0FF", lit)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - dx * .38, Y0, x + dx * .38, Y1), 3, 3), relleno(col, (.35 + .25 * lit + (.35 if k in busy else 0)) * ua))
        if busy:
            ab = aparece(t - to, .2)
            for k0, k1 in ((20, 31), (52, 60)):
                xa = X0 + k0 * dx; xb = X0 + (k1 + 1) * dx
                for q in range(3):
                    ph = ((t * .8) + q / 3) % 1; _glow(c, xa + (xb - xa) * ph, Y0 + (Y1 - Y0) * (.3 + .4 * math.sin(q + t)), 60, "#FF5A3A", .3 * ab)
            texto(c, "WIFI", X0 + 25.5 * dx, Y0 - 30, F(800, 26), "#FF8A7A", alfa=ab)
            texto(c, "MICROONDAS", X0 + 56 * dx, Y0 - 30, F(800, 26), "#FF8A7A", alfa=ab)
        # el paquete de música salta (ritmo visible: 12 saltos/s; el texto dice el real)
        if t > ts - .2:
            rate = 12.0; kk = int((t - ts + .2) * rate); frac = (t - ts + .2) * rate - kk
            def ch(i):
                j = 0; v = _canal(i)
                while v in busy and j < 10: j += 1; v = _canal(i + 1000 * j)
                return v
            for j in range(8, -1, -1):                                               # estela
                i = kk - j
                if i < 0: continue
                xx = X0 + (ch(i) + .5) * dx; yy = Y0 + (Y1 - Y0) * (.5 + .35 * math.sin(i * 1.7))
                if j == 0:
                    _glow(c, xx, yy, 90, "#FFE15A", .7); _nota(c, xx, yy + 24, 1.6, 1.0, "#FFFFFF", True)
                else:
                    c.drawCircle(xx, yy, 16 - j, relleno("#FFE15A", .7 * (1 - j / 9)))
                    if j == 1:
                        xp = X0 + (ch(i - 0) + .5) * dx
                        c.drawLine(xp, yy, xx, yy, trazo("#FFE15A", 2, .3))
        if t > tc: _pill(self, c, s.get("canales_txt", "79 CANALES"), CX, Y0 - 90, S, aparece(t - tc, .15) * (1 - TI.clamp((t - tv + .25) / .2)), fondo="#1C3A6A")
        if t > tv:
            a = aparece(t - tv, .15)
            c.drawRRect(rrc(CX, 230, 760, 110, 55), relleno("#0B1430", .85 * a)); c.drawRRect(rrc(CX, 230, 760, 110, 55), trazo("#FFE15A", 3, a))
            texto(c, s.get("veces_txt", "1.600 SALTOS POR SEGUNDO"), CX, 230, F(800, 44), "#FFE15A", alfa=a)
        # emparejados: mismo baile en el móvil y en el auricular
        if t > tp - .3:
            ap = aparece(t - tp + .3, .2); yb = 990
            R = _movil(c, 150, yb, 110, 210, 0, ap); _pantalla_musica(c, R, t, ap, onda=.3); _auri(c, 890, yb - 20, .8, 0, ap)
            for row, xr0 in enumerate((240, 240)):
                pass
            kk = int((t - tp + .3) * 6)
            for j in range(7):
                x = 250 + j * 85; v1 = _canal(kk + j); col = _mix("#2D5BB8", "#FFE15A", .5 + .5 * math.sin(v1))
                c.drawCircle(x, yb - 40, 16, relleno(col, ap)); c.drawCircle(x, yb + 20, 16, relleno(col, ap))
                c.drawLine(x, yb - 22, x, yb + 2, trazo("#FFFFFF", 2, .4 * ap))
            _pill(self, c, s.get("pareja_txt", "MISMO BAILE"), CX, yb + 90, S, aparece(t - tp, .15), fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- el auricular por dentro
    def e_auricular(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ks = ("antena_word", "chip_word", "conversor_word", "bobina_word", "iman_word", "vibra_word", "timpano_word")
        ta, tch, tcv, tb, ti, tv, tt = (_tw(self, e, k) for k in ks)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#1A1440", "#0C0A22", "#05030E"])))
        _bokeh(c, t, .5, seed=17, cols=("#7A4AE0", "#3A6AE0"))
        # oído (izquierda): conducto y tímpano
        OY = -120
        c.save(); c.translate(0, OY)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-300, 360, 250, 920), 140, 140), _p(_lin(360, 920, ["#F6CDAE", "#E0A47E", "#B87A5A"])))
        c.drawArc(skia.Rect(-200, 400, 220, 880), -60, 120, False, trazo("#C98763", 10, .5))
        canal = skia.Path(); canal.moveTo(-80, 560); canal.cubicTo(60, 560, 150, 590, 240, 600); canal.lineTo(240, 700); canal.cubicTo(150, 710, 60, 740, -80, 740); canal.close()
        c.drawPath(canal, _p(_lin(560, 740, ["#7A3A3A", "#A05050", "#7A3A3A"])))
        uv = _io((t - tv) / .3); vib = math.sin(t * 50) * uv
        tx_ = 30
        c.drawOval(skia.Rect(tx_ - 14 + 6 * vib * (1 if t > tt else .3), 575, tx_ + 14 + 6 * vib * (1 if t > tt else .3), 725), relleno("#FFD0C0", .95))
        # carcasa del auricular (grande, cortada)
        hx, hy = 600, 640
        sh = skia.Path(); sh.addCircle(hx, hy, 300); sh.addRRect(rrc(hx + 150, hy + 400, 170, 360, 85))
        c.drawPath(sh, relleno("#FFFFFF", .08)); c.drawCircle(hx, hy, 300, trazo("#FFFFFF", 5, .85)); c.drawRRect(rrc(hx + 150, hy + 400, 170, 360, 85), trazo("#FFFFFF", 5, .85))
        c.drawPath(skia.Path.Polygon([(hx - 300, hy - 60), (hx - 360, hy - 50), (hx - 360, hy + 50), (hx - 300, hy + 60)], True), trazo("#FFFFFF", 5, .85))   # boquilla hacia el oído
        # antena en el palito
        aa = aparece(t - ta, .2) if t > ta else .35
        an = skia.Path(); an.moveTo(hx + 150, hy + 540)
        for k in range(7): an.lineTo(hx + 150 + (30 if k % 2 else -30), hy + 540 - 26 * (k + 1))
        c.drawPath(an, trazo(_mix("#AEB8CA", "#FFE15A", aa), 6, .9))
        if t > ta - .4:
            for q in range(4):
                ph = ((t - ta + .4) * 1.2 + q / 4) % 1; r = 300 - 240 * ph
                c.drawArc(skia.Rect(hx + 150 - r, hy + 460 - r, hx + 150 + r, hy + 460 + r), -20, 80, False, trazo("#7FD3FF", 5, .7 * math.sin(math.pi * ph)))
        # chip
        cx_, cy_ = hx + 140, hy + 170; ach = aparece(t - tch, .2) if t > tch else 0
        c.drawRRect(rrc(cx_, cy_, 130, 130, 14), _p(_lin(cy_ - 65, cy_ + 65, ["#2A2F44", "#0E1220"])))
        for k in range(6):
            for sg in (-1, 1):
                c.drawLine(cx_ - 50 + k * 20, cy_ + sg * 65, cx_ - 50 + k * 20, cy_ + sg * 82, trazo("#E3B53C", 5))
                c.drawLine(cx_ + sg * 65, cy_ - 50 + k * 20, cx_ + sg * 82, cy_ - 50 + k * 20, trazo("#E3B53C", 5))
        if ach > 0:
            _glow(c, cx_, cy_, 140, "#7FD3FF", .45 * ach)
            for k in range(10):                                                     # bits que se expanden (descomprime)
                ph = ((t - tch) * .9 + k / 10) % 1; an_ = k * .63
                texto(c, "01"[k % 2], cx_ + (40 + 120 * ph) * math.cos(an_), cy_ + (40 + 120 * ph) * math.sin(an_), F(800, int(20 + 14 * ph), "JetBrainsMono"), "#7FD3FF", alfa=ach * math.sin(math.pi * ph))
        c.drawLine(hx + 150, hy + 360, cx_ + 20, cy_ + 82, trazo("#AEB8CA", 5, .8))
        # conversor y cable con corriente
        vx, vy = hx + 10, hy + 40; acv = aparece(t - tcv, .2) if t > tcv else 0
        c.drawRRect(rrc(vx, vy, 80, 60, 10), relleno(_mix("#2A2F44", "#3A4A7A", acv)))
        c.drawLine(cx_ - 65, cy_ - 30, vx + 40, vy + 10, trazo("#AEB8CA", 4, .8))
        wire = skia.Path(); wire.moveTo(vx - 40, vy); wire.cubicTo(vx - 120, vy - 20, hx - 120, hy + 40, hx - 160, hy)
        c.drawPath(wire, trazo(_mix("#AEB8CA", "#FFE15A", acv), 5, .9))
        if acv > 0:
            me = skia.PathMeasure(wire, False); L = me.getLength()
            for k in range(6):
                ph = ((t - tcv) * 1.4 + k / 6) % 1; ok, pos, _tan = (lambda r: (True, r[0], r[1]))(me.getPosTan(L * ph)) if hasattr(me, "getPosTan") else (False, None, None)
                if ok and pos is not None: _glow(c, pos.x(), pos.y(), 22, "#FFE15A", .8 * acv)
        # altavoz: imán, bobina, membrana (junto a la boquilla)
        sx_, sy_ = hx - 200, hy
        ai = aparece(t - ti, .2) if t > ti else 0; ab = aparece(t - tb, .2) if t > tb else 0
        c.drawRRect(rrc(sx_ + 10, sy_, 70, 170, 10), _p(_lin(sy_ - 85, sy_ + 85, ["#E5322D", "#E5322D", "#2A5AE0", "#2A5AE0"], 1, pos=[0, .5, .5, 1])))
        texto(c, "N", sx_ + 10, sy_ - 45, F(800, 30), "#FFFFFF"); texto(c, "S", sx_ + 10, sy_ + 45, F(800, 30), "#FFFFFF")
        if ai > 0: _glow(c, sx_ + 10, sy_, 130, "#FF5A8A", .35 * ai * (.7 + .3 * math.sin(t * 20)))
        mv = 10 * math.sin(t * 44) * (aparece(t - tv, .1) if t > tv else (.25 if t > ti else 0))
        for k in range(7):                                                          # bobina
            c.drawOval(skia.Rect(sx_ - 40 + mv, sy_ - 70 + k * 20, sx_ - 14 + mv, sy_ - 58 + k * 20), trazo(_mix("#C98A3A", "#FFE15A", ab), 5, .95))
        if ab > 0: _glow(c, sx_ - 27 + mv, sy_, 90, "#FFE15A", .35 * ab)
        mem = skia.Path(); mem.moveTo(sx_ - 60 + mv, sy_ - 130); mem.quadTo(sx_ - 100 + mv * 1.6, sy_, sx_ - 60 + mv, sy_ + 130)
        c.drawPath(mem, trazo("#FFFFFF", 8, .95))
        # ondas de aire hacia el tímpano
        if t > tv:
            av = aparece(t - tv, .2)
            for q in range(5):
                ph = ((t - tv) * 1.5 + q / 5) % 1; x = sx_ - 110 - (sx_ - 110 - tx_ - 20) * ph
                c.drawArc(skia.Rect(x - 40, sy_ - 70, x + 40, sy_ + 70), 150, 60, False, trazo("#7FD3FF", 6, av * math.sin(math.pi * ph)))
        if t > tt:
            _glow(c, tx_, 650, 120, "#FFE15A", .45 * aparece(t - tt, .2))
        # etiquetas
        for (tw, txt, x, y, col) in ((ta, s.get("antena_txt", "ANTENA"), hx + 330, hy + 480, "#1C5A8A"), (tch, s.get("chip_txt", "CHIP"), cx_ + 60, cy_ - 125, "#1C3A6A"),
                                     (tcv, s.get("conversor_txt", "CONVERSOR"), vx + 40, vy - 70, "#5A3A8A"), (tb, s.get("bobina_txt", "BOBINA"), sx_ - 30, sy_ - 190, "#8A5A0A"),
                                     (ti, s.get("iman_txt", "IMÁN"), sx_ + 110, sy_ + 140, "#8A1A3A"), (tv, s.get("membrana_txt", "MEMBRANA"), sx_ - 90, sy_ + 200, "#1E6A3A"),
                                     (tt, s.get("timpano_txt", "TÍMPANO"), 120, 480, "#7A2A6A")):
            if t > tw: _pill(self, c, txt, x, y, S, aparece(t - tw, .15), fondo=col, grande=False)
        c.restore()
        _franja(c)

    # ---------------------------------------------------------------- relevo entre auriculares
    def e_relevo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tr, tp = _tw(self, e, "recibe_word"), _tw(self, e, "pasa_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2E62E6", "#1A3FB0", "#0A1E60"])))
        for k in range(6): c.drawCircle(CX, 700, 180 + 130 * k + 20 * math.sin(t * .7 + k), trazo("#FFFFFF", 2, .06))
        # cabeza de espaldas (silueta)
        hx, hy = CX, 700
        c.drawOval(skia.Rect(hx - 200, hy - 240, hx + 200, hy + 230), _p(_rad(hx - 40, hy - 80, 300, ["#5A3A26", "#3A2418", "#24160E"])))
        c.drawRect(skia.Rect(hx - 90, hy + 180, hx + 90, hy + 330), _p(_lin(hy + 180, hy + 330, ["#E6AC86", "#C98763"])))
        c.drawPath(skia.Path.Polygon([(hx - 330, hy + 560), (hx - 300, hy + 340), (hx - 90, hy + 300), (hx + 90, hy + 300), (hx + 300, hy + 340), (hx + 330, hy + 560)], True), _p(_lin(hy + 300, hy + 560, ["#FF9A4D", "#B8401C"])))
        for sx in (-1, 1): c.drawOval(skia.Rect(hx + sx * 205 - 28, hy - 30, hx + sx * 205 + 28, hy + 50), _p(_lin(hy - 30, hy + 50, ["#F1C3A0", "#C98763"])))
        L, Rr = (hx - 225, hy), (hx + 225, hy)
        ar = aparece(t - tr, .1) if t > tr else 0; ap_ = aparece(t - tp, .1) if t > tp else 0
        _auri(c, L[0], L[1], .8, 15, 1.0, glow=ar, lado=-1)
        _auri(c, Rr[0], Rr[1], .8, -15, 1.0, glow=ap_, lado=1)
        mx, my = CX, 230
        R = _movil(c, mx, my, 120, 230, 0); _pantalla_musica(c, R, t, onda=.4)
        def rayo(p0, p1, u, col):
            n = 20
            for k in range(n):
                q = k / n
                if q > u: break
                x = p0[0] + (p1[0] - p0[0]) * q; y = p0[1] + (p1[1] - p0[1]) * q - 120 * math.sin(math.pi * q) * (1 if p0[1] > 500 else 0)
                c.drawCircle(x, y, 6, relleno(col, .9))
            ph = (t * 1.2) % 1
            for k in range(3):
                q = (ph + k / 3) % 1
                if q > u: continue
                x = p0[0] + (p1[0] - p0[0]) * q; y = p0[1] + (p1[1] - p0[1]) * q - 120 * math.sin(math.pi * q) * (1 if p0[1] > 500 else 0)
                _nota(c, x, y, .8, 1.0, "#FFE15A", k % 2 == 1)
        if t > tr: rayo((mx, my + 120), (L[0], L[1] - 50), TI.clamp((t - tr) / .5), "#7FD3FF")
        if t > tp: rayo((L[0] + 20, L[1] - 40), (Rr[0] - 20, Rr[1] - 40), TI.clamp((t - tp) / .6), "#FFE15A")
        if t > tr: _pill(self, c, s.get("principal_txt", "PRINCIPAL"), L[0] + 30, L[1] + 190, S, ar, fondo="#0B1430")
        if t > tp + .3: _pill(self, c, s.get("otro_txt", "EL OTRO"), Rr[0] - 30, Rr[1] + 190, S, aparece(t - tp - .3, .15), fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- el rey vikingo
    def _rey(c, x, y, s, t, a=1.0, diente=0.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        P = ("#FBE0C8", "#F1C3A0", "#D99A74")
        # capa roja y armadura
        cp = skia.Path(); cp.moveTo(-300, 520); cp.cubicTo(-300, 300, -220, 220, -100, 200); cp.lineTo(100, 200); cp.cubicTo(220, 220, 300, 300, 300, 520); cp.close()
        c.drawPath(cp, _p(_lin(200, 520, ["#C0392B", "#7A1A12"], a)))
        c.drawPath(skia.Path.Polygon([(-150, 520), (-120, 240), (120, 240), (150, 520)], True), _p(_lin(240, 520, ["#8A94A8", "#4A5268"], a)))
        for k in range(5): c.drawLine(-110 + k * 55, 250, -120 + k * 60, 520, trazo("#5A6478", 3, .6 * a))
        c.drawCircle(-150, 230, 26, relleno("#E3B53C", a)); c.drawCircle(150, 230, 26, relleno("#E3B53C", a))
        # cabeza
        c.drawOval(skia.Rect(-150, -170, 150, 170), _p(_rad(-40, -60, 240, P, [0, .6, 1], a)))
        # barba roja trenzada
        bp = skia.Path(); bp.moveTo(-150, 0); bp.cubicTo(-160, 160, -80, 260, 0, 300); bp.cubicTo(80, 260, 160, 160, 150, 0); bp.cubicTo(100, 80, -100, 80, -150, 0); bp.close()
        c.drawPath(bp, _p(_lin(0, 300, ["#D9772A", "#A04A12"], a)))
        for k in range(9):
            x0 = -120 + k * 30; c.drawLine(x0, 40, x0 * .6, 240, trazo("#7A3208", 3, .5 * a))
        for sx in (-1, 1):
            c.drawRRect(rrc(sx * 40, 300, 30, 60, 12), _p(_lin(270, 330, ["#D9772A", "#A04A12"], a))); c.drawRect(skia.Rect(sx * 40 - 16, 306, sx * 40 + 16, 316), relleno("#E3B53C", a))
        # bigote y boca sonriente con diente azul
        c.drawPath(skia.Path.Polygon([(-90, 40), (0, 20), (90, 40), (60, 60), (0, 46), (-60, 60)], True), relleno("#B8541A", a))
        mo = skia.Path(); mo.moveTo(-50, 70); mo.quadTo(0, 130, 50, 70); mo.close(); c.drawPath(mo, relleno("#5A1E1E", a))
        for k in range(4):
            col = "#2A6AE8" if k == 1 else "#FFFFFF"; c.drawRect(skia.Rect(-38 + k * 19, 70, -22 + k * 19, 86), relleno(col, a))
        if diente > 0:
            _glow(c, -11, 78, 70, "#5AC8FF", .7 * diente)
            for k in range(4):
                an = k * math.pi / 2 + t * 2; c.drawLine(-11 + 20 * math.cos(an), 78 + 20 * math.sin(an), -11 + 44 * math.cos(an), 78 + 44 * math.sin(an), trazo("#BFE6FF", 4, diente))
        # ojos y cejas
        for sx in (-1, 1):
            c.drawCircle(sx * 55, -40, 18, relleno("#FFFFFF", a)); c.drawCircle(sx * 55 + 3, -38, 9, relleno("#1A2A4A", a))
            c.drawLine(sx * 30, -80, sx * 85, -74, trazo("#A04A12", 12, a))
        c.drawOval(skia.Rect(-20, -10, 20, 30), relleno(P[2], .5 * a))
        # casco (sin cuernos: los vikingos no los llevaban) con corona
        hm = skia.Path(); hm.moveTo(-160, -60); hm.cubicTo(-160, -250, 160, -250, 160, -60); hm.close()
        c.drawPath(hm, _p(_lin(-230, -60, ["#C9D0DE", "#6A7488"], a)))
        c.drawRect(skia.Rect(-14, -230, 14, -60), relleno("#8A94A8", a)); c.drawRect(skia.Rect(-162, -84, 162, -56), relleno("#E3B53C", a))
        cr = skia.Path(); cr.moveTo(-120, -200)
        for k in range(5): cr.lineTo(-120 + k * 60 + 30, -270); cr.lineTo(-120 + (k + 1) * 60, -210)
        cr.close(); c.drawPath(cr, _p(_lin(-270, -200, ["#FFE58A", "#E3B53C"], a)))
        for k in range(5): c.drawCircle(-90 + k * 60, -262, 8, relleno(("#E5322D", "#2A6AE8")[k % 2], a))
        c.restore()
    def e_rey(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tr, td, tu, tj = (_tw(self, e, k) for k in ("rey_word", "diente_word", "unio_word", "une_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#4A2A18", "#2A160C", "#120804"])))
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(CX, 520, 600, _p(_rad(CX, 520, 600, ["#FFB45C", "#000000"], None, .22)))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=33, n=40, col="#FFD9A0")
        um = _io((t - tu + .2) / .7)
        uj = _io((t - tj + .2) / .7)
        # rey: centrado y grande → se va a la izquierda cuando sale el mapa
        ar = aparece(t - tr + .3, .25) if t > tr - .3 else 0
        rx = CX - 210 * um + 210 * uj; ry = 620 - 40 * um + 40 * uj; rs = 1.15 - .5 * um + .1 * uj
        if ar > 0: _rey(c, rx, ry + 60 * (1 - resorte(t - tr + .3, 7, 9)), rs, t, ar, diente=(aparece(t - td, .2) if t > td else 0))
        if t > td and um < .5: _pill(self, c, "HARALD «DIENTE AZUL»", CX, 160 + 0, S, aparece(t - td, .15) * (1 - um * 2), fondo="#1C3A6A")
        # mapa de Dinamarca y Noruega
        am = um * (1 - uj)
        if am > 0:
            G_ = self.geo([12.0, 60.0]); cx_, cy_ = 700, 560; k = .32 * (.9 + .1 * um); cen = np.array(G_["pr"](11.0, 62.0))
            c.save(); c.translate(cx_, cy_); c.scale(k, -k); c.translate(-cen[0], -cen[1])
            for pk in ("tierra", "francia"): c.drawPath(G_[pk], relleno("#6A4A2A", .9 * am))
            for cid, col in ((s.get("dk", "208"), "#E5322D"), (s.get("no", "578"), "#2A6AE8")):
                if cid in G_["ids"]:
                    c.drawPath(G_["ids"][cid], relleno(col, .85 * am)); c.drawPath(G_["ids"][cid], trazo("#FFFFFF", 2.5 / k, .9 * am))
            c.restore()
            P = lambda lon, lat: (lambda q: (cx_ + (q[0] - cen[0]) * k, cy_ - (q[1] - cen[1]) * k))(G_["pr"](lon, lat))
            x1, y1 = P(9.5, 56.0); x2, y2 = P(9.0, 61.5)
            _pill(self, c, s.get("dk_txt", "DINAMARCA"), x1 + 40, y1 + 70, S, am, fondo="#8A1A0A", grande=False)
            _pill(self, c, s.get("no_txt", "NORUEGA"), x2 + 10, y2 - 20, S, am, fondo="#1C3A8A", grande=False)
            _pill(self, c, s.get("anio_txt", "AÑO 958"), 700, 180, S, am, fondo="#7A4A05")
            if t > tu + .3:
                q = TI.clamp((t - tu - .3) / .6); pth = skia.Path(); pth.moveTo(x1, y1); pth.quadTo((x1 + x2) / 2 + 80, (y1 + y2) / 2, x2, y2)
                me = skia.PathMeasure(pth, False); sp = skia.Path(); me.getSegment(0, me.getLength() * q, sp, True); c.drawPath(sp, trazo("#FFE15A", 6, am))
        # juntar aparatos
        if uj > 0:
            ap = uj
            pts = [(170, 560), (870, 560), (520, 230)]
            R = _movil(c, pts[0][0], pts[0][1], 130, 250, -10, ap)
            c.save(); c.translate(pts[0][0], pts[0][1]); c.rotate(-10); c.translate(-pts[0][0], -pts[0][1]); _pantalla_musica(c, R, t, ap, onda=.5); c.restore()
            _auri(c, pts[1][0] - 40, pts[1][1], .8, -10, ap); _auri(c, pts[1][0] + 50, pts[1][1] + 20, .8, 10, ap, lado=-1)
            for (x, y) in pts[:2]:
                pl = trazo("#FFE15A", 5, .8 * ap); pl.setPathEffect(skia.DashPathEffect.Make([14, 10], -t * 40)); c.drawLine(x, y - 40, rx, ry - 60, pl)
            _pill(self, c, s.get("une_txt", "UNIR APARATOS"), CX, 1010, S, aparece(t - tj, .15), fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_auris(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "oreja":
            if s.get("modo") == "gancho":
                if g("corte_word") is not None: sf(g("corte_word") - .5, "desliz", .5); sf(g("corte_word") - .05, "tijera", 1.0); sf(g("corte_word") + .35, "caida", .5)
                if g("aire_word") is not None:
                    for j in range(4): sf(g("aire_word") - .2 + j * .45, "nota", .5 - .08 * j)
            else:
                for j in range(5): sf(e["t0"] + .2 + j * .3, "salto", .5)
                if g("saltos_word") is not None: self.rodillo(g("saltos_word"), .9)
                if g("oreja_word") is not None: sf(g("oreja_word") - .2, "nota", .7); sf(g("oreja_word") + .2, "destello", .5)
        if tp == "bits":
            sf(e["t0"] + .2, "nota", .4)
            if g("numeros_word") is not None: sf(g("numeros_word") - .1, "datos", .9); sf(g("numeros_word") + .8, "datos", .5)
            if g("comprime_word") is not None: sf(g("comprime_word"), "prensa", 1.0); sf(g("comprime_word") + .55, "pop", .5); sf(g("comprime_word") + 2.2, "whoosh", .5)
        if tp == "ondas":
            if g("ondas_word") is not None: sf(g("ondas_word") - .1, "subida", .5)
            if g("vibran_word") is not None: self.rodillo(g("vibran_word"), 1.6)
            if g("luz_word") is not None: sf(g("luz_word"), "zum", .9)
            if g("llega_word") is not None: sf(g("llega_word"), "ding", .7); sf(g("llega_word") + .15, "pop", .4)
        if tp == "lleno":
            if g("wifi_word") is not None: sf(g("wifi_word"), "bip", .6); sf(g("wifi_word") + .2, "pop", .4)
            if g("moviles_word") is not None: sf(g("moviles_word"), "noti", .6); sf(g("moviles_word") + .2, "vibra", .5)
            if g("micro_word") is not None: sf(g("micro_word") - .15, "bip", .6); sf(g("micro_word") + .05, "micro", 1.0); sf(g("micro_word") + 1.0, "golpe", .4)
        if tp == "saltos":
            if g("salta_word") is not None:
                tt = g("salta_word") - .2; k = 0
                while tt + k * .25 < e["t1"] - .3 and k < 40: sf(tt + k * .25, "salto", .35); k += 1
            if g("canales_word") is not None: sf(g("canales_word"), "barrido", .6)
            if g("veces_word") is not None: sf(g("veces_word"), "pop", .6)
            if g("ocupado_word") is not None: sf(g("ocupado_word"), "alarma", .5)
            if g("pareja_word") is not None: sf(g("pareja_word") - .3, "campana", .6)
        if tp == "auricular":
            for k, n in (("antena_word", "subida"), ("chip_word", "datos"), ("conversor_word", "electrico"), ("bobina_word", "zumbido"),
                         ("iman_word", "golpe"), ("vibra_word", "vibra"), ("timpano_word", "nota")):
                if g(k) is not None: sf(g(k), n, .7)
        if tp == "relevo":
            if g("recibe_word") is not None: sf(g("recibe_word"), "whoosh", .5); sf(g("recibe_word") + .5, "pop", .5)
            if g("pasa_word") is not None: sf(g("pasa_word"), "whoosh", .5); sf(g("pasa_word") + .6, "pop", .5)
        if tp == "rey":
            if g("rey_word") is not None: sf(g("rey_word") - .3, "corona", .9)
            if g("diente_word") is not None: sf(g("diente_word") + .1, "destello2", .9)
            if g("unio_word") is not None: sf(g("unio_word") - .2, "whoosh", .5); sf(g("unio_word") + .4, "rotulador", .6)
            if g("une_word") is not None: sf(g("une_word") - .2, "campana", .6); sf(g("une_word") + .3, "pop", .5)

    for k, fn in (("oreja", e_oreja), ("bits", e_bits), ("ondas", e_ondas), ("lleno", e_lleno), ("saltos", e_saltos),
                  ("auricular", e_auricular), ("relevo", e_relevo), ("rey", e_rey)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_auris)
