"""Escenas del documental 19 («Si tienes 20 años, ya has vivido la mitad de tu vida»: la ley de Paul Janet).

reloj_arena  reloj de arena de TU VIDA. gancho: la arena cae hasta la mitad (edad_word, mitad_word) y dos rótulos: los años que te
             quedan (tachado) / cómo los sientes (✓) en sientes_word. cierre: la mitad de abajo se apaga (ido_word) y la de arriba se
             enciende (otra_word, decides_word).
verano       playa con el protagonista de pequeño: el verano dura y dura (barra lenta); volando_word: calendario que vuela y barra rápida.
janet        retrato de 1877 (anio_word, nombre_word) y balanza: este año contra todo lo vivido (compara_word).
tarta        tarta de la vida con la porción de un año: pasos [{word, edad, txt}], corto_word (las porciones en fila).
cinta        tu vida como una cinta de años: igual → se estrecha (estrecha_word, ley de Janet con a0 y vida), recuerdos_word (antes de a0
             en gris), mitad_word (la mitad cae en √(a0·vida)).
memoria      corcho con las fotos de las primeras veces (fotos [{word, txt, icono: cole/viaje/beso}]); repetido_word / rutina_word:
             semana gris de días iguales que se encoge (encoge_word).
vacaciones   al vivirlas (reloj que corre, rapido_word) / al recordarlas (tira de fotos larguísima, largas_word).
nuevo        las primeras veces (items [{word, txt, icono: pin/ruta/guitarra}]) y la cinta del tiempo que se estira (estira_word).
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
    def s_arena():
        d = 1.2; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 191), 2500, 9000) * np.sin(np.pi * u) ** .5 * (1 + .3 * np.sin(2 * np.pi * 13 * u))
    def s_clonc():
        d = .4; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.tanh(1.8 * (np.sin(2 * np.pi * 180 * t) * np.exp(-t / .08) + .5 * np.sin(2 * np.pi * 410 * t) * np.exp(-t / .05)))
    def s_ola2():
        d = 1.0; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 192), 200, 3000) * np.sin(np.pi * u) ** 2
    def s_pagina():
        d = .18; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 193), 1500, 7000) * np.sin(np.pi * t / d) ** 2
    def s_boing():
        d = .6; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        f = 180 + 90 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / .2)
        return np.sin(2 * np.pi * np.cumsum(f) / AU.SR) * np.exp(-t / .25) * np.minimum(1, t / .005)
    def s_chincheta():
        d = .12; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * 1800 * t) * np.exp(-t / .015) + .5 * AU._banda(AU._ruido(n, 194), 800, 3000) * np.exp(-t / .01)
    def s_camara():
        d = .3; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = AU._banda(AU._ruido(n, 195), 1000, 6000) * np.exp(-t / .02)
        k = int(.12 * AU.SR); x[k:] += .8 * AU._banda(AU._ruido(n - k, 196), 1000, 6000) * np.exp(-t[:n - k] / .03); return x
    for nom, fn, db in (("arena", s_arena, -33), ("clonc", s_clonc, -25), ("ola2", s_ola2, -33), ("pagina", s_pagina, -31),
                        ("boing", s_boing, -27), ("chincheta", s_chincheta, -29), ("camara", s_camara, -29)):
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
    def _estrellas(c, t, a, seed=41, n=90, ymax=1100):
        rng = np.random.default_rng(seed)
        for k in range(n):
            x, y, r = rng.random() * W, rng.random() * ymax, .8 + 2 * rng.random()
            c.drawCircle(x, y, r, relleno("#FFFFFF", a * (.35 + .55 * rng.random()) * (.65 + .35 * math.sin(t * (1 + 2 * rng.random()) + k))))
    def _check(c, x, y, s, u, col="#2ED47A", a=1.0):
        pk = skia.Path(); pk.moveTo(x - 22 * s, y); pk.lineTo(x - 6 * s, y + 18 * s); pk.lineTo(x + 26 * s, y - 22 * s)
        me = skia.PathMeasure(pk, False); sp = skia.Path(); me.getSegment(0, me.getLength() * TI.clamp(u), sp, True); c.drawPath(sp, trazo(col, 10 * s, a))
    def _cruz(c, x, y, s, u, col="#FF4A4A", a=1.0):
        for k, (dx0, dy0, dx1, dy1) in enumerate(((-1, -1, 1, 1), (1, -1, -1, 1))):
            uu = TI.clamp(u * 2 - k)
            if uu > 0: c.drawLine(x + dx0 * 20 * s, y + dy0 * 20 * s, x + (dx0 + (dx1 - dx0) * uu) * 20 * s, y + (dy0 + (dy1 - dy0) * uu) * 20 * s, trazo(col, 9 * s, a))
    def _tachar(c, x0, x1, y, u, a=1.0):
        if u > 0: c.drawLine(x0, y, x0 + (x1 - x0) * TI.clamp(u), y + 4, trazo("#FF4A4A", 8, a))

    # ---------------------------------------------------------------- reloj de arena
    def _reloj(c, x, y, s, t, arriba, abajo, cae, a=1.0, col_ab="#FFC24A", col_ar="#FFC24A", brillo_ar=0.0):
        """arriba / abajo: fracción de arena (0–1) en cada bulbo; cae: chorro 0–1."""
        c.save(); c.translate(x, y); c.scale(s, s)
        _sombra(c, 0, 420, 260, 30, .35 * a)
        bul = lambda sg: skia.Path.Polygon([(-200, sg * 360), (200, sg * 360), (190, sg * 250), (120, sg * 110), (22, sg * 14), (-22, sg * 14), (-120, sg * 110), (-190, sg * 250)], True)
        for sg in (-1, 1):
            c.drawPath(bul(sg), relleno("#DDEBFF", .12 * a))
        # arena de arriba (se vacía desde arriba: el nivel baja)
        if arriba > 0:
            c.save(); c.clipPath(bul(-1), doAntiAlias=True)
            lvl = -14 - 346 * arriba ** .8
            c.drawRect(skia.Rect(-210, lvl, 210, 0), _p(_lin(lvl, 0, [_mix(col_ar, "#FFFFFF", .25), col_ar, _mix(col_ar, "#000000", .25)], a)))
            dip = skia.Path(); dip.moveTo(-60, lvl); dip.quadTo(0, lvl + 30, 60, lvl); dip.close(); c.drawPath(dip, relleno(_mix(col_ar, "#000000", .3), .5 * a))
            c.restore()
            if brillo_ar > 0: _glow(c, 0, -150, 260, col_ar, .35 * brillo_ar * a)
        # chorro
        if cae > 0:
            c.drawLine(0, 14, 0, 360 - 300 * abajo ** .8, trazo(col_ab, 6, .9 * cae * a))
            for k in range(8):
                yy = 20 + (k * 47 + t * 400) % (330 - 280 * abajo ** .8); c.drawCircle(2 * math.sin(k + t * 20), yy, 3, relleno("#FFFFFF", .5 * cae * a))
        # arena de abajo: montón
        if abajo > 0:
            c.save(); c.clipPath(bul(1), doAntiAlias=True)
            h = 300 * abajo ** .8; pk = skia.Path(); pk.moveTo(-210, 360); pk.lineTo(-210, 360 - h * .55); pk.quadTo(0, 360 - h * 1.3, 210, 360 - h * .55); pk.lineTo(210, 360); pk.close()
            c.drawPath(pk, _p(_lin(360 - h * 1.1, 360, [_mix(col_ab, "#FFFFFF", .2), col_ab, _mix(col_ab, "#000000", .3)], a)))
            c.restore()
        for sg in (-1, 1):
            c.drawPath(bul(sg), trazo("#FFFFFF", 5, .75 * a))
            c.drawLine(-150 * 1, sg * 300, -120, sg * 140, trazo("#FFFFFF", 8, .25 * a))
        for sg in (-1, 1):                                                      # tapas de madera y columnas
            c.drawRRect(rrc(0, sg * 385, 500, 50, 16), _p(_lin(sg * 385 - 25, sg * 385 + 25, ["#B07A4A", "#7A4A22", "#5A3416"], a)))
        for sx in (-1, 1):
            c.drawRRect(rrc(sx * 225, 0, 26, 730, 13), _p(_linx(sx * 225 - 13, sx * 225 + 13, ["#9A6A3A", "#C9945A", "#7A4A22"], a)))
        c.restore()
    def e_reloj_arena(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "gancho")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#1A1440", "#0C0A22", "#05030E"])))
        _estrellas(c, t, .7, seed=51, n=80)
        _glow(c, CX, 600, 520, "#5A3AB0", .3)
        rx, ry, rs = CX, 660, .95
        if modo == "gancho":
            te, tm, ts = _tw(self, e, "edad_word"), _tw(self, e, "mitad_word"), _tw(self, e, "sientes_word")
            u = _io((t - te + .1) / (tm - te + .4))
            ar, ab = 1 - .5 * u, .5 * u
            _reloj(c, rx, ry, rs, t, ar, ab, 1.0 if 0 < u < 1 else (.0 if u >= 1 else 0))
            # línea de la mitad
            if t > tm:
                a = aparece(t - tm, .15); pl = trazo("#FFFFFF", 3, .7 * a); pl.setPathEffect(skia.DashPathEffect.Make([14, 10], -t * 30))
                c.drawLine(rx - 330, ry, rx + 330, ry, pl)
                if t - tm < 1.0: self.comic_t(c, "¡MITAD!", rx + 150, ry - 430, 70, -8, .7 + .3 * resorte(t - tm, 10, 14), 1 - TI.clamp((t - tm - .75) / .25), "#FFE15A")
            if t > te: _pill(self, c, s.get("edad_txt", "20 AÑOS"), rx + 340, ry - 60, S, aparece(t - te, .15), fondo="#7A4A05")
            # dos rótulos: tachado / ✓
            tq = _tw(self, e, "sientes_word") - 2.2
            if t > tq:
                a1 = aparece(t - tq, .15); y1 = 215
                c.drawRRect(rrc(rx, y1, 640, 76, 38), relleno("#0B1430", .8 * a1)); texto(c, s.get("quedan_txt", ""), rx, y1, F(800, 32), "#AFC3EE", alfa=a1)
                w1 = ancho(s.get("quedan_txt", ""), F(800, 32)); _tachar(c, rx - w1 / 2 - 10, rx + w1 / 2 + 10, y1, TI.clamp((t - tq - .5) / .4), a1)
            if t > ts - .1:
                a2 = aparece(t - ts + .1, .15); y2 = 1110
                c.drawRRect(rrc(rx, y2, 560, 84, 42), relleno("#1E6A3A", .9 * a2)); texto(c, s.get("sientes_txt", ""), rx + 26, y2, F(800, 34), "#FFFFFF", alfa=a2)
                _check(c, rx - 230, y2 - 2, .9, TI.clamp((t - ts) / .35), "#FFFFFF", a2)
        else:
            ti, to, td = _tw(self, e, "ido_word"), _tw(self, e, "otra_word"), _tw(self, e, "decides_word")
            ui = _io((t - ti) / .5); uo = _io((t - to) / .5)
            _reloj(c, rx, ry, rs, t, .5, .5, .6 * (1 - ui), col_ab=_mix("#FFC24A", "#5A5A6A", ui), col_ar="#FFC24A", brillo_ar=uo * (.7 + .3 * math.sin(t * 4)))
            if t > to:
                rng = np.random.default_rng(5)
                for k in range(14):
                    ph = ((t - to) * .4 + rng.random()) % 1; an = rng.random() * math.tau; r = 120 + 260 * ph
                    c.drawCircle(rx + r * math.cos(an), ry - 180 + r * .6 * math.sin(an), 3 + 3 * (1 - ph), relleno("#FFE58A", (1 - ph) * uo))
            if t > ti: _pill(self, c, s.get("ido_txt", "YA SE HA IDO"), rx + 340, ry + 330, S, aparece(t - ti, .15), fondo="#3A3A4A")
            if t > td: _pill(self, c, s.get("decides_txt", "LA DECIDES TÚ"), rx, ry - 450, S, aparece(t - td, .15), fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- el verano eterno / el año que vuela
    MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    def e_verano(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tv = _tw(self, e, "volando_word")
        uv = _io((t - tv + .3) / .6)
        # cielo y mar
        c.drawRect(skia.Rect(-80, -80, W + 80, 700), _p(_lin(0, 700, [_mix("#4E9AF0", "#3A4A8A", uv), _mix("#BFE3FF", "#E9A07A", uv)])))
        sx_ = 200 + 500 * TI.clamp(dt0 / 14) if uv < 1 else 200 + 500 * TI.clamp(dt0 / 14)
        c.drawCircle(sx_, 400, 70, _p(_rad(sx_ - 20, 380, 80, ["#FFFFFF", "#FFE58A", "#FFB43A"], [0, .45, 1])))
        _glow(c, sx_, 400, 260, "#FFE9A0", .4)
        c.drawRect(skia.Rect(-80, 640, W + 80, 860), _p(_lin(640, 860, ["#2A8AD8", "#1A5AA8"])))
        for k in range(6):
            yy = 670 + k * 32; ph = t * (.6 + .1 * k) + k
            wv = skia.Path(); wv.moveTo(-80, yy)
            for xx in range(-80, W + 100, 40): wv.lineTo(xx, yy + 6 * math.sin(xx / 60 + ph))
            c.drawPath(wv, trazo("#FFFFFF", 3, .25))
        c.drawRect(skia.Rect(-80, 840, W + 80, H + 80), _p(_lin(840, H, ["#F6DFA8", "#E2C07A", "#B08A4A"])))
        rng = np.random.default_rng(3)
        for k in range(60): c.drawCircle(rng.random() * W, 860 + rng.random() * 900, 2 + 2 * rng.random(), relleno("#B08A4A", .35))
        # sombrilla y castillo de arena
        c.drawLine(800, 1100, 760, 760, trazo("#F4F6FA", 10))
        um = skia.Path(); um.moveTo(600, 800); um.quadTo(760, 600, 940, 760); um.close()
        c.drawPath(um, _p(_linx(600, 940, ["#E5322D", "#FFFFFF", "#E5322D", "#FFFFFF", "#E5322D"])))
        c.drawRect(skia.Rect(560, 1000, 680, 1080), relleno("#E2B060")); c.drawPath(skia.Path.Polygon([(560, 1000), (620, 950), (680, 1000)], True), relleno("#D9A050"))
        # el protagonista de pequeño
        ak = 1 - uv
        if ak > 0: self.persona_t(c, 330, 900, 1.05, t, pose="de_pie", cara="feliz", a=ak)
        # barra de duración
        bx0, bx1, by = 120, 920, 200
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx0, by - 22, bx1, by + 22), 22, 22), relleno("#0B1430", .55))
        if uv < 1:
            ul = TI.clamp(dt0 / 30)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx0, by - 22, bx0 + (bx1 - bx0) * max(.04, ul), by + 22), 22, 22), relleno("#FFE15A", 1 - uv))
            _pill(self, c, s.get("verano_txt", "UN VERANO"), CX, by - 70, S, aparece(dt0 - .2, .15) * (1 - uv), fondo="#7A4A05")
            texto(c, f"DÍA {1 + int(dt0 * .8)}", bx1 - 70, by + 60, F(800, 30), "#FFFFFF", alfa=(1 - uv) * aparece(dt0 - .5, .2))
        if uv > 0:
            ua = TI.clamp((t - tv) / 1.2)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx0, by - 22, bx0 + (bx1 - bx0) * max(.04, ua), by + 22), 22, 22), relleno("#FF5A8A", uv))
            _pill(self, c, s.get("anio_txt", "UN AÑO"), CX, by - 70, S, uv, fondo="#8A1A3A")
            # adulto que mira el calendario volar
            self.cara_b(c, 330, 760, .9, t, cob=.55, largo=3, parches=.3, expr="o", mira=(.6, -.3), a=uv)
            cx_, cy_ = 760, 520
            c.drawRRect(rrc(cx_, cy_, 280, 300, 20), _p(_lin(cy_ - 150, cy_ + 150, ["#FFFFFF", "#E2E7F0"], uv)))
            c.drawRRect(rrc(cx_, cy_ - 120, 280, 60, 16), relleno("#E5322D", uv))
            km = int((t - tv) * 9)
            texto(c, MESES[min(11, km) % 12], cx_, cy_ - 120, F(800, 34), "#FFFFFF", alfa=uv)
            texto(c, str(1 + (km * 7) % 28), cx_, cy_ + 30, F(800, 120), "#1C2340", alfa=uv, tnum=True)
            for j in range(6):                                                 # hojas que salen volando
                ph = ((t - tv) * 1.6 + j / 6) % 1
                if t - tv < j / 6 / 1.6: continue
                c.save(); c.translate(cx_ + 300 * ph + 40 * j, cy_ - 60 - 500 * ph * ph); c.rotate(200 * ph + 30 * j)
                c.drawRect(skia.Rect(-80, -90, 80, 90), relleno("#FFFFFF", (1 - ph) * uv)); c.drawRect(skia.Rect(-80, -90, 80, -60), relleno("#E5322D", (1 - ph) * uv))
                c.restore()
        _franja(c)

    # ---------------------------------------------------------------- Paul Janet
    def _filosofo(c, x, y, s, t, a=1.0):
        P = ("#F6E2CC", "#E0BC98", "#B88A64")
        c.save(); c.translate(x, y); c.scale(s, s)
        c.drawPath(skia.Path.Polygon([(-170, 330), (-150, 160), (-60, 120), (60, 120), (150, 160), (170, 330)], True), _p(_lin(120, 330, ["#3A3026", "#1A140E"], a)))
        c.drawPath(skia.Path.Polygon([(-40, 120), (40, 120), (0, 230)], True), relleno("#F4EEE0", a))
        c.drawPath(skia.Path.Polygon([(-24, 126), (24, 126), (0, 150)], True), relleno("#1A140E", a))
        c.drawOval(skia.Rect(-100, -130, 100, 110), _p(_rad(-30, -50, 170, P, [0, .6, 1], a)))
        bd = skia.Path(); bd.moveTo(-96, -10); bd.cubicTo(-110, 140, -40, 200, 0, 210); bd.cubicTo(40, 200, 110, 140, 96, -10); bd.cubicTo(60, 50, -60, 50, -96, -10); bd.close()
        c.drawPath(bd, _p(_lin(-10, 210, ["#F2F2F2", "#C9C9D0"], a)))
        for k in range(7): c.drawLine(-70 + k * 23, 30, -50 + k * 17, 180, trazo("#AEB0B8", 2, .5 * a))
        c.drawPath(skia.Path.Polygon([(-60, 40), (0, 26), (60, 40), (40, 56), (0, 48), (-40, 56)], True), relleno("#E2E2E6", a))
        hp = skia.Path(); hp.moveTo(-100, -40); hp.cubicTo(-110, -120, -60, -130, -40, -126); hp.lineTo(-90, -40); hp.close(); c.drawPath(hp, relleno("#E9E9EE", a))
        hp2 = skia.Path(); hp2.moveTo(100, -40); hp2.cubicTo(110, -120, 60, -130, 40, -126); hp2.lineTo(90, -40); hp2.close(); c.drawPath(hp2, relleno("#E9E9EE", a))
        for sx in (-1, 1):
            c.drawCircle(sx * 38, -26, 9, relleno("#2A1A12", a)); c.drawLine(sx * 20, -54, sx * 58, -50, trazo("#D9D9DE", 8, a))
            c.drawCircle(sx * 38, -26, 20, trazo("#8A6A3A", 3, .8 * a))
        c.drawLine(-18, -26, 18, -26, trazo("#8A6A3A", 3, .8 * a))
        c.restore()
    def e_janet(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; ty, tn, tc = _tw(self, e, "anio_word"), _tw(self, e, "nombre_word"), _tw(self, e, "compara_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#5A3A22", "#3A2414", "#1E1008"])))
        _glow(c, CX, 500, 560, "#FFB45C", .22)
        _polvo(c, t, 0, W, 100, 1150, .5, seed=61, n=40, col="#FFE0B0")
        uc = _io((t - tc + .2) / .7)
        # retrato en marco ovalado (sube y se encoge cuando llega la balanza)
        px, py, ps = CX, 560 - 290 * uc, 1.0 - .45 * uc
        ar = aparece(dt0 - .05, .25)
        c.save(); c.translate(px, py); c.scale(ps, ps)
        _sombra(c, 10, 20, 230, 290, .4 * ar)
        c.drawOval(skia.Rect(-250, -310, 250, 310), _p(_lin(-310, 310, ["#E3B53C", "#8A6A22", "#E3B53C"], ar)))
        c.drawOval(skia.Rect(-222, -282, 222, 282), _p(_rad(0, -60, 320, ["#E9D9B8", "#B8A07A"], None, ar)))
        c.save(); c.clipPath(skia.Path.Oval(skia.Rect(-222, -282, 222, 282)), doAntiAlias=True); _filosofo(c, 0, 10, 1.15, t, ar); c.restore()
        c.restore()
        if t > ty: _pill(self, c, s.get("anio_txt", "1877"), px + 230 * ps, py - 260 * ps, S, aparece(t - ty, .15), fondo="#7A4A05")
        if t > tn: _pill(self, c, s.get("nombre_txt", "PAUL JANET"), px, py + 330 * ps, S, aparece(t - tn, .15) * (1 - uc) + uc * aparece(t - tn, .15), fondo="#3A2414")
        # balanza: este año contra todo lo vivido
        if uc > 0:
            a = uc; bx, by = CX, 700
            ang = -14 * _io((t - tc) / 1.0)
            c.drawRRect(rrc(bx, by + 260, 260, 40, 14), _p(_lin(by + 240, by + 280, ["#E3B53C", "#8A6A22"], a)))
            c.drawRect(skia.Rect(bx - 12, by, bx + 12, by + 250), _p(_linx(bx - 12, bx + 12, ["#8A6A22", "#E3B53C", "#8A6A22"], a)))
            c.save(); c.translate(bx, by); c.rotate(ang)
            c.drawRRect(rrc(0, 0, 700, 20, 10), _p(_lin(-10, 10, ["#F2D27A", "#8A6A22"], a))); c.drawCircle(0, 0, 18, relleno("#E3B53C", a))
            ends = [(-330, 0), (330, 0)]
            c.restore()
            r = math.radians(ang)
            for k, (ex, ey) in enumerate(ends):
                X = bx + ex * math.cos(r) - ey * math.sin(r); Y = by + ex * math.sin(r) + ey * math.cos(r)
                c.drawLine(X, Y, X - 90, Y + 160, trazo("#C9A24A", 3, a)); c.drawLine(X, Y, X + 90, Y + 160, trazo("#C9A24A", 3, a))
                c.drawArc(skia.Rect(X - 110, Y + 120, X + 110, Y + 200), 0, 180, True, _p(_lin(Y + 120, Y + 200, ["#F2D27A", "#8A6A22"], a)))
                if k == 0:     # este año: un bloque pequeño
                    c.drawRRect(rrc(X, Y + 130, 70, 50, 8), _p(_lin(Y + 105, Y + 155, ["#FF8A9A", "#C0392B"], a)))
                    _pill(self, c, s.get("nuevo_txt", "ESTE AÑO"), X, Y + 250, S, a, fondo="#8A1A3A", grande=False)
                else:          # todo lo vivido: pila de bloques
                    n = 2 + int(14 * TI.clamp((t - tc) / 1.6))
                    for j in range(n):
                        c.drawRRect(rrc(X + 8 * math.sin(j * 1.7), Y + 130 - j * 26, 150, 24, 6), _p(_lin(Y + 118 - j * 26, Y + 142 - j * 26, [_mix("#7FD3FF", "#3A6AE0", j / 16), "#1A3FB0"], a)))
                    _pill(self, c, s.get("vivido_txt", "TODO LO VIVIDO"), X - 40, Y + 250, S, a, fondo="#1C3A6A", grande=False)
        _franja(c)

    # ---------------------------------------------------------------- tarta de la vida
    def e_tarta(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; pasos = s.get("pasos", []); tco = _tw(self, e, "corto_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0B1530", "#071026", "#050A18"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=71, n=40, col="#6EA0FF")
        ts_ = [self.ta(p["word"], e) for p in pasos]
        k = max([i for i, tt in enumerate(ts_) if t >= tt - .15] or [0])
        p = pasos[k]; fr = 1 / p["edad"]
        fr0 = 1 / pasos[k - 1]["edad"] if k > 0 else fr
        u = _io((t - ts_[k] + .15) / .6) if k > 0 else 1
        f = fr0 + (fr - fr0) * u
        ed = pasos[k - 1]["edad"] + (p["edad"] - pasos[k - 1]["edad"]) * TI.cubic_out(TI.clamp((t - ts_[k] + .15) / .6)) if k > 0 else p["edad"]
        uco = _io((t - tco + .1) / .6)
        px, py, R = CX, 600 - 120 * uco, 300 * (1 - .35 * uco)
        a0 = aparece(dt0 - .05, .2)
        _sombra(c, px, py + R + 20, R * .8, 26, .35 * a0)
        c.drawCircle(px, py, R + 12, _p(_lin(py - R, py + R, ["#F6D9A8", "#C98A4A"], a0)))
        c.drawCircle(px, py, R, _p(_rad(px - R * .3, py - R * .3, R * 1.4, ["#FFF0D0", "#F2C98A", "#D9A060"], [0, .6, 1], a0)))
        for j in range(24): c.drawCircle(px + R * .75 * math.cos(j * .7 + 1), py + R * .75 * math.sin(j * 1.3), 4, relleno("#FF6A8A", .6 * a0))
        # porción de un año
        sw = 360 * f; st = -90 - sw / 2
        rect = skia.Rect(px - R, py - R, px + R, py + R)
        lift = 40 * (1 - math.exp(-6 * max(0, t - ts_[0] - .2)))
        mid = math.radians(st + sw / 2); ox, oy = lift * math.cos(mid), lift * math.sin(mid)
        c.drawArc(rect, st, 360 - 0, True, relleno("#000000", 0))
        c.save(); c.translate(ox, oy)
        c.drawArc(rect, st, sw, True, _p(_rad(px, py - R * .5, R, ["#FF8A9A", "#E5322D"], None, a0)))
        c.drawArc(rect, st, sw, True, trazo("#FFFFFF", 4, a0))
        c.restore()
        c.drawArc(rect, st + sw, 360 - sw, True, trazo("#FFFFFF", 2, .25 * a0))
        # edad y fracción
        a1 = aparece(dt0 - .2, .15) * (1 - uco)
        c.drawRRect(rrc(px, py + R + 120, 380, 120, 30), relleno("#FFFFFF", .95 * a1))
        texto(c, f"{int(round(ed))} " + s.get("edad_txt", "AÑOS"), px, py + R + 120, F(800, 60), "#1C2340", alfa=a1, tnum=True)
        _pill(self, c, "1 AÑO = " + p["txt"], px, py - R - 70, S, a1 * (1 - uco), fondo="#8A1A3A")
        # fila de tartas: cada vez más finas
        if uco > 0:
            for j, q in enumerate(pasos):
                xx = 200 + j * 320; yy = 900; r = 90
                c.drawCircle(xx, yy, r, _p(_rad(xx - 20, yy - 20, r * 1.3, ["#FFF0D0", "#D9A060"], None, uco)))
                ff = 1 / q["edad"]; c.drawArc(skia.Rect(xx - r, yy - r, xx + r, yy + r), -90 - 180 * ff, 360 * ff, True, relleno("#E5322D", uco))
                texto(c, f"{q['edad']} AÑOS", xx, yy + r + 34, F(800, 28), "#FFFFFF", alfa=uco)
                texto(c, q["txt"], xx, yy - r - 30, F(800, 30), "#FF8A9A", alfa=uco)
            for j in range(len(pasos) - 1):
                c.drawLine(200 + j * 320 + 110, 900, 200 + (j + 1) * 320 - 110, 900, trazo("#6EA0FF", 4, .6 * uco))
        _franja(c)

    # ---------------------------------------------------------------- la cinta de la vida
    COLS = ["#FF8A9A", "#FFB45C", "#FFE15A", "#7CFF8A", "#5AC8FF", "#9A7AFF"]
    def e_cinta(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tes, trc, tmi = _tw(self, e, "estrecha_word"), _tw(self, e, "recuerdos_word"), _tw(self, e, "mitad_word")
        a0_, L = s.get("a0", 4.5), s.get("vida", 80)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#F4F7FD", "#DCE6F6", "#B8C8E6"])))
        for k in range(30): c.drawLine(-80, k * 70, W + 80, k * 70, trazo("#9AAFD6", 1.5, .25))
        Y0, Y1, X0, X1 = 220, 1120, 170, 430
        ue = _io((t - tes + .1) / 1.4)
        ur = _io((t - trc) / .6)
        def ypos(age):
            lin = age / L
            lg = math.log(max(age, a0_) / a0_) / math.log(L / a0_)
            return Y0 + (Y1 - Y0) * (lin + (lg - lin) * ue)
        a = aparece(dt0 - .05, .3)
        for k in range(L):
            ya, yb = ypos(k), ypos(k + 1)
            if yb - ya < .2 and k > 10: pass
            col = COLS[k % len(COLS)]
            if k < a0_ and ur > 0: col = _mix(col, "#9AA4B8", ur)
            c.drawRect(skia.Rect(X0, ya, X1, max(yb, ya + .6)), _p(_linx(X0, X1, [_mix(col, "#FFFFFF", .3), col, _mix(col, "#000000", .15)], a)))
            if yb - ya > 10: c.drawLine(X0, yb, X1, yb, trazo("#FFFFFF", 2, .7 * a))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(X0 - 4, Y0 - 4, X1 + 4, Y1 + 4), 10, 10), trazo("#1C2340", 4, .8 * a))
        # edades a la derecha
        for ag in (0, 5, 10, 20, 30, 40, 60, 80):
            if ag == 0 and ue > .3: continue
            if ag == 30 and ue > .6: continue
            yy = ypos(ag); c.drawLine(X1 + 6, yy, X1 + 40, yy, trazo("#1C2340", 3, .8 * a))
            texto(c, f"{ag}", X1 + 50, yy, F(800, 34), "#1C2340", alinear="i", alfa=a, tnum=True)
        texto(c, "AÑOS", X1 + 50, Y0 - 50, F(800, 26), "#5A6A8A", alinear="i", alfa=a, tracking=.15)
        lbl = s.get("igual_txt") if ue < .5 else s.get("sentido_txt")
        _pill(self, c, lbl, X0 - 20 + 110, Y0 - 70, S, a, fondo="#1C2340" if ue < .5 else "#8A1A3A")
        # un año a los 5 contra un año a los 60 (corchete y grosor)
        if ue > .2:
            ab = _io((ue - .2) / .5)
            for k, (ag, txt, yo) in enumerate(((5, "UN AÑO A LOS 5", 0), (60, "UN AÑO A LOS 60", 0))):
                ya, yb = ypos(ag), ypos(ag + 1); yb0 = (ya + yb) / 2; ym_ = yb0 + (150 if k == 0 else 0)
                c.drawRect(skia.Rect(X0, ya, X1, max(yb, ya + 2)), trazo("#1C2340", 3, ab))
                c.drawLine(X1 + 6, yb0, X1 + 170, ym_, trazo("#1C2340", 2, .6 * ab))
                fx = X1 + 330
                c.drawRRect(rrc(fx, ym_, 300, max(8, (yb - ya) * 1.0) + 50, 14), relleno("#FFFFFF", .9 * ab))
                c.drawRect(skia.Rect(fx - 130, ym_ - max(2, (yb - ya)) / 2, fx + 130, ym_ + max(2, (yb - ya)) / 2), relleno(COLS[ag % len(COLS)], ab))
                texto(c, txt, fx, ym_ - max(2, (yb - ya)) / 2 - 18, F(800, 24), "#1C2340", alfa=ab)
        # primeros recuerdos
        if t > trc:
            yr = ypos(a0_); ar = aparece(t - trc, .15)
            c.drawLine(X0 - 60, yr, X1 + 10, yr, trazo("#7A4AE0", 5, ar))
            _pill(self, c, s.get("recuerdos_txt", "PRIMEROS RECUERDOS"), 760, yr + 40, S, ar, fondo="#5A3A8A", grande=False)
        # la mitad
        if t > tmi:
            am = aparece(t - tmi, .15); ym = (Y0 + Y1) / 2; amid = math.sqrt(a0_ * L)
            pl = trazo("#E5322D", 6, am); pl.setPathEffect(skia.DashPathEffect.Make([18, 10], -t * 30)); c.drawLine(X0 - 40, ym, X1 + 140, ym, pl)
            c.drawRect(skia.Rect(X0, Y0, X1, ym), relleno("#E5322D", .12 * am))
            ag18, ag20 = ypos(18), ypos(20)
            br = skia.Path(); br.moveTo(X1 + 150, ag18 - 6); br.lineTo(X1 + 170, ag18 - 6); br.lineTo(X1 + 170, ag20 + 6); br.lineTo(X1 + 150, ag20 + 6)
            c.drawPath(br, trazo("#E5322D", 5, am))
            c.drawRRect(rrc(X1 + 330, ym, 300, 150, 24), relleno("#FFFFFF", .95 * am)); c.drawRRect(rrc(X1 + 330, ym, 300, 150, 24), trazo("#E5322D", 4, am))
            texto(c, s.get("mitad_txt", "LA MITAD"), X1 + 330, ym - 40, F(800, 30), "#8A1A0A", alfa=am, tracking=.12)
            texto(c, "18–20", X1 + 330, ym + 22, F(800, 70), "#E5322D", alfa=am)
        c.drawRect(skia.Rect(-80, 1150, W + 80, H + 80), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1150), (0, 1290)], [color("#0B1430", 0), color("#0B1430", .92)])))   # fondo claro: franja oscura para leer
        _franja(c)

    # ---------------------------------------------------------------- memoria: fotos de las primeras veces y la rutina que se encoge
    def _icono(c, tipo, x, y, s, t, a=1.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        if tipo == "cole":
            c.drawRect(skia.Rect(-80, -20, 80, 70), relleno("#E5322D", a)); c.drawPath(skia.Path.Polygon([(-95, -20), (0, -80), (95, -20)], True), relleno("#7A1A12", a))
            c.drawRect(skia.Rect(-18, 20, 18, 70), relleno("#5A3A20", a)); c.drawCircle(0, -30, 14, relleno("#FFFFFF", a))
            for sx in (-1, 1): c.drawRect(skia.Rect(sx * 50 - 14, 0, sx * 50 + 14, 24), relleno("#BFE3FF", a))
            c.drawLine(60, -50, 60, -110, trazo("#2A2F44", 4, a)); c.drawPath(skia.Path.Polygon([(60, -110), (100, -98), (60, -86)], True), relleno("#FFE15A", a))
        elif tipo == "viaje":
            c.drawRRect(rrc(0, 20, 150, 110, 16), _p(_lin(-35, 75, ["#5AC8FF", "#2A6AE8"], a))); c.drawRRect(rrc(0, -40, 60, 24, 10), trazo("#2A2F44", 6, a))
            for k in (-40, 40): c.drawLine(k, -35, k, 75, trazo("#FFFFFF", 6, .6 * a))
            c.save(); c.translate(40 * math.sin(t), -110); c.rotate(-15)
            c.drawRRect(rrc(0, 0, 140, 22, 11), relleno("#FFFFFF", a)); c.drawPath(skia.Path.Polygon([(-10, 0), (20, -50), (40, 0)], True), relleno("#FFFFFF", a)); c.restore()
        elif tipo == "beso":
            for sx, col in ((-1, "#FFB45C"), (1, "#7A4AE0")):
                c.drawCircle(sx * 50, 10, 46, relleno("#F6CDAE", a)); c.drawArc(skia.Rect(sx * 50 - 48, -38, sx * 50 + 48, 40), 180, 180, True, relleno(col, a))
            hp = skia.Path(); hp.moveTo(0, -60); hp.cubicTo(-40, -100, -80, -50, 0, -10); hp.cubicTo(80, -50, 40, -100, 0, -60)
            sc = 1 + .12 * math.sin(t * 6); c.save(); c.translate(0, -50); c.scale(sc, sc); c.translate(0, 50); c.drawPath(hp, relleno("#FF4A6A", a)); c.restore()
        elif tipo == "pin":
            c.drawCircle(0, -30, 50, relleno("#E5322D", a)); c.drawPath(skia.Path.Polygon([(-42, -4), (42, -4), (0, 70)], True), relleno("#E5322D", a)); c.drawCircle(0, -30, 20, relleno("#FFFFFF", a))
        elif tipo == "ruta":
            pth = skia.Path(); pth.moveTo(-90, 60); pth.cubicTo(-90, -20, 90, 40, 90, -50)
            pl = trazo("#FFE15A", 8, a); pl.setPathEffect(skia.DashPathEffect.Make([16, 12], -t * 40)); c.drawPath(pth, pl)
            c.drawCircle(-90, 60, 14, relleno("#2ED47A", a)); c.drawPath(skia.Path.Polygon([(70, -70), (110, -50), (76, -26)], True), relleno("#FFE15A", a))
        elif tipo == "guitarra":
            c.save(); c.rotate(-30)
            c.drawCircle(0, 40, 50, relleno("#D9772A", a)); c.drawCircle(0, -10, 40, relleno("#D9772A", a)); c.drawCircle(0, 30, 16, relleno("#3A2010", a))
            c.drawRect(skia.Rect(-9, -130, 9, -10), relleno("#5A3A20", a)); c.drawRect(skia.Rect(-16, -160, 16, -128), relleno("#3A2010", a))
            for k in (-4, 0, 4): c.drawLine(k, -130, k, 60, trazo("#F4F6FA", 1.5, a))
            c.restore()
        c.restore()
    def _polaroid(c, x, y, rot, s, tipo, txt, t, a, F_):
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
        c.drawRect(skia.Rect(-130 + 8, -140 + 12, 130 + 8, 160 + 12), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
        c.drawRect(skia.Rect(-130, -140, 130, 160), relleno("#FBF8F0", a))
        c.drawRect(skia.Rect(-110, -120, 110, 90), _p(_lin(-120, 90, ["#BFE3FF", "#7FB0E0"], a)))
        c.save(); c.clipRect(skia.Rect(-110, -120, 110, 90)); _icono(c, tipo, 0, 0, .9, t, a); c.restore()
        texto(c, txt, 0, 125, F_(800, 18), "#3A2414", alfa=a)
        c.drawCircle(0, -132, 12, relleno("#E5322D", a)); c.drawCircle(-3, -135, 4, relleno("#FFFFFF", .7 * a))
        c.restore()
    def e_memoria(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; trp, tru, ten = _tw(self, e, "repetido_word"), _tw(self, e, "rutina_word"), _tw(self, e, "encoge_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#1A1440", "#0C0A22", "#05030E"])))
        # corcho
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(60, 170, 960, 1130), 24, 24), _p(_lin(170, 1130, ["#C9945A", "#A8743E"])))
        rng = np.random.default_rng(81)
        for k in range(260): c.drawCircle(70 + 880 * rng.random(), 180 + 940 * rng.random(), 1.5 + 2 * rng.random(), relleno("#7A4A22", .35))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(60, 170, 960, 1130), 24, 24), trazo("#5A3416", 14))
        # cerebro brillante (la memoria)
        am = aparece(dt0 - .1, .2) * (1 - _io((t - trp + .3) / .4) * .0)
        fotos = s.get("fotos", [])
        pos = [(270, 420, -6), (690, 430, 7), (480, 720, -3)]
        urep = _io((t - tru + .2) / .6); ue = _io((t - ten) / .8)
        for k, f in enumerate(fotos):
            tf = self.ta(f["word"], e) - .2
            if t < tf: continue
            u = resorte(t - tf, 9, 12); a = aparece(t - tf, .12)
            x, y, rot = pos[k % 3]
            dim = 1 - .55 * urep
            _polaroid(c, x, y - 120 * (1 - u) - 140 * urep, rot, (1.05 * u) * (1 - .25 * urep), f["icono"], f["txt"], t, a * dim, F)
        t1 = self.ta(fotos[0]["word"], e) - .2 if fotos else 1e9; tm_ = _tw(self, e, "memoria_word")
        at = aparece(dt0 - .1, .2) * (1 - _io((t - tm_ + .5) / .3))
        if at > 0:
            for k, (txt, ok_) in enumerate(((s.get("teoria_txt", "TEORÍA"), True), (s.get("ley_txt", "LEY EXACTA"), False))):
                yy_ = 520 + k * 200; u_ = resorte(dt0 - .1 - .9 * k, 8, 10); ak = at * aparece(dt0 - .1 - .9 * k, .15)
                c.drawRRect(rrc(CX, yy_, 560 * u_ + 1, 140, 30), relleno("#FBF8F0", ak)); c.drawRRect(rrc(CX, yy_, 560 * u_ + 1, 140, 30), trazo("#3A2414", 4, ak))
                texto(c, txt, CX - 50, yy_, F(800, 56), "#3A2414", alfa=ak)
                (_check if ok_ else _cruz)(c, CX + 200, yy_, 1.6, TI.clamp((dt0 - .4 - .9 * k) / .3), "#1E9A4A" if ok_ else "#E5322D", ak)
        ub = aparece(t - tm_ + .3, .25) * (1 - _io((t - t1 + .1) / .4)) if t > tm_ - .3 else 0
        if ub > 0:
            bx, by_ = CX, 640; sc = (.9 + .1 * resorte(t - tm_ + .3, 7, 9)) * (1 + .03 * math.sin(t * 3))
            _glow(c, bx, by_, 380, "#FFE15A", .25 * ub)
            c.save(); c.translate(bx, by_); c.scale(sc, sc)
            br = skia.Path(); br.moveTo(-260, 40); br.cubicTo(-300, -110, -200, -250, -30, -250); br.cubicTo(130, -265, 270, -180, 285, -30)
            br.cubicTo(300, 70, 240, 130, 160, 140); br.cubicTo(120, 190, 50, 200, 15, 165); br.cubicTo(-65, 205, -210, 180, -260, 40); br.close()
            c.drawPath(br, _p(_rad(-60, -110, 380, ["#FFD0DC", "#F49AB2", "#C2577A"], [0, .6, 1], ub)))
            rng = np.random.default_rng(12)
            for k in range(14):
                x0 = -250 + rng.random() * 500; y0 = -220 + rng.random() * 360; g_ = skia.Path(); g_.moveTo(x0, y0)
                for j in range(4): g_.quadTo(x0 + 25 * j + 16, y0 + (24 if j % 2 else -24), x0 + 25 * (j + 1) + 16, y0)
                c.drawPath(g_, trazo("#B04A6E", 5, .45 * ub))
            c.drawPath(br, trazo("#8A2A4A", 5, .8 * ub))
            for k in range(8):
                an = k * math.pi / 4 + t * .8; c.drawCircle(330 * math.cos(an), 260 * math.sin(an), 6, relleno("#FFE15A", .8 * ub))
            c.restore()
        # la semana de rutina: 7 días grises iguales que se encogen
        if t > tru - .2:
            ar = aparece(t - tru + .2, .2); n = 7; wd = 108 * (1 - .78 * ue); gap = 10 * (1 - .8 * ue)
            tot = n * wd + (n - 1) * gap; x0 = CX - tot / 2; yy = 930
            c.drawRRect(rrc(CX, yy, tot + 40, 200, 20), relleno("#0B0A14", .75 * ar))
            for k in range(n):
                x = x0 + k * (wd + gap) + wd / 2
                c.drawRRect(rrc(x, yy, wd, 160, 10), _p(_lin(yy - 80, yy + 80, ["#8A94A8", "#5A6478"], ar)))
                if wd > 40:
                    c.save(); c.translate(x, yy); s_ = wd / 108
                    c.drawRRect(rrc(0, 16 * s_, 70 * s_, 34 * s_, 6), relleno("#3A4258", ar)); c.drawRect(skia.Rect(-28 * s_, -40 * s_, 28 * s_, 0), relleno("#AEB8CA", ar))   # mesa y pantalla
                    c.restore()
            _pill(self, c, s.get("rutina_txt", "SEMANA DE RUTINA"), CX, yy - 130, S, ar, fondo="#3A3A4A")
            if t > ten and t - ten < 1.2: self.comic_t(c, "¡ÑIC!", CX + 270, yy - 200, 60, 8, .7 + .3 * resorte(t - ten, 10, 14), 1 - TI.clamp((t - ten - .9) / .3), "#FFE15A")
        _franja(c)

    # ---------------------------------------------------------------- vacaciones: al vivirlas / al recordarlas
    def e_vacaciones(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tr, tl = _tw(self, e, "rapido_word"), _tw(self, e, "largas_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2E62E6", "#1A3FB0", "#0A1E60"])))
        for k in range(6): c.drawCircle(CX, 640, 180 + 130 * k + 20 * math.sin(t * .7 + k), trazo("#FFFFFF", 2, .06))
        # maleta que entra
        a0 = aparece(dt0 - .05, .2); mx, my = CX, 330 + 30 * (1 - resorte(dt0, 8, 10))
        c.drawRRect(rrc(mx, my, 300, 210, 26), _p(_lin(my - 105, my + 105, ["#FFB45C", "#E07A1A"], a0)))
        c.drawRRect(rrc(mx, my - 125, 110, 40, 16), trazo("#7A3A0A", 10, a0))
        for k in (-80, 80): c.drawLine(mx + k, my - 100, mx + k, my + 100, trazo("#7A3A0A", 8, .5 * a0))
        for k, (dx, dy, col) in enumerate(((-60, -30, "#5AC8FF"), (50, 20, "#7CFF8A"), (-10, 50, "#FF8A9A"))):
            c.drawCircle(mx + dx, my + dy, 22, relleno(col, a0)); c.drawCircle(mx + dx, my + dy, 22, trazo("#FFFFFF", 3, a0))
        # al vivirlas: reloj que vuela
        if t > tr - .2:
            a = aparece(t - tr + .2, .15); cx_, cy_ = 260, 720
            c.drawCircle(cx_, cy_, 130, _p(_rad(cx_ - 30, cy_ - 30, 160, ["#FFFFFF", "#DCE6F6"], None, a))); c.drawCircle(cx_, cy_, 130, trazo("#1C2340", 6, a))
            for k in range(12):
                an = k * math.pi / 6; c.drawLine(cx_ + 105 * math.cos(an), cy_ + 105 * math.sin(an), cx_ + 120 * math.cos(an), cy_ + 120 * math.sin(an), trazo("#1C2340", 4, a))
            an1 = (t - tr) * 14; an2 = (t - tr) * 1.2
            c.drawLine(cx_, cy_, cx_ + 90 * math.cos(an1 - math.pi / 2), cy_ + 90 * math.sin(an1 - math.pi / 2), trazo("#E5322D", 6, a))
            c.drawLine(cx_, cy_, cx_ + 60 * math.cos(an2 - math.pi / 2), cy_ + 60 * math.sin(an2 - math.pi / 2), trazo("#1C2340", 9, a))
            for k in range(3): c.drawLine(cx_ - 150 - 20 * k, cy_ - 40 + 40 * k, cx_ - 200 - 40 * k, cy_ - 40 + 40 * k, trazo("#FFFFFF", 5, .6 * a))
            _pill(self, c, s.get("vivir_txt", "AL VIVIRLAS"), cx_, cy_ + 190, S, a, fondo="#0B1430")
        # al recordarlas: tira de fotos larguísima que se despliega
        if t > tl - 1.3:
            a = aparece(t - tl + 1.3, .15); ul = _io((t - tl + 1.3) / 1.0)
            x0, y0 = 600, 560; Lh = 560 * ul
            c.drawRect(skia.Rect(x0, y0, x0 + 300, y0 + Lh), relleno("#14141E", a))
            for k in range(int(Lh // 28)):
                c.drawRect(skia.Rect(x0 + 10, y0 + 8 + k * 28, x0 + 26, y0 + 22 + k * 28), relleno("#F4F6FA", a)); c.drawRect(skia.Rect(x0 + 274, y0 + 8 + k * 28, x0 + 290, y0 + 22 + k * 28), relleno("#F4F6FA", a))
            cols = ["#5AC8FF", "#FFB45C", "#7CFF8A", "#FF8A9A", "#FFE15A", "#9A7AFF"]
            for k in range(int(Lh // 120) + 1):
                yy = y0 + 14 + k * 120
                if yy + 100 > y0 + Lh: break
                c.drawRect(skia.Rect(x0 + 40, yy, x0 + 260, yy + 100), _p(_lin(yy, yy + 100, [cols[k % 6], _mix(cols[k % 6], "#000000", .3)], a)))
                c.drawCircle(x0 + 150 + 40 * math.sin(k), yy + 50, 22, relleno("#FFFFFF", .6 * a))
            _pill(self, c, s.get("recordar_txt", "AL RECORDARLAS"), x0 + 150, y0 - 50, S, a, fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- cosas nuevas que estiran el tiempo
    def e_nuevo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tes = _tw(self, e, "estira_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0B1530", "#071026", "#050A18"])))
        _polvo(c, t, 0, W, 100, 1150, .6, seed=91, n=50, col="#FFE15A")
        items = s.get("items", [])
        pos = [(250, 430), (CX + 260, 430), (CX, 790)]
        t1 = self.ta(items[0]["word"], e) - .15 if items else 1e9
        ub = aparece(dt0 - .1, .2) * (1 - _io((t - t1 + .2) / .4))
        if ub > 0:
            sc = (.6 + .4 * resorte(dt0 - .1, 8, 10)) * (1 + .04 * math.sin(t * 5)); c.save(); c.translate(CX, 600); c.rotate(-8 + 3 * math.sin(t * 2)); c.scale(sc, sc)
            st_ = skia.Path()
            for j in range(24):
                rr = 260 if j % 2 == 0 else 210; aa = j * math.pi / 12
                (st_.moveTo if j == 0 else st_.lineTo)(rr * math.cos(aa), rr * math.sin(aa))
            st_.close(); _glow(c, 0, 0, 360, "#FFE15A", .3 * ub)
            c.drawPath(st_, _p(_rad(-40, -40, 300, ["#FFF2A0", "#FFD24A", "#E0A21A"], None, ub))); c.drawPath(st_, trazo("#FFFFFF", 5, ub))
            texto(c, "¡NUEVO!", 0, 0, F(900, 92), "#7A1A12", alfa=ub)
            c.restore()
        ues = _io((t - tes + .1) / .5)
        for k, it in enumerate(items):
            ti = self.ta(it["word"], e) - .15
            if t < ti: continue
            u = resorte(t - ti, 9, 12); a = aparece(t - ti, .12) * (1 - .6 * ues)
            x, y = pos[k % 3]; y -= 30 * (1 - u)
            c.drawCircle(x, y, 140 * u, _p(_rad(x - 30, y - 30, 170, ["#2A3456", "#121830"], None, a))); c.drawCircle(x, y, 140 * u, trazo("#FFE15A", 4, a))
            _glow(c, x, y, 200, "#FFE15A", .15 * a)
            _icono(c, it["icono"], x, y, 1.1 * u, t, a)
            _pill(self, c, it["txt"], x, y + 185, S, a, fondo="#7A4A05")
        # la cinta del tiempo que se estira
        if t > tes - .1:
            a = aparece(t - tes + .1, .15); st = _io((t - tes) / .5); bo = math.exp(-(t - tes) * 4) * math.sin((t - tes) * 18) * .15 if t > tes else 0
            wb = 220 + 560 * st * (1 + bo); yb = 1090; xb0 = CX - wb / 2
            for k in range(12):
                x = xb0 + wb * k / 12; c.drawRect(skia.Rect(x, yb - 40, x + wb / 12 + 1, yb + 40), relleno(COLS[k % 6], a))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xb0, yb - 40, xb0 + wb, yb + 40), 12, 12), trazo("#FFFFFF", 4, a))
            for sx in (-1, 1):
                hx = CX + sx * (wb / 2 + 40)
                c.drawCircle(hx, yb, 40, relleno("#F6CDAE", a)); c.drawRRect(rrc(hx + sx * 50, yb, 70, 40, 18), relleno("#F6CDAE", a))
            if 0 < t - tes < 1.1: self.comic_t(c, "¡BOING!", CX - 280, yb - 150, 66, -6, .7 + .3 * resorte(t - tes, 10, 14), 1 - TI.clamp((t - tes - .8) / .3), "#FFE15A")
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_vida(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "reloj_arena":
            if s.get("modo") == "gancho":
                if g("edad_word") is not None: sf(g("edad_word") - .1, "arena", 1.0)
                if g("mitad_word") is not None: sf(g("mitad_word"), "clonc", 1.0)
                if g("sientes_word") is not None: sf(g("sientes_word") - 1.7, "rotulador", .6); sf(g("sientes_word"), "palomita", .8)
            else:
                if g("ido_word") is not None: sf(g("ido_word"), "bajada", .6)
                if g("otra_word") is not None: sf(g("otra_word"), "destello", .7)
                if g("decides_word") is not None: sf(g("decides_word"), "campana", .6)
        if tp == "verano":
            sf(e["t0"] + .1, "ola2", .8); sf(e["t0"] + 1.6, "pajaros", .5)
            if g("volando_word") is not None:
                tv = g("volando_word")
                for j in range(6): sf(tv + j * .16, "pagina", .6)
                sf(tv - .2, "whoosh", .5)
        if tp == "janet":
            sf(e["t0"] + .1, "pop", .4)
            if g("anio_word") is not None: sf(g("anio_word"), "pop", .5)
            if g("nombre_word") is not None: sf(g("nombre_word"), "camara", .7)
            if g("compara_word") is not None:
                sf(g("compara_word") - .2, "whoosh", .4)
                for j in range(6): sf(g("compara_word") + .2 + j * .22, "tac", .45)
                sf(g("compara_word") + 1.0, "golpe", .5)
        if tp == "tarta":
            sf(e["t0"] + .15, "pop", .5)
            for p in s.get("pasos", [])[1:]: sf(Tw(p["word"]) - .15, "desliz", .6); sf(Tw(p["word"]) + .3, "pop", .4)
            for p in s.get("pasos", []): self.rodillo(Tw(p["word"]) - .15, .6)
            if g("corto_word") is not None: sf(g("corto_word") - .1, "whoosh", .5)
        if tp == "cinta":
            sf(e["t0"] + .1, "barrido", .5)
            if g("estrecha_word") is not None: sf(g("estrecha_word") - .1, "bajada", .6)
            if g("recuerdos_word") is not None: sf(g("recuerdos_word"), "pop", .5)
            if g("mitad_word") is not None: sf(g("mitad_word"), "rotulador", .7); sf(g("mitad_word") + .3, "golpe", .5)
        if tp == "memoria":
            for f in s.get("fotos", []): sf(Tw(f["word"]) - .2, "camara", .7); sf(Tw(f["word"]) + .05, "chincheta", .6)
            if g("rutina_word") is not None: sf(g("rutina_word") - .2, "tic", .4); sf(g("rutina_word"), "tic", .4)
            if g("encoge_word") is not None: sf(g("encoge_word"), "bajada", .6)
        if tp == "vacaciones":
            sf(e["t0"] + .1, "pop", .5)
            if g("rapido_word") is not None:
                for j in range(8): sf(g("rapido_word") - .2 + j * .09, "tic", .45)
            if g("largas_word") is not None: sf(g("largas_word") - .5, "desliz", .7); sf(g("largas_word") + .5, "camara", .5)
        if tp == "nuevo":
            for it in s.get("items", []): sf(Tw(it["word"]) - .15, "pop", .6)
            if g("estira_word") is not None: sf(g("estira_word"), "boing", 1.0)

    for k, fn in (("reloj_arena", e_reloj_arena), ("verano", e_verano), ("janet", e_janet), ("tarta", e_tarta), ("cinta", e_cinta),
                  ("memoria", e_memoria), ("vacaciones", e_vacaciones), ("nuevo", e_nuevo)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_vida)
