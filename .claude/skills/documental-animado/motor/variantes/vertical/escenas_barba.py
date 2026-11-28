"""Escenas del documental 17 («¿Te afeitas para que te salga más barba? No funciona»).

Protagonista nuevo en primer plano (`self.cara_b`): chaval con sudadera naranja (la misma del 14–16), cara grande con BARBA PARAMÉTRICA
(cobertura 0–1, largo en px, parches 0–1: las zonas de las mejillas que «pasan» de la DHT), espuma de afeitar que la cuchilla limpia,
expresiones (neutral, feliz, o, triste, meh, mira_izq) y canas (abuelo).
espejo       baño con espejo y luces: modo gancho (afeita_word: la cuchilla limpia una franja de espuma; no_word: sello «NO FUNCIONA»)
             o cierre (suelta_word: deja la cuchilla en el vaso; crece_word: días que ruedan y la barba crece; parches_word: sale a
             parches; abuelo_word: aparece el retrato del abuelo con la misma barba a parches).
piel         corte de la piel con folículos: foliculo_word (se ilumina uno), cuchilla_word (la hoja corta a ras y las puntas caen),
             raiz_word (los bulbos siguen a lo suyo, «z», y el pelo vuelve a salir).
laboratorio  1928 en sepia: año que rueda (anio_word), Mildred Trotter al microscopio (nombre_word), ficha con zonas afeitada / sin
             afeitar (zonas_word) y tres comprobaciones (checks [{word, txt}]).
piernas      1970: dos piernas, la cuchilla pasa por una (afeita_word), la otra se queda (otra_word), semanas después lupas con el
             mismo pelo (medir_word + pill).
punta        un pelo sin cortar (punta fina) y otro afeitado: punta_word, lapiz_word, corte_word (la cuchilla lo corta), romo_word,
             pincha_word (dedo, ¡RASP!), sol_word (el sol aclara la punta larga), oscuro_word.
genes        ADN que gira, folículo con la testosterona que entra y se convierte en DHT (testo_word, dht_word), dial de «caso»
             (caso_word); parches_word: cara con zonas que escuchan (escuchan_word) y que pasan (pasan_word).
edad         la cara con años que ruedan (edad_word: desde → hasta) y la barba que se rellena; regla_word: regla + 1 cm al mes.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]
    G["SUP"].setdefault("bano", dict(a="#CFE6E8", b="#7FAAB2", txt="#FFFFFF", sub="#E6F6F8", acc="#FFD84A", tierra="#9CC7CC", borde="#5E9AA4", grid=False))
    FNT = {}
    def F(peso, px, fam="Inter"):
        k = (fam, peso, px)
        if k not in FNT: FNT[k] = fuente(fam, peso, px)
        return FNT[k]

    # ---------------------------------------------------------------- sonidos propios (eventos cortos y suaves)
    def s_cuchilla():
        """Pasada de cuchilla: raspado de banda alta con granos (pelos que se cortan)."""
        d = .45; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        x = AU._banda(AU._ruido(n, 171), 2500, 9000) * np.sin(np.pi * u) ** .8
        g = (AU._ruido(n, 172) > 2.2).astype(float) * AU._ruido(n, 173)
        return x * .7 + .5 * AU._banda(g, 3000, 9000) * np.sin(np.pi * u)
    def s_espuma():
        d = .5; n = int(d * AU.SR); u = np.linspace(0, 1, n); rng = np.random.default_rng(174); x = np.zeros(n)
        for k in range(26):
            a = int(rng.random() * (n - 900)); m = 300 + int(rng.random() * 500); tt = np.arange(m) / AU.SR
            x[a:a + m] += np.sin(2 * np.pi * (1800 + 2500 * rng.random()) * tt) * np.exp(-tt / .004) * .5
        return x * np.sin(np.pi * u)
    def s_rasp():
        d = .35; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 175), 1200, 6000) * (.6 + .4 * np.sign(np.sin(2 * np.pi * 38 * t))) * np.sin(np.pi * t / d)
    def s_sello():
        d = .3; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.tanh(2 * (np.sin(2 * np.pi * (95 - 40 * t) * t) * np.exp(-t / .06) + .4 * AU._banda(AU._ruido(n, 176), 200, 1500) * np.exp(-t / .03)))
    def s_cristal():
        d = .25; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 3100 * t) + .6 * np.sin(2 * np.pi * 4650 * t)) * np.exp(-t / .05) * np.minimum(1, t / .002)
    def s_flash():
        d = .3; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 177), 3000, 10000) * np.exp(-t / .02) + .4 * np.sin(2 * np.pi * 1400 * t) * np.exp(-t / .05)
    for nom, fn, db in (("cuchilla", s_cuchilla, -27), ("espuma", s_espuma, -32), ("rasp", s_rasp, -27), ("sello2", s_sello, -24),
                        ("cristal", s_cristal, -30), ("flash", s_flash, -31)):
        AU.SFX.setdefault(nom, (fn, db))

    # ---------------------------------------------------------------- utilidades de dibujo
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
    def _polvo(c, t, x0, x1, y0, y1, a, seed=5, n=40, col="#FFF6D0"):
        rng = np.random.default_rng(seed)
        for k in range(n):
            x = x0 + (x1 - x0) * ((rng.random() + .02 * t * (rng.random() - .5)) % 1); y = y0 + (y1 - y0) * ((rng.random() - .015 * t * (.5 + rng.random())) % 1)
            c.drawCircle(x, y, 1.2 + 2.4 * rng.random(), relleno(col, a * (.3 + .5 * rng.random()) * (.6 + .4 * math.sin(t * 2 + k))))
    def _sello(c, txt, x, y, t, tw, col="#E5322D", rot=-12, px=92):
        """Sello de goma que cae con golpe (escala 1.6 → 1) y textura de tinta gastada."""
        if t < tw: return
        dt = t - tw; a = aparece(dt, .06); sc = 1 + .6 * math.exp(-dt * 16) * math.cos(dt * 10)
        f = F(900, px); w = ancho(txt, f) + 70; h = px * 1.5
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
        c.drawRRect(rrc(6, 10, w, h, 18), skia.Paint(AntiAlias=True, Color=color("#000000", .25 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
        c.drawRRect(rrc(0, 0, w, h, 18), relleno("#FFFFFF", .16 * a))
        c.drawRRect(rrc(0, 0, w, h, 18), trazo(col, 10, a)); c.drawRRect(rrc(0, 0, w - 26, h - 26, 10), trazo(col, 3, .8 * a))
        texto(c, txt, 0, 2, f, col, alfa=a, tracking=.04)
        rng = np.random.default_rng(31)                                         # huecos de tinta
        for k in range(26):
            c.drawCircle(-w / 2 + w * rng.random(), -h / 2 + h * rng.random(), 2 + 5 * rng.random(), relleno("#FFFFFF", .35 * a))
        c.restore()
    def _mano(c, x, y, sc, a=1.0, rot=0.0):
        """Puño que agarra un mango vertical en (x, y); el antebrazo con manga naranja baja hacia abajo-derecha."""
        P = ("#F8D5B8", "#E6AC86", "#C98763")
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
        c.drawLine(40, 40, 230, 420, skia.Paint(AntiAlias=True, StrokeWidth=92, StrokeCap=skia.Paint.kRound_Cap, Color=color(P[1], a)))
        c.drawLine(120, 200, 300, 560, skia.Paint(AntiAlias=True, StrokeWidth=130, StrokeCap=skia.Paint.kRound_Cap, Shader=_lin(200, 560, ["#FF8A3D", "#B8401C"], a)))
        c.drawLine(110, 190, 150, 270, skia.Paint(AntiAlias=True, StrokeWidth=134, Color=color("#FFB070", .5 * a)))
        c.drawRRect(rrc(18, 30, 100, 120, 44), _p(_rad(0, 0, 110, P, [0, .6, 1], a)))
        for k in range(4): c.drawRRect(rrc(-26, -14 + k * 26, 46, 30, 15), _p(_linx(-50, -2, [P[0], P[2]], a)))
        c.drawRRect(rrc(-14, -38, 30, 52, 15), _p(_lin(-64, -12, P, a)))
        c.restore()
    def _cuchilla(c, x, y, sc, rot, a=1.0, mano=True):
        """Maquinilla: cabezal en (x, y), mango hacia abajo. rot en grados."""
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
        _sombra(c, 10, 140, 40, 120, .25 * a)
        c.drawRRect(rrc(0, 150, 46, 250, 23), _p(_linx(-23, 23, ["#2A4A8A", "#4A7AD8", "#1A2E5A"], a, [0, .4, 1])))
        for k in range(6): c.drawLine(-14, 90 + k * 22, 14, 90 + k * 22, trazo("#1A2E5A", 3, .6 * a))
        c.drawRRect(rrc(0, 24, 30, 30, 8), relleno("#C9D0DE", a))
        c.drawRRect(rrc(0, 0, 150, 52, 14), _p(_lin(-26, 26, ["#F4F6FA", "#AEB8CA", "#7A8498"], a)))
        for k in range(3): c.drawLine(-64, -12 + k * 12, 64, -12 + k * 12, trazo("#5A6478", 2, .9 * a))
        c.drawRRect(rrc(0, -22, 150, 10, 5), relleno("#7FD3FF", .8 * a))               # banda lubricante
        c.restore()
        if mano:
            r = math.radians(rot); gx, gy = x - 190 * math.sin(r) * sc, y + 190 * math.cos(r) * sc
            _mano(c, gx, gy, sc * .9, a, rot)

    # ---------------------------------------------------------------- protagonista: cara grande con barba paramétrica
    SUDA = ["#FF9A4D", "#F26B1D", "#B8401C"]; PIEL = ["#FBE0C8", "#F1C3A0", "#D99A74"]
    _BP = {}
    def _cabeza_path():
        p = skia.Path(); p.moveTo(0, -250)
        p.cubicTo(120, -250, 196, -170, 196, -50); p.cubicTo(196, 50, 180, 120, 140, 180)
        p.cubicTo(100, 235, 50, 258, 0, 258); p.cubicTo(-50, 258, -100, 235, -140, 180)
        p.cubicTo(-180, 120, -196, 50, -196, -50); p.cubicTo(-196, -170, -120, -250, 0, -250); p.close()
        return p
    HEAD = _cabeza_path()
    def _barba_pts():
        """Puntos fijos de la barba (x, y, sensibilidad 0–1). Las mejillas altas son las zonas que «pasan»."""
        if _BP: return _BP["p"]
        rng = np.random.default_rng(1717); pts = []
        while len(pts) < 1500:
            x, y = rng.uniform(-195, 195), rng.uniform(-60, 262)
            if not HEAD.contains(x, y): continue
            r_boca = ((x / 72) ** 2 + ((y - 128) / 26) ** 2)
            if r_boca < 1: continue                                                       # boca libre
            bigote = abs(x) < 80 and 92 < y < 112
            mejilla = y > 40 + .18 * abs(x) * 0 and (abs(x) > 60 or y > 150)
            patilla = abs(x) > 168 and y > -60
            if not (bigote or patilla or (y > 60 and mejilla) or y > 150): continue
            if abs(x) < 168 and y < 60 and not bigote: continue
            # sensibilidad: alta en barbilla y bigote, baja en dos parches de mejilla (forma orgánica)
            s = .85 + .15 * rng.random()
            for cx_, cy_, rr in ((-120, 85, 62), (118, 95, 58), (-75, 175, 28), (150, 20, 30)):
                d = math.hypot(x - cx_, (y - cy_) * 1.2) / rr
                if d < 1: s = min(s, .15 + .5 * d + .1 * rng.random())
            pts.append((x, y, s, rng.random(), rng.uniform(-.25, .25)))
        _BP["p"] = np.array(pts); return _BP["p"]
    def _espuma_pts():
        if "e" in _BP: return _BP["e"]
        rng = np.random.default_rng(1718); pts = []
        while len(pts) < 150:
            x, y = rng.uniform(-190, 190), rng.uniform(-20, 262)
            if not HEAD.contains(x, y * .98) or ((x / 70) ** 2 + ((y - 128) / 24) ** 2) < 1: continue
            if abs(x) < 120 and y < 70: continue
            pts.append((x, y, 18 + 22 * rng.random(), rng.random()))
        _BP["e"] = np.array(pts); return _BP["e"]

    def cara(self, c, x, y, s, t, cob=.5, largo=3.0, parches=0.0, espuma=0.0, limpio=None, expr="neutral", mira=(0.0, 0.0), canas=0.0,
             a=1.0, zonas=None, ropa=True):
        """Busto: (x, y) = centro de la cabeza. limpio(x, y) → True si la cuchilla ya ha pasado por ahí (sin espuma ni pelo)."""
        if a <= 0: return
        pelo_c = _mix("#4A2C1A", "#D8D8DE", canas); barba_c = _mix("#3A2216", "#CFCFD6", canas)
        c.save(); c.translate(x, y); c.scale(s, s)
        if ropa:                                                                   # hombros y sudadera
            c.drawPath(skia.Path.Polygon([(-70, 200), (70, 200), (80, 330), (-80, 330)], True), _p(_lin(200, 330, [PIEL[1], PIEL[2]], a)))
            sh = skia.Path(); sh.moveTo(-330, 600); sh.cubicTo(-330, 380, -250, 310, -90, 290); sh.lineTo(90, 290)
            sh.cubicTo(250, 310, 330, 380, 330, 600); sh.close()
            c.drawPath(sh, _p(_lin(290, 600, SUDA, a)))
            c.drawPath(sh, _p(_rad(-120, 340, 300, ["#FFFFFF", "#FFFFFF"], None, .0)))
            cu = skia.Path(); cu.moveTo(-100, 292); cu.quadTo(0, 380, 100, 292); cu.quadTo(0, 340, -100, 292); cu.close()
            c.drawPath(cu, relleno(SUDA[2], .8 * a))
            for sx in (-1, 1):
                c.drawLine(sx * 34, 330, sx * 40 + 4 * math.sin(t * 1.5 + sx), 440, trazo("#FFFFFF", 7, .9 * a))
                c.drawCircle(sx * 40 + 4 * math.sin(t * 1.5 + sx), 446, 8, relleno("#E9EDF4", a))
            c.drawRRect(rrc(-170, 420, 90, 140, 40), relleno("#FFFFFF", .07 * a))
        _sombra(c, 0, 250, 150, 30, .25 * a)
        for sx in (-1, 1):                                                         # orejas
            c.drawOval(skia.Rect(sx * 196 - 30, -60, sx * 196 + 30, 50), _p(_lin(-60, 50, PIEL, a)))
            c.drawOval(skia.Rect(sx * 196 - 14, -36, sx * 196 + 12, 26), relleno(PIEL[2], .45 * a))
        c.drawPath(HEAD, _p(_rad(-60, -90, 380, PIEL, [0, .62, 1], a)))
        c.drawOval(skia.Rect(-150, -40, -60, 40), relleno("#FF8A80", .16 * a)); c.drawOval(skia.Rect(60, -40, 150, 40), relleno("#FF8A80", .16 * a))
        # ---- barba
        P = _barba_pts(); thr = cob
        vis = P[:, 3] < thr * (P[:, 2] ** (1 + 4 * parches))
        if limpio is not None: vis &= ~np.array([limpio(px, py) for px, py in P[:, :2]])
        if zonas:                                                                # mapa de zonas: escuchan (verde) / pasan (gris)
            z_si, z_no = zonas if isinstance(zonas, tuple) else (zonas, zonas)
            for zx, zy, rr in ((0, 205, 95), (-60, 105, 55), (60, 105, 55), (-175, 10, 40), (175, 10, 40), (-110, 190, 55), (110, 190, 55)):
                with capa(c, modo=skia.BlendMode.kPlus):
                    c.drawCircle(zx, zy, rr * 1.4, _p(_rad(zx, zy, rr * 1.4, ["#46E0A0", "#000000"], None, .3 * z_si * a)))
            for zx, zy, rr in ((-120, 85, 62), (118, 95, 58)):
                c.drawCircle(zx, zy, rr, _p(_rad(zx, zy, rr, ["#5A6478", "#5A6478", "#000000"], [0, .6, 1], .0)))
                p_ = trazo("#AEB8CA", 4, .9 * z_no * a); p_.setPathEffect(skia.DashPathEffect.Make([10, 8], t * 20))
                c.drawCircle(zx, zy, rr, p_)
                c.drawLine(zx - 18, zy - 18, zx + 18, zy + 18, trazo("#AEB8CA", 6, z_no * a)); c.drawLine(zx + 18, zy - 18, zx - 18, zy + 18, trazo("#AEB8CA", 6, z_no * a))
        if vis.any():
            c.save()
            if largo < 30: c.clipPath(HEAD, doAntiAlias=True)
            # sombra azulada de barba (lo que se ve bajo la piel)
            sombra_a = .32 * min(1.0, cob * 1.2) * TI.clamp(largo / 2)
            if sombra_a > 0:
                for px, py, ss, rr, ang in P[vis][::3]:
                    c.drawCircle(px, py, 13, relleno(_mix("#5A6A7A", barba_c, .3), sombra_a * .22 * a))
            L = largo
            if L < 6:
                for px, py, ss, rr, ang in P[vis]:
                    c.drawCircle(px, py, 8, relleno(_mix("#6A7A8A", barba_c, .35), .07 * a))
                for px, py, ss, rr, ang in P[vis]:
                    c.drawCircle(px + 2 * ang, py, .9 + .22 * L, relleno(_mix(barba_c, "#5A6A7A", .3), (.32 + .08 * L) * a))
            else:
                if L > 12:
                    for px, py, ss, rr, ang in P[vis][::2]:
                        c.drawCircle(px, py + L * .3, 7 + L * .22, relleno(barba_c, .5 * a))
                for px, py, ss, rr, ang in P[vis]:
                    dx = px / 260 + ang + .08 * math.sin(t * 1.3 + rr * 9); dy = 1.0
                    nn = math.hypot(dx, dy); l = L * (.75 + .5 * rr)
                    if abs(px) < 80 and 90 < py < 115: dx, dy, nn = (1 if px > 0 else -1) * .9, .45, 1.0       # bigote hacia los lados
                    pa = skia.Paint(AntiAlias=True, StrokeWidth=3.2 + .04 * L, StrokeCap=skia.Paint.kRound_Cap, Color=color(_mix(barba_c, "#000000", .25 * rr), .85 * a))
                    c.drawLine(px, py, px + dx / nn * l, py + dy / nn * l, pa)
                    c.drawLine(px - .8, py, px + dx / nn * l * .7 - .8, py + dy / nn * l * .7, skia.Paint(AntiAlias=True, StrokeWidth=1.2, Color=color(_mix(barba_c, "#FFFFFF", .35), .35 * a)))
            c.restore()
        # ---- espuma
        if espuma > 0:
            E = _espuma_pts()
            for px, py, r, rr in E:
                if limpio is not None and limpio(px, py): continue
                c.drawCircle(px + 2, py + 4, r, relleno("#9FB3C9", .45 * espuma * a))
            for px, py, r, rr in E:
                if limpio is not None and limpio(px, py): continue
                c.drawCircle(px, py, r, _p(_rad(px - r * .35, py - r * .4, r * 1.3, ["#FFFFFF", "#F2F6FA", "#D9E2EC"], [0, .6, 1], espuma * a)))
                if rr > .6: c.drawCircle(px - r * .3, py - r * .35, r * .22, relleno("#FFFFFF", espuma * a))
        # ---- ojos, cejas, nariz, boca
        bl = 1.0 if (t * .9 + .3) % 3.4 > .13 else .1
        if expr == "meh": bl *= .55
        for sx in (-1, 1):
            ex, ey = sx * 78, -40
            c.drawOval(skia.Rect(ex - 34, ey - 26 * bl, ex + 34, ey + 26 * bl), relleno("#FFFFFF", a))
            if bl > .4:
                ix, iy = ex + mira[0] * 12, ey + mira[1] * 9
                c.drawCircle(ix, iy, 17, _p(_rad(ix - 4, iy - 4, 19, ["#7A4A2A", "#3A2010"], None, a)))
                c.drawCircle(ix, iy, 8, relleno("#120A06", a)); c.drawCircle(ix - 6, iy - 7, 5, relleno("#FFFFFF", .95 * a))
            c.drawOval(skia.Rect(ex - 34, ey - 26 * bl, ex + 34, ey + 26 * bl), trazo("#6A3A28", 3, .7 * a))
            lev = {"o": 18, "feliz": 6, "triste": -6, "meh": -2}.get(expr, 4); inc = {"triste": -.22, "meh": .1}.get(expr, 0) * sx
            c.drawLine(ex - 36, ey - 46 - lev + 36 * inc, ex + 34, ey - 50 - lev - 36 * inc,
                       skia.Paint(AntiAlias=True, StrokeWidth=13, StrokeCap=skia.Paint.kRound_Cap, Color=color(pelo_c, a)))
        c.drawPath(skia.Path.Polygon([(0, -14), (-22, 62), (20, 64)], True), relleno(PIEL[2], .35 * a))
        c.drawOval(skia.Rect(-26, 48, 26, 72), relleno(PIEL[2], .55 * a))
        my = 128
        if expr == "feliz":
            pb = skia.Path(); pb.moveTo(-52, my - 8); pb.quadTo(0, my + 50, 52, my - 8); pb.close(); c.drawPath(pb, relleno("#5A1E1E", a))
            c.drawRect(skia.Rect(-38, my - 8, 38, my + 2), relleno("#FFFFFF", a))
        elif expr == "o":
            c.drawOval(skia.Rect(-22, my - 18, 22, my + 22), relleno("#5A1E1E", a)); c.drawOval(skia.Rect(-12, my + 6, 12, my + 18), relleno("#E0646E", a))
        elif expr == "triste":
            c.drawArc(skia.Rect(-40, my, 40, my + 40), 200, 140, False, trazo("#5A1E1E", 8, a))
        elif expr == "meh":
            c.drawLine(-34, my + 6, 34, my + 2, trazo("#5A1E1E", 8, a))
        else:
            c.drawArc(skia.Rect(-40, my - 24, 40, my + 14), 20, 140, False, trazo("#5A1E1E", 8, a))
        # ---- pelo de arriba
        hp = skia.Path(); hp.moveTo(-200, -40); hp.cubicTo(-215, -230, -90, -300, 10, -290); hp.cubicTo(140, -290, 220, -220, 200, -40)
        for k in range(9):
            xx = 180 - k * 44; hp.lineTo(xx - 6, -150 - 30 * (k % 2) + 6 * math.sin(t * 2 + k)); hp.lineTo(xx - 26, -128)
        hp.close(); c.drawPath(hp, _p(_lin(-300, -120, [_mix(pelo_c, "#FFFFFF", .15), pelo_c], a)))
        c.drawOval(skia.Rect(-120, -268, -10, -240), relleno("#FFFFFF", .14 * a))
        c.restore()
    V.cara_b = cara

    # ---------------------------------------------------------------- baño con espejo
    def _bano(c, t, luz=1.0):
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#D6ECEE", "#A9CED3", "#7FAAB2", "#5E8A92"])))
        for i in range(-1, 14):
            for j in range(0, 24):
                x0, y0 = i * 86 + (43 if j % 2 else 0), j * 86
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + 3, y0 + 3, x0 + 83, y0 + 83), 6, 6), relleno("#FFFFFF", .10))
                c.drawLine(x0, y0, x0 + 86, y0, trazo("#5E9AA4", 2, .25))
        MX0, MX1, MY0, MY1 = 90, 950, 240, 1110
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(MX0 - 30, MY0 - 30, MX1 + 30, MY1 + 30), 60, 60), skia.Paint(AntiAlias=True, Color=color("#000000", .25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(MX0 - 24, MY0 - 24, MX1 + 24, MY1 + 24), 56, 56), _p(_lin(MY0, MY1, ["#F4F6FA", "#C9D0DE"])))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(MX0, MY0, MX1, MY1), 40, 40), _p(_lin(MY0, MY1, ["#E9F3F6", "#C4DCE2", "#A6C6CE"])))
        for k in range(5):                                                         # bombillas
            bx = MX0 + 90 + k * (MX1 - MX0 - 180) / 4; by = MY0 - 70
            with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(bx, by, 90, _p(_rad(bx, by, 90, ["#FFF2C0", "#000000"], None, .45 * luz)))
            c.drawCircle(bx, by, 26, _p(_rad(bx - 6, by - 6, 30, ["#FFFFFF", "#FFE9A8"], None, 1)))
        return MX0, MX1, MY0, MY1
    def _reflejo(c, MX0, MX1, MY0, MY1, t):
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(MX0, MY0, MX1, MY1), 40, 40), doAntiAlias=True)
        for k, (x, w) in enumerate(((180, 70), (300, 26), (760, 50))):
            xx = x + 20 * math.sin(t * .3 + k)
            c.drawPath(skia.Path.Polygon([(xx, MY0), (xx + w, MY0), (xx + w - 300, MY1), (xx - 300, MY1)], True), relleno("#FFFFFF", .10))
        c.restore()
    def _lavabo(c):
        c.drawRect(skia.Rect(-80, 1190, W + 80, H + 80), _p(_lin(1190, H, ["#6A4426", "#3A2410", "#24160A"])))   # mueble de madera oscura
        for k in range(4): c.drawLine(-80 + k * 380, 1200, -80 + k * 380, H, trazo("#1A0E04", 4, .5))
        c.drawRRect(rrc(CX, 1168, 960, 60, 28), _p(_lin(1138, 1198, ["#FFFFFF", "#D9E2EC", "#AEB8CA"])))
        c.drawRRect(rrc(CX, 1138, 980, 22, 11), relleno("#FFFFFF"))
        c.drawRRect(rrc(CX, 1112, 46, 50, 14), _p(_linx(CX - 23, CX + 23, ["#AEB8CA", "#FFFFFF", "#7A8498"])))
        c.drawRRect(rrc(CX + 36, 1092, 100, 26, 12), _p(_lin(1079, 1105, ["#FFFFFF", "#AEB8CA"])))
    def _vaso(c, x, y, a=1.0):
        c.drawPath(skia.Path.Polygon([(x - 60, y - 120), (x + 60, y - 120), (x + 48, y + 40), (x - 48, y + 40)], True), relleno("#E6F4FF", .45 * a))
        c.drawPath(skia.Path.Polygon([(x - 60, y - 120), (x + 60, y - 120), (x + 48, y + 40), (x - 48, y + 40)], True), trazo("#FFFFFF", 4, .8 * a))
        c.drawLine(x - 40, y - 100, x - 30, y + 20, trazo("#FFFFFF", 6, .5 * a))

    def e_espejo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "gancho")
        MX0, MX1, MY0, MY1 = _bano(c, t)
        fx, fy, fs = CX, 640, 1.3
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(MX0, MY0, MX1, MY1), 40, 40), doAntiAlias=True)
        c.drawRect(skia.Rect(MX0, MY0, MX1, MY1), _p(_rad(CX, 500, 600, ["#F2F8FA", "#C4DCE2"])))
        for i in range(0, 12):                                                     # azulejos reflejados detrás
            c.drawLine(MX0 + i * 86, MY0, MX0 + i * 86, MY1, trazo("#7FAAB2", 2, .18))
        if modo == "gancho":
            ta = _tw(self, e, "afeita_word"); tn = _tw(self, e, "no_word")
            # pasada de cuchilla: baja por la mejilla izquierda (de la imagen) entre ta−.25 y ta+.55
            u = _io((t - ta + .25) / .8); x_band = (-150, -40); y_c = -10 + 260 * u
            limpio = (lambda px, py: x_band[0] < px < x_band[1] and py < y_c) if t > ta - .25 else None
            expr = "o" if t > tn else ("neutral" if t < ta else "feliz")
            cara(self, c, fx, fy, fs, t, cob=.45, largo=2.6, parches=.6, espuma=1.0, limpio=limpio, expr=expr, mira=(0, .1))
            # cuchilla en la mano
            hx = fx + fs * (-95); hy = fy + fs * (y_c - 10) if t > ta - .25 else fy + fs * -20
            in_ = _io(dt0 / .5); out = _io((t - ta - .9) / .5)
            rx = hx + 520 * (1 - in_) + 520 * out
            _cuchilla(c, rx, hy, 1.0, -8 + 6 * math.sin(t * 2), 1.0)
            if 0 < t - ta < .9:
                self.comic_t(c, "¡ZAS!", fx + 250, fy - 260, 88, -8, .7 + .3 * resorte(t - ta, 10, 14), 1 - TI.clamp((t - ta - .65) / .25), "#FFE15A")
            # pelitos cortados que caen
            if t > ta - .1:
                rng = np.random.default_rng(3)
                for k in range(30):
                    t_k = ta - .1 + .7 * rng.random()
                    if t < t_k: continue
                    d = t - t_k; px = fx + fs * (-150 + 110 * rng.random()) + 40 * d * (rng.random() - .5); py = fy + fs * (260 * (t_k - ta + .25) / .8) + 500 * d * d + 30 * d
                    c.save(); c.translate(px, py); c.rotate(d * 300 * (rng.random() - .5))
                    c.drawLine(-4, 0, 4, 0, trazo("#3A2216", 3, TI.clamp(1.2 - d)))
                    c.restore()
        else:
            ts = _tw(self, e, "suelta_word"); tc = _tw(self, e, "crece_word"); tp = _tw(self, e, "paciencia_word"); tq = _tw(self, e, "parches_word"); tb = _tw(self, e, "abuelo_word")
            uc = _io((t - tc) / (tp - tc + 1.2)) if t > tc else 0
            largo = 2.5 + 30 * uc; cob = .45 + .55 * uc
            par = .15 + .85 * _io((t - tq) / .6)
            expr = "neutral"
            if t > tc: expr = "feliz"
            if t > tq: expr = "meh"
            if t > tb + .3: expr = "o"
            mira = (-.9, -.1) if t > tb + .2 else (0, .1)
            cara(self, c, fx, fy, fs, t, cob=cob, largo=largo, parches=par, expr=expr, mira=mira)
            # contador de días
            if t > tc:
                ud = TI.clamp((t - tc) / max(.5, (tp - tc + 1.0))); dia = 1 + int(round(89 * TI.cubic_out(ud)))
                a = aparece(t - tc, .15); cx_, cy_ = 835, 310
                c.save(); c.translate(cx_, cy_); c.scale(.78, .78); c.translate(-cx_, -cy_)
                c.drawRRect(rrc(cx_, cy_, 250, 140, 26), _p(_lin(cy_ - 70, cy_ + 70, ["#FFFFFF", "#E2E7F0"], a)))
                c.drawRRect(rrc(cx_, cy_ - 52, 250, 36, 18), relleno("#E5322D", a))
                texto(c, s.get("dias_txt", "DÍA"), cx_, cy_ - 52, F(800, 24), "#FFFFFF", alfa=a, tracking=.2)
                with capa(c, alfa=a, blur=(1.5 if 0 < ud < 1 else 0)): texto(c, str(dia), cx_, cy_ + 18, F(800, 74), "#1C2340", tnum=True)
                c.restore()
        c.restore()
        _reflejo(c, MX0, MX1, MY0, MY1, t)
        _lavabo(c)
        if modo == "gancho":
            _sello(c, s.get("sello", "NO FUNCIONA"), CX, 700, t, _tw(self, e, "no_word") - .05, rot=-12, px=96)
        else:
            # la cuchilla se deja en el vaso
            ts = _tw(self, e, "suelta_word"); vx, vy = 830, 1100
            u = _io((t - ts) / .55)
            if t < ts + .6:
                _cuchilla(c, 820, 800 + 230 * u, .8, -10 + 24 * u, 1.0 - .0 * u, mano=u < .35)
            _vaso(c, vx, vy)
            if t > ts + .5:
                c.save(); c.clipRect(skia.Rect(0, 0, W, vy + 20)); _cuchilla(c, vx - 6, vy - 190, .7, 14, 1.0, mano=False); c.restore()
                _vaso(c, vx, vy, .6)
            # retrato del abuelo
            tb = _tw(self, e, "abuelo_word")
            if t > tb - .15:
                u = resorte(t - tb + .15, 9, 12); a = aparece(t - tb + .15, .12); px_, py_ = 230, 430
                c.save(); c.translate(px_, py_); c.rotate(-6 + 3 * (1 - u)); c.scale(.4 + .6 * u, .4 + .6 * u)
                c.drawRRect(rrc(8, 14, 300, 370, 16), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
                c.drawRRect(rrc(0, 0, 300, 370, 16), _p(_lin(-185, 185, ["#C08A4A", "#7A4A22"], a)))
                c.drawRect(skia.Rect(-120, -155, 120, 135), _p(_lin(-155, 135, ["#E9D9B8", "#C9B48A"], a)))
                c.save(); c.clipRect(skia.Rect(-120, -155, 120, 135))
                cara(self, c, 0, -10, .42, t, cob=1.0, largo=24, parches=1.0, expr="feliz", canas=.85, a=a)
                c.restore()
                texto(c, s.get("abuelo_txt", "EL ABUELO"), 0, 160, F(800, 26), "#FFF2D0", alfa=a, tracking=.15)
                c.restore()
                if t > tb + .2: self.comic_t(c, "¡JA!", 360, 250, 60, 8, .7 + .3 * resorte(t - tb - .2, 10, 14), aparece(t - tb - .2, .1), "#FFE15A")
        _franja(c)

    # ---------------------------------------------------------------- corte de la piel con folículos
    FOL = [(-330, .95), (-170, 1.0), (0, 1.05), (170, .98), (330, .95)]
    def e_piel(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tf = _tw(self, e, "foliculo_word"); tk = _tw(self, e, "cuchilla_word"); tr = _tw(self, e, "raiz_word")
        SY = 430                                                                   # superficie de la piel
        c.drawRect(skia.Rect(-80, -80, W + 80, SY), _p(_lin(-80, SY, ["#0E1430", "#1E2A55"])))
        _polvo(c, t, 0, W, 60, SY - 20, .5, seed=8, n=30, col="#9FC3FF")
        # capas: epidermis, dermis, grasa
        c.drawRect(skia.Rect(-80, SY, W + 80, SY + 70), _p(_lin(SY, SY + 70, ["#F7D2BC", "#E9B49A"])))
        c.drawRect(skia.Rect(-80, SY + 70, W + 80, 940), _p(_lin(SY + 70, 940, ["#F2A99A", "#D9787A"])))
        rng = np.random.default_rng(4)
        for k in range(40):                                                        # fibras de la dermis
            x0 = rng.random() * W; y0 = SY + 90 + rng.random() * 380; pth = skia.Path(); pth.moveTo(x0, y0)
            pth.cubicTo(x0 + 40, y0 - 20, x0 + 80, y0 + 20, x0 + 140, y0 + 4 * math.sin(t + k)); c.drawPath(pth, trazo("#FFFFFF", 3, .12))
        c.drawRect(skia.Rect(-80, 940, W + 80, H + 80), _p(_lin(940, 1240, ["#F6D98A", "#E2B85A"])))
        for k in range(22):
            x0 = (k * 97 + 30) % (W + 100) - 50; y0 = 990 + (k * 53 % 220)
            c.drawCircle(x0, y0, 44, _p(_rad(x0 - 12, y0 - 12, 50, ["#FFF0B8", "#E8C26A"], None, .9))); c.drawCircle(x0, y0, 44, trazo("#C99A3A", 2, .5))
        c.drawRect(skia.Rect(-80, 1230, W + 80, H + 80), _p(_lin(1230, H, ["#7A2A30", "#3A0E14", "#1A0408"])))     # músculo
        for k in range(18): c.drawLine(-80, 1250 + k * 36, W + 80, 1262 + k * 36 + 10 * math.sin(k), trazo("#A03A44", 4, .25))
        # vaso sanguíneo
        vp = skia.Path(); vp.moveTo(-80, 880)
        for xx in range(-80, W + 100, 60): vp.lineTo(xx, 880 + 18 * math.sin(xx / 90))
        c.drawPath(vp, trazo("#B0202A", 22, .9)); c.drawPath(vp, trazo("#E04A50", 8, .7))
        # folículos y pelos
        cut = _io((t - tk - .15) / .9)                                             # la hoja recorre la superficie
        bx_hoja = -200 + (W + 400) * cut
        regrow = TI.clamp((t - tr - .6) / 3.0) if t > tr else 0
        for i, (fx, k) in enumerate(FOL):
            x = CX + fx; bot = 820; hi = i == 2 and t > tf
            # vaina
            vs = skia.Path(); vs.moveTo(x - 30, SY); vs.cubicTo(x - 34, SY + 160, x - 44, bot - 120, x - 48, bot - 40)
            vs.lineTo(x + 48, bot - 40); vs.cubicTo(x + 44, bot - 120, x + 34, SY + 160, x + 30, SY); vs.close()
            c.drawPath(vs, _p(_linx(x - 48, x + 48, ["#C9607A", "#F0A0A8", "#C9607A"])))
            # bulbo con papila
            pul = 1 + .04 * math.sin(t * 3 + i)
            c.drawOval(skia.Rect(x - 62 * pul, bot - 90 * pul, x + 62 * pul, bot + 30), _p(_rad(x - 18, bot - 50, 80, ["#FFC0C8", "#E07A8A", "#B04A62"], [0, .6, 1])))
            c.drawOval(skia.Rect(x - 26, bot - 20, x + 26, bot + 30), _p(_rad(x, bot, 30, ["#FF7A6A", "#C02A3A"])))
            c.drawLine(x, bot + 30, x, 880, trazo("#C02A3A", 8, .9))
            if hi:
                with capa(c, modo=skia.BlendMode.kPlus):
                    c.drawOval(skia.Rect(x - 110, bot - 140, x + 110, bot + 60), _p(_rad(x, bot - 40, 120, ["#FFE15A", "#000000"], None, .45 * aparece(t - tf, .2))))
            # pelo: desde el bulbo hasta arriba (antes del corte con punta fina; después, romo a ras y vuelve a salir)
            cortado = t > tk + .15 and bx_hoja > x
            top = SY - 230 * k if not cortado else SY - 6 - 60 * regrow
            n = 14; pts = []
            for j in range(n + 1):
                u = j / n; yy = bot - 60 + (top - (bot - 60)) * u
                xx = x + 6 * math.sin(u * 3 + t * .8 + i) * u * (0 if cortado else 1)
                pts.append((xx, yy, u))
            for j in range(n):
                x0, y0, u0 = pts[j]; x1, y1, u1 = pts[j + 1]
                g = 22 * (1 - .9 * u1 ** 2.2) if not cortado else 22
                if y1 < SY - 2 and not cortado and u1 > .97: g = 3
                c.drawLine(x0, y0, x1, y1, skia.Paint(AntiAlias=True, StrokeWidth=max(2.0, g), StrokeCap=skia.Paint.kRound_Cap, Color=color(_mix("#2A160E", "#5A3A26", u1 * .5))))
            c.drawLine(pts[0][0] - 5, pts[0][1], pts[-1][0] - 5, pts[-1][1], trazo("#FFFFFF", 3, .12))
            if cortado:
                c.drawOval(skia.Rect(x - 11, top - 5, x + 11, top + 5), relleno("#6A4A36"))
            # puntas cortadas que caen
            if t > tk + .15 and bx_hoja > x:
                tc_ = tk + .15 + .9 * ((x + 200) / (W + 400)); d = t - tc_
                if 0 < d < 1.6:
                    c.save(); c.translate(x + 120 * d, SY - 120 - 50 * d + 500 * d * d); c.rotate(140 * d + i * 20)
                    c.drawLine(0, -100, 0, 100, skia.Paint(AntiAlias=True, StrokeWidth=12, StrokeCap=skia.Paint.kRound_Cap, Color=color("#3A2216", TI.clamp(1.6 - d))))
                    c.restore()
            # el bulbo «ni se entera»: ojos tranquilos y zzz
            if t > tr:
                a = aparece(t - tr, .2)
                for sx in (-1, 1): c.drawArc(skia.Rect(x + sx * 18 - 10, bot - 52, x + sx * 18 + 10, bot - 38), 10, 160, False, trazo("#5A1E2A", 4, a))
                c.drawArc(skia.Rect(x - 10, bot - 30, x + 10, bot - 18), 20, 140, False, trazo("#5A1E2A", 4, a))
                ph = ((t - tr) * .5 + i * .2) % 1
                texto(c, "z", x + 50 + 30 * ph, bot - 100 - 90 * ph, F(800, int(26 + 18 * ph)), "#FFFFFF", alfa=a * math.sin(math.pi * ph))
        # piel de arriba con poros
        c.drawLine(-80, SY, W + 80, SY, trazo("#FFE6D6", 6, .9))
        # hoja de la cuchilla
        if 0 < cut < 1:
            hx = bx_hoja
            c.save(); c.translate(hx, SY - 22)
            c.drawRRect(rrc(-60, 0, 280, 34, 8), _p(_lin(-17, 17, ["#FFFFFF", "#AEB8CA", "#6A7488"])))
            c.drawPath(skia.Path.Polygon([(80, -17), (110, 0), (80, 17)], True), relleno("#E9EDF4"))
            with capa(c, modo=skia.BlendMode.kPlus): c.drawLine(80, 0, 110, 0, trazo("#BFE6FF", 6, .6))
            c.restore()
        if t > tf: _pill(self, c, s.get("foliculo_txt", "FOLÍCULO"), CX + 140, 700, S, aparece(t - tf - .1, .15), fondo="#8A1A3A")
        if dt0 > .4: _pill(self, c, s.get("piel_txt", "PIEL"), 150, SY + 35, S, aparece(dt0 - .4, .15) * (1 - TI.clamp((t - tf) / .2)), fondo="#6A3A28")
        _franja(c)

    # ---------------------------------------------------------------- laboratorio de 1928
    def _papel(c, x0, y0, x1, y1, a=1.0):
        c.drawRect(skia.Rect(x0 + 8, y0 + 12, x1 + 8, y1 + 12), skia.Paint(AntiAlias=True, Color=color("#000000", .3 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
        c.drawRect(skia.Rect(x0, y0, x1, y1), _p(_lin(y0, y1, ["#F6E9CC", "#E6D2A6"], a)))
        rng = np.random.default_rng(int(x0 + y0))
        for k in range(30): c.drawCircle(x0 + (x1 - x0) * rng.random(), y0 + (y1 - y0) * rng.random(), 2 + 4 * rng.random(), relleno("#B89A60", .12 * a))
    def _cientifica(c, x, y, s, t, a=1.0):
        """Anatomista con bata, moño y gafas, inclinada sobre el microscopio (mira a la derecha)."""
        c.save(); c.translate(x, y); c.scale(s, s)
        c.drawRRect(rrc(0, 180, 300, 330, 90), _p(_lin(20, 340, ["#FFFFFF", "#D9DEE8"], a)))
        c.drawPath(skia.Path.Polygon([(-20, 30), (20, 30), (0, 110)], True), relleno("#3A4A6A", a))
        c.drawLine(0, 100, 0, 330, trazo("#AEB8CA", 3, a))
        c.drawRRect(rrc(0, 10, 60, 50, 20), relleno(PIEL[1], a))
        c.save(); c.rotate(12)
        c.drawOval(skia.Rect(-80, -170, 80, 10), _p(_rad(-20, -100, 120, PIEL, [0, .6, 1], a)))
        c.drawCircle(-30, -185, 50, _p(_lin(-235, -135, ["#5A3A26", "#3A2418"], a)))             # moño
        hp = skia.Path(); hp.moveTo(-84, -60); hp.cubicTo(-90, -180, 80, -190, 84, -80); hp.lineTo(40, -120); hp.lineTo(-40, -110); hp.close()
        c.drawPath(hp, _p(_lin(-180, -60, ["#5A3A26", "#3A2418"], a)))
        for sx in (8, 52):
            c.drawCircle(sx, -70, 20, trazo("#2A2A30", 5, a)); c.drawCircle(sx, -70, 18, relleno("#DDEBFF", .35 * a))
        c.drawLine(28, -70, 32, -70, trazo("#2A2A30", 5, a))
        c.drawArc(skia.Rect(10, -30, 50, -8), 20, 140, False, trazo("#5A1E1E", 5, a))
        c.restore()
        bt = math.sin(t * 2.2) * 4
        c.drawLine(110, 120, 190, 40 + bt, trazo("#FFFFFF", 40, a)); c.drawCircle(196, 36 + bt, 20, relleno(PIEL[1], a))
        c.restore()
    def _microscopio(c, x, y, s, a=1.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        c.drawRRect(rrc(0, 150, 220, 40, 14), _p(_lin(130, 170, ["#3A3A44", "#1A1A22"], a)))
        c.drawPath(skia.Path.Polygon([(40, 140), (80, 140), (60, -60), (20, -60)], True), _p(_linx(20, 80, ["#2A2A30", "#5A5A66", "#2A2A30"], a)))
        c.drawPath(skia.Path.Polygon([(30, -60), (70, -60), (60, -100), (36, -100)], True), relleno("#2A2A30", a))     # brazo
        c.save(); c.translate(40, -90); c.rotate(-35)
        c.drawRRect(rrc(0, -70, 46, 150, 12), _p(_linx(-23, 23, ["#8A6A22", "#F2D27A", "#C9A24A"], a)))            # tubo
        c.drawRRect(rrc(0, -150, 34, 30, 8), relleno("#2A2A30", a))                                             # ocular
        c.drawRRect(rrc(0, 14, 56, 26, 8), relleno("#5A5A66", a)); c.restore()
        c.drawRRect(rrc(-10, 60, 140, 16, 6), relleno("#2A2A30", a))
        c.drawCircle(-10, 90, 16, relleno("#FFE9A8", .8 * a))
        c.drawCircle(80, 20, 14, relleno("#5A5A66", a))
        c.restore()
    def e_laboratorio(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ty = _tw(self, e, "anio_word"); tn = _tw(self, e, "nombre_word"); tz = _tw(self, e, "zonas_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#5A3A22", "#3A2414", "#1E1008"])))
        for k in range(7): c.drawLine(-80, 1000 + k * 120, W + 80, 1000 + k * 120, trazo("#120A06", 6, .5))
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(300, 380, 520, _p(_rad(300, 380, 520, ["#FFD9A0", "#000000"], None, .22)))
        _polvo(c, t, 0, W, 100, 1150, .55, seed=12, n=45, col="#FFE0B0")
        # año que rueda (2025 → 1928), grande y luego arriba
        u = TI.cubic_out(TI.clamp((t - ty + .2) / 1.0)) if t > ty - .2 else 0
        anio = int(round(s.get("desde", 2025) + (s.get("anio", 1928) - s.get("desde", 2025)) * u))
        sube = _io((t - ty - 1.1) / .6)
        ay = 560 - 330 * sube; asc = 1.0 - .55 * sube
        c.save(); c.translate(CX, ay); c.scale(asc, asc)
        c.drawRRect(rrc(0, 0, 560, 210, 40), _p(_lin(-105, 105, ["#2A1A10", "#120A06"], .9)))
        c.drawRRect(rrc(0, 0, 560, 210, 40), trazo("#FFB45C", 4, .9))
        with capa(c, blur=(3 if 0 < u < 1 else 0)): texto(c, str(anio), 0, 6, F(800, 170), "#FFE6B0", tnum=True)
        c.restore()
        # escena de laboratorio que sube
        ul = _io((t - ty - 1.0) / .7)
        if ul > 0:
            c.save(); c.translate(0, 400 * (1 - ul))
            c.drawRRect(rrc(CX, 960, 900, 40, 10), _p(_lin(940, 980, ["#8A5A32", "#5A3A20"], ul)))          # mesa
            _microscopio(c, 600, 760, 1.1, ul)
            _cientifica(c, 360, 640, 1.0, t, ul)
            c.restore()
            if t > tn: _pill(self, c, s.get("nombre_txt", "MILDRED TROTTER"), CX, 450, S, aparece(t - tn, .15), fondo="#6A3A14")
        # ficha con las dos zonas
        if t > tz - .1:
            uz = _io((t - tz + .1) / .5); a = uz
            c.save(); c.translate(0, 120 * (1 - uz))
            _papel(c, 110, 360, 930, 1150, a)
            cara(self, c, 330, 640, .62, t, cob=.85, largo=4, parches=.1, ropa=False, a=a, limpio=lambda px, py: px < 0)
            c.drawPath(skia.Path.Circle(260, 760, 90), (lambda p: (p.setPathEffect(skia.DashPathEffect.Make([14, 10], t * 30)), p)[1])(trazo("#C0392B", 5, a)))
            c.drawPath(skia.Path.Circle(400, 760, 90), (lambda p: (p.setPathEffect(skia.DashPathEffect.Make([14, 10], t * 30)), p)[1])(trazo("#1E6A3A", 5, a)))
            texto(c, s.get("afeitada_txt", "AFEITADA"), 230, 880, F(800, 26), "#C0392B", alfa=a)
            texto(c, s.get("sin_txt", "SIN AFEITAR"), 430, 880, F(800, 26), "#1E6A3A", alfa=a)
            for k, ch in enumerate(s.get("checks", [])):
                tc_ = self.ta(ch["word"], e)
                if t < tc_ - .1: continue
                ac = aparece(t - tc_ + .1, .12) * a; yy = 470 + k * 170; xx = 700
                c.drawRRect(rrc(xx, yy, 380, 130, 20), relleno("#FFFFFF", .55 * ac)); c.drawRRect(rrc(xx, yy, 380, 130, 20), trazo("#B89A60", 2, ac))
                # icono: color, grosor, velocidad
                ix = xx - 125
                if k == 0:
                    c.drawCircle(ix - 22, yy - 14, 20, relleno("#3A2216", ac)); c.drawCircle(ix + 22, yy - 14, 20, relleno("#3A2216", ac))
                elif k == 1:
                    c.drawLine(ix - 22, yy - 40, ix - 22, yy + 10, trazo("#3A2216", 12, ac)); c.drawLine(ix + 22, yy - 40, ix + 22, yy + 10, trazo("#3A2216", 12, ac))
                else:
                    for sx in (-1, 1):
                        c.drawLine(ix + sx * 22, yy + 10, ix + sx * 22, yy - 40, trazo("#3A2216", 6, ac)); c.drawPath(skia.Path.Polygon([(ix + sx * 22 - 12, yy - 34), (ix + sx * 22, yy - 52), (ix + sx * 22 + 12, yy - 34)], True), relleno("#3A2216", ac))
                texto(c, "=", ix, yy - 14, F(800, 40), "#1E6A3A", alfa=ac)
                texto(c, ch["txt"], xx + 40, yy + 38, F(800, 27), "#3A2414", alfa=ac)
                # ✓ que se traza
                uk = TI.clamp((t - tc_ - .05) / .3); pk = skia.Path(); pk.moveTo(xx + 90, yy - 22); pk.lineTo(xx + 120, yy + 6); pk.lineTo(xx + 170, yy - 50)
                me = skia.PathMeasure(pk, False); L = me.getLength(); sp = skia.Path(); me.getSegment(0, L * uk, sp, True)
                c.drawPath(sp, trazo("#1E9A4A", 12, ac))
            c.restore()
        _franja(c)

    # ---------------------------------------------------------------- piernas de 1970
    def _pierna(c, x, t, pelos, largo, a=1.0, seed=0, limpio_y=None, sx=1):
        P = ("#FBE0C8", "#F1C3A0", "#D99A74")
        pth = skia.Path(); pth.moveTo(x - 95, 120); pth.cubicTo(x - 110, 380, x - 70, 520, x - 64, 820)
        pth.lineTo(x + 64, 820); pth.cubicTo(x + 74, 560, x + 120, 380, x + 95, 120); pth.close()
        c.drawPath(pth, _p(_linx(x - 110, x + 110, [P[2], P[0], P[1], P[2]], a, [0, .35, .7, 1])))
        c.drawOval(skia.Rect(x - 30, 180, x + 30, 250), relleno(P[2], .3 * a))       # rodilla
        # pie / zapatilla
        c.drawRRect(rrc(x + sx * 30, 860, 210, 90, 40), _p(_lin(815, 905, ["#FFFFFF", "#D9DEE8"], a)))
        c.drawRRect(rrc(x + sx * 30, 895, 214, 22, 10), relleno("#C9CFDB", a)); c.drawLine(x + sx * 30 - 50, 840, x + sx * 30 + 20, 840, trazo("#FF6A3D", 6, a))
        c.drawRect(skia.Rect(x - 66, 800, x + 66, 830), relleno("#FFFFFF", a)); c.drawRect(skia.Rect(x - 66, 812, x + 66, 818), relleno("#E5322D", a))
        if pelos > 0:
            rng = np.random.default_rng(seed)
            for k in range(130):
                yy = 140 + 640 * rng.random(); half = 95 - 30 * (yy - 140) / 680; xx = x + (2 * rng.random() - 1) * (half - 12)
                if limpio_y is not None and yy < limpio_y: continue
                if rng.random() > pelos: continue
                l = largo * (.6 + .6 * rng.random()); an = .5 + .3 * rng.random() + .1 * math.sin(t + k)
                c.drawLine(xx, yy, xx + l * math.sin(an) * (1 if xx > x else -1), yy + l * math.cos(an), skia.Paint(AntiAlias=True, StrokeWidth=2.4, StrokeCap=skia.Paint.kRound_Cap, Color=color("#3A2216", .8 * a)))
    def e_piernas(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ta = _tw(self, e, "afeita_word"); to = _tw(self, e, "otra_word"); tm = _tw(self, e, "medir_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 960, ["#F4F7FD", "#DCE6F6"])))
        c.drawRect(skia.Rect(-80, 960, W + 80, H + 80), _p(_lin(960, H, ["#B8C8E6", "#7A8CB8"])))
        for k in range(14): c.drawLine(-80, 980 + k * (20 + 4 * k), W + 80, 980 + k * (20 + 4 * k), trazo("#5A6A9A", 2, .25))
        _sombra(c, 300, 960, 160, 20, .2); _sombra(c, 740, 960, 160, 20, .2)
        # ficha 1970
        a0 = aparece(dt0 - .05, .15); sy = 250
        c.drawRRect(rrc(CX, sy, 240, 90, 45), relleno("#1C2340", .9 * a0)); texto(c, s.get("anio_txt", "1970"), CX, sy, F(800, 56), "#FFFFFF", alfa=a0, tnum=True)
        # cuchilla bajando por la pierna izquierda
        u = _io((t - ta + .2) / .9); ly = 120 + 720 * u if t > ta - .2 else None
        regrow = TI.clamp((t - tm + .4) / 1.0) if t > tm - .4 else 0
        lim = ly if regrow == 0 else None
        largo_i = 14 if regrow == 0 else 14 * regrow
        _pierna(c, 300, t, 1.0, largo_i if t > ta + .8 else 14, seed=11, limpio_y=(ly if t < ta + .8 else (None if regrow > 0 else 900)), sx=-1)
        _pierna(c, 740, t, 1.0, 14, seed=12, sx=1)
        if t > ta - .2 and u < 1:
            _cuchilla(c, 300, ly, .9, 180 + 4 * math.sin(t * 6), 1.0, mano=False)
        if t > ta: _pill(self, c, s.get("izq_txt", "AFEITADA"), 300, 1010, S, aparece(t - ta, .15), fondo="#8A1A0A", grande=False)
        if t > to: _pill(self, c, s.get("der_txt", "SIN AFEITAR"), 740, 1010, S, aparece(t - to, .15), fondo="#1E6A3A", grande=False)
        # semanas después: lupas con el mismo pelo
        if t > tm - .4:
            al = aparece(t - tm + .4, .2)
            for k, lx in enumerate((300, 740)):
                ux = resorte(t - tm + .4 - .1 * k, 9, 12); r = 120 * ux; ly_ = 480
                c.drawCircle(lx, ly_, r + 14, _p(_lin(ly_ - r, ly_ + r, ["#3A4258", "#1A1F33"], al)))
                c.drawCircle(lx, ly_, r, _p(_rad(lx, ly_, r, ["#FFF0E0", "#F1C3A0"], None, al)))
                c.drawLine(lx - 8, ly_ + r * .7, lx + 6, ly_ - r * .7, skia.Paint(AntiAlias=True, StrokeWidth=14 * ux, StrokeCap=skia.Paint.kRound_Cap, Color=color("#3A2216", al)))
                c.drawLine(lx + (r + 10) * .7, ly_ + (r + 10) * .7, lx + (r + 90) * .7, ly_ + (r + 90) * .7, trazo("#1A1F33", 26 * ux, al))
                with capa(c, modo=skia.BlendMode.kPlus): c.drawArc(skia.Rect(lx - r * .8, ly_ - r * .8, lx + r * .8, ly_ + r * .8), 200, 60, False, trazo("#FFFFFF", 6, .4 * al))
            if t > tm + .2: texto(c, "=", CX, 480, F(800, 120), "#1E6A3A", alfa=aparece(t - tm - .2, .12))
            _pill(self, c, s.get("pill", "NI UN PELO DE DIFERENCIA"), CX, 340, S, aparece(t - tm - .3, .15), fondo="#1E6A3A")
            if t > tm - .4 and t < tm + .8:
                pass
        _franja(c)

    # ---------------------------------------------------------------- la punta del pelo
    def _pelo(c, x, y0, y1, g, t, a=1.0, aclarado=0.0, romo=False, ondea=1.0):
        n = 30; prev = None
        for j in range(n + 1):
            u = j / n; yy = y0 + (y1 - y0) * u; xx = x + 10 * math.sin(u * 3 + t * .9) * u * ondea
            if prev:
                gg = g if romo else g * max(.04, 1 - u ** 1.6)
                col = _mix("#2A160E", "#E8C27A", aclarado * u ** 1.5)
                c.drawLine(prev[0], prev[1], xx, yy, skia.Paint(AntiAlias=True, StrokeWidth=gg, StrokeCap=skia.Paint.kButt_Cap if romo and j == n else skia.Paint.kRound_Cap, Color=color(col, a)))
            prev = (xx, yy)
        c.drawLine(x - g * .22, y0, prev[0] - g * .22 * (0 if not romo else 1), (y0 + y1) / 2, trazo("#FFFFFF", max(2, g * .12), .16 * a))
        if romo:
            c.drawOval(skia.Rect(prev[0] - g / 2, prev[1] - g * .18, prev[0] + g / 2, prev[1] + g * .18), _p(_rad(prev[0], prev[1], g * .5, ["#8A6A50", "#4A2E1E"], None, a)))
    def _lapiz(c, x, y, h, a=1.0):
        """Lápiz vertical con la punta arriba en y."""
        c.drawRect(skia.Rect(x - 30, y + 130, x + 30, y + h), _p(_linx(x - 30, x + 30, ["#E0A21A", "#FFD24A", "#C9820A"], a)))
        for k in (-10, 10): c.drawLine(x + k, y + 130, x + k, y + h, trazo("#B07A0A", 2, .5 * a))
        c.drawPath(skia.Path.Polygon([(x - 30, y + 130), (x + 30, y + 130), (x, y)], True), _p(_linx(x - 30, x + 30, ["#E9C9A0", "#F6E0C0", "#C9A07A"], a)))
        c.drawPath(skia.Path.Polygon([(x - 9, y + 40), (x + 9, y + 40), (x, y)], True), relleno("#2A2A30", a))
        c.drawRect(skia.Rect(x - 31, y + h - 40, x + 31, y + h), relleno("#C9CFDB", a)); c.drawRRect(rrc(x, y + h + 20, 62, 44, 14), relleno("#FF8A9A", a))
    def e_punta(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tp, tl, tc, tr, tq, ts, to = (_tw(self, e, k) for k in ("punta_word", "lapiz_word", "corte_word", "romo_word", "pincha_word", "sol_word", "oscuro_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1300, ["#1A1440", "#0C0A22", "#05030E"])))
        for k in range(5): c.drawCircle(CX, 640, 180 + 120 * k + 20 * math.sin(t * .8 + k), trazo("#6A58C8", 2, .08))
        _polvo(c, t, 0, W, 100, 1100, .5, seed=21, n=40, col="#D9CCFF")
        SY = 1000
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(CX, SY, 700, _p(_rad(CX, SY, 700, ["#5A3A9A", "#000000"], None, .35)))
        c.drawRect(skia.Rect(-80, SY, W + 80, H + 80), _p(_lin(SY, H, ["#F6CDAE", "#E0A47E", "#A86A4A"])))
        c.drawLine(-80, SY, W + 80, SY, trazo("#FFE6D6", 5, .8))
        rng = np.random.default_rng(23)
        for k in range(70):                                                     # poros y pelitos cortos de alrededor
            px, py = rng.random() * W, SY + 40 + rng.random() * 800; c.drawCircle(px, py, 3 + 3 * rng.random(), relleno("#A86A4A", .35))
        for k in range(16):
            px = 40 + k * 66 + 20 * rng.random()
            if abs(px - 330) < 70 or abs(px - 700) < 70: continue
            c.drawRect(skia.Rect(px - 7, SY - 24 - 10 * rng.random(), px + 7, SY + 4), relleno("#3A2216", .85))
        # sol que aclara
        us = _io((t - ts) / .6)
        if us > 0:
            with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(180, 270, 260, _p(_rad(180, 270, 260, ["#FFE9A0", "#000000"], None, .5 * us)))
            c.drawCircle(180, 270, 62, _p(_rad(164, 254, 70, ["#FFFFFF", "#FFE58A", "#FFB43A"], [0, .45, 1], us)))
            for k in range(12):
                an = k * math.pi / 6 + t * .3; c.drawLine(180 + 72 * math.cos(an), 270 + 72 * math.sin(an), 180 + 98 * math.cos(an), 270 + 98 * math.sin(an), trazo("#FFE58A", 7, .8 * us))
        # pelo largo (izquierda): sin cortar, punta fina
        g = 66; xL, xR = 330, 700; TOP = 340
        _pelo(c, xL, SY + 20, TOP, g, t, aclarado=.75 * us)
        if t > tp: _pill(self, c, s.get("fino_txt", "PUNTA FINA"), xL, TOP - 80, S, aparece(t - tp, .15), fondo="#3A2A7A")
        if t > tp:
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawCircle(xL + 8, TOP + 10, 80, _p(_rad(xL + 8, TOP + 10, 80, ["#BFA6FF", "#000000"], None, .5 * aparece(t - tp, .2))))
        # lápiz junto al pelo largo
        if t > tl - .1:
            ul = resorte(t - tl + .1, 9, 12); al = aparece(t - tl + .1, .12) * (1 - TI.clamp((t - tc + .3) / .3))
            if al > 0: _lapiz(c, xL + 150, TOP + 300 * (1 - ul), 640, al)
        # pelo derecho: se corta
        cort = t > tc + .25
        if not cort:
            _pelo(c, xR, SY + 20, TOP, g, t)
            if t > tc - .3:
                u = _io((t - tc + .3) / .55); hx = -100 + (W + 200) * u
                _cuchilla(c, hx, SY - 70, 1.0, -90, 1.0, mano=False)
        else:
            d = t - tc - .25
            if d < 1.8:                                                           # el trozo cortado cae dando vueltas
                c.save(); c.translate(xR + 200 * d, (SY - 60 + TOP) / 2 - 150 * d + 700 * d * d); c.rotate(160 * d)
                _pelo(c, 0, (SY - 60 - TOP) / 2, -(SY - 60 - TOP) / 2, g * .95, 0, a=TI.clamp(1.8 - d), ondea=0)
                c.restore()
            _pelo(c, xR, SY + 20, SY - 60, g, t, romo=True, ondea=0)
            if t > tr - .1: _pill(self, c, s.get("romo_txt", "CORTE ROMO"), xR, SY - 160, S, aparece(t - tr + .1, .15) * (1 - TI.clamp((t - tq + .5) / .2)), fondo="#7A1A3A")
            # lupa sobre el corte
            if t > tr:
                ul = resorte(t - tr, 9, 12); R = 130 * ul; lx, ly = xR + 110, SY - 400
                c.drawLine(xR, SY - 62, lx - R * .7, ly + R * .7, trazo("#FFFFFF", 3, .5))
                c.drawCircle(lx, ly, R + 12, relleno("#2A2F44")); c.drawCircle(lx, ly, R, _p(_rad(lx, ly, R, ["#3A2A6A", "#1A1440"])))
                c.save(); c.clipPath(skia.Path.Circle(lx, ly, R), doAntiAlias=True)
                c.drawRect(skia.Rect(lx - 70, ly - 10, lx + 70, ly + R), _p(_linx(lx - 70, lx + 70, ["#1A0E08", "#3A2216", "#1A0E08"])))
                c.drawOval(skia.Rect(lx - 70, ly - 34, lx + 70, ly + 14), _p(_rad(lx, ly - 10, 70, ["#9A7A5A", "#5A3A26"])))
                c.restore()
        # dedo que toca y pincha
        if t > tq - .4:
            u = _io((t - tq + .4) / .4) * (1 - _io((t - tq - 1.2) / .4))
            fx, fy = xR - 10, SY - 64 - 1100 * (1 - u) - 6 * math.sin(t * 40) * (1 if 0 < t - tq < .5 else 0)
            P = ("#F8D5B8", "#E6AC86", "#C98763")
            c.drawLine(fx + 60, fy - 300, fx + 330, fy - 760, skia.Paint(AntiAlias=True, StrokeWidth=150, StrokeCap=skia.Paint.kRound_Cap, Shader=_lin(fy - 760, fy - 300, ["#B8401C", "#FF8A3D"])))
            c.drawRRect(rrc(fx + 70, fy - 250, 190, 170, 70), _p(_rad(fx + 40, fy - 290, 200, P, [0, .6, 1])))
            for k in range(3): c.drawRRect(rrc(fx + 90 + k * 46, fy - 170, 44, 90, 22), _p(_lin(fy - 215, fy - 125, P)))
            c.drawRRect(rrc(fx, fy - 105, 76, 230, 38), _p(_linx(fx - 38, fx + 38, [P[2], P[0], P[1]])))
            c.drawRRect(rrc(fx, fy - 30, 50, 44, 18), relleno("#FFE6D6", .7))
            if 0 < t - tq < 1.0:
                self.comic_t(c, "¡RASP!", 520, 790, 76, -8, .7 + .3 * resorte(t - tq, 10, 14), 1 - TI.clamp((t - tq - .75) / .25), "#FFE15A")
        if t > to - .1 and t < ts:
            with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(xR, SY - 70, 80, _p(_rad(xR, SY - 70, 80, ["#FF5A8A", "#000000"], None, .35 * aparece(t - to + .1, .2))))
        if t > ts + .4: _pill(self, c, s.get("oscuro_txt", "SIN ACLARAR POR EL SOL"), xR - 40, SY - 590, S, aparece(t - ts - .4, .15), fondo="#5A3A14")
        _franja(c)

    # ---------------------------------------------------------------- genes, DHT y zonas
    def _adn(c, x, y, h, t, a=1.0):
        n = 22
        for k in range(n):
            yy = y - h / 2 + h * k / (n - 1); ph = t * 1.6 + k * .55
            x1 = x + 70 * math.sin(ph); x2 = x - 70 * math.sin(ph); fr = math.cos(ph)
            cols = ("#FF5A8A", "#5AC8FF", "#FFE15A", "#7CFF8A")
            c.drawLine(x1, yy, x2, yy, trazo(cols[k % 4], 7, .8 * a))
            for xx, z in ((x1, fr), (x2, -fr)):
                c.drawCircle(xx, yy, 12 + 4 * z, _p(_rad(xx - 4, yy - 4, 16, ["#FFFFFF", "#6EA0FF" if z > 0 else "#3A5FB8"], None, a * (.7 + .3 * z))))
    def _molecula(c, x, y, r, col, txt, a=1.0, rot=0.0):
        c.save(); c.translate(x, y); c.rotate(rot)
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(0, 0, r * 2, _p(_rad(0, 0, r * 2, [col, "#000000"], None, .35 * a)))
        for dx in (-r * .85, r * .85):
            hx = skia.Path.Polygon([(dx + r * .55 * math.cos(k * math.pi / 3), r * .55 * math.sin(k * math.pi / 3)) for k in range(6)], True)
            c.drawPath(hx, relleno(col, .35 * a)); c.drawPath(hx, trazo(col, 4, a))
        c.restore()
        texto(c, txt, x, y + r * 1.2, F(800, 24), "#FFFFFF", alfa=a)
    def e_genes(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tg, tt, td, tk, tp, te, tn = (_tw(self, e, k) for k in ("adn_word", "testo_word", "dht_word", "caso_word", "parches_word", "escuchan_word", "pasan_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1300, ["#0B1530", "#071026", "#050A18"])))
        _polvo(c, t, 0, W, 100, 1150, .55, seed=31, n=50, col="#6EA0FF")
        sal = _io((t - tp + .1) / .6)                                              # sale la parte del folículo, entra la cara
        if sal < 1:
            c.save(); c.translate(0, 120 - 1100 * sal)
            ag = aparece(t - tg + .3, .2) if t > tg - .3 else aparece(dt0, .2)
            _adn(c, 150, 600, 820, t, ag)
            # folículo grande
            x, y = 600, 560
            vs = skia.Path(); vs.moveTo(x - 60, 120); vs.cubicTo(x - 70, 380, x - 90, 600, x - 110, 760)
            vs.lineTo(x + 110, 760); vs.cubicTo(x + 90, 600, x + 70, 380, x + 60, 120); vs.close()
            c.drawPath(vs, _p(_linx(x - 110, x + 110, ["#8A3050", "#E0909A", "#8A3050"])))
            c.drawOval(skia.Rect(x - 170, 640, x + 170, 960), _p(_rad(x - 40, 760, 200, ["#FFC0C8", "#E07A8A", "#A04060"], [0, .55, 1])))
            c.drawLine(x - 22, 830, x - 6, 150, skia.Paint(AntiAlias=True, StrokeWidth=34, StrokeCap=skia.Paint.kRound_Cap, Color=color("#2A160E")))
            # vaso de sangre por debajo
            c.drawLine(-80, 1010, W + 80, 990, trazo("#B0202A", 40, .9)); c.drawLine(-80, 1010, W + 80, 990, trazo("#E04A50", 14, .6))
            # receptores: antenas en el bulbo, con brillo según «caso»
            uk = _io((t - tk) / .8)
            for k in range(7):
                an = math.pi * (1.05 + .9 * k / 6); rx_, ry_ = x + 175 * math.cos(an) * -1, 800 - 165 * math.sin(an) * -1
                rx_, ry_ = x + 170 * math.cos(math.pi + an), 800 + 160 * math.sin(an) * -1
            for k in range(6):
                an = -math.pi * .9 + k * math.pi * .36; ax, ay = x + 168 * math.cos(an) * 1.0, 800 + 158 * math.sin(an)
                if ay < 700: continue
                on = TI.clamp(uk * 1.6 - k * .12)
                c.drawLine(ax, ay, ax + 26 * math.cos(an), ay + 26 * math.sin(an), trazo("#FFE15A" if on > .5 else "#6A7488", 6))
                c.drawCircle(ax + 32 * math.cos(an), ay + 32 * math.sin(an), 10, relleno(_mix("#6A7488", "#FFE15A", on)))
            # testosterona que entra y se convierte en DHT
            if t > tt - .2:
                for k in range(5):
                    ph = ((t - tt + .2) * .45 + k / 5) % 1
                    if t - tt + .2 < k / 5 / .45: continue
                    if ph < .45:
                        mx_, my_ = -60 + (x - 60 + 60) * ph / .45, 1000 - 10 * ph / .45; col, txt = "#5AC8FF", "T"
                    else:
                        q = (ph - .45) / .55; mx_, my_ = x - 20 + 40 * math.sin(q * 6), 960 - 200 * q
                        conv = t > td - .3; col, txt = ("#FFC23A", "DHT") if conv and q > .3 else ("#5AC8FF", "T")
                    _molecula(c, mx_, my_, 24, col, txt, 1.0, t * 40 + k * 30)
                _pill(self, c, s.get("testo_txt", "TESTOSTERONA"), 240, 920, S, aparece(t - tt, .15) * (1 - TI.clamp((t - td) / .25)), fondo="#1C5A8A")
            if t > td:
                with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(x, 790, 220, _p(_rad(x, 790, 220, ["#FFC23A", "#000000"], None, .35 * aparece(t - td, .2))))
                _pill(self, c, s.get("dht_txt", "DHT"), x + 190, 640, S, aparece(t - td, .15), fondo="#8A5A0A")
            # dial de «caso»
            if t > tk - .1:
                a = aparece(t - tk + .1, .15); dx, dy = 840, 330
                c.drawCircle(dx, dy, 90, _p(_rad(dx - 20, dy - 20, 110, ["#2A3456", "#121830"], None, a))); c.drawCircle(dx, dy, 90, trazo("#6EA0FF", 3, a))
                for k in range(9):
                    an = math.radians(135 + k * 33.75); c.drawLine(dx + 70 * math.cos(an), dy + 70 * math.sin(an), dx + 82 * math.cos(an), dy + 82 * math.sin(an), trazo(_mix("#6A7488", "#FFE15A", k / 8), 5, a))
                an = math.radians(135 + 270 * (.15 + .7 * (.5 + .5 * math.sin((t - tk) * 2.2)))); c.drawLine(dx, dy, dx + 60 * math.cos(an), dy + 60 * math.sin(an), trazo("#FFFFFF", 8, a))
                c.drawCircle(dx, dy, 14, relleno("#FFFFFF", a))
                texto(c, "CASO", dx, dy + 125, F(800, 28), "#AFC3EE", alfa=a, tracking=.2)
            c.restore()
        if sal > 0:
            c.save(); c.translate(0, 1100 * (1 - sal))
            ue, un = _io((t - te) / .5), _io((t - tn) / .5)
            cara(self, c, CX, 600, 1.25, t, cob=.6 + .4 * ue, largo=3 + 7 * ue, parches=1.0, zonas=(ue, un) if t > tp else 0, expr="meh" if t > tn else "neutral")
            c.restore()
            if t > te: _pill(self, c, s.get("si_txt", "ESCUCHA"), CX, 1010, S, aparece(t - te, .15), fondo="#1E6A3A")
            if t > tn:
                _pill(self, c, s.get("no_txt", "PASA"), CX - 290, 640, S, aparece(t - tn, .15), fondo="#4A5268")
                _pill(self, c, s.get("no_txt", "PASA"), CX + 290, 650, S, aparece(t - tn - .1, .15), fondo="#4A5268")
        _franja(c)

    # ---------------------------------------------------------------- edad y velocidad
    def e_edad(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; te = _tw(self, e, "edad_word"); tr = _tw(self, e, "regla_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1300, ["#2E62E6", "#1A3FB0", "#0D2A86"])))
        for k in range(6):
            r = 200 + 140 * k + 30 * math.sin(t * .7 + k)
            c.drawCircle(CX, 560, r, trazo("#FFFFFF", 2, .06))
        _polvo(c, t, 0, W, 100, 1150, .6, seed=41, n=50, col="#FFFFFF")
        u = TI.cubic_out(TI.clamp((t - te + .25) / 1.4)) if t > te - .25 else 0
        edad = s.get("desde", 16) + (s.get("hasta", 30) - s.get("desde", 16)) * u
        cara(self, c, CX - 40, 600, 1.12, t, cob=.35 + .65 * u, largo=3 + 13 * u, parches=1 - .85 * u, expr="feliz" if dt0 < 1.4 or u > .9 else "neutral", mira=(.3, -.1))
        if dt0 < 1.6:                                                              # destellos de «buena noticia»
            for k in range(6):
                an = k * math.pi / 3 + t; r = 330 + 20 * math.sin(t * 4 + k); ax, ay = CX - 40 + r * math.cos(an), 560 + r * .9 * math.sin(an)
                sc = aparece(dt0 - .1 * k, .15) * (1 - TI.clamp((dt0 - 1.2) / .4))
                pth = skia.Path()
                for j in range(8):
                    rr = 26 if j % 2 == 0 else 8; aa = j * math.pi / 4
                    (pth.moveTo if j == 0 else pth.lineTo)(ax + rr * sc * math.cos(aa), ay + rr * sc * math.sin(aa))
                pth.close(); c.drawPath(pth, relleno("#FFE15A", sc))
        # contador de edad
        a = aparece(dt0 - .2, .15); bx, by = 800, 200
        c.drawRRect(rrc(bx, by, 260, 200, 30), _p(_lin(by - 100, by + 100, ["#FFFFFF", "#DCE6F6"], a)))
        with capa(c, alfa=a, blur=(2 if 0 < u < 1 else 0)): texto(c, str(int(round(edad))), bx, by - 18, F(800, 110), "#1A3FB0", tnum=True)
        texto(c, s.get("edad_txt", "AÑOS"), bx, by + 62, F(800, 30), "#5A6A8A", alfa=a, tracking=.2)
        # regla: 1 cm al mes
        if t > tr - .2:
            ar = aparece(t - tr + .2, .15); rx, ry = 860, 560
            ug = _io((t - tr) / 1.6)
            c.drawRRect(rrc(rx, ry + 60, 90, 420, 10), _p(_linx(rx - 45, rx + 45, ["#FFE9A8", "#FFD24A", "#E0A21A"], ar)))
            for k in range(41):
                yy = ry - 140 + k * 10; L = 30 if k % 10 == 0 else (20 if k % 5 == 0 else 12)
                c.drawLine(rx - 45, yy, rx - 45 + L, yy, trazo("#5A3A0A", 2, ar))
                if k % 10 == 0: texto(c, str(4 - k // 10), rx + 18, yy, F(700, 22), "#5A3A0A", alfa=ar)
            # pelo que crece de 0 a 1 cm (escala ×10 visual: 100 px)
            c.drawLine(rx - 70, ry + 260, rx - 70, ry + 260 - 100 * ug, skia.Paint(AntiAlias=True, StrokeWidth=12, StrokeCap=skia.Paint.kRound_Cap, Color=color("#3A2216", ar)))
            c.drawLine(rx - 70, ry + 260, rx - 70, ry + 160, (lambda p: (p.setPathEffect(skia.DashPathEffect.Make([8, 8], 0)), p)[1])(trazo("#FFFFFF", 2, .5 * ar)))
            _pill(self, c, s.get("regla_txt", "≈ 1 CM AL MES"), rx - 60, ry + 310, S, aparece(t - tr - .3, .15), fondo="#0B1430")
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_barba(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "espejo":
            if s.get("modo") == "gancho":
                sf(e["t0"] + .05, "espuma", .8)
                if g("afeita_word") is not None: sf(g("afeita_word") - .25, "cuchilla", 1.0); sf(g("afeita_word") + .2, "pop", .4)
                if g("no_word") is not None: sf(g("no_word") - .05, "sello2", 1.0)
            else:
                if g("suelta_word") is not None: sf(g("suelta_word") + .5, "cristal", .9)
                if g("crece_word") is not None:
                    tc = g("crece_word"); tpq = g("paciencia_word") or tc + 2
                    k = 0
                    while tc + k * .12 < tpq + 1.0 and k < 20: sf(tc + k * .12, "tic", .3 * (1 - k / 25)); k += 1
                    sf(tpq + 1.0, "ding", .6)
                if g("parches_word") is not None: sf(g("parches_word"), "bajada", .5)
                if g("abuelo_word") is not None: sf(g("abuelo_word") - .15, "flash", .9); sf(g("abuelo_word") + .2, "pop", .5)
        if tp == "piel":
            sf(e["t0"] + .2, "burbuja", .5)
            if g("foliculo_word") is not None: sf(g("foliculo_word"), "destello", .6)
            if g("cuchilla_word") is not None: sf(g("cuchilla_word") + .15, "cuchilla", 1.0)
            if g("raiz_word") is not None: sf(g("raiz_word") + .1, "zzz", .6); sf(g("raiz_word") + 1.0, "subida", .4)
        if tp == "laboratorio":
            if g("anio_word") is not None: self.rodillo(g("anio_word") - .2, 1.0); sf(g("anio_word") + 1.0, "whoosh", .5)
            if g("nombre_word") is not None: sf(g("nombre_word"), "pop", .5)
            if g("zonas_word") is not None: sf(g("zonas_word") - .1, "hoja", .8); sf(g("zonas_word") + .4, "rotulador", .6)
            for ch in s.get("checks", []): sf(Tw(ch["word"]) + .05, "palomita", .8)
        if tp == "piernas":
            sf(e["t0"] + .1, "pop", .5)
            if g("afeita_word") is not None: sf(g("afeita_word") - .2, "cuchilla", 1.0)
            if g("otra_word") is not None: sf(g("otra_word"), "pop", .5)
            if g("medir_word") is not None: sf(g("medir_word") - .4, "subida", .5); sf(g("medir_word") + .2, "ding", .6)
        if tp == "punta":
            if g("punta_word") is not None: sf(g("punta_word"), "destello", .5)
            if g("lapiz_word") is not None: sf(g("lapiz_word") - .1, "desliz", .6)
            if g("corte_word") is not None: sf(g("corte_word") - .3, "cuchilla", 1.0); sf(g("corte_word") + .5, "caida", .5)
            if g("romo_word") is not None: sf(g("romo_word"), "pop", .5)
            if g("pincha_word") is not None: sf(g("pincha_word"), "rasp", 1.0)
            if g("sol_word") is not None: sf(g("sol_word"), "subida", .5); sf(g("sol_word") + .4, "pop", .4)
        if tp == "genes":
            if g("adn_word") is not None: sf(g("adn_word"), "destello", .5)
            if g("testo_word") is not None:
                for j in range(3): sf(g("testo_word") + .2 + j * .6, "burbuja", .5)
            if g("dht_word") is not None: sf(g("dht_word") - .1, "destello2", .8)
            if g("caso_word") is not None:
                for j in range(5): sf(g("caso_word") + j * .1, "tic", .4)
            if g("parches_word") is not None: sf(g("parches_word") - .1, "whoosh", .5)
            if g("escuchan_word") is not None: sf(g("escuchan_word"), "subida", .5)
            if g("pasan_word") is not None: sf(g("pasan_word"), "bajada", .5)
        if tp == "edad":
            sf(e["t0"] + .1, "destello", .6)
            if g("edad_word") is not None: self.rodillo(g("edad_word") - .25, 1.4)
            if g("regla_word") is not None: sf(g("regla_word") - .2, "pop", .5); sf(g("regla_word") + .2, "subida", .4)

    for k, fn in (("espejo", e_espejo), ("piel", e_piel), ("laboratorio", e_laboratorio), ("piernas", e_piernas), ("punta", e_punta),
                  ("genes", e_genes), ("edad", e_edad)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_barba)
