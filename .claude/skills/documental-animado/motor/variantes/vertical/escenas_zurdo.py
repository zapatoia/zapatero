"""Escenas del documental 20 («¿Por qué hay tan pocos zurdos?»).

Reutiliza `self.cara_b` (17) y `self.persona_t` (14). Mano izquierda ilustrada (`_mano`) con poses: abierta, lapiz, tijeras.
reves       habitación: gancho (mano_word: la mano izquierda saluda; flip_word: el mundo se da la vuelta como un espejo, ¡FLIP!);
            cierre (arma_word: medalla ARMA SECRETA; tijeras_word: las tijeras le ganan, ¡ÑAC!).
objetos     cuatro tarjetas con lo que se le hace cuesta arriba a un zurdo: items [{word, tipo: tijeras/espiral/tinta/pupitre, txt}].
diez        diez personas y una zurda (uno_word, pct_txt) y la línea de 10.000 años con manos de cueva (anios_word).
cerebro_z   cerebro visto desde arriba: lado izquierdo → mano derecha (lado_word), lenguaje (lenguaje_word), genes ≈ 1/4 (genes_word, cuarta_word).
escuela     aula antigua: «CON LA DERECHA» en la pizarra (obliga_word), la mano izquierda atada (ata_word), sinister → siniestro (siniestro_word).
pelea       duelo de esgrima: el zurdo pilla por sorpresa (golpe_word, ¡TOCADO!); más peleas → más zurdos (estudios_word); barras gente /
            esgrima de élite (esgrima_word).
equilibrio  deslizador de % de zurdos y medidor de SORPRESA: a la mitad no sorprenden (mitad_word), vuelve a pocos (pocos_word), nunca cero (cero_word).
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

    # ---------------------------------------------------------------- sonidos
    def s_flip():
        d = .5; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        return AU._banda(AU._ruido(n, 201), 600, 5000) * np.sin(np.pi * u) ** 1.5 * (1 + .5 * np.sin(2 * np.pi * (6 + 20 * u) * t))
    def s_espada():
        d = .45; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 2700 * t) + .6 * np.sin(2 * np.pi * 4100 * t) + .4 * np.sin(2 * np.pi * 5400 * t)) * np.exp(-t / .12) * np.minimum(1, t / .002)
    def s_cuerda():
        d = .5; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 202), 300, 2500) * (np.sin(2 * np.pi * 7 * u * d * 6) > 0) * np.sin(np.pi * u)
    def s_tiza():
        d = .6; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 203), 2000, 8000) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 11 * t))) * np.sin(np.pi * t / d)
    def s_ay():
        d = .25; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * (700 - 900 * t) * t) * np.exp(-t / .08)
    def s_tijeretazo():
        d = .2; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 204), 2500, 9000) * np.exp(-t / .02) + .7 * np.sin(2 * np.pi * 3300 * t) * np.exp(-t / .03)
    for nom, fn, db in (("flip", s_flip, -28), ("espada", s_espada, -30), ("cuerda", s_cuerda, -31), ("tiza", s_tiza, -32),
                        ("ay", s_ay, -30), ("tijeretazo", s_tijeretazo, -27)):
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
    def _polvo(c, t, x0, x1, y0, y1, a, seed=5, n=40, col="#FFF6D0"):
        rng = np.random.default_rng(seed)
        for k in range(n):
            x = x0 + (x1 - x0) * ((rng.random() + .02 * t * (rng.random() - .5)) % 1); y = y0 + (y1 - y0) * ((rng.random() - .015 * t * (.5 + rng.random())) % 1)
            c.drawCircle(x, y, 1.2 + 2.4 * rng.random(), relleno(col, a * (.3 + .5 * rng.random()) * (.6 + .4 * math.sin(t * 2 + k))))
    PIEL = ("#FBE0C8", "#F1C3A0", "#D99A74")

    def _mano(c, x, y, s, rot=0.0, pose="abierta", a=1.0, t=0.0, manga="#FF8A3D"):
        """Mano IZQUIERDA vista por la palma (pulgar a la derecha del dibujo). (x, y) = centro de la palma; la manga baja."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
        c.drawRRect(rrc(0, 170, 130, 170, 50), _p(_lin(100, 260, [manga, _mix(manga, "#000000", .35)], a)))
        c.drawRRect(rrc(0, 110, 140, 26, 13), relleno(_mix(manga, "#FFFFFF", .3), a))
        c.drawRRect(rrc(0, 30, 150, 150, 60), _p(_rad(-20, 0, 140, PIEL, [0, .6, 1], a)))
        if pose == "abierta":
            for k, (dx, L, an) in enumerate(((-52, 92, -14), (-18, 110, -4), (18, 104, 4), (50, 84, 14))):
                c.save(); c.translate(dx, -30); c.rotate(an + 4 * math.sin(t * 8 + k))
                c.drawRRect(rrc(0, -L / 2, 34, L, 17), _p(_linx(-17, 17, [PIEL[1], PIEL[0], PIEL[1]], a)))
                c.drawRRect(rrc(0, -L + 12, 22, 16, 8), relleno("#FFFFFF", .5 * a)); c.restore()
            c.save(); c.translate(70, 30); c.rotate(48); c.drawRRect(rrc(0, -40, 36, 86, 18), _p(_linx(-18, 18, [PIEL[1], PIEL[0], PIEL[1]], a))); c.restore()
        else:
            for k in range(4):                                                    # nudillos de puño
                c.drawRRect(rrc(-54 + k * 36, -38, 38, 56, 18), _p(_lin(-66, -10, [PIEL[0], PIEL[1]], a)))
            c.save(); c.translate(60, 0); c.rotate(-30); c.drawRRect(rrc(0, -30, 34, 76, 17), _p(_linx(-17, 17, [PIEL[1], PIEL[0], PIEL[1]], a))); c.restore()
            if pose == "lapiz":
                c.save(); c.translate(-10, -40); c.rotate(-35)
                c.drawRect(skia.Rect(-10, -150, 10, 60), _p(_linx(-10, 10, ["#E0A21A", "#FFD24A", "#C9820A"], a)))
                c.drawPath(skia.Path.Polygon([(-10, 60), (10, 60), (0, 96)], True), relleno("#E9C9A0", a)); c.drawPath(skia.Path.Polygon([(-4, 84), (4, 84), (0, 96)], True), relleno("#2A2A30", a))
                c.drawRect(skia.Rect(-11, -170, 11, -150), relleno("#FF8A9A", a)); c.restore()
            if pose == "tijeras":
                c.save(); c.translate(-20, -70); ab = 14 + 10 * math.sin(t * 6)
                for sg in (-1, 1):
                    c.save(); c.rotate(sg * ab); c.drawPath(skia.Path.Polygon([(0, 0), (-12, -170), (6, -170), (10, 0)], True), _p(_linx(-12, 10, ["#FFFFFF", "#AEB8CA"], a))); c.restore()
                c.drawCircle(0, 0, 8, relleno("#5A6478", a)); c.restore()
        c.restore()

    # ---------------------------------------------------------------- habitación (gancho / cierre)
    def _habitacion(c, t, S, s, a=1.0):
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2A2448", "#1A1634", "#0C0A1E"])))
        for k in range(14): c.drawLine(k * 90 - 40, -80, k * 90 - 40, 1300, trazo("#FFFFFF", 2, .03))
        # ventana con luna
        c.drawRRect(rrc(200, 300, 260, 300, 16), relleno("#C9945A")); c.drawRRect(rrc(200, 300, 230, 270, 10), _p(_lin(165, 435, ["#0E1640", "#2A3A7A"])))
        c.drawCircle(240, 250, 36, _p(_rad(230, 240, 40, ["#FFFFFF", "#DDE6F6"]))); c.drawCircle(256, 240, 30, relleno("#1A2456"))
        c.drawLine(200, 165, 200, 435, trazo("#C9945A", 8)); c.drawLine(85, 300, 315, 300, trazo("#C9945A", 8))
        # póster con texto
        c.save(); c.translate(780, 300); c.rotate(3)
        c.drawRect(skia.Rect(-130, -150, 130, 150), _p(_lin(-150, 150, ["#FF5A8A", "#7A4AE0"])))
        texto(c, s.get("cartel", "HOLA"), 0, -40, F(900, 70), "#FFFFFF"); c.drawCircle(0, 70, 40, relleno("#FFE15A")); c.drawCircle(-14, 62, 6, relleno("#1A1634")); c.drawCircle(14, 62, 6, relleno("#1A1634"))
        c.drawArc(skia.Rect(-20, 62, 20, 92), 20, 140, False, trazo("#1A1634", 5))
        c.restore()
        # reloj
        c.drawCircle(520, 170, 60, _p(_rad(505, 155, 70, ["#FFFFFF", "#DCE6F6"]))); c.drawCircle(520, 170, 60, trazo("#1C2340", 5))
        c.drawLine(520, 170, 520 + 40 * math.cos(t * .8 - 1.5), 170 + 40 * math.sin(t * .8 - 1.5), trazo("#1C2340", 5)); c.drawLine(520, 170, 548, 170, trazo("#E5322D", 4))
        # lámpara
        c.drawLine(900, 700, 900, 1060, trazo("#5A6478", 8)); c.drawPath(skia.Path.Polygon([(840, 700), (960, 700), (930, 620), (870, 620)], True), relleno("#FFE15A"))
        _glow(c, 900, 700, 220, "#FFE9A0", .3)
        c.drawRect(skia.Rect(-80, 1060, W + 80, H + 80), _p(_lin(1060, H, ["#3A2A22", "#1A120E"])))
    def e_reves(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "gancho")
        fx, fy, fs = CX, 640, 1.0
        if modo == "gancho":
            tm, tf = _tw(self, e, "mano_word"), _tw(self, e, "flip_word")
            u = TI.clamp((t - tf + .1) / .7); ang = math.pi * _io(u); sx = math.cos(ang)
            mir = -1 if u > .5 else 1
            c.save(); c.translate(CX, 640); c.scale(abs(sx) * .9 + .1 * abs(sx) if True else 1, 1); c.scale(mir, 1); c.translate(-CX, -640)
            _habitacion(c, t, S, s)
            self.cara_b(c, fx, fy, fs, t, cob=0, largo=0, expr=("feliz" if t > tm else "neutral"), mira=(.3, 0))
            # la mano izquierda saluda (a la derecha del dibujo: así es la izquierda de quien mira de frente)
            am = aparece(t - tm + .2, .2) if t > tm - .2 else 0
            if am > 0:
                wv = 12 * math.sin((t - tm) * 9) * math.exp(-max(0, t - tm - 1.5) * 1.5)
                _mano(c, fx + 340, fy + 90 - 40 * resorte(t - tm + .2, 8, 10), 1.0, -10 + wv, "abierta", am, t)
                _glow(c, fx + 340, fy + 40, 180, "#FFE15A", .25 * am)
            c.restore()
            if 0.05 < u < .95: _glow(c, CX, 640, 600, "#FFFFFF", .25 * math.sin(math.pi * u))
            if t > tm: _pill(self, c, "MANO IZQUIERDA", 730, 1000, S, aparece(t - tm, .15) * (1 - TI.clamp((t - tf + .3) / .2)), fondo="#7A4A05")
            if 0 < t - tf < 1.0: self.comic_t(c, "¡FLIP!", CX, 180, 90, -6, .7 + .3 * resorte(t - tf, 10, 14), 1 - TI.clamp((t - tf - .75) / .25), "#FFE15A")
        else:
            ta, tt = _tw(self, e, "arma_word"), _tw(self, e, "tijeras_word")
            c.save(); c.translate(CX, 640); c.scale(-1, 1); c.translate(-CX, -640); _habitacion(c, t, S, s); c.restore()
            expr = "feliz" if t < tt + .3 else "meh"
            self.cara_b(c, fx, fy, fs, t, cob=0, largo=0, expr=expr, mira=((.8, .3) if t > tt else (0, 0)))
            if t > ta - .2:                                                       # medalla
                a = aparece(t - ta + .2, .2); u = resorte(t - ta + .2, 8, 10); my = fy + 330 - 60 * (1 - u)
                c.drawPath(skia.Path.Polygon([(fx - 60, fy + 230), (fx - 20, my - 40), (fx + 20, my - 40), (fx + 60, fy + 230)], True), relleno("#2A6AE8", a))
                c.drawCircle(fx, my + 30, 70, _p(_rad(fx - 20, my + 10, 90, ["#FFF2A0", "#E3B53C", "#8A6A22"], [0, .6, 1], a))); c.drawCircle(fx, my + 30, 52, trazo("#8A6A22", 4, a))
                texto(c, "Z", fx, my + 30, F(900, 60), "#8A6A22", alfa=a)
                _glow(c, fx, my + 30, 200, "#FFE15A", .3 * a)
                _pill(self, c, s.get("arma_txt", "ARMA SECRETA"), fx - 280, fy + 330, S, a, fondo="#7A4A05")
            if t > tt - .3:                                                       # las tijeras le ganan
                a = aparece(t - tt + .3, .15)
                _mano(c, fx + 340, fy + 120, 1.0, -15, "tijeras", a, t * 3)
                if 0 < t - tt < 1.2: self.comic_t(c, "¡ÑAC!", fx + 300, fy - 170, 76, 8, .7 + .3 * resorte(t - tt, 10, 14), 1 - TI.clamp((t - tt - .9) / .3), "#FFE15A")
                for k in range(5):
                    ph = ((t - tt) * .8 + k / 5) % 1; c.drawLine(fx + 300 + 60 * math.cos(k), fy + 20 + 400 * ph, fx + 330 + 60 * math.cos(k), fy + 30 + 400 * ph, trazo("#FFFFFF", 4, .7 * (1 - ph) * a))
        _franja(c)

    # ---------------------------------------------------------------- cuatro tarjetas
    def _tarjeta(self, c, tipo, x, y, t, dt, a, txt, S):
        c.save(); c.translate(x, y)
        c.drawRRect(rrc(8, 14, 430, 400, 30), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        c.drawRRect(rrc(0, 0, 430, 400, 30), _p(_lin(-200, 200, ["#FBF8F0", "#E9E2D0"], a)))
        c.save(); c.clipRRect(rrc(0, 0, 430, 400, 30), doAntiAlias=True)
        if tipo == "tijeras":
            c.drawRect(skia.Rect(-180, -120, 180, 140), relleno("#FFFFFF", a))
            pl = trazo("#2A6AE8", 5, a); pl.setPathEffect(skia.DashPathEffect.Make([16, 10], 0)); c.drawLine(-180, 20, 180, 20, pl)
            cx = 120 - 160 * TI.clamp(dt / 2.0)
            c.drawRect(skia.Rect(cx - 60, -10, 200, 50), relleno("#FBF8F0", 0))
            _mano(c, cx + 60, 90, .7, -100, "tijeras", a, t * 2)
            c.drawRRect(rrc(cx - 40, 18, 90, 26, 6), relleno("#AEB8CA", .9 * a))              # la hoja tapa la línea
            texto(c, "?", cx - 70, -60, F(900, 80), "#E5322D", alfa=a * aparece(dt - .5, .2))
        elif tipo == "espiral":
            c.drawRRect(rrc(0, 0, 320, 300, 10), relleno("#FFFFFF", a))
            for k in range(9): c.drawLine(-150, -110 + k * 28, 150, -110 + k * 28, trazo("#9FC3FF", 2, .7 * a))
            for k in range(9): c.drawOval(skia.Rect(-20, -128 + k * 30, 20, -112 + k * 30), trazo("#6A7488", 5, a))
            hx = -60 + 30 * math.sin(dt * 3)
            _mano(c, hx + 40, 40, .7, -20, "lapiz", a, t)
            if dt > .6:
                c.drawOval(skia.Rect(-10, 40, 30, 70), relleno("#FF5A6A", .5 * a * aparece(dt - .6, .2)))
                if dt < 2.0: self.comic_t(c, "¡AY!", 120, -120, 56, 8, .7 + .3 * resorte(dt - .6, 10, 14), 1 - TI.clamp((dt - 1.7) / .3), "#E5322D")
        elif tipo == "tinta":
            c.drawRect(skia.Rect(-180, -120, 180, 140), relleno("#FFFFFF", a))
            p = TI.clamp(dt / 1.8); xe = -150 + 280 * p
            ln = skia.Path(); ln.moveTo(-150, -20)
            for k in range(int(p * 40) + 1):
                xx = -150 + 7 * k; ln.lineTo(xx, -20 + 16 * math.sin(k * 1.3) * math.sin(k * .5))
            c.drawPath(ln, trazo("#1A2A6A", 5, a))
            c.drawRect(skia.Rect(-150, -6, xe - 40, 20), skia.Paint(AntiAlias=True, Color=color("#1A2A6A", .25 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
            _mano(c, xe + 30, 60, .7, -40, "lapiz", a, t)
            c.drawOval(skia.Rect(xe - 30, 60, xe + 10, 80), relleno("#1A2A6A", .4 * a))
        else:   # pupitre con la mesita a la derecha
            c.drawRRect(rrc(-20, 110, 260, 30, 10), relleno("#8A5A32", a))
            for sx in (-100, 60): c.drawRect(skia.Rect(sx - 6, 120, sx + 6, 180), relleno("#3A4258", a))
            c.drawRRect(rrc(-110, 40, 30, 150, 10), relleno("#8A5A32", a))
            c.drawRRect(rrc(80, -10, 160, 40, 10), relleno("#B07A4A", a)); c.drawRect(skia.Rect(150, 10, 158, 110), relleno("#3A4258", a))
            self.persona_t(c, -40, 60, .55, t, pose="de_pie", cara="o", a=a, rot=-12 + 4 * math.sin(t * 3))
            c.drawLine(-160, -130, -40, -130, trazo("#E5322D", 6, a)); c.drawPath(skia.Path.Polygon([(-170, -130), (-145, -145), (-145, -115)], True), relleno("#E5322D", a))
            c.drawPath(skia.Path.Polygon([(150, -60), (180, -100), (190, -50)], True), relleno("#2ED47A", a))
        c.restore()
        c.drawRRect(rrc(0, 0, 430, 400, 30), trazo("#C9A87A", 3, a))
        c.restore()
        self.pildora(c, txt, x, y + 170, S, a, fnt=self.F["pillb"], fondo="#7A3A14")
    def e_objetos(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#4A2A18", "#2A160C", "#120804"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=13, n=40, col="#FFD9A0")
        pos = [(270, 410), (770, 410), (270, 880), (770, 880)]
        items = s.get("items", [])
        ts = [self.ta(it["word"], e) - .25 for it in items]
        act = max([i for i, tt in enumerate(ts) if t >= tt] or [-1])
        for k, it in enumerate(items):
            if t < ts[k]: continue
            u = resorte(t - ts[k], 8, 10); a = aparece(t - ts[k], .15)
            x, y = pos[k]; sc = (.6 + .4 * u) * (1.1 if k == act else .98)
            c.save(); c.translate(x, y); c.scale(sc, sc); c.translate(-x, -y)
            _tarjeta(self, c, it["tipo"], x, y, t, t - ts[k], a * (1 if k == act else .75), it["txt"], S)
            c.restore()
            if k == act: c.drawRRect(rrc(x, y, 450 * sc, 420 * sc, 34), trazo("#FFE15A", 5, .8 * a))
        _franja(c)

    # ---------------------------------------------------------------- uno de cada diez / diez mil años
    def _persona(c, x, y, s, col, a=1.0, saluda=0.0, t=0.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        c.drawCircle(0, -120, 40, _p(_rad(-10, -130, 50, [_mix(col, "#FFFFFF", .3), col], None, a)))
        c.drawRRect(rrc(0, -20, 100, 140, 44), _p(_lin(-90, 50, [_mix(col, "#FFFFFF", .2), col, _mix(col, "#000000", .3)], a)))
        if saluda > 0:
            an = -150 + 20 * math.sin(t * 9)
            c.save(); c.translate(42, -60); c.rotate(an + 180); c.drawRRect(rrc(0, 50, 30, 100, 15), relleno(col, a)); c.drawCircle(0, 104, 20, relleno("#F1C3A0", a)); c.restore()
        c.restore()
    def e_diez(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tu, ta = _tw(self, e, "uno_word"), _tw(self, e, "anios_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0B1530", "#071026", "#050A18"])))
        _polvo(c, t, 0, W, 100, 1150, .6, seed=23, n=50, col="#6EA0FF")
        ua = _io((t - ta + .2) / .6)
        c.save(); c.translate(0, -230 * ua); c.scale(1, 1)
        for k in range(10):
            col_, fila = k % 5, k // 5; x = 150 + col_ * 185; y = 480 + fila * 300
            z = k == 7; on = aparece(t - tu, .2) if (z and t > tu) else 0
            ap = aparece(dt0 - .05 * k, .12)
            _persona(c, x, y - 20 * on * abs(math.sin((t - tu) * 6)) * math.exp(-max(0, t - tu - 1) * 2), .95, _mix("#4A6AB8", "#FF8A3D", on), ap * (1 - .8 * ua), saluda=on, t=t)
            if on > 0: _glow(c, x, y - 40, 160, "#FF8A3D", .35 * on * (1 - ua))
        c.restore()
        if t > tu + .2 and ua < 1:
            a = aparece(t - tu - .2, .15) * (1 - ua)
            c.drawRRect(rrc(CX, 230, 560, 130, 40), relleno("#FFFFFF", .95 * a))
            texto(c, s.get("pct_txt", "10,6 %"), CX, 230, F(800, 84), "#C2410C", alfa=a)
        # diez mil años: línea de tiempo con manos de cueva
        if ua > 0:
            a = ua; y0 = 850; x0, x1 = 100, 940
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 - 20, 640, x1 + 20, 1060), 30, 30), _p(_lin(640, 1060, ["#6A4A2A", "#3A2414"], a)))
            rng = np.random.default_rng(3)
            for k in range(30): c.drawCircle(x0 + (x1 - x0) * rng.random(), 660 + 380 * rng.random(), 6 + 14 * rng.random(), relleno("#2A1A0E", .25 * a))
            pl = trazo("#FFE9C0", 6, a); c.drawLine(x0, y0 + 120, x0 + (x1 - x0) * TI.clamp((t - ta) / 1.2), y0 + 120, pl)
            v = int(10000 * TI.cubic_out(TI.clamp((t - ta) / 1.2)))
            texto(c, f"−{v:,}".replace(",", ".") + " AÑOS", x0 + 40, y0 + 165, F(800, 30), "#FFE9C0", alinear="i", alfa=a, tnum=True)
            texto(c, "HOY", x1 - 20, y0 + 165, F(800, 30), "#FFE9C0", alinear="d", alfa=a)
            for k in range(10):
                x = x0 + 50 + k * 86; izq = k == 6; ak = aparece(t - ta - .1 * k, .15) * a
                c.save(); c.translate(x, y0 - 30); c.scale(-.38 if izq else .38, .38); c.rotate(-8 + 4 * k % 3)
                _glow(c, 0, 0, 160, "#FF8A3D" if izq else "#C9945A", .25 * ak)
                c.drawRRect(rrc(0, 30, 150, 150, 60), relleno("#C2410C" if izq else "#E9C9A0", .85 * ak))
                for j, (dx, L) in enumerate(((-52, 92), (-18, 110), (18, 104), (50, 84))): c.drawRRect(rrc(dx, -30 - L / 2 + 20, 34, L, 17), relleno("#C2410C" if izq else "#E9C9A0", .85 * ak))
                c.save(); c.translate(70, 30); c.rotate(48); c.drawRRect(rrc(0, -40, 36, 86, 18), relleno("#C2410C" if izq else "#E9C9A0", .85 * ak)); c.restore()
                c.restore()
            _pill(self, c, s.get("anios_txt", "MÁS DE 10.000 AÑOS"), CX, 600, S, a, fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- cerebro y genes
    def e_cerebro_z(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tl, tg, tq, tgn = _tw(self, e, "lado_word"), _tw(self, e, "lenguaje_word"), _tw(self, e, "cuarta_word"), _tw(self, e, "genes_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#1A1440", "#0C0A22", "#05030E"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=33, n=40, col="#D9CCFF")
        ug = _io((t - tgn + .2) / .6)
        bx, by = CX, 520 - 120 * ug; bs = 1.0 - .3 * ug
        a0 = aparece(dt0 - .05, .2)
        if dt0 < 1.6:
            texto(c, "?", CX + 330, 260, F(900, 160), "#FFE15A", alfa=aparece(dt0, .15) * (1 - TI.clamp((dt0 - 1.3) / .3)))
        c.save(); c.translate(bx, by); c.scale(bs, bs)
        _glow(c, 0, 0, 420, "#7A4AE0", .25 * a0)
        ul = aparece(t - tl, .2) if t > tl else 0
        for sg in (-1, 1):                                                       # dos hemisferios vistos desde arriba
            hp = skia.Path(); hp.moveTo(sg * 8, -280); hp.cubicTo(sg * 200, -290, sg * 270, -140, sg * 260, 20); hp.cubicTo(sg * 250, 200, sg * 150, 300, sg * 8, 290); hp.close()
            lit = ul if sg < 0 else 0
            c.drawPath(hp, _p(_rad(sg * 100, -60, 330, [_mix("#FFD0DC", "#FFE9A0", lit), _mix("#F49AB2", "#FFB45C", lit), _mix("#C2577A", "#C27A2A", lit)], [0, .6, 1], a0)))
            rng = np.random.default_rng(40 + sg)
            for k in range(10):
                x0 = sg * (30 + 200 * rng.random()); y0 = -230 + 460 * rng.random(); g_ = skia.Path(); g_.moveTo(x0, y0)
                for j in range(3): g_.quadTo(x0 + sg * (20 * j + 14), y0 + (22 if j % 2 else -22), x0 + sg * 20 * (j + 1), y0)
                c.drawPath(g_, trazo("#8A2A4A", 5, .35 * a0))
            c.drawPath(hp, trazo("#8A2A4A", 4, .7 * a0))
        texto(c, "IZQ.", -140, 250, F(800, 30), "#FFFFFF", alfa=a0); texto(c, "DER.", 140, 250, F(800, 30), "#FFFFFF", alfa=a0)
        if t > tg - .1:
            a = aparece(t - tg + .1, .15)
            c.drawRRect(rrc(-140, -60, 170, 100, 40), relleno("#FFFFFF", a)); c.drawPath(skia.Path.Polygon([(-170, -14), (-140, -14), (-180, 20)], True), relleno("#FFFFFF", a))
            texto(c, "BLA BLA", -140, -62, F(800, 34), "#5A3A8A", alfa=a)
        c.restore()
        # cruce: lado izquierdo → mano derecha
        if ul > 0:
            hx, hy = 830, 900 - 120 * ug
            pth = skia.Path(); pth.moveTo(bx - 120 * bs, by + 60 * bs); pth.cubicTo(bx - 60, by + 330, hx - 300, hy + 40, hx - 60, hy)
            me = skia.PathMeasure(pth, False); sp = skia.Path(); me.getSegment(0, me.getLength() * TI.clamp((t - tl) / .8), sp, True)
            c.drawPath(sp, trazo("#FFE15A", 8, ul)); _glow(c, hx - 60, hy, 80, "#FFE15A", .4 * TI.clamp((t - tl - .7) / .2))
            c.save(); c.translate(hx, hy); c.scale(-1, 1); c.translate(-hx, -hy); _mano(c, hx, hy + 20, .8, 10 * math.sin(t * 3), "abierta", ul * (1 - ug), t); c.restore()
            _pill(self, c, s.get("mano_txt", "MANO DERECHA"), hx - 300, hy + 110, S, ul * (1 - ug), fondo="#7A4A05")
        if t > tg: _pill(self, c, s.get("lenguaje_txt", "LENGUAJE"), bx - 150 * bs, by - 330 * bs, S, aparece(t - tg, .15), fondo="#5A3A8A")
        # genes ≈ 1/4
        if ug > 0:
            dx_, dy_ = 260, 900
            for k in range(14):
                yy = dy_ - 160 + k * 24; ph = t * 1.6 + k * .55; x1 = dx_ + 50 * math.sin(ph); x2 = dx_ - 50 * math.sin(ph)
                c.drawLine(x1, yy, x2, yy, trazo(("#FF5A8A", "#5AC8FF", "#FFE15A", "#7CFF8A")[k % 4], 5, .8 * ug))
                c.drawCircle(x1, yy, 8, relleno("#FFFFFF", ug)); c.drawCircle(x2, yy, 8, relleno("#9FC3FF", ug))
            px_, py_ = 680, 900; R = 130
            c.drawCircle(px_, py_, R, relleno("#2A3456", ug)); c.drawCircle(px_, py_, R, trazo("#FFFFFF", 3, .5 * ug))
            sw = 90 * TI.clamp((t - tq + .1) / .5)
            c.drawArc(skia.Rect(px_ - R, py_ - R, px_ + R, py_ + R), -90, sw, True, relleno("#FFE15A", ug))
            texto(c, "≈ 1/4", px_ + 200, py_ - 40, F(800, 56), "#FFE15A", alfa=ug * aparece(t - tq, .15) if t > tq else 0)
            _pill(self, c, s.get("genes_txt", "GENES ≈ 1/4"), CX, 1100, S, ug, fondo="#1C3A6A")
        _franja(c)

    # ---------------------------------------------------------------- escuela de antes
    def e_escuela(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; to, ta, ts = _tw(self, e, "obliga_word"), _tw(self, e, "ata_word"), _tw(self, e, "siniestro_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#5A3A22", "#3A2414", "#1E1008"])))
        _glow(c, CX, 400, 600, "#FFB45C", .18)
        _polvo(c, t, 0, W, 100, 1150, .45, seed=43, n=40, col="#FFE0B0")
        # pizarra
        px0, px1, py0, py1 = 90, 950, 170, 560
        c.drawRect(skia.Rect(px0 - 20, py0 - 20, px1 + 20, py1 + 20), _p(_lin(py0, py1, ["#8A5A32", "#5A3A20"])))
        c.drawRect(skia.Rect(px0, py0, px1, py1), _p(_lin(py0, py1, ["#2A4A3A", "#1A3226"])))
        for k in range(6): c.drawLine(px0 + 40 + k * 140, py0 + 30, px0 + 100 + k * 140, py1 - 30, trazo("#FFFFFF", 3, .04))
        us = _io((t - ts + .1) / .4)
        lema = s.get("lema", "CON LA DERECHA"); nl = len(lema)
        if t > to - .3 and us < 1:
            k = int(nl * TI.clamp((t - to + .3) / .9)); a = 1 - us
            texto(c, lema[:k], CX, py0 + 120, F(800, 70, "Montserrat"), "#F4F2EC", alfa=.92 * a)
            if k >= nl: _check(c, CX + 330, py0 + 230, 1.2, TI.clamp((t - to - .7) / .3), "#F4F2EC", .8 * a); c.drawLine(CX - 300, py0 + 175, CX + 300, py0 + 178, trazo("#F4F2EC", 4, .6 * a))
        if us > 0:
            a = us
            texto(c, s.get("latin_txt", "SINISTER"), CX - 200, py0 + 110, F(800, 60, "Montserrat"), "#F4F2EC", alfa=a)
            texto(c, "= " + s.get("latin_sig", "IZQUIERDA"), CX + 170, py0 + 110, F(800, 52, "Montserrat"), "#FFE15A", alfa=a)
            c.drawLine(CX - 40, py0 + 175, CX - 40, py0 + 245, trazo("#F4F2EC", 5, a)); c.drawPath(skia.Path.Polygon([(CX - 56, py0 + 240), (CX - 24, py0 + 240), (CX - 40, py0 + 265)], True), relleno("#F4F2EC", a))
            texto(c, s.get("es_txt", "SINIESTRO"), CX - 40, py0 + 315, F(900, 76, "Montserrat"), "#FF8A7A", alfa=a * aparece(t - ts - .3, .15))
        # pupitre y niño
        kx, ky = 380, 900
        self.persona_t(c, kx, ky, .95, t, pose="de_pie", cara=("o" if t > to else "feliz"), a=1.0)
        c.drawRRect(rrc(kx + 20, ky + 40, 560, 40, 12), _p(_lin(ky + 20, ky + 60, ["#B07A4A", "#7A4A22"])))
        c.drawRect(skia.Rect(kx - 240, ky + 60, kx + 290, ky + 260), _p(_lin(ky + 60, ky + 260, ["#8A5A32", "#5A3A20"])))
        c.drawRect(skia.Rect(kx + 120, ky + 10, kx + 300, ky + 30), relleno("#FBF8F0"))
        # la mano derecha escribe torpe (lado izquierdo del dibujo: el niño mira a cámara)
        if t > to:
            ww = 8 * math.sin(t * 13)
            c.save(); c.translate(kx - 60, ky); c.scale(-1, 1); _mano(c, 0, 0, .55, 20 + ww, "lapiz", aparece(t - to, .15), t); c.restore()
            if t - to < 1.4: self.comic_t(c, "¡TAC!", kx - 240, ky - 330, 60, -8, .7 + .3 * resorte(t - to, 10, 14), 1 - TI.clamp((t - to - 1.1) / .3), "#FFE15A")
        # la izquierda, atada
        if t > ta - .2:
            a = aparece(t - ta + .2, .15); hx, hy = kx + 200, ky - 60
            _mano(c, hx, hy, .55, 30, "puño", a, t)
            ur = TI.clamp((t - ta) / .8)
            for k in range(int(4 * ur) + 1):
                c.drawOval(skia.Rect(hx - 50, hy + 40 + k * 18 - 10, hx + 50, hy + 40 + k * 18 + 10), trazo("#C9A24A", 8, a))
            c.drawLine(hx + 40, hy + 80, hx + 140, hy + 200, trazo("#C9A24A", 8, a))
        if dt0 > .3 and us < 1: _pill(self, c, s.get("epoca_txt", "ESPAÑA, FRANQUISMO"), CX, py0 + 200 if t < to - .3 else 650, S, aparece(dt0 - .3, .15) * (1 - us), fondo="#3A2414", grande=t < to - .3)
        if dt0 > .3 and t < to - .3:                                                # fecha en tiza mientras llega la frase
            texto(c, s.get("antes_txt", "LA ESCUELA DE ANTES"), CX, py0 + 100, F(800, 64, "Montserrat"), "#F4F2EC", alfa=.85 * aparece(dt0 - .3, .2) * TI.clamp((to - .3 - t) / .2))
        _franja(c)
    def _check(c, x, y, s, u, col="#2ED47A", a=1.0):
        pk = skia.Path(); pk.moveTo(x - 22 * s, y); pk.lineTo(x - 6 * s, y + 18 * s); pk.lineTo(x + 26 * s, y - 22 * s)
        me = skia.PathMeasure(pk, False); sp = skia.Path(); me.getSegment(0, me.getLength() * TI.clamp(u), sp, True); c.drawPath(sp, trazo(col, 10 * s, a))

    # ---------------------------------------------------------------- duelo de esgrima
    def _tirador(c, x, y, s, lado, t, a, col, estoc=0.0):
        """Tirador de esgrima. lado = +1 mira a la derecha. estoc 0–1: se tira a fondo."""
        c.save(); c.translate(x + lado * 90 * estoc, y); c.scale(s * lado, s)
        bob = 6 * math.sin(t * 4)
        c.drawLine(-30, 60, -90 - 40 * estoc, 230, trazo("#F4F6FA", 34, a)); c.drawLine(30, 60, 80 + 60 * estoc, 230, trazo("#F4F6FA", 34, a))
        for xx in (-90 - 40 * estoc, 80 + 60 * estoc): c.drawRRect(rrc(xx + 10, 240, 70, 26, 12), relleno("#2A2F44", a))
        c.drawRRect(rrc(0, -20 + bob, 120, 170, 46), _p(_linx(-60, 60, ["#FFFFFF", "#E2E7F0", "#C9D0DE"], a)))
        c.drawLine(-8, -80 + bob, -8, 60 + bob, trazo(col, 8, a))
        c.drawCircle(0, -150 + bob, 52, _p(_rad(-14, -160, 60, ["#5A6478", "#2A2F44"], None, a)))
        for k in range(5): c.drawLine(-30 + 15 * k, -190 + bob, -30 + 15 * k, -110 + bob, trazo("#8A94A8", 2, .6 * a))
        c.drawRRect(rrc(0, -90 + bob, 90, 30, 12), relleno("#F4F6FA", a))
        # brazo del arma y florete
        ax, ay = 50, -60 + bob
        hx, hy = ax + 110 + 70 * estoc, ay + 10 - 20 * estoc
        c.drawLine(ax, ay, hx, hy, trazo("#F4F6FA", 26, a)); c.drawCircle(hx, hy, 16, relleno(col, a))
        c.drawLine(hx, hy, hx + 260, hy - 30 + 30 * estoc, trazo("#DDE3EC", 5, a))
        c.drawLine(-50, -60 + bob, -110, -140 + bob, trazo("#F4F6FA", 24, a))
        c.restore()
    def e_pelea(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tg, te, tes = _tw(self, e, "golpe_word"), _tw(self, e, "estudios_word"), _tw(self, e, "esgrima_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2E62E6", "#1A3FB0", "#0A1E60"])))
        for k in range(6): c.drawCircle(CX, 640, 180 + 130 * k + 20 * math.sin(t * .7 + k), trazo("#FFFFFF", 2, .06))
        ue = _io((t - te + .2) / .6)
        c.save(); c.translate(0, 260 * ue); s_ = 1 - .3 * ue; c.translate(CX, 640); c.scale(s_, s_); c.translate(-CX, -640)
        c.drawRect(skia.Rect(40, 880, 1000, 920), relleno("#DDE3EC", .8)); c.drawLine(CX, 870, CX, 930, trazo("#E5322D", 4))
        est = _io((t - tg + .1) / .3) * (1 - _io((t - tg - .9) / .4))
        _tirador(c, 300, 640, 1.0, 1, t, 1.0, "#FF8A3D", estoc=est)          # zurdo (en espejo: el arma en la izquierda)
        _tirador(c, 760, 640, 1.0, -1, t + 1.3, 1.0, "#5AC8FF", estoc=0)
        if 0 < t - tg < 1.2:
            self.comic_t(c, "¡TOCADO!", 700, 380, 74, 8, .7 + .3 * resorte(t - tg - .2, 10, 14), aparece(t - tg - .2, .1) * (1 - TI.clamp((t - tg - .9) / .3)), "#FFE15A")
            _glow(c, 690, 560, 120, "#FFFFFF", .6 * aparece(t - tg - .2, .05) * (1 - TI.clamp((t - tg - .5) / .3)))
        c.restore()
        texto(c, "ZURDO", 300, 220 + 0, F(800, 36), "#FFB45C", alfa=aparece(dt0 - .3, .15) * (1 - ue)); texto(c, "DIESTRO", 760, 220, F(800, 36), "#BFE6FF", alfa=aparece(dt0 - .3, .15) * (1 - ue))
        # más peleas → más zurdos + barras
        if ue > 0:
            a = ue
            gx0, gy0, gx1, gy1 = 110, 230, 470, 560
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(gx0 - 30, gy0 - 40, gx1 + 30, gy1 + 50), 24, 24), relleno("#0B1430", .7 * a))
            c.drawLine(gx0, gy1, gx1, gy1, trazo("#FFFFFF", 3, a)); c.drawLine(gx0, gy1, gx0, gy0, trazo("#FFFFFF", 3, a))
            rng = np.random.default_rng(7)
            for k in range(9):
                q = (k + .5) / 9; xx = gx0 + 20 + (gx1 - gx0 - 40) * q; yy = gy1 - 30 - (gy1 - gy0 - 60) * (q * .8 + .2 * rng.random())
                c.drawCircle(xx, yy, 10, relleno("#FFB45C", a * aparece(t - te - .1 * k, .1)))
            c.drawLine(gx0 + 20, gy1 - 40, gx1 - 20, gy0 + 40, trazo("#FFE15A", 4, .7 * a * TI.clamp((t - te - .9) / .3)))
            texto(c, "PELEAS →", (gx0 + gx1) / 2, gy1 + 30, F(800, 22), "#AFC3EE", alfa=a); c.save(); c.translate(gx0 - 22, (gy0 + gy1) / 2); c.rotate(-90); texto(c, "ZURDOS →", 0, 0, F(800, 22), "#AFC3EE", alfa=a); c.restore()
            if t > tes - .2:
                ab = aparece(t - tes + .2, .15); bx0, by1 = 600, 560
                for k, (txt, pct, col) in enumerate(((s.get("calle_txt", "GENTE"), s.get("calle_pct", 10), "#9FC3FF"), (s.get("esgrima_txt", "ESGRIMA"), s.get("esgrima_pct", 22), "#FFB45C"))):
                    hh = 12 * pct * TI.cubic_out(TI.clamp((t - tes - .2 * k) / .8)); x = bx0 + k * 180
                    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 60, by1 - hh, x + 60, by1), 12, 12), _p(_lin(by1 - hh, by1, [col, _mix(col, "#000000", .3)], ab)))
                    texto(c, f"≈{pct} %" if k else f"{pct} %", x, by1 - hh - 34, F(800, 36), "#FFFFFF", alfa=ab)
                    texto(c, txt, x, by1 + 34, F(800, 20 if k else 24), "#FFFFFF", alfa=ab)
            _pill(self, c, s.get("mas_txt", "MÁS PELEAS → MÁS ZURDOS"), 290, 175, S, a, fondo="#7A4A05", grande=False)
        _franja(c)

    # ---------------------------------------------------------------- el equilibrio
    def e_equilibrio(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tm, tp, t0_ = _tw(self, e, "mitad_word"), _tw(self, e, "pocos_word"), _tw(self, e, "cero_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0B1530", "#071026", "#050A18"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=53, n=40, col="#6EA0FF")
        pct = .10 + .40 * _io((t - tm + .2) / .8) - .38 * _io((t - tp + .1) / .8)
        pct = max(pct, .1 if t < tp else .07)
        if t > t0_ - .3: pct = max(pct, .07 + .03 * abs(math.sin((t - t0_) * 5)) * math.exp(-(t - t0_) * 2))
        sor = max(0.0, 1 - (pct - .1) / .4) if pct > .1 else 1.0
        # multitud de 40 personitas: las zurdas en naranja
        n = 40; nz = int(round(pct * n))
        for k in range(n):
            col_, fila = k % 10, k // 10; x = 110 + col_ * 92; y = 260 + fila * 120
            z = k in set(int(j * n / max(1, nz)) for j in range(nz)) if nz else False
            _persona(c, x, y, .5, "#FF8A3D" if z else "#4A6AB8", aparece(dt0 - .02 * k, .1))
        # deslizador
        sx0, sx1, sy = 120, 920, 790
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx0, sy - 12, sx1, sy + 12), 12, 12), relleno("#2A3456"))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx0, sy - 12, sx0 + (sx1 - sx0) * pct, sy + 12), 12, 12), relleno("#FF8A3D"))
        kx = sx0 + (sx1 - sx0) * pct; c.drawCircle(kx, sy, 30, relleno("#FFFFFF")); c.drawCircle(kx, sy, 30, trazo("#FF8A3D", 5))
        texto(c, f"{int(round(pct * 100))} %", kx, sy - 62, F(800, 40), "#FFFFFF", tnum=True)
        texto(c, s.get("zurdos_txt", "ZURDOS"), sx0, sy + 50, F(800, 26), "#AFC3EE", alinear="i", tracking=.15)
        for v in (0, 50, 100): texto(c, f"{v}", sx0 + (sx1 - sx0) * v / 100, sy + 50, F(700, 22), "#6A7AA8")
        # medidor de sorpresa
        gx, gy, R = CX, 1010, 120
        c.drawArc(skia.Rect(gx - R, gy - R, gx + R, gy + R), 180, 180, False, trazo("#2A3456", 26))
        c.drawArc(skia.Rect(gx - R, gy - R, gx + R, gy + R), 180, 180 * sor, False, trazo(_mix("#E5322D", "#FFE15A", sor), 26))
        an = math.pi + math.pi * sor; c.drawLine(gx, gy, gx + (R - 20) * math.cos(an), gy + (R - 20) * math.sin(an), trazo("#FFFFFF", 7)); c.drawCircle(gx, gy, 12, relleno("#FFFFFF"))
        texto(c, s.get("sorpresa_txt", "SORPRESA"), gx, gy - R - 40, F(800, 30), "#FFE15A", tracking=.15)
        if t > tm + .6 and t < tp: _pill(self, c, "YA NO SORPRENDE", gx + 270, gy - 40, S, aparece(t - tm - .6, .15) * TI.clamp((tp - t) / .2), fondo="#8A1A0A", grande=False)
        if t > t0_: _pill(self, c, s.get("cero_txt", "POCOS, PERO NUNCA CERO"), CX, 180, S, aparece(t - t0_, .15), fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_zurdo(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "reves":
            if s.get("modo") == "gancho":
                if g("mano_word") is not None: sf(g("mano_word") - .2, "pop", .6); sf(g("mano_word") + .1, "aleteo", .4)
                if g("flip_word") is not None: sf(g("flip_word") - .15, "flip", 1.0); sf(g("flip_word") + .55, "golpe", .4)
            else:
                if g("arma_word") is not None: sf(g("arma_word") - .2, "campana", .7); sf(g("arma_word") + .1, "destello", .5)
                if g("tijeras_word") is not None: sf(g("tijeras_word") - .1, "tijeretazo", 1.0); sf(g("tijeras_word") + .25, "tijeretazo", .7); sf(g("tijeras_word") + .5, "bajada", .4)
        if tp == "objetos":
            for it in s.get("items", []):
                tt = Tw(it["word"]) - .25; sf(tt, "desliz", .5)
                n = {"tijeras": "tijeretazo", "espiral": "ay", "tinta": "rotulador", "pupitre": "tac"}[it["tipo"]]
                sf(tt + (.6 if it["tipo"] == "espiral" else .35), n, .8)
        if tp == "diez":
            for k in range(10): sf(e["t0"] + .05 * k, "tic", .25)
            if g("uno_word") is not None: sf(g("uno_word"), "pop", .7); sf(g("uno_word") + .2, "destello", .5)
            if g("anios_word") is not None: self.rodillo(g("anios_word"), 1.2); sf(g("anios_word") - .2, "whoosh", .5)
        if tp == "cerebro_z":
            sf(e["t0"] + .1, "pop", .5)
            if g("lado_word") is not None: sf(g("lado_word"), "zumbido", .5); sf(g("lado_word") + .7, "pop", .5)
            if g("lenguaje_word") is not None: sf(g("lenguaje_word") - .1, "mensaje", .6)
            if g("genes_word") is not None: sf(g("genes_word") - .2, "whoosh", .4)
            if g("cuarta_word") is not None: sf(g("cuarta_word") - .1, "rotulador", .6)
        if tp == "escuela":
            if g("obliga_word") is not None: sf(g("obliga_word") - .3, "tiza", .9); sf(g("obliga_word") + .05, "tac", .9)
            if g("ata_word") is not None: sf(g("ata_word"), "cuerda", 1.0)
            if g("siniestro_word") is not None: sf(g("siniestro_word") - .1, "tiza", .8); sf(g("siniestro_word") + .3, "golpe", .4)
        if tp == "pelea":
            sf(e["t0"] + .2, "espada", .5)
            if g("golpe_word") is not None: sf(g("golpe_word") - .1, "whoosh", .6); sf(g("golpe_word") + .2, "espada", 1.0); sf(g("golpe_word") + .3, "golpe", .5)
            if g("estudios_word") is not None:
                for j in range(5): sf(g("estudios_word") + .1 + .12 * j, "pop", .35)
            if g("esgrima_word") is not None: sf(g("esgrima_word") - .2, "subida", .6); sf(g("esgrima_word") + .6, "pop", .5)
        if tp == "equilibrio":
            sf(e["t0"] + .1, "barrido", .4)
            if g("mitad_word") is not None: sf(g("mitad_word") - .2, "subida", .6); sf(g("mitad_word") + .6, "bajada", .6)
            if g("pocos_word") is not None: sf(g("pocos_word") - .1, "bajada", .5); sf(g("pocos_word") + .7, "pop", .5)
            if g("cero_word") is not None: sf(g("cero_word"), "boing", .7)

    for k, fn in (("reves", e_reves), ("objetos", e_objetos), ("diez", e_diez), ("cerebro_z", e_cerebro_z), ("escuela", e_escuela),
                  ("pelea", e_pelea), ("equilibrio", e_equilibrio)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_zurdo)
