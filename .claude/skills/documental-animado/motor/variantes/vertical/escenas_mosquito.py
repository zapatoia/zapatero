"""Escenas del documental 12 («¿Y si desaparecieran los mosquitos?»): conceptos animados con un mosquito ilustrado.

mosquito    mosquito grande volando; zumbido [words] (bzzz + sonido), golpe_word: una mano lo estampa (¡PLAF!) y se esfuma en polvo;
            reloj "3:00" (despertador en la esquina), pill {txt, word?}.
ranking     tiburon_word (tiburón que entra y se tacha), mosquito_word (mosquito con corona), pill_txt.
contagio    corte de piel: pica_word (la trompa entra), parasitos_word (parásitos a la sangre), stat {word, valor, label},
            cero_word (la cifra baja a 0 y los parásitos desaparecen), cero_label.
zumbido     dormitorio a las 3:00: zumbido_word (bzzz junto a la oreja), despierta_word (ojos abiertos), fin_word (mosquito fuera, duerme).
estanque    corte de un estanque: larvas_word, pez_word (pez que se come las larvas), libelula_word.
tundra      renos que caminan; nube_word (nube de mosquitos), ruta_word (los renos se dan la vuelta).
orquidea    orquídea; macho_word (mosquito macho que bebe néctar), polen_word (polen pegado a la cabeza), rotulos [{word, txt}].
red         red de comida: nodos [txt] alrededor del mosquito; hueco_word (el mosquito sale y queda el hueco), relleno_word (otro insecto entra).
especies    total/pican: cuadrícula de puntos que se llena con contador (word) y solo `pican` se encienden en rojo (pican_word).
selectivo   enjambre de mosquitos: objetivo_word (miras sobre los que transmiten), borra_word (solo esos desaparecen).
Efectos: zumbido, ¡plaf!, puf de polvo, burbujas, ñam, pasos, brillo, tics de cuadrícula.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]

    # ---------------------------------------------------------------- sonidos
    def s_zumbido():
        d = .9; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        f = 560 + 40 * np.sin(2 * np.pi * 7 * t) + 60 * np.sin(2 * np.pi * 1.3 * t)
        ph = np.cumsum(f) / AU.SR; x = 2 * (ph % 1) - 1                       # diente de sierra
        x = AU._banda(x, 400, 4000) * (.6 + .4 * np.sin(2 * np.pi * 3.1 * t) ** 2)
        return x * np.sin(np.pi * u) ** 1.2
    def s_plaf():
        d = .32; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        x = AU._banda(AU._ruido(n, 71), 900, 5000) * np.exp(-t / .025) * 1.3 + np.sin(2 * np.pi * (110 - 50 * t / d) * t) * np.exp(-t / .07)
        return np.tanh(2 * x)
    def s_puf():
        d = .55; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 72), 200, 1800) * np.sin(np.pi * u) ** .8 * (1 - u)
    def s_nam():
        d = .18; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * (300 - 900 * t) * t) * np.exp(-t / .05) * np.minimum(1, t / .004)
    def s_paso():
        d = .16; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._bajos(np.sin(2 * np.pi * 70 * t) * np.exp(-t / .04) + .3 * AU._ruido(n, 73) * np.exp(-t / .02), 600)
    for nom, fn, db in (("zumbido", s_zumbido, -30), ("plaf", s_plaf, -21), ("puf", s_puf, -31), ("nam", s_nam, -28), ("paso", s_paso, -30)):
        AU.SFX.setdefault(nom, (fn, db))

    def _io(u): return u * u * (3 - 2 * u)
    def _sombra_oval(c, x, y, rx, ry, a):
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), skia.Paint(AntiAlias=True, Color=color("#000000", a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, ry * .8 + 4)))
    def _tw(self, e, w): return self.ta(w, e) if w else 1e9

    # ================================================================ MOSQUITO ilustrado (mira a la izquierda)
    def _pata(c, pts, a, ancho_=3.6):
        p = skia.Path(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=ancho_, Color=color("#1C1C24", a), StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap))
        # anillas blancas en el último tramo
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        for k in (.3, .55, .8):
            xa, ya = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k; xb, yb = x0 + (x1 - x0) * (k + .08), y0 + (y1 - y0) * (k + .08)
            c.drawLine(xa, ya, xb, yb, skia.Paint(AntiAlias=True, StrokeWidth=ancho_ + .4, Color=color("#F2F2F2", .9 * a), StrokeCap=skia.Paint.kButt_Cap))

    def _mosquito(c, x, y, s, t, a=1.0, rot=0.0, macho=False, rojo=0.0, flip=False, cuerpo="#2A2A34", alas=True, sentado=False):
        if a <= 0: return
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(-s if flip else s, s)
        bob = 0 if sentado else 3 * math.sin(t * 9)
        c.translate(0, bob)
        _sombra_oval(c, 20, 150, 110, 12, .18 * a) if not sentado else None
        # patas (detrás del cuerpo): delanteras, medias y traseras levantadas
        for pts in (((-22, 12), (-70, 48), (-112, 128)), ((-10, 16), (-36, 70), (-58, 140)), ((2, 18), (18, 72), (12, 145)),
                    ((10, 16), (70, 60), (118, 132)), ((16, 10), (100, 0), (165, -38)), ((20, 8), (96, -14), (150, -64))):
            _pata(c, pts, a)
        # abdomen con bandas
        c.save(); c.translate(82, -6); c.rotate(-14)
        ab = skia.Rect(-70, -22, 72, 22)
        c.drawOval(ab, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -22), (0, 22)], [color("#4A4A58", a), color(cuerpo, a), color("#101016", a)])))
        if rojo > 0:   # barriga llena de sangre
            c.drawOval(skia.Rect(-60, -14, 64, 20), relleno("#C81E2A", .85 * rojo * a))
        c.save(); pth = skia.Path(); pth.addOval(ab); c.clipPath(pth, doAntiAlias=True)
        for k in range(6): c.drawRect(skia.Rect(-52 + k * 22, -24, -46 + k * 22, 24), relleno("#EDEDED", .75 * a))
        c.restore(); c.drawOval(skia.Rect(-50, -18, 40, -6), relleno("#FFFFFF", .12 * a)); c.restore()
        # tórax con la «lira» blanca
        c.drawOval(skia.Rect(-36, -40, 34, 22), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-6, -22), 50, [color("#5A5A68", a), color(cuerpo, a), color("#0E0E14", a)], [0, .5, 1])))
        ly = skia.Path(); ly.moveTo(-16, -30); ly.cubicTo(-26, -10, -14, 4, -4, 10); ly.moveTo(10, -30); ly.cubicTo(20, -10, 8, 4, -2, 10)
        c.drawPath(ly, trazo("#F4F4F4", 2.6, .85 * a))
        # cabeza, ojo compuesto, trompa, palpos y antenas
        c.drawCircle(-42, 0, 17, relleno("#1A1A22", a))
        c.drawCircle(-46, -3, 13, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-50, -8), 14, [color("#6A2A30", a), color("#2A0E12", a), color("#0A0406", a)], [0, .55, 1])))
        c.drawCircle(-50, -8, 3.5, relleno("#FFFFFF", .8 * a))
        c.drawLine(-56, 8, -132, 34, skia.Paint(AntiAlias=True, StrokeWidth=3.6, Color=color("#15151C", a), StrokeCap=skia.Paint.kRound_Cap))
        c.drawLine(-56, 6, -76, 16, skia.Paint(AntiAlias=True, StrokeWidth=3, Color=color("#3A3A46", a), StrokeCap=skia.Paint.kRound_Cap))
        for ax, ay in ((-86, -50), (-74, -58)):
            c.drawLine(-50, -12, ax, ay, skia.Paint(AntiAlias=True, StrokeWidth=2.2, Color=color("#22222C", a), StrokeCap=skia.Paint.kRound_Cap))
            if macho:   # antenas plumosas del macho
                for k in range(1, 9):
                    q = k / 9; px_, py_ = -50 + (ax + 50) * q, -12 + (ay + 12) * q; L = 14 * (1 - .5 * q)
                    c.drawLine(px_ - L * .7, py_ - L * .3, px_ + L * .7, py_ + L * .3, trazo("#44444F", 1.3, .8 * a))
        # alas translúcidas que baten (con estela)
        if alas:
            for k, w_ in ((0, 1.0), (1, .35), (2, .18)):
                ang = -62 + 26 * math.sin(t * 2 * math.pi * 11 - k * .5) if not sentado else -78
                c.save(); c.translate(2, -30); c.rotate(ang)
                wing = skia.Rect(0, -16, 132, 16)
                c.drawOval(wing, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (132, 0)], [color("#DDEBFF", .55 * w_ * a), color("#BFD4F5", .25 * w_ * a)])))
                c.drawOval(wing, trazo("#FFFFFF", 1.2, .5 * w_ * a))
                for vx in (30, 62, 94): c.drawLine(vx - 20, 0, vx + 14, -8 + vx * .1, trazo("#9FB5DA", 1, .4 * w_ * a))
                c.restore()
                if sentado: break
        c.restore()

    def _vuelo(t, cx, cy, ax=170, ay=90):
        return cx + ax * math.sin(1.25 * t) + 25 * math.sin(3.7 * t), cy + ay * math.sin(2.05 * t + 1) + 18 * math.sin(5.3 * t)

    # ================================================================ MANO que estampa
    def _mano(c, x, y, s, rot, a):
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
        piel = lambda y0, y1: skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [color("#F6D2B4", a), color("#E3A983", a), color("#C98A66", a)])
        _sombra_oval(c, 20, 60, 230, 230, .35 * a)
        # pulgar
        c.save(); c.translate(-140, 70); c.rotate(-42)
        c.drawRRect(rrc(0, -40, 74, 190, 37), skia.Paint(AntiAlias=True, Shader=piel(-130, 60))); c.drawOval(skia.Rect(-20, -128, 20, -92), relleno("#F9E1CE", .8 * a)); c.restore()
        # dedos
        for fx, L, rr in ((-96, 190, -6), (-32, 228, -2), (32, 214, 2), (94, 168, 7)):
            c.save(); c.translate(fx, -40); c.rotate(rr)
            c.drawRRect(rrc(0, -L / 2, 62, L, 31), skia.Paint(AntiAlias=True, Shader=piel(-L, 0)))
            c.drawOval(skia.Rect(-19, -L + 12, 19, -L + 52), relleno("#FBE5D4", .85 * a))
            for k in (.38, .66): c.drawLine(-16, -L * k, 16, -L * k, trazo("#B67652", 2, .45 * a))
            c.restore()
        # palma
        c.drawRRect(rrc(0, 60, 280, 270, 110), skia.Paint(AntiAlias=True, Shader=piel(-80, 200)))
        pl = skia.Path(); pl.moveTo(-90, 20); pl.cubicTo(-20, 60, 40, 40, 110, 10); pl.moveTo(-100, 120); pl.cubicTo(-40, 70, 20, 80, 60, 150)
        c.drawPath(pl, trazo("#B67652", 2.5, .4 * a))
        c.drawRRect(rrc(0, 60, 280, 270, 110), trazo("#9A5E40", 2, .35 * a))
        c.restore()

    def _estrella(c, x, y, dt, a=1.0):
        """Estrella de impacto (detrás de la mano), dt desde el golpe."""
        if dt < 0 or dt > .9: return
        u = TI.cubic_out(TI.clamp(dt / .18)); al = a * (1 - TI.clamp((dt - .5) / .4))
        R = 300 * u; p = skia.Path()
        for k in range(28):
            r = R if k % 2 == 0 else R * .55; an = math.pi * 2 * k / 28 + .2
            (p.moveTo if k == 0 else p.lineTo)(x + r * math.cos(an), y + r * math.sin(an))
        p.close()
        c.drawPath(p, relleno("#FFE15A", .9 * al)); c.drawCircle(x, y, R * .42, relleno("#FFFFFF", .9 * al))

    def _rotulo_plaf(c, x, y, dt, a=1.0):
        """«¡PLAF!» de cómic encima de todo."""
        if dt < 0 or dt > 1.0: return
        al = a * (1 - TI.clamp((dt - .6) / .4)); f = fuente("Inter", 800, 130); sc = .6 + .4 * resorte(dt, 10, 14)
        c.save(); c.translate(x, y); c.rotate(-9); c.scale(sc, sc)
        texto(c, "¡PLAF!", 6, 10, f, "#14182A", alfa=al); texto(c, "¡PLAF!", 0, 0, f, "#FFE15A", alfa=al, sombra=(3, 12, .5))
        c.restore()

    def _puf(c, x, y, dt, a=1.0, R=150):
        if dt < 0 or dt > 1.1: return
        u = TI.cubic_out(TI.clamp(dt / .9)); al = a * (1 - u) ** 1.2
        rng = np.random.default_rng(8)
        for k in range(11):
            an = rng.random() * 6.28; d = R * (.2 + .8 * rng.random()) * u; r = (26 + 30 * rng.random()) * (.5 + u)
            c.drawCircle(x + d * math.cos(an), y + d * math.sin(an) - 30 * u, r, relleno("#C9CED8", .55 * al))
        for k in range(14):   # chispas
            an = 6.28 * k / 14; d = R * 1.3 * u
            c.drawCircle(x + d * math.cos(an), y + d * math.sin(an), 4 * (1 - u), relleno("#FFFFFF", al))

    def _bzz(c, x, y, t, a):
        f = fuente("Inter", 800, 54)
        for k, ch in enumerate("bzzz"):
            texto(c, ch, x + k * 30, y + 8 * math.sin(t * 18 + k), f, "#FFFFFF", alfa=a * (.6 + .4 * math.sin(t * 12 + k)), sombra=(2, 8, .5))
        for k in range(3):
            r = 30 + k * 22 + (t * 60) % 22
            c.drawArc(skia.Rect(x - 60 - r, y - r, x - 60 + r, y + r), -40, 80, False, trazo("#FFFFFF", 3, .35 * a * (1 - k / 3)))

    def _reloj(c, x, y, txt, a, t):
        c.drawRRect(rrc(x, y, 220, 110, 22), relleno("#0B0B12", .9 * a)); c.drawRRect(rrc(x, y, 220, 110, 22), trazo("#3A3A4A", 3, a))
        with capa(c, alfa=a, blur=14): texto(c, txt, x, y + 4, fuente("Inter", 800, 70), "#FF4A3A")
        texto(c, txt, x, y + 4, fuente("Inter", 800, 70), "#FF6A5A", alfa=a * (.85 + .15 * math.sin(t * 3)))

    # ---------------------------------------------------------------- escena: mosquito + golpe
    def e_mosquito(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tg = _tw(self, e, s.get("golpe_word"))
        # sacudida al golpear
        if 0 < t - tg < .35:
            k = (1 - (t - tg) / .35) ** 2; c.translate(18 * k * math.sin(t * 90), 14 * k * math.cos(t * 77))
        if s.get("pill"):
            q = s["pill"]; dp = t - (_tw(self, e, q.get("word")) if q.get("word") else e["t0"])
            if dp > 0: self.pildora(c, q["txt"], CX, 200 + 20 * (1 - resorte(dp, 9, 12)), S, aparece(dp, .15), fnt=self.F["pillb"])
        if s.get("reloj"): _reloj(c, CX + 290, 300, s["reloj"], aparece(dt0, .2), t)
        tv = min(t, tg) if t > tg else t
        mx, my = _vuelo(tv, CX + 10, 690, 110, 70)
        ent = resorte(dt0 + .1, 5, 7)
        mx += 500 * (1 - ent)
        if t < tg:
            _mosquito(c, mx, my, s.get("tam", 2.3), t, aparece(dt0 + .1, .2), rot=4 * math.sin(t * 2), flip=math.cos(1.25 * t) > 0.6 and False)
            for w in s.get("zumbido", []):
                dz = t - self.ta(w, e)
                if 0 < dz < 1.1: _bzz(c, mx + 120, my - 260, t, math.sin(math.pi * dz / 1.1))
        # mano: entra por abajo a la derecha, golpea en tg, se va. Orden: polvo y estrella detrás, mano, «¡PLAF!» encima.
        if tg < 1e8:
            u_in = TI.clamp((t - (tg - .28)) / .28); u_out = TI.clamp((t - (tg + .45)) / .4)
            if t > tg:
                _puf(c, mx, my, t - tg - .55, 1.0, 170)
                _estrella(c, mx, my, t - tg)
            if 0 < u_in and u_out < 1:
                ui = u_in ** 2.2; hx = mx + 20 + 520 * (1 - ui) + 600 * _io(u_out); hy = my + 40 + 700 * (1 - ui) + 400 * _io(u_out)
                sq = 1 - .06 * math.sin(math.pi * TI.clamp((t - tg) / .2)) if t > tg else 1
                c.save(); c.translate(hx, hy); c.scale(1, sq); c.translate(-hx, -hy)
                _mano(c, hx, hy, 1.75, 18 * (1 - ui) - 6 + 20 * u_out, 1.0)
                c.restore()
            if t > tg:
                _rotulo_plaf(c, CX - 80, max(260, my - 430), t - tg)
                if s.get("fin_txt"):
                    df = t - tg - .95
                    if df > 0:
                        sc = .6 + .4 * resorte(df, 8, 11); c.save(); c.translate(CX, 690); c.scale(sc, sc)
                        f = fuente("Inter", 800, 96); w = ancho(s["fin_txt"], f); k = min(1, 820 / w); c.scale(k, k)
                        texto(c, s["fin_txt"], 0, 0, f, "#FFFFFF", alfa=aparece(df, .15), sombra=(4, 16, .5)); c.restore()

    # ---------------------------------------------------------------- ranking: no es el tiburón, es él
    def _tiburon(c, x, y, s, a, t):
        c.save(); c.translate(x, y + 6 * math.sin(t * 2)); c.scale(s, s)
        b = skia.Path(); b.moveTo(-170, 0); b.cubicTo(-120, -55, 60, -62, 130, -10); b.lineTo(200, -60); b.lineTo(180, 0); b.lineTo(205, 55); b.lineTo(128, 12)
        b.cubicTo(60, 50, -120, 45, -170, 0); b.close()
        c.drawPath(b, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -60), (0, 50)], [color("#7E93B5", a), color("#4D6187", a), color("#D9E2F0", a)], [0, .55, .8])))
        fin = skia.Path.Polygon([(-20, -45), (30, -120), (50, -40)], True); c.drawPath(fin, relleno("#5E739A", a))
        c.drawPath(skia.Path.Polygon([(-40, 25), (0, 70), (10, 28)], True), relleno("#5E739A", a))
        c.drawCircle(-118, -12, 6, relleno("#0A0A10", a))
        for k in range(3): c.drawLine(-80 + k * 12, -8, -86 + k * 12, 18, trazo("#3C4C70", 2.5, .7 * a))
        c.restore()

    def e_ranking(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tt, tm = _tw(self, e, s.get("tiburon_word")), _tw(self, e, s.get("mosquito_word"))
        ut = resorte(t - tt + .05, 7, 9) if t > tt - .05 else 0
        tx = _tw(self, e, s["cruz_word"]) if s.get("cruz_word") else tt + .45
        ux = TI.clamp((t - tx) / .3); um = TI.clamp((t - tm + .05) / .5)
        if s.get("titulo"): self.pildora(c, s["titulo"], CX, 200 + 20 * (1 - resorte(dt0, 9, 12)), S, aparece(dt0, .15), fnt=self.F["pillb"])
        if ut > 0:
            sc = 1.25 - .65 * _io(um); x = CX - 260 * _io(um) + 300 * (1 - ut); y = 600 - 330 * _io(um)
            _tiburon(c, x, y, sc, (1 - .5 * _io(um)) * min(1, ut * 2), t)
            if ux > 0:
                L = 150 * sc; p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=22 * sc, Color=color("#E5322D"), StrokeCap=skia.Paint.kRound_Cap)
                u1, u2 = TI.cubic_out(TI.clamp(ux * 2)), TI.cubic_out(TI.clamp(ux * 2 - 1))
                c.drawLine(x - L, y - L * .6, x - L + 2 * L * u1, y - L * .6 + 1.2 * L * u1, p)
                if u2 > 0: c.drawLine(x + L, y - L * .6, x + L - 2 * L * u2, y - L * .6 + 1.2 * L * u2, p)
            if um <= 0: texto(c, "TIBURÓN", x, y + 150 * sc, fuente("Inter", 800, 44), S["sub"], alfa=min(1, ut * 2))
        if um > 0:
            k = resorte(t - tm + .05, 6, 8); y = 700 + 30 * (1 - k)
            # halo y pedestal
            c.drawCircle(CX, y, 330, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((CX, y), 330, [color("#F2C14E", .35 * um), color("#F2C14E", 0)])))
            _mosquito(c, CX + 20, y, 1.45 * (.6 + .4 * k), t, min(1, um * 2), rot=-4)
            # corona
            ck = TI.clamp((t - tm - .35) / .35)
            if ck > 0:
                cy_ = y - 200 - 120 * (1 - resorte(t - tm - .35, 8, 11)); cx_ = CX - 45
                cr = skia.Path.Polygon([(cx_ - 70, cy_ + 35), (cx_ - 80, cy_ - 30), (cx_ - 38, cy_ + 2), (cx_, cy_ - 50), (cx_ + 38, cy_ + 2), (cx_ + 80, cy_ - 30), (cx_ + 70, cy_ + 35)], True)
                c.drawPath(cr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, cy_ - 50), (0, cy_ + 35)], [color("#FFE7A3", ck), color("#E0A82E", ck)])))
                c.drawPath(cr, trazo("#8A6420", 3, ck))
                for gx, gc in ((-40, "#E5322D"), (0, "#2F6BFF"), (40, "#2FBF71")): c.drawCircle(cx_ + gx, cy_ + 18, 8, relleno(gc, ck))
            if s.get("pill_txt"):
                dp = t - tm - .6
                if dp > 0: self.pildora(c, s["pill_txt"], CX, 1020 + 16 * (1 - resorte(dp, 9, 12)), S, aparece(dp, .15), fnt=self.F["pillb"], fondo="#E5322D")

    # ---------------------------------------------------------------- contagio: corte de piel y sangre
    def e_contagio(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tp, tpa, t0_ = _tw(self, e, s.get("pica_word")), _tw(self, e, s.get("parasitos_word")), _tw(self, e, s.get("cero_word"))
        ysk = 560
        # piel en corte
        c.drawRect(skia.Rect(-40, ysk, W + 40, 1000), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, ysk), (0, 1000)], [color("#F2B9A0"), color("#E59A86"), color("#C76E66")], [0, .3, 1])))
        c.drawRect(skia.Rect(-40, ysk, W + 40, ysk + 22), relleno("#F8CDB6"))
        rng = np.random.default_rng(3)
        for k in range(40): c.drawCircle(float(rng.random() * W), float(ysk + 40 + rng.random() * 120), float(10 + rng.random() * 18), relleno("#F7C4AE", .35))
        # vaso sanguíneo con glóbulos que corren
        vy = 820
        c.drawRRect(rrc(CX, vy, W + 200, 150, 75), relleno("#8E1520", .95)); c.drawRRect(rrc(CX, vy, W + 200, 150, 75), trazo("#5E0A12", 4))
        for k in range(16):
            x = ((k * 97 + t * 160) % (W + 200)) - 100; y = vy - 40 + (k * 37 % 80)
            c.save(); c.translate(x, y); c.rotate(k * 23 + t * 30)
            c.drawOval(skia.Rect(-26, -14, 26, 14), relleno("#E2333F")); c.drawOval(skia.Rect(-14, -6, 14, 6), relleno("#B81E2A")); c.restore()
        # mosquito posado que pica
        up = TI.clamp((t - tp + .2) / .5)
        ms, rot_ = 1.5, -24 * _io(up); mx, my = CX + 190, ysk - 205 + 30 * (1 - _io(up))
        _mosquito(c, mx, my, ms, t, aparece(dt0, .2), rot=rot_, sentado=up > .9, rojo=TI.clamp((t - tp - .6) / 2.5))
        ra = math.radians(rot_); lx, ly = -132 * ms, (34 + 0) * ms
        tipx, tipy = mx + lx * math.cos(ra) - ly * math.sin(ra), my + lx * math.sin(ra) + ly * math.cos(ra)
        if up > .6:   # estilete que entra en la piel
            ue = TI.clamp((up - .6) / .4); c.drawLine(tipx, tipy, tipx + (CX - 25 - tipx) * ue, tipy + (ysk + 70 - tipy) * ue, skia.Paint(AntiAlias=True, StrokeWidth=4, Color=color("#15151C"), StrokeCap=skia.Paint.kRound_Cap))
        # parásitos que bajan de la trompa a la sangre
        if t > tpa:
            ua = t - tpa; fade = 1 - TI.clamp((t - t0_) / .5)
            for k in range(14):
                ph = (ua * .5 + k / 14) % 1 if ua > k * .12 else -1
                if ph < 0: continue
                if ph < .35: x, y = CX - 25 + 10 * math.sin(k), ysk + 20 + (vy - 60 - ysk) * ph / .35
                else: x, y = CX - 25 + (ph - .35) * 900 * (1 if k % 2 else -1) * .6, vy - 30 + 50 * math.sin(k * 1.7 + ua)
                c.save(); c.translate(x, y); c.rotate(ua * 120 + k * 30)
                pg = skia.Path(); pg.moveTo(-16, 0); pg.cubicTo(-8, -12, 8, 12, 16, 0)
                c.drawPath(pg, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Color=color("#7CF27C", .95 * fade), StrokeCap=skia.Paint.kRound_Cap))
                c.restore()
            if 0 < t - tpa < 1.6: self.pildora(c, s.get("parasitos_txt", "MALARIA"), CX - 220, ysk + 110, S, aparece(t - tpa, .15) * (1 - TI.clamp((t - t0_) / .3)), fnt=self.F["pillb"], fondo="#1F7A3A")
        # cifra
        st = s.get("stat")
        if st and t > self.ta(st["word"], e) - .1:
            tw = self.ta(st["word"], e); dt = t - tw; dd = st.get("dur", 1.0)
            v = st["valor"] * TI.cubic_out(TI.clamp(dt / dd)) if dt > 0 else 0
            if t > t0_: v = st["valor"] * (1 - TI.cubic_out(TI.clamp((t - t0_) / 1.0)))
            verde = TI.clamp((t - t0_ - .9) / .2)
            a = aparece(dt + .1, .15); txt = f"{int(round(v)):,}".replace(",", ".")
            c.drawRRect(rrc(CX, 1060, 900, 230, 40), relleno("#0B1530", .78 * a))
            c.save(); c.translate(CX, 1035); sc = .9 + .1 * resorte(dt + .1, 8, 11); c.scale(sc, sc)
            texto(c, txt, 0, 0, fuente("Inter", 800, 150), "#7CF27C" if verde > .5 else "#FFFFFF", alfa=a, tnum=True, sombra=(4, 14, .4))
            c.restore()
            lab = s.get("cero_label", "") if verde > .5 else st["label"]
            texto(c, lab, CX, 1128, fuente("Inter", 800, 38), "#7CF27C" if verde > .5 else "#FFB4B4", alfa=a)

    # ---------------------------------------------------------------- zumbido a las 3:00
    def e_zumbido(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tz, td, tf = _tw(self, e, s.get("zumbido_word")), _tw(self, e, s.get("despierta_word")), _tw(self, e, s.get("fin_word"))
        c.save(); c.translate(CX, 650); c.scale(1.18, 1.18); c.translate(-CX, -560)
        # ventana con luna
        c.drawRRect(rrc(CX - 250, 330, 260, 300, 18), relleno("#1B2350")); c.drawRRect(rrc(CX - 250, 330, 260, 300, 18), trazo("#3C4A8A", 8))
        c.drawCircle(CX - 290, 280, 44, relleno("#FFF2C4", .95)); c.drawCircle(CX - 272, 268, 40, relleno("#1B2350"))
        c.drawLine(CX - 250, 180, CX - 250, 480, trazo("#3C4A8A", 6)); c.drawLine(CX - 380, 330, CX - 120, 330, trazo("#3C4A8A", 6))
        _reloj(c, CX + 250, 360, s.get("reloj", "3:00"), aparece(dt0, .2), t)
        # cama, almohada y persona
        by = 860
        c.drawRRect(rrc(CX, by + 120, 860, 120, 20), relleno("#3A2A4A")); c.drawRRect(rrc(CX - 400, by - 20, 50, 360, 16), relleno("#4A3660"))
        c.drawRRect(rrc(CX - 210, by - 30, 300, 120, 50), relleno("#E8E6F5"))
        hx, hy = CX - 200, by - 95
        c.drawCircle(hx, hy, 92, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((hx - 20, hy - 30), 110, [color("#F6D2B4"), color("#D99A78")])))
        pel = skia.Path(); pel.addArc(skia.Rect(hx - 96, hy - 100, hx + 96, hy + 80), 180, 180); c.drawPath(pel, relleno("#3A2418"))
        desp = TI.clamp((t - td) / .15) * (1 - TI.clamp((t - tf - .3) / .3))
        for ex in (-32, 32):
            if desp > .5:
                c.drawCircle(hx + ex, hy + 5, 17, relleno("#FFFFFF")); c.drawCircle(hx + ex + 4 * math.sin(t * 6), hy + 7, 8, relleno("#14182A"))
                c.drawLine(hx + ex - 20, hy - 26 + (8 if ex < 0 else -8) * .0, hx + ex + 20, hy - 20 - (6 if ex < 0 else -6), trazo("#3A2418", 5))
            else:
                c.drawArc(skia.Rect(hx + ex - 16, hy - 4, hx + ex + 16, hy + 16), 10, 160, False, trazo("#3A2418", 4))
        c.drawPath(skia.Path.Polygon([(hx - 20, hy + 46), (hx + 20, hy + 46), (hx, hy + 52)], True), relleno("#8A4A3A")) if desp > .5 else c.drawLine(hx - 14, hy + 48, hx + 14, hy + 48, trazo("#8A4A3A", 4))
        # manta
        m = skia.Path(); m.moveTo(CX - 360, by + 70); m.cubicTo(CX - 200, by - 30 + 6 * math.sin(t * 1.4), CX + 150, by - 10, CX + 430, by + 30); m.lineTo(CX + 430, by + 150); m.lineTo(CX - 360, by + 150); m.close()
        c.drawPath(m, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, by - 30), (0, by + 150)], [color("#6A7CF0"), color("#3A4ABF")])))
        for k in range(5): c.drawLine(CX - 300 + k * 150, by + 40, CX - 260 + k * 150, by + 140, trazo("#FFFFFF", 3, .12))
        # mosquito junto a la oreja
        fuera = TI.clamp((t - tf) / .35)
        if t > tz - .4 and fuera < 1:
            mx, my = _vuelo(t, hx + 150, hy - 150, 60, 40)
            _mosquito(c, mx + 300 * fuera, my - 200 * fuera, .75, t, aparece(t - tz + .4, .2) * (1 - fuera), flip=True)
            dz = t - tz
            if 0 < dz < 2.2 and fuera <= 0: _bzz(c, mx + 30, my - 90, t, min(1, dz * 4) * (1 - TI.clamp((dz - 1.8) / .4)))
            if fuera > 0: _puf(c, mx, my, t - tf, 1.0, 90)
        if t > tf + .3:
            dz = t - tf - .3
            for k in range(3):
                ph = (dz * .45 + k / 3) % 1; texto(c, "z", hx + 120 + 90 * ph, hy - 140 - 220 * ph, fuente("Inter", 800, int(50 + 40 * ph)), "#FFFFFF", alfa=math.sin(math.pi * ph) * aparece(dz, .3))
        c.restore()

    # ---------------------------------------------------------------- estanque: larvas, pez y libélula
    def _pez(c, x, y, s, a, t, boca=0):
        c.save(); c.translate(x, y); c.scale(s, s)
        cola = skia.Path.Polygon([(-95, 0), (-150, -48 + 8 * math.sin(t * 9)), (-140, 0), (-150, 48 + 8 * math.sin(t * 9))], True)
        c.drawPath(cola, relleno("#E8862E", a))
        b = skia.Path(); b.addOval(skia.Rect(-110, -52, 110, 52))
        c.drawPath(b, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -52), (0, 52)], [color("#FFB15A", a), color("#F27B1F", a), color("#FFE0B8", a)], [0, .6, 1])))
        for k in range(4): c.drawArc(skia.Rect(-40 + k * 26, -40, 20 + k * 26, 40), -60, 120, False, trazo("#C95A10", 2, .5 * a))
        c.drawPath(skia.Path.Polygon([(-20, -48), (30, -86), (40, -46)], True), relleno("#E8862E", a))
        c.drawCircle(70, -12, 13, relleno("#FFFFFF", a)); c.drawCircle(74, -12, 7, relleno("#14182A", a))
        if boca > 0: c.drawOval(skia.Rect(96, 4 - 14 * boca, 116, 4 + 14 * boca), relleno("#5A1A10", a))
        c.restore()

    def _libelula(c, x, y, s, a, t):
        c.save(); c.translate(x, y); c.scale(s, s)
        for sy in (-1, 1):
            for dx, L in ((-6, 150), (20, 130)):
                ang = sy * (14 + 22 * math.sin(t * 40 + dx)); c.save(); c.translate(dx, 0); c.rotate(ang - 90 * sy)
                c.drawOval(skia.Rect(-14, 0, 14, L) if sy > 0 else skia.Rect(-14, -L, 14, 0), relleno("#CFE8FF", .45 * a)); c.restore()
        c.drawRRect(rrc(80, 0, 190, 16, 8), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (180, 0)], [color("#1FA38A", a), color("#2F6BFF", a)])))
        c.drawOval(skia.Rect(-30, -16, 20, 16), relleno("#1C8C76", a)); c.drawCircle(-36, 0, 15, relleno("#0F5A4C", a)); c.drawCircle(-42, -4, 6, relleno("#9FF0D8", a))
        c.restore()

    def e_estanque(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tl, tp, tb = _tw(self, e, s.get("larvas_word")), _tw(self, e, s.get("pez_word")), _tw(self, e, s.get("libelula_word"))
        ws = 560
        # cielo y juncos
        c.drawRect(skia.Rect(-40, -40, W + 40, ws), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, ws)], [color("#8FD3F5"), color("#D9F1FF")])))
        for k in range(9):
            x = 70 + k * 105 + (k % 3) * 20; h = 180 + (k * 53 % 90); sw = 6 * math.sin(t * 1.3 + k)
            c.drawLine(x, ws + 10, x + sw, ws - h, trazo("#3E8A3A", 7)); c.drawRRect(rrc(x + sw, ws - h + 10, 16, 60, 8), relleno("#6A4A2A"))
        # agua
        c.drawRect(skia.Rect(-40, ws, W + 40, 1250), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, ws), (0, 1250)], [color("#2E8FB8"), color("#14507A"), color("#0A2A44")])))
        sup = skia.Path(); sup.moveTo(-40, ws)
        for x in range(-40, W + 60, 30): sup.lineTo(x, ws + 5 * math.sin(x * .03 + t * 3))
        c.drawPath(sup, trazo("#BFE9FF", 4, .8))
        for k in range(6):   # rayos de luz
            x = 100 + k * 160 + 30 * math.sin(t * .5 + k)
            c.drawPath(skia.Path.Polygon([(x, ws), (x + 50, ws), (x - 60, 1250), (x - 150, 1250)], True), relleno("#FFFFFF", .05))
        # larvas colgando de la superficie
        tp_pos = lambda tt: -200 + (W + 400) * TI.clamp((tt - tp) / 2.4)
        px_ = tp_pos(t) if t > tp else -999
        al_l = aparece(t - tl + .1, .25)
        for k in range(8):
            x = 110 + k * 108 + 12 * math.sin(k * 2.3); comida = t > tp and px_ > x - 40
            if comida or al_l <= 0: continue
            c.save(); c.translate(x, ws + 8); c.rotate(10 * math.sin(t * 5 + k)); c.scale(1.7, 1.7)
            c.drawLine(0, 0, 0, 22, trazo("#3A2A1A", 4, al_l))
            lv = skia.Path(); lv.moveTo(0, 20)
            for j in range(1, 7): lv.lineTo(8 * math.sin(t * 7 + j + k), 20 + j * 13)
            c.drawPath(lv, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9, Color=color("#4A3A28", al_l), StrokeCap=skia.Paint.kRound_Cap))
            c.drawCircle(8 * math.sin(t * 7 + 6 + k), 20 + 6 * 13 + 6, 10, relleno("#2A1E14", al_l))
            c.restore()
        if 0 < t - tl < 2.0: self.pildora(c, "LARVAS", CX, ws + 290, S, aparece(t - tl, .15) * (1 - TI.clamp((t - tl - 1.6) / .3)), fnt=self.F["pillb"], fondo="#0C1630")
        # pez que se las come
        if t > tp:
            boca = abs(math.sin(t * 10))
            _pez(c, px_, ws + 200 + 18 * math.sin(t * 2), 2.1, 1.0, t, boca)
            for k in range(8):
                bx = px_ - 60 - k * 40; by_ = ws + 100 - ((t * 120 + k * 37) % 300)
                if by_ > ws: c.drawCircle(bx, by_, 6 + k % 3 * 3, trazo("#DFF6FF", 2, .6))
            if t - tp < 2.4: self.pildora(c, "PECES", CX, ws + 420, S, aparece(t - tp, .15), fnt=self.F["pillb"], fondo="#E8862E")
        # libélula
        if t > tb:
            u = resorte(t - tb, 4, 6); lx = W + 200 - (W + 200 - CX - 120) * u + 20 * math.sin(t * 2); ly = 330 + 40 * math.sin(t * 1.7)
            _libelula(c, lx, ly, 1.6, 1.0, t)
            self.pildora(c, "LIBÉLULAS", CX, 1130, S, aparece(t - tb, .15), fnt=self.F["pillb"], fondo="#1C8C76")

    # ---------------------------------------------------------------- tundra: renos y nube
    def _reno(c, x, y, s, a, t, dirx=1, fase=0):
        c.save(); c.translate(x, y); c.scale(s * dirx, s)
        col = "#6B4A33"
        for k, lx in enumerate((-55, -35, 40, 60)):
            sw = 14 * math.sin(t * 6 + fase + k * math.pi / 2)
            c.drawLine(lx, 10, lx + sw, 95, trazo("#4A3020", 9, a)); c.drawLine(lx + sw, 95, lx + sw + 4, 100, trazo("#2A1A10", 10, a))
        c.drawOval(skia.Rect(-85, -40, 90, 30), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -40), (0, 30)], [color("#8A6446", a), color(col, a), color("#E6DCCB", a)], [0, .6, 1])))
        c.drawPath(skia.Path.Polygon([(60, -20), (90, -80), (115, -70), (95, -10)], True), relleno(col, a))
        c.drawOval(skia.Rect(88, -100, 140, -64), relleno("#7A5A3E", a)); c.drawCircle(136, -80, 6, relleno("#1A1010", a))
        ant = skia.Path(); ant.moveTo(100, -96); ant.cubicTo(80, -150, 60, -170, 40, -175); ant.moveTo(88, -140); ant.lineTo(110, -165); ant.moveTo(70, -160); ant.lineTo(78, -190)
        ant.moveTo(110, -96); ant.cubicTo(115, -140, 130, -160, 150, -170); ant.moveTo(122, -140); ant.lineTo(145, -150)
        c.drawPath(ant, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=color("#D9C6A0", a), StrokeCap=skia.Paint.kRound_Cap))
        c.drawOval(skia.Rect(-92, -36, -74, -10), relleno("#F2ECE0", a))
        c.restore()

    def e_tundra(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tn, tr = _tw(self, e, s.get("nube_word")), _tw(self, e, s.get("ruta_word"))
        gy = 860
        for k, (col, yy) in enumerate((("#AFC2D6", gy - 140), ("#93A9C0", gy - 70))):
            m = skia.Path(); m.moveTo(-40, gy)
            for x in range(-40, W + 80, 80): m.lineTo(x, yy - 60 * math.sin(x * .006 + k * 2) - 30 * math.sin(x * .017))
            m.lineTo(W + 40, gy); m.close(); c.drawPath(m, relleno(col))
        c.drawRect(skia.Rect(-40, gy, W + 40, 1260), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, gy), (0, 1260)], [color("#9CB48A"), color("#6E8A5E")])))
        rng = np.random.default_rng(6)
        for k in range(50): c.drawLine(float(rng.random() * W), float(gy + 10 + rng.random() * 300), float(rng.random() * W), float(gy + 10 + rng.random() * 300), trazo("#5A7048", 2, .0))
        for k in range(40):
            x = float(rng.random() * W); y = float(gy + 20 + rng.random() * 300); c.drawLine(x, y, x + 6, y - 18, trazo("#4E6A3E", 3, .6)); c.drawLine(x + 8, y, x + 4, y - 22, trazo("#4E6A3E", 3, .6))
        gira = _io(TI.clamp((t - tr) / .6))
        for k in range(3):
            base = 235 + k * 265; y = gy + 70 + (k % 2) * 90
            x = base + 6 * (t - e["t0"]) * (1 if gira < .5 else -1)
            dirx = 1 if gira < .5 else -1
            _reno(c, x, y, 1.15 - .08 * (k % 2), 1.0, t, dirx, k)
        if t > tn - .2:
            un = TI.clamp((t - tn + .2) / 1.2); cx_, cy_ = CX + 60, 520
            rng = np.random.default_rng(11); pts = skia.Path()
            for k in range(int(500 * un)):
                r = 300 * math.sqrt(rng.random()); an = rng.random() * 6.28 + t * (.3 + rng.random())
                x = cx_ + r * math.cos(an) * 1.4 + 10 * math.sin(t * 9 + k); y = cy_ + r * math.sin(an) * .75 + 8 * math.cos(t * 11 + k)
                pts.addCircle(x, y, 3.2)
            c.drawPath(pts, relleno("#1A1A22", .75))
            if un > .6: self.pildora(c, s.get("nube_txt", "NUBE DE MOSQUITOS"), cx_, cy_ - 300, S, aparece(t - tn - .5, .15), fnt=self.F["pillb"], fondo="#0C1630")
        if gira > 0: self.pildora(c, s.get("ruta_txt", "CAMBIAN DE RUTA"), CX, 1150, S, gira, fnt=self.F["pillb"], fondo="#E5322D")

    # ---------------------------------------------------------------- orquídea y mosquito macho
    def _flor(c, x, y, s, a, t, brillo=0):
        c.save(); c.translate(x, y); c.scale(s, s); c.rotate(4 * math.sin(t * 1.1))
        for ang, L, W_ in ((-90, 90, 46), (-20, 80, 34), (200, 80, 34), (30, 70, 30), (150, 70, 30)):
            c.save(); c.rotate(ang)
            c.drawOval(skia.Rect(0, -W_ / 2, L, W_ / 2), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (L, 0)], [color("#F4FBE6", a), color("#CFE7A8", a)])))
            c.drawLine(8, 0, L - 10, 0, trazo("#A9C97A", 1.5, .6 * a)); c.restore()
        lab = skia.Path(); lab.moveTo(-14, 10); lab.cubicTo(-20, 80, 0, 120, 6, 130); lab.cubicTo(14, 100, 22, 60, 14, 10); lab.close()
        c.drawPath(lab, relleno("#DDEFB8", a))
        c.drawLine(0, 6, 40, 150, trazo("#B8D88A", 6, a))   # espolón con néctar
        c.drawCircle(0, 0, 14, relleno("#E8F5C8", a))
        if brillo > 0:
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawCircle(0, 0, 60, skia.Paint(AntiAlias=True, Color=color("#FFF3A0", .5 * brillo), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20)))
        c.restore()

    def e_orquidea(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tm, tpo = _tw(self, e, s.get("macho_word")), _tw(self, e, s.get("polen_word"))
        # tallo y hojas
        st = skia.Path(); st.moveTo(CX - 40, 1250); st.cubicTo(CX - 60, 950, CX + 40, 700, CX + 10, 330)
        c.drawPath(st, trazo("#4E8A3A", 14))
        for sx, yy in ((-1, 1080), (1, 960)):
            lf = skia.Path(); lf.moveTo(CX - 40, yy); lf.cubicTo(CX - 40 + sx * 200, yy - 120, CX - 40 + sx * 320, yy - 40, CX - 40 + sx * 360, yy - 140)
            lf.cubicTo(CX - 40 + sx * 260, yy + 20, CX - 40 + sx * 120, yy + 40, CX - 40, yy); c.drawPath(lf, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(CX, yy - 140), (CX, yy + 40)], [color("#7CC25A"), color("#3E7A2C")])))
        flores = [(CX + 10, 340, 1.0), (CX - 90, 490, 1.1), (CX + 100, 630, 1.75), (CX - 60, 800, 1.1), (CX + 50, 930, 1.0)]
        bri = TI.clamp((t - tpo) / .3) * (1 - TI.clamp((t - tpo - 1.5) / .6))
        for k, (fx, fy, fs) in enumerate(flores): _flor(c, fx, fy, fs, aparece(dt0 - k * .08, .2), t, bri if k == 2 else 0)
        # mosquito macho que llega a la flor grande
        if t > tm - .6:
            u = resorte(t - tm + .6, 4, 6); tx_, ty_ = CX + 300, 530
            mx = tx_ + 500 * (1 - u); my = ty_ - 220 * (1 - u) + 6 * math.sin(t * 3)
            _mosquito(c, mx, my, 1.25, t, 1.0, rot=-28, macho=True, sentado=u > .95)
            if t > tpo:   # polinios amarillos pegados a la cabeza
                for k in range(2): c.drawOval(skia.Rect(mx - 84 + k * 18, my - 52, mx - 66 + k * 18, my - 18), relleno("#FFD23A", aparece(t - tpo, .2)))
            if t - tm > .8: self.pildora(c, s.get("macho_txt", "MACHO · NO PICA"), CX, 1160, S, aparece(t - tm - .8, .15), fnt=self.F["pillb"], fondo="#2F6BFF")
        for q in s.get("rotulos", []):
            dq = t - self.ta(q["word"], e)
            if dq > 0: self.pildora(c, q["txt"], CX, 210, S, aparece(dq, .15), fnt=self.F["pillb"], fondo="#0C1630")

    # ---------------------------------------------------------------- red de comida
    def e_red(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        th, tr = _tw(self, e, s.get("hueco_word")), _tw(self, e, s.get("relleno_word"))
        nodos = s["nodos"]; n = len(nodos); R = 360; cy = 680
        uh = TI.clamp((t - th) / .4); ur = resorte(t - tr, 6, 8) if t > tr else 0
        for k, txt in enumerate(nodos):
            an = -math.pi / 2 + 2 * math.pi * k / n; x = CX + R * math.cos(an); y = cy + R * math.sin(an) * .95
            a = aparece(dt0 - .1 * k, .2)
            col = "#2FBF71" if ur > .5 else ("#E5322D" if uh > 0 else "#9DB8FF")
            if ur > .5 or uh <= 0:
                c.drawLine(CX, cy, x, y, trazo(col, 5, .8 * a))
            else:
                L = math.hypot(x - CX, y - cy); nseg = int(L / 26)
                for j in range(0, nseg, 2):
                    q0, q1 = j / nseg, (j + 1) / nseg; c.drawLine(CX + (x - CX) * q0, cy + (y - cy) * q0, CX + (x - CX) * q1, cy + (y - cy) * q1, trazo(col, 5, .8 * a))
            sc = .8 + .2 * resorte(dt0 - .1 * k, 8, 11)
            c.drawCircle(x, y, 104 * sc, relleno("#0B1530", .85 * a)); c.drawCircle(x, y, 104 * sc, trazo(col, 4, a))
            f = fuente("Inter", 800, 34); ww = ancho(txt, f); f = f if ww < 180 else fuente("Inter", 800, int(34 * 180 / ww))
            texto(c, txt, x, y, f, "#FFFFFF", alfa=a)
        # centro: mosquito → hueco → otro insecto
        if uh < 1:
            c.drawCircle(CX, cy, 120, relleno("#0B1530", .9 * (1 - uh))); _mosquito(c, CX + 10, cy, .55 * (1 - uh), t, 1 - uh)
        if uh > 0:
            dash = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=color("#E5322D" if ur < .5 else "#2FBF71"), PathEffect=skia.DashPathEffect.Make([18, 12], t * 30))
            c.drawCircle(CX, cy, 120, dash); _puf(c, CX, cy, t - th, 1.0, 120)
            if ur <= 0: texto(c, "?", CX, cy, fuente("Inter", 800, 110), "#E5322D", alfa=uh)
        if ur > 0:
            x = CX + 600 * (1 - ur)
            c.drawCircle(x, cy, 120, relleno("#0E3A26", .95)); _mosquito(c, x + 10, cy, .5, t, 1.0, cuerpo="#3A5A2A")
            self.pildora(c, s.get("relleno_txt", "OTROS INSECTOS"), CX, cy + 440, S, min(1, ur), fnt=self.F["pillb"], fondo="#1F7A3A")

    # ---------------------------------------------------------------- especies: 3.500 puntos, solo 100 pican
    def e_especies(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tw = self.ta(s["word"], e); tp = _tw(self, e, s.get("pican_word"))
        tot, pic = s.get("total", 3500), s.get("pican", 100); cols = 70; rows = math.ceil(tot / cols)
        x0, y0, dx = CX - 410, 430, 820 / cols
        llen = TI.cubic_out(TI.clamp((t - tw + .1) / 1.2)); nvis = int(tot * llen)
        up = TI.clamp((t - tp) / .4)
        rng = np.random.default_rng(12); rojos = set(rng.choice(tot, pic, replace=False).tolist())
        pn = skia.Path(); pr = skia.Path()
        for i in range(nvis):
            r_, c_ = divmod(i, cols); x = x0 + c_ * dx + dx / 2; y = y0 + r_ * dx + dx / 2
            if i in rojos and up > 0: pr.addCircle(x, y, 3.6 + 4 * up)
            else: pn.addCircle(x, y, 3.6)
        c.drawPath(pn, relleno(S["sub"], .85 - .6 * up))
        if up > 0:
            with capa(c, alfa=up, blur=8): c.drawPath(pr, relleno("#FF4A3A"))
            c.drawPath(pr, relleno("#FF5A4A", up))
        v = 3500 * llen if up <= 0 else 3500 + (pic - 3500) * TI.cubic_out(up)
        txt = f"{int(round(v)):,}".replace(",", ".")
        c.save(); c.translate(CX, 300); sc = .9 + .1 * resorte(t - tw + .1, 8, 11); c.scale(sc, sc)
        texto(c, txt, 0, 0, fuente("Inter", 800, 130), "#FF5A4A" if up > .5 else S["txt"], alfa=aparece(t - tw + .1, .15), tnum=True); c.restore()
        lab = s.get("pican_label", "PICAN A HUMANOS") if up > .5 else s.get("label", "ESPECIES DE MOSQUITO")
        texto(c, lab, CX, y0 + rows * dx + 70, fuente("Inter", 800, 44), "#FF5A4A" if up > .5 else S["acc"], alfa=aparece(t - tw, .2))

    # ---------------------------------------------------------------- selectivo: solo los que enferman
    def e_selectivo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        to, tb = _tw(self, e, s.get("objetivo_word")), _tw(self, e, s.get("borra_word"))
        malos = s.get("malos", [4, 10]); uo = TI.clamp((t - to) / .4); ub = TI.clamp((t - tb) / .3)
        for k in range(15):
            r_, c_ = divmod(k, 5); bx, by = CX - 340 + c_ * 170, 430 + r_ * 270
            x, y = bx + 18 * math.sin(t * 2.1 + k), by + 14 * math.sin(t * 2.7 + k * 1.3)
            malo = k in malos; a = aparece(dt0 - k * .03, .2)
            if malo and ub > 0:
                _puf(c, x, y, t - tb, 1.0, 80)
                continue
            _mosquito(c, x, y, .58, t + k * .1, a, flip=k % 2 == 0, cuerpo="#5A1A22" if (malo and uo > 0) else "#2A2A34")
            if malo and uo > 0:
                rr = 95 - 25 * _io(uo); col = color("#FF4A3A", uo)
                c.drawCircle(x, y, rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col))
                for ang in (0, 90, 180, 270):
                    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                    c.drawLine(x + ca * (rr - 20), y + sa * (rr - 20), x + ca * (rr + 20), y + sa * (rr + 20), skia.Paint(AntiAlias=True, StrokeWidth=5, Color=col))
        if s.get("pill_txt") and uo > 0: self.pildora(c, s["pill_txt"], CX, 1150, S, uo, fnt=self.F["pillb"], fondo="#E5322D")

    # ---------------------------------------------------------------- efectos
    def efectos_mosquito(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; T = lambda w: self.ta(w, e)
        if tp == "mosquito":
            self.sfx(TI.f_de_t(e["t0"] + .05), "zumbido", .8)
            for w in s.get("zumbido", []): self.sfx(TI.f_de_t(T(w)), "zumbido", .9)
            if s.get("golpe_word"):
                tg = T(s["golpe_word"]); self.sfx(TI.f_de_t(tg - .2), "whoosh", .5); self.sfx(TI.f_de_t(tg), "plaf", 1.0); self.sfx(TI.f_de_t(tg + .5), "puf", .9)
            if s.get("reloj"): self.sfx(TI.f_de_t(e["t0"] + .4), "bip", .5)
        if tp == "ranking":
            if s.get("tiburon_word"): pon(T(s["tiburon_word"]), "whoosh", .4); self.sfx(TI.f_de_t((T(s["cruz_word"]) if s.get("cruz_word") else T(s["tiburon_word"]) + .45) + .05), "sello", .55)
            if s.get("mosquito_word"): self.sfx(TI.f_de_t(T(s["mosquito_word"])), "zumbido", .8); self.sfx(TI.f_de_t(T(s["mosquito_word"]) + .45), "campana", .5)
        if tp == "contagio":
            if s.get("pica_word"): self.sfx(TI.f_de_t(T(s["pica_word"]) + .1), "tic", .7)
            if s.get("parasitos_word"):
                for j in range(4): self.sfx(TI.f_de_t(T(s["parasitos_word"]) + j * .25), "burbuja", .5)
            if s.get("stat"): self.rodillo(T(s["stat"]["word"]), s["stat"].get("dur", 1.0))
            if s.get("cero_word"): self.rodillo(T(s["cero_word"]), 1.0); self.sfx(TI.f_de_t(T(s["cero_word"]) + 1.0), "destello", .7)
        if tp == "zumbido":
            if s.get("zumbido_word"): self.sfx(TI.f_de_t(T(s["zumbido_word"])), "zumbido", 1.0); self.sfx(TI.f_de_t(T(s["zumbido_word"]) + .95), "zumbido", .7)
            if s.get("despierta_word"): self.sfx(TI.f_de_t(T(s["despierta_word"])), "parpadeo", .9)
            if s.get("fin_word"): self.sfx(TI.f_de_t(T(s["fin_word"])), "puf", .8); self.sfx(TI.f_de_t(T(s["fin_word"]) + .5), "zzz", .8)
        if tp == "estanque":
            if s.get("larvas_word"): pon(T(s["larvas_word"]), "pop", .4)
            if s.get("pez_word"):
                for j in range(5): self.sfx(TI.f_de_t(T(s["pez_word"]) + .35 + j * .38), "nam", .7)
                self.sfx(TI.f_de_t(T(s["pez_word"])), "burbuja", .6)
            if s.get("libelula_word"): self.sfx(TI.f_de_t(T(s["libelula_word"])), "zum", .5)
        if tp == "tundra":
            for j in range(8): self.sfx(TI.f_de_t(e["t0"] + .3 + j * .5), "paso", .5)
            if s.get("nube_word"): self.sfx(TI.f_de_t(T(s["nube_word"])), "zumbido", 1.0); self.sfx(TI.f_de_t(T(s["nube_word"]) + .8), "zumbido", .8)
            if s.get("ruta_word"): pon(T(s["ruta_word"]), "whoosh", .5)
        if tp == "orquidea":
            if s.get("macho_word"): self.sfx(TI.f_de_t(T(s["macho_word"]) - .5), "zumbido", .6)
            if s.get("polen_word"): self.sfx(TI.f_de_t(T(s["polen_word"]) + .05), "destello", .8)
            for q in s.get("rotulos", []): pon(T(q["word"]), "pop", .4)
        if tp == "red":
            if s.get("hueco_word"): self.sfx(TI.f_de_t(T(s["hueco_word"])), "puf", .8)
            if s.get("relleno_word"): self.sfx(TI.f_de_t(T(s["relleno_word"])), "desliz", .7); self.sfx(TI.f_de_t(T(s["relleno_word"]) + .4), "clac", .8)
        if tp == "especies":
            tw = T(s["word"])
            for j in range(10): self.sfx(TI.f_de_t(tw + j * .11), "tic", .5)
            if s.get("pican_word"): self.sfx(TI.f_de_t(T(s["pican_word"])), "golpe", .6); self.rodillo(T(s["pican_word"]), .5)
        if tp == "selectivo":
            if s.get("objetivo_word"): self.sfx(TI.f_de_t(T(s["objetivo_word"])), "bip", .6); self.sfx(TI.f_de_t(T(s["objetivo_word"]) + .2), "bip", .5)
            if s.get("borra_word"): self.sfx(TI.f_de_t(T(s["borra_word"])), "puf", .9)

    for k, fn in (("mosquito", e_mosquito), ("ranking", e_ranking), ("contagio", e_contagio), ("zumbido", e_zumbido), ("estanque", e_estanque),
                  ("tundra", e_tundra), ("orquidea", e_orquidea), ("red", e_red), ("especies", e_especies), ("selectivo", e_selectivo)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_mosquito)
