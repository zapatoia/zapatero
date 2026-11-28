"""Escenas del documental 21 («¿Por qué de repente te tiembla el párpado?»).

Reutiliza `self.cara_b` (17) para el protagonista en primer plano y añade un OJO GRANDE ilustrado (`_ojo`: párpados que abren/cierran,
temblor del párpado de abajo, iris con fibras, pestañas) y el músculo orbicular en anillo (`_anillo_m`: fibras que se dibujan y se encogen).
parpado      habitación de noche: gancho (tic_word: el párpado de abajo tiembla, lupa y ¡TIC!; nadie_word: el amigo mira y no ve nada;
             terremoto_word: sismógrafo «LO QUE NOTAS» y la escena tiembla; fuera_word: sismógrafo plano «LO QUE SE VE»);
             cierre (tic_word: vuelve a temblar; dormir_word: cierra los ojos, Zzz y la lámpara se apaga; nadie_word: el amigo pasa con
             los cascos, «NI SE HA ENTERADO»).
anillo       ojo grande sobre piel: nombre_word (ficha MIOQUIMIA PALPEBRAL), anillo_word (el músculo orbicular se dibuja alrededor),
             cierra_word / parpadea_word (el anillo se encoge y el ojo se cierra).
nervio       el mismo ojo más pequeño con su anillo y el nervio como un cable con pulsos: chispa_word (chispazos sueltos), trozo_word
             (un trocito del anillo se encoge una y otra vez), ojo_word / abajo_word (un ojo, el párpado de abajo).
sospechosos  rueda de reconocimiento: items [{word, tipo: sueno/estres/cafe/movil/vicios, txt}] con cartel numerado y flash.
vaso         vaso que se llena con una gota por sospechoso (suma_word → vaso_word), rebosa (rebosa_word) y el ojo hace ¡TIC! (tic_word).
magnesio     bote de MAGNESIO, rumores en bocadillos (dice_word) y lupa sobre el estudio + sello NO DEMOSTRADO (demo_word).
sevasolo     calendario que pasa días y semanas con el temblor que se apaga (dias_word, semanas_word) y tres remedios (duerme/cafe/vista).
medico       ficha «AL MÉDICO SI…» con tres avisos: items [{word, tipo: calendario/cerrado/cara, txt}].
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]
    G["SUP"].setdefault("piel", dict(a="#6A3A2C", b="#2A140E", txt="#FFFFFF", sub="#FFE0CC", acc="#FFD27A", tierra="#5A2E22", borde="#C9775A", grid=False))
    FNT = {}
    def F(peso, px, fam="Inter"):
        k = (fam, peso, px)
        if k not in FNT: FNT[k] = fuente(fam, peso, px)
        return FNT[k]

    # ---------------------------------------------------------------- sonidos propios (eventos cortos y suaves)
    def s_tictic():
        """Tres golpecitos secos y muy cortos (el párpado que salta)."""
        d = .32; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for k, t0 in enumerate((0, .1, .19)):
            m = t >= t0; tt = t[m] - t0
            x[m] += (.9 - .2 * k) * np.sin(2 * np.pi * (1500 - 300 * k) * tt) * np.exp(-tt / .012)
        return x
    def s_chispa():
        d = .35; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        crep = (np.random.default_rng(301).random(n) > .985).astype(float)
        return AU._banda(AU._ruido(n, 302), 2500, 9000) * np.exp(-t / .09) * .5 + AU._banda(crep, 1500, 9000) * 3 * np.exp(-t / .2)
    def s_terremoto():
        d = .8; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        return (AU._banda(AU._ruido(n, 303), 30, 180) * 2 + .4 * np.sin(2 * np.pi * 48 * t)) * np.sin(np.pi * u) ** 1.2
    def s_gota():
        d = .22; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * (500 + 1400 * t / d) * t) * np.exp(-t / .05) * np.minimum(1, t / .003)
    def s_rebosa():
        d = .7; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        return AU._banda(AU._ruido(n, 304), 400, 3000) * np.sin(np.pi * u) * (1 + .6 * np.sin(2 * np.pi * 13 * t))
    def s_lamp():
        d = .12; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * 2200 * t) * np.exp(-t / .01) + .5 * AU._banda(AU._ruido(n, 305), 1000, 5000) * np.exp(-t / .015)
    for nom, fn, db in (("tictic", s_tictic, -27), ("chispa", s_chispa, -30), ("terremoto", s_terremoto, -26), ("gota", s_gota, -28),
                        ("rebosa", s_rebosa, -31), ("lampara", s_lamp, -29)):
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
        if a <= 0: return
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
    def _fade(t, t_in, t_out=1e9, d_in=.18, d_out=.2):
        return aparece(t - t_in, d_in) * TI.clamp((t_out - t) / d_out)
    def _tic(t, t0, dur=99.0):
        """Temblor del párpado: ráfagas irregulares (0..1) desde t0."""
        if t < t0 or t > t0 + dur: return 0.0
        dt = t - t0; ph = (dt * 1.15) % 1.0
        if ph > .62: return 0.0
        return abs(math.sin(dt * 46)) * (.6 + .4 * math.sin(dt * 7.3)) * math.sin(math.pi * ph / .62) ** .4
    PIEL = ("#FBE0C8", "#F1C3A0", "#D99A74")

    # ---------------------------------------------------------------- ojo grande ilustrado
    def _ojo(c, x, y, s, t, abierto=1.0, tic=0.0, mira=(0.0, 0.0), a=1.0, rojo=0.0, piel=PIEL):
        """Ojo en primer plano: (x, y) = centro; hw = 300·s. abierto 0..1 (párpado de arriba); tic 0..1 sube el párpado de abajo."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.scale(s, s)
        hw = 300.0; U = 8 + 168 * TI.clamp(abierto); Lo = 118 - 46 * tic
        # pliegue del párpado y sombra de la cuenca
        c.drawOval(skia.Rect(-hw - 70, -250, hw + 70, 210), skia.Paint(AntiAlias=True, Color=color(piel[2], .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 50)))
        pl = skia.Path(); pl.moveTo(-hw - 10, -10); pl.quadTo(0, -U * 2 - 120, hw + 10, -10)
        c.drawPath(pl, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=12, Color=color("#7A4030", .45 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
        ojo = skia.Path(); ojo.moveTo(-hw, 0); ojo.quadTo(0, -U * 2, hw, 0); ojo.quadTo(0, Lo * 2 * TI.clamp(abierto * 3), -hw, 0); ojo.close()
        if abierto > .03:
            c.save(); c.clipPath(ojo, doAntiAlias=True)
            c.drawRect(skia.Rect(-hw, -300, hw, 300), _p(_rad(0, 0, 340, ["#FFFFFF", _mix("#F4E4DE", "#F2B0A8", rojo), _mix("#D8B0A8", "#C86A64", rojo)], [0, .6, 1], a)))
            if rojo > 0:
                vr = np.random.default_rng(7); pv = skia.Path()
                for k in range(14):
                    sx = -1 if k % 2 else 1; xx, yy = sx * hw * .96, (vr.random() - .5) * 80; pv.moveTo(xx, yy)
                    for _ in range(4): xx -= sx * (30 + 40 * vr.random()); yy += (vr.random() - .5) * 40; pv.lineTo(xx, yy)
                c.drawPath(pv, trazo("#C8242A", 2.2, .7 * rojo * a))
            ix, iy, R = mira[0] * 60, 6 + mira[1] * 30, 118
            c.drawCircle(ix, iy, R, _p(_rad(ix, iy, R, ["#1E2A12", "#4E7A3A", "#8DB060", "#2E4A1C"], [0, .42, .8, 1], a)))
            fib = skia.Path(); fr = np.random.default_rng(5)
            for k in range(120):
                an = 2 * math.pi * k / 120 + fr.random() * .04; r0 = 50 + 8 * fr.random(); r1 = R * (.72 + .26 * fr.random())
                fib.moveTo(ix + r0 * math.cos(an), iy + r0 * math.sin(an)); fib.lineTo(ix + r1 * math.cos(an), iy + r1 * math.sin(an))
            c.drawPath(fib, trazo("#E6F2B0", 1.4, .32 * a))
            c.drawCircle(ix, iy, R, trazo("#16200C", 6, .7 * a))
            c.drawCircle(ix, iy, 48, relleno("#06080A", a))
            c.drawCircle(ix - 36, iy - 40, 22, relleno("#FFFFFF", .92 * a)); c.drawCircle(ix + 30, iy + 26, 9, relleno("#FFFFFF", .6 * a))
            c.drawRect(skia.Rect(-hw, -U * 2, hw, -U * 2 + 60 + 40 * abierto), _p(_lin(-U * 1.2, -U * .5, ["#3A1A12", "#3A1A12"], .0)))
            c.drawPath(ojo, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=30, Color=color("#5A2A1E", .28 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
            c.restore()
        # párpado de arriba: borde y pestañas
        up = skia.Path(); up.moveTo(-hw, 0); up.quadTo(0, -U * 2, hw, 0)
        c.drawPath(up, trazo("#2A120C", 9, a))
        for k in range(1, 22):
            u = k / 22; px = -hw + 2 * hw * u; py = (1 - u) * u * 2 * (-U * 2)    # quad: y = 2u(1-u)·cy
            ang = -math.pi / 2 + (u - .5) * 1.5
            L = 34 + 26 * math.sin(math.pi * u)
            c.drawLine(px, py, px + L * math.cos(ang) * 1.1, py + L * math.sin(ang), skia.Paint(AntiAlias=True, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap, Color=color("#1A0A06", a)))
        # párpado de abajo (el que tiembla)
        lo_y = Lo * 2 * TI.clamp(abierto * 3)
        lw = skia.Path(); lw.moveTo(-hw, 0); lw.quadTo(0, lo_y, hw, 0)
        c.drawPath(lw, trazo(_mix("#7A3A2A", "#C2483A", tic), 6, .9 * a))
        for k in range(2, 20, 2):
            u = k / 20; px = -hw + 2 * hw * u; py = 2 * u * (1 - u) * lo_y
            c.drawLine(px, py, px + (u - .5) * 16, py + 16, skia.Paint(AntiAlias=True, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap, Color=color("#1A0A06", .8 * a)))
        if tic > .05:                                                              # rayitas de vibración bajo el párpado
            for k in range(3):
                yy = lo_y * .55 + 40 + k * 22
                c.drawArc(skia.Rect(-150 - 20 * k, yy - 20, 150 + 20 * k, yy + 20), 20, 140, False, trazo("#FFFFFF", 5, .7 * tic * a))
        c.restore()

    def _anillo_m(c, x, y, s, t, prog=1.0, squeeze=0.0, trozo=0.0, a=1.0):
        """Músculo orbicular: anillo de fibras rojizas alrededor del ojo. prog 0..1 se dibuja; squeeze lo encoge; trozo enciende un sector abajo."""
        if a <= 0 or prog <= 0: return
        c.save(); c.translate(x, y); sq = 1 - .07 * squeeze; c.scale(s * sq, s * (1 - .1 * squeeze))
        rx, ry, gw = 430.0, 330.0, 92.0
        n = 96; m = int(n * TI.clamp(prog))
        for k in range(m):
            an0 = -math.pi / 2 + 2 * math.pi * k / n; an1 = an0 + 2 * math.pi / n * 1.05
            sector = 1.0 if (trozo > 0 and math.sin(an0) > .55 and abs(math.cos(an0)) < .55) else 0.0
            enc = .18 * trozo * sector
            for j in range(5):
                f = (j - 2) / 2.0; r_x, r_y = rx + f * gw / 2, ry + f * gw / 2
                col = _mix("#B8404A", "#E8707A", (j % 2) * .4 + .3 * math.sin(k * 1.7)) if not sector else _mix("#E8707A", "#FFD27A", trozo)
                p0 = (r_x * math.cos(an0), r_y * math.sin(an0) * (1 - enc)); p1 = (r_x * math.cos(an1), r_y * math.sin(an1) * (1 - enc))
                c.drawLine(p0[0], p0[1], p1[0], p1[1], skia.Paint(AntiAlias=True, StrokeWidth=gw / 5 + 2, StrokeCap=skia.Paint.kRound_Cap, Color=color(col, .9 * a)))
            hx, hy = (rx - gw / 2.6) * math.cos(an0), (ry - gw / 2.6) * math.sin(an0)
            c.drawLine(hx, hy, (rx + gw / 2.6) * math.cos(an0) * .999, (ry + gw / 2.6) * math.sin(an0) * .999, trazo("#FFFFFF", 1.2, .18 * a))
        # brillo en el borde de lo que se va dibujando
        if prog < 1:
            an = -math.pi / 2 + 2 * math.pi * prog; _glow(c, rx * math.cos(an), ry * math.sin(an), 90, "#FFB0A0", .5 * a)
        if trozo > 0: _glow(c, 0, ry, 160, "#FFD27A", .35 * trozo * a)
        c.restore()

    # ---------------------------------------------------------------- personajes de la habitación
    def _amigo(c, x, y, s, t, a=1.0, mira=(0.0, 0.0), cascos=False, exprs="neutral"):
        """Amigo (sudadera verde): busto pequeño. (x, y) = centro de la cabeza."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.scale(s, s)
        sh = skia.Path(); sh.moveTo(-230, 520); sh.cubicTo(-230, 330, -170, 250, -70, 240); sh.lineTo(70, 240); sh.cubicTo(170, 250, 230, 330, 230, 520); sh.close()
        c.drawPath(sh, _p(_lin(240, 520, ["#4FD08A", "#24A060", "#126A3C"], a)))
        c.drawRRect(rrc(0, 210, 90, 80, 30), _p(_lin(170, 250, [PIEL[1], PIEL[2]], a)))
        c.drawOval(skia.Rect(-165, -190, 165, 190), _p(_rad(-40, -60, 260, ["#E9B48A", "#C98A62", "#9A603E"], [0, .6, 1], a)))
        bl = 1.0 if (t * .8 + .9) % 3.1 > .12 else .1
        for sx in (-1, 1):
            ex, ey = sx * 62 + mira[0] * 14, -20 + mira[1] * 8
            c.drawOval(skia.Rect(ex - 24, ey - 18 * bl, ex + 24, ey + 18 * bl), relleno("#FFFFFF", a))
            if bl > .4: c.drawCircle(ex + mira[0] * 8, ey, 11, relleno("#2A1A10", a)); c.drawCircle(ex + mira[0] * 8 - 4, ey - 4, 3.5, relleno("#FFFFFF", a))
            c.drawLine(ex - 26, ey - 40, ex + 24, ey - 44 - (8 if exprs == "o" else 0), skia.Paint(AntiAlias=True, StrokeWidth=10, StrokeCap=skia.Paint.kRound_Cap, Color=color("#1A120C", a)))
        if exprs == "o": c.drawOval(skia.Rect(-16, 80, 16, 112), relleno("#5A1E1E", a))
        else: c.drawArc(skia.Rect(-34, 60, 34, 100), 20, 140, False, trazo("#5A1E1E", 7, a))
        hp = skia.Path(); hp.moveTo(-170, -40); hp.cubicTo(-190, -230, 160, -260, 170, -40); hp.cubicTo(120, -150, -60, -170, -170, -40); hp.close()
        c.drawPath(hp, _p(_lin(-240, -40, ["#2A1A12", "#120A06"], a)))
        if cascos:
            c.drawArc(skia.Rect(-190, -230, 190, 120), 180, 180, False, trazo("#20242E", 22, a))
            for sx in (-1, 1):
                c.drawRRect(rrc(sx * 182, 0, 60, 110, 26), _p(_lin(-55, 55, ["#3A4052", "#141822"], a)))
                c.drawRRect(rrc(sx * 182, 0, 30, 70, 14), relleno("#FF5A8A", .9 * a))
        c.restore()

    def _cuarto(c, t, luz=1.0, sacude=(0.0, 0.0)):
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#241E46", "#17122E", "#0A0818"])))
        for k in range(16): c.drawLine(k * 76 - 30, -80, k * 76 - 30, 1300, trazo("#FFFFFF", 2, .025))
        # ventana con luna y estrellas
        c.drawRRect(rrc(190, 290, 250, 290, 16), relleno("#8A6440")); c.drawRRect(rrc(190, 290, 222, 262, 10), _p(_lin(160, 420, ["#0B1236", "#24306A"])))
        rng = np.random.default_rng(41)
        for k in range(14):
            sx, sy = 95 + 190 * rng.random(), 170 + 240 * rng.random()
            c.drawCircle(sx, sy, 1.5 + 1.5 * rng.random(), relleno("#FFFFFF", .4 + .5 * abs(math.sin(t * 1.7 + k))))
        c.drawCircle(250, 220, 30, _p(_rad(240, 212, 34, ["#FFFFFF", "#DDE6F6"]))); c.drawCircle(264, 212, 25, relleno("#16204E"))
        c.drawLine(190, 159, 190, 421, trazo("#8A6440", 7)); c.drawLine(79, 290, 301, 290, trazo("#8A6440", 7))
        # estantería con libros
        c.drawRect(skia.Rect(640, 300, 940, 312), relleno("#5A3E2A"))
        for k, (w_, h_, col) in enumerate(((30, 90, "#E85A4A"), (24, 110, "#4A8AE8"), (34, 80, "#E8B84A"), (22, 100, "#6AD08A"), (28, 70, "#B06AE8"))):
            xx = 660 + sum(q[0] + 6 for q in ((30, 0), (24, 0), (34, 0), (22, 0), (28, 0))[:k])
            c.drawRect(skia.Rect(xx, 300 - h_, xx + w_, 300), relleno(col, .85))
        c.drawCircle(880, 260, 34, relleno("#2E8A5A", .9)); c.drawRect(skia.Rect(866, 270, 894, 300), relleno("#B0603A"))
        # lámpara de mesa
        c.drawLine(140, 820, 140, 1060, trazo("#4A5268", 8)); c.drawPath(skia.Path.Polygon([(80, 830), (200, 830), (172, 750), (108, 750)], True), relleno(_mix("#3A3428", "#FFE15A", luz)))
        _glow(c, 140, 840, 330, "#FFE9A0", .32 * luz)
        c.drawRect(skia.Rect(-80, 1060, W + 80, H + 80), _p(_lin(1060, H, ["#2E2238", "#120C18"])))

    def _sismo(c, x, y, t, amp, a, titulo, S, col="#FF5A6A", self=None):
        """Tarjeta de sismógrafo con la línea que corre."""
        if a <= 0: return
        w, h = 400, 190
        c.drawRRect(rrc(x + 6, y + 10, w, h, 24), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
        c.drawRRect(rrc(x, y, w, h, 24), _p(_lin(y - h / 2, y + h / 2, ["#FBF8F0", "#E7E0CE"], a)))
        for k in range(1, 6): c.drawLine(x - w / 2 + 20, y - h / 2 + 30 + k * 26, x + w / 2 - 20, y - h / 2 + 30 + k * 26, trazo("#9AAFD6", 1.2, .5 * a))
        pth = skia.Path(); yc = y + 22
        for k in range(0, 121):
            xx = x - w / 2 + 24 + (w - 48) * k / 120; ph = k * .55 - t * 22
            v = amp * (math.sin(ph) * .6 + .4 * math.sin(ph * 2.7 + 1.3)) * (.5 + .5 * abs(math.sin(k * .09 - t * 2)))
            (pth.moveTo if k == 0 else pth.lineTo)(xx, yc + 62 * v)
        c.drawPath(pth, trazo(col, 4, a))
        c.drawCircle(x + w / 2 - 24, yc + 62 * amp * math.sin(-t * 22 + 66) * .6, 7, relleno(col, a))
        texto(c, titulo, x, y - h / 2 + 30, F(800, 30), "#14182A", alfa=a)
        c.drawRRect(rrc(x, y, w, h, 24), trazo("#C9A87A", 2.5, a))

    def _cara_tic(self, c, fx, fy, fs, t, tic, cerrado=0.0):
        """Encima de cara_b: el párpado de abajo del ojo izquierdo (del dibujo) salta; cerrado tapa los dos ojos."""
        c.save(); c.translate(fx, fy); c.scale(fs, fs)
        if tic > 0:
            ex, ey = -78, -40
            c.save(); c.clipRect(skia.Rect(ex - 40, ey - 4, ex + 40, ey + 34))
            h = 3 + 15 * tic
            c.drawRect(skia.Rect(ex - 40, ey + 26 - h, ex + 40, ey + 40), relleno(PIEL[1]))
            c.restore()
            c.drawArc(skia.Rect(ex - 34, ey + 26 - h - 10, ex + 34, ey + 26 - h + 10), 10, 160, False, trazo("#6A3A28", 3, .8))
            for k in range(3):
                an = math.pi * (.15 + .35 * k); r = 52 + 6 * tic
                c.drawLine(ex + r * math.cos(an + math.pi * .55), ey + 30 + r * .6 * math.sin(an), ex + (r + 18) * math.cos(an + math.pi * .55), ey + 30 + (r + 18) * .6 * math.sin(an), trazo("#FFFFFF", 4, .8 * tic))
        if cerrado > 0:
            for sx in (-1, 1):
                ex, ey = sx * 78, -40
                c.drawOval(skia.Rect(ex - 38, ey - 30, ex + 38, ey - 30 + 60 * cerrado), relleno(PIEL[1]))
                if cerrado > .8: c.drawArc(skia.Rect(ex - 32, ey - 10, ex + 32, ey + 14), 10, 160, False, trazo("#4A2418", 5))
        c.restore()

    # ---------------------------------------------------------------- parpado: gancho / cierre
    def e_parpado(self, c, e, t, S):
        s = e["spec"]; modo = s.get("modo", "gancho")
        fx, fy, fs = CX + 20, 820, 1.28
        if modo == "gancho":
            tt, tn, tq, tf = (_tw(self, e, k) for k in ("tic_word", "nadie_word", "terremoto_word", "fuera_word"))
            sac = 0.0
            if tq - .1 < t < tq + .8: sac = 14 * math.sin(math.pi * (t - tq + .1) / .9)
            dx, dy = sac * math.sin(t * 61), sac * .6 * math.cos(t * 53)
            c.save(); c.translate(dx, dy)
            _cuarto(c, t)
            tic = _tic(t, tt - .05) * (1 if t < tf + .3 else .5)
            self.cara_b(c, fx, fy, fs, t, cob=0, largo=0, expr=("o" if tt < t < tn else ("meh" if t > tf else "neutral")), mira=((.6, .2) if t > tn and t < tq else (0, 0)))
            _cara_tic(self, c, fx, fy, fs, t, tic)
            # lupa sobre el ojo que tiembla
            if t > tt - .1:
                a = _fade(t, tt - .1, tn, .15, .25)
                lx, ly = fx - 78 * fs, fy - 40 * fs
                c.drawCircle(lx, ly, 120, skia.Paint(AntiAlias=True, Color=color("#FFFFFF", .10 * a)))
                c.drawCircle(lx, ly, 120, trazo("#20242E", 16, a)); c.drawCircle(lx, ly, 120, trazo("#AEB8CA", 5, a))
                c.save(); c.translate(lx, ly); c.rotate(40); c.drawRRect(rrc(0, 200, 40, 150, 18), _p(_linx(-20, 20, ["#5A3A20", "#2A1A10"], a))); c.restore()
                c.drawArc(skia.Rect(lx - 95, ly - 95, lx + 95, ly + 95), 200, 60, False, trazo("#FFFFFF", 8, .5 * a))
                if t - tt < 1.6: self.comic_t(c, "¡TIC!", lx + 210, ly - 170, 84, -8, .7 + .3 * resorte(t - tt, 10, 14), 1 - TI.clamp((t - tt - 1.3) / .3), "#FFE15A")
            # el amigo mira y no ve nada
            if t > tn - .2:
                a = _fade(t, tn - .2, 1e9, .2)
                ax = 165 - 260 * (1 - resorte(t - tn + .2, 7, 9)); ay = 1000
                _amigo(c, ax, ay, .62, t, a, mira=(1, -.2), exprs="neutral")
                bub_a = _fade(t, tn + .3, tq - .1)
                if bub_a > 0:
                    bx, by = ax + 70, ay - 220
                    c.drawRRect(rrc(bx, by, 150, 110, 40), relleno("#FFFFFF", .96 * bub_a)); c.drawPath(skia.Path.Polygon([(bx - 30, by + 50), (bx + 5, by + 50), (bx - 40, by + 90)], True), relleno("#FFFFFF", .96 * bub_a))
                    texto(c, "¿?", bx, by, F(900, 60), "#14182A", alfa=bub_a)
            c.restore()
            if t > tq - .1: _sismo(c, 300, 250, t, 1.0, _fade(t, tq - .1, 1e9, .2), s.get("notas_txt", "LO QUE NOTAS"), S, "#FF5A6A")
            if t > tf - .1: _sismo(c, 750, 250, t, .06, _fade(t, tf - .1, 1e9, .2), s.get("ve_txt", "LO QUE SE VE"), S, "#2A6AE8")
        else:
            tt, td, tn = (_tw(self, e, k) for k in ("tic_word", "dormir_word", "nadie_word"))
            luz = 1 - _io((t - td - .3) / .5)
            _cuarto(c, t, luz=max(.15, luz))
            dorm = _io((t - td) / .45)
            tic = _tic(t, tt - .05) * (1 - dorm)
            self.cara_b(c, fx, fy, fs, t, cob=0, largo=0, expr=("feliz" if t < td else "meh"), mira=(0, 0))
            _cara_tic(self, c, fx, fy, fs, t, tic, cerrado=dorm)
            if luz < 1:
                c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), relleno("#05030E", .45 * (1 - luz)))
            if t > td:
                for k in range(3):
                    ph = ((t - td) * .55 + k / 3) % 1
                    texto(c, "Z" if k % 2 == 0 else "z", fx + 160 + 120 * ph, fy - 260 - 260 * ph, F(900, int(60 + 40 * (1 - ph))), "#D9CCFF", alfa=(1 - ph) * aparece(t - td, .3))
            if t > tn - .5:                                                       # el amigo pasa con los cascos y ni se entera
                u = TI.clamp((t - tn + .5) / 2.6); ax = -200 + 560 * _io(u)
                _amigo(c, ax, 1010, .6, t, aparece(t - tn + .5, .2), mira=(-.2, .6), cascos=True)
                for k in range(3):
                    ph = ((t - tn) * .9 + k / 3) % 1
                    c.drawCircle(ax + 150 + 60 * ph, 800 - 90 * ph, 9, relleno("#FF5A8A", (1 - ph) * aparece(t - tn, .2)))
                _pill(self, c, s.get("nadie_txt", "NI SE HA ENTERADO"), CX, 190, S, _fade(t, tn + .3), fondo="#5A2A9A")
        _franja(c)

    # ---------------------------------------------------------------- anillo: el músculo orbicular
    def _piel_fondo(c, t, oscuro=0.0):
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, [_mix("#C98A68", "#5A3428", oscuro), _mix("#B47454", "#4A2A20", oscuro), "#6A3A2C", "#2A140E", "#120806"], 1, 0, [0, .3, .55, .72, .85])))
        rng = np.random.default_rng(3); po = skia.Path()
        for _ in range(500): po.addCircle(float(rng.random() * W), float(rng.random() * 1150), float(.6 + rng.random() * 1.3))
        c.drawPath(po, relleno("#4A2418", .12))
        # ceja
        ce = skia.Path(); ce.moveTo(CX - 420, 250); ce.cubicTo(CX - 200, 140, CX + 160, 130, CX + 430, 210)
        for k in range(22):
            o = (k - 11) * 2.4
            c.save(); c.translate(o * .6, o); c.drawPath(ce, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.4, Color=color("#2A160E", .5))); c.restore()
    def e_anillo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        tn, ta, tc, tp = (_tw(self, e, k) for k in ("nombre_word", "anillo_word", "cierra_word", "parpadea_word"))
        _piel_fondo(c, t)
        # parpadeos: automático cada ~3 s y uno grande en «cierra»/«parpadeas»
        ab = 1.0
        ph = (t + .4) % 3.3
        if ph < .18: ab = abs(math.cos(math.pi * ph / .18))
        for tk in (tc, tp):
            if tk - .1 < t < tk + .45: ab = min(ab, abs(math.cos(math.pi * (t - tk + .1) / .55)))
        sq = 0.0
        for tk in (tc, tp):
            if tk - .1 < t < tk + .45: sq = max(sq, math.sin(math.pi * (t - tk + .1) / .55))
        oy = 640
        _ojo(c, CX, oy, 1.0, t, abierto=ab, mira=(.15 * math.sin(t * .5), 0))
        prog = _io((t - ta + .2) / .9) if t > ta - .2 else 0
        _anillo_m(c, CX, oy, 1.0, t, prog=prog, squeeze=sq, a=1.0)
        if prog > 0:
            for k in range(4):                                                     # flechas hacia dentro al cerrar
                an = math.pi / 4 + k * math.pi / 2; r = 560 - 40 * sq
                ax, ay = CX + r * math.cos(an), oy + r * .78 * math.sin(an)
                aa = sq * prog
                if aa > .05:
                    c.save(); c.translate(ax, ay); c.rotate(math.degrees(an) + 180)
                    c.drawLine(0, 0, 60, 0, trazo("#FFE15A", 9, aa)); c.drawPath(skia.Path.Polygon([(70, 0), (46, -18), (46, 18)], True), relleno("#FFE15A", aa)); c.restore()
            _pill(self, c, s.get("musculo_txt", "MÚSCULO ORBICULAR"), CX, 1060, S, aparece(t - ta - .5, .2), fondo="#8A2A30")
        if t > tn - .15:                                                          # ficha con el nombre
            a = aparece(t - tn + .15, .2) * (1 - TI.clamp((t - ta + .4) / .3)); u = resorte(t - tn + .15, 8, 10)
            if a > 0:
                c.save(); c.translate(CX, 190 - 30 * (1 - u)); c.rotate(-2)
                c.drawRRect(rrc(6, 10, 720, 150, 26), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
                c.drawRRect(rrc(0, 0, 720, 150, 26), _p(_lin(-75, 75, ["#FFFDF6", "#EDE4CF"], a)))
                texto(c, s.get("nombre_txt", ""), 0, -22, F(900, 54), "#8A2A30", alfa=a)
                texto(c, s.get("nombre_sub", ""), 0, 38, F(700, 32), "#3A2A20", alfa=a)
                c.restore()
        _franja(c)

    # ---------------------------------------------------------------- nervio: el cable que da chispazos
    def e_nervio(self, c, e, t, S):
        s = e["spec"]
        tnv, tcb, tch, ttr, toj, tab = (_tw(self, e, k) for k in ("nervio_word", "cable_word", "chispa_word", "trozo_word", "ojo_word", "abajo_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2453D6", "#163A9E", "#0A1E5A"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=31, n=50, col="#BFD4FF")
        ox, oy, os_ = CX + 60, 560, .8
        c.drawOval(skia.Rect(ox - 430, oy - 340, ox + 430, oy + 340), _p(_rad(ox, oy, 360, ["#E6A886", "#B87050", "#7A4A3A"], [0, .7, 1])))
        trz = _io((t - ttr + .1) / .25) * (1 - _io((t - tab - .8) / .5)) if t > ttr - .1 else 0
        sacudida = _tic(t, ttr) if t > ttr else 0
        _ojo(c, ox, oy, os_, t, abierto=1.0 if (t + .7) % 3.6 > .16 else .2, tic=sacudida * (1 if t > tab - .2 else .6), mira=(-.3, 0))
        _anillo_m(c, ox, oy, os_, t, prog=1.0, trozo=trz * (.5 + .5 * sacudida), a=.95)
        # el nervio: cable desde abajo a la izquierda hasta el anillo
        pc = skia.Path(); pc.moveTo(-60, 1080); pc.cubicTo(160, 1000, 60, 820, ox - 320, oy + 160)
        ca = _io((t - tnv + .2) / .6) if t > tnv - .2 else 0
        if ca > 0:
            me = skia.PathMeasure(pc, False); L = me.getLength()
            seg = skia.Path(); me.getSegment(0, L * ca, seg, True)
            c.drawPath(seg, trazo("#6A4A10", 30, .9)); c.drawPath(seg, trazo("#FFD24A", 20)); c.drawPath(seg, trazo("#FFF2A0", 6, .8))
            if t > tcb:                                                            # pulsos que viajan
                for k in range(4):
                    ph = ((t - tcb) * .9 + k / 4) % 1
                    pos, _tg = me.getPosTan(L * ph)
                    _glow(c, pos.x(), pos.y(), 50, "#FFFFFF", .7); c.drawCircle(pos.x(), pos.y(), 10, relleno("#FFFFFF"))
            _pill(self, c, s.get("nervio_txt", "NERVIO"), 300, 1000, S, aparece(t - tnv, .2), fondo="#7A5A05")
            # chispazos por su cuenta en la punta
            if t > tch - .1:
                ex, ey = ox - 320, oy + 160
                for k in range(3):
                    ph = (t * 3.1 + k * .37) % 1
                    if ph < .35:
                        rng = np.random.default_rng(int(t * 9) + k * 17); zz = skia.Path(); zx, zy = ex, ey; zz.moveTo(zx, zy)
                        an = rng.random() * 2 * math.pi
                        for _ in range(5): zx += 26 * math.cos(an) + rng.normal() * 14; zy += 26 * math.sin(an) + rng.normal() * 14; zz.lineTo(zx, zy)
                        c.drawPath(zz, trazo("#FFFFFF", 5, 1 - ph / .35)); c.drawPath(zz, trazo("#FFE15A", 11, .4 * (1 - ph / .35)))
                _glow(c, ex, ey, 130, "#FFE15A", .45 + .25 * math.sin(t * 23))
                if t - tch < 1.4: self.comic_t(c, "¡BZZT!", ex - 60, ey - 380, 70, -6, .7 + .3 * resorte(t - tch, 10, 14), 1 - TI.clamp((t - tch - 1.1) / .3), "#FFE15A")
        if t > toj - .2:
            _pill(self, c, s.get("uno_txt", "UN OJO"), 270, 190, S, aparece(t - toj + .2, .15), fondo="#0B1430")
        if t > tab - .2:
            _pill(self, c, s.get("abajo_txt", "PÁRPADO DE ABAJO"), 650, 190, S, aparece(t - tab + .2, .15), fondo="#8A2A30")
            a = aparece(t - tab, .2)
            c.drawLine(ox, oy + 230, ox, 270 + 40, trazo("#FFE15A", 0, 0))
            p_ = trazo("#FFE15A", 5, .9 * a); p_.setPathEffect(skia.DashPathEffect.Make([14, 10], -t * 40))
            c.drawLine(650, 230, ox + 20, oy + 90, p_)
        _franja(c)

    # ---------------------------------------------------------------- iconos de los sospechosos
    def _icono(c, tipo, x, y, s, t, a=1.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        if tipo == "sueno":                                                        # almohada + despertador
            c.drawRRect(rrc(0, 40, 230, 110, 50), _p(_lin(-15, 95, ["#FFFFFF", "#C8D2EA"], a)))
            c.drawLine(-80, 40, 80, 40, trazo("#AEB8CA", 3, .6 * a))
            c.drawCircle(60, -50, 60, _p(_rad(45, -65, 70, ["#FF7A6A", "#C8302A"], None, a))); c.drawCircle(60, -50, 46, relleno("#FFFFFF", a))
            for sx in (-1, 1): c.drawCircle(60 + sx * 42, -102, 18, relleno("#C8302A", a))
            c.drawLine(60, -50, 60, -80, trazo("#14182A", 6, a)); c.drawLine(60, -50, 60 + 24 * math.cos(t * 2), -50 + 24 * math.sin(t * 2), trazo("#14182A", 5, a))
            if math.sin(t * 20) > 0:
                for sx in (-1, 1): c.drawLine(60 + sx * 70, -110, 60 + sx * 92, -130, trazo("#FFE15A", 5, a))
            texto(c, "z", -60, -40, F(900, 50), "#5A6A9A", alfa=a * (.5 + .5 * math.sin(t * 3)))
        elif tipo == "estres":                                                     # nube de tormenta con rayo
            for ox, oy, r in ((-60, 0, 60), (0, -30, 75), (65, 0, 58), (0, 20, 65)):
                c.drawCircle(ox, oy, r, _p(_rad(ox - 20, oy - 25, r * 1.3, ["#8A92A8", "#4A5268"], None, a)))
            zz = skia.Path.Polygon([(-5, 40), (-35, 120), (0, 115), (-20, 190), (40, 95), (5, 100), (25, 40)], True)
            c.drawPath(zz, relleno("#FFE15A", a * (.7 + .3 * (math.sin(t * 17) > 0))))
            for k in range(4): c.drawLine(-80 + 50 * k, 70, -90 + 50 * k, 70 + 40 + 30 * ((t * 2 + k * .3) % 1), trazo("#7AB0FF", 4, .7 * a))
        elif tipo == "cafe":                                                       # taza con vapor
            c.drawRRect(rrc(0, 30, 150, 160, 30), _p(_linx(-75, 75, ["#E8E2D6", "#FFFFFF", "#C8C0B0"], a)))
            c.drawArc(skia.Rect(60, -10, 130, 70), -90, 180, False, trazo("#D8D0C0", 16, a))
            c.drawOval(skia.Rect(-70, -55, 70, -35), relleno("#5A341A", a))
            c.drawOval(skia.Rect(-110, 100, 110, 130), relleno("#C8C0B0", .8 * a))
            for k in range(3):
                ph = (t * .7 + k / 3) % 1; vx = -40 + 40 * k
                vp = skia.Path(); vp.moveTo(vx, -60); vp.cubicTo(vx - 20, -90 - 40 * ph, vx + 20, -110 - 40 * ph, vx, -150 - 50 * ph)
                c.drawPath(vp, trazo("#FFFFFF", 7, .5 * (1 - ph) * a))
        elif tipo == "movil":
            c.save(); c.rotate(-8)
            c.drawRRect(rrc(0, 0, 150, 270, 26), _p(_lin(-135, 135, ["#3A4052", "#14182A"], a)))
            c.drawRRect(rrc(0, 0, 128, 240, 18), _p(_lin(-120, 120, ["#6EA0FF", "#2A6AE8", "#7A4AE0"], a)))
            for k in range(4):
                yy = -80 + k * 50 - (t * 30) % 50
                c.drawRRect(rrc(0, yy, 96, 30, 8), relleno("#FFFFFF", .35 * a))
            c.restore()
            _glow(c, 0, 0, 200, "#6EA0FF", .3 * a)
        elif tipo == "vicios":                                                     # copa + cigarro
            c.drawPath(skia.Path.Polygon([(-110, -90), (-10, -90), (-40, 10), (-80, 10)], True), _p(_lin(-90, 10, ["#E8F0FF", "#B8C8E8"], .6 * a)))
            c.drawPath(skia.Path.Polygon([(-100, -60), (-20, -60), (-38, 0), (-82, 0)], True), relleno("#A01A3A", .85 * a))
            c.drawLine(-60, 10, -60, 100, trazo("#C8D4EA", 8, a)); c.drawLine(-100, 100, -20, 100, trazo("#C8D4EA", 8, a))
            c.save(); c.translate(70, 40); c.rotate(-20)
            c.drawRect(skia.Rect(-70, -10, 50, 10), relleno("#F4F2EC", a)); c.drawRect(skia.Rect(-70, -10, -30, 10), relleno("#E0A060", a))
            c.drawRect(skia.Rect(50, -10, 62, 10), relleno("#FF6A3A", a * (.7 + .3 * math.sin(t * 9))))
            c.restore()
            for k in range(2):
                ph = (t * .5 + k / 2) % 1
                c.drawCircle(140 + 20 * math.sin(ph * 6), 20 - 120 * ph, 12 + 14 * ph, relleno("#D8DCE6", .4 * (1 - ph) * a))
        elif tipo == "calendario":
            c.drawRRect(rrc(0, 0, 150, 150, 18), relleno("#FFFFFF", a)); c.drawRRect(rrc(0, -55, 150, 40, 12), relleno("#E5322D", a))
            for i in range(3):
                for j in range(3): c.drawRRect(rrc(-45 + 45 * i, -5 + 38 * j, 30, 26, 5), relleno("#C8D2EA", a))
            c.drawLine(-50, -30, 50, 60, trazo("#E5322D", 7, a))
        elif tipo == "cerrado":                                                    # ojo cerrado y tranquilo
            al = skia.Path(); al.moveTo(-100, 0); al.quadTo(0, -70, 100, 0); al.quadTo(0, 40, -100, 0); al.close()
            c.drawPath(al, _p(_lin(-40, 30, ["#F6CFB0", "#D99A74"], a)))
            cl = skia.Path(); cl.moveTo(-95, 2); cl.quadTo(0, 50, 95, 2)
            c.drawPath(cl, trazo("#2A120C", 7, a))
            for k in range(7):
                u = (k + 1) / 8; px = -95 + 190 * u; py = 2 + 2 * u * (1 - u) * 48
                c.drawLine(px, py, px + (u - .5) * 22, py + 26, trazo("#2A120C", 5, a))
        elif tipo == "cara":
            c.drawOval(skia.Rect(-70, -90, 70, 90), _p(_rad(-20, -30, 110, ["#F6CFB0", "#D99A74"], None, a)))
            for sx in (-1, 1): c.drawCircle(sx * 28, -20, 9, relleno("#2A1A10", a))
            c.drawArc(skia.Rect(-26, 20, 26, 50), 20, 140, False, trazo("#5A1E1E", 5, a))
            for (zx, zy) in ((-40, 30), (40, 30), (0, 60)):
                c.drawCircle(zx, zy, 16 + 4 * math.sin(t * 9 + zx), trazo("#FFE15A", 4, a))
        c.restore()

    # ---------------------------------------------------------------- sospechosos: rueda de reconocimiento
    def e_sospechosos(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#4A3A30", "#2E221C", "#120C08"])))
        for k in range(10):                                                         # regla de alturas de la pared
            yy = 140 + k * 92
            c.drawLine(40, yy, 1000, yy, trazo("#FFFFFF", 2, .10))
            texto(c, f"{200 - 10 * k}", 70, yy - 18, F(700, 22), "#FFFFFF", alfa=.25)
        c.drawRect(skia.Rect(-80, 1060, W + 80, H + 80), relleno("#14100C"))
        pos = [(200, 360), (510, 360), (815, 360), (355, 800), (680, 800)]
        items = s.get("items", [])
        ts = [self.ta(it["word"], e) - .2 for it in items]
        act = max([i for i, tt in enumerate(ts) if t >= tt] or [-1])
        for k, it in enumerate(items):                                              # siluetas con «?» hasta que se revela cada uno
            if t >= ts[k]: continue
            x, y = pos[k]; a = aparece(dt0 - .1 * k, .2)
            c.save(); c.translate(x, y - 40 + 6 * math.sin(t * 2 + k))
            c.drawCircle(0, -70, 62, relleno("#0A0604", .55 * a)); c.drawRRect(rrc(0, 70, 190, 170, 70), relleno("#0A0604", .55 * a))
            texto(c, "?", 0, -70, F(900, 74), "#FFE15A", alfa=.85 * a)
            c.restore()
            c.drawRRect(rrc(x, y + 170, 262, 72, 12), relleno("#14182A", .5 * a)); texto(c, "???", x, y + 170, F(800, 30), "#FFFFFF", alfa=.4 * a)
        if dt0 < 3.0:                                                              # foco que barre la rueda
            fx_ = CX + 380 * math.sin(dt0 * 1.6)
            _glow(c, fx_, 560, 360, "#FFF2C0", .18 * aparece(dt0, .3))
        for k, it in enumerate(items):
            if t < ts[k]: continue
            u = resorte(t - ts[k], 8, 10); a = aparece(t - ts[k], .12)
            x, y = pos[k]; y_ = y - 60 * (1 - u)
            on = k == act
            _sombra(c, x, y + 125, 140, 20, .35 * a)
            _glow(c, x, y - 20, 230, "#FFF2C0", (.35 if on else .12) * a)
            _icono(c, it["tipo"], x, y_ - 30, 1.3 if on else 1.1, t, a * (1 if on else .75))
            # cartel numerado
            c.drawRRect(rrc(x, y + 170, 262, 72, 12), relleno("#14182A", .92 * a)); c.drawRRect(rrc(x, y + 170, 262, 72, 12), trazo("#FFFFFF", 2, .3 * a))
            fx_ = F(800, 30 if len(it["txt"]) < 13 else 23)
            texto(c, it["txt"], x, y + 170, fx_, "#FFFFFF", alfa=a)
            c.drawCircle(x - 130, y - 160, 30, relleno("#FFE15A", a)); texto(c, str(k + 1), x - 130, y - 160, F(900, 34), "#14182A", alfa=a)
            if 0 < t - ts[k] < .18: c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), relleno("#FFF6E0", .16 * (1 - (t - ts[k]) / .18)))   # flash de la foto
        _franja(c)

    # ---------------------------------------------------------------- vaso que se llena
    def e_vaso(self, c, e, t, S):
        s = e["spec"]; ts, tv, tr, tk = (_tw(self, e, k) for k in ("suma_word", "vaso_word", "rebosa_word", "tic_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#0B1530", "#071026", "#050A18"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=17, n=40, col="#6EA0FF")
        gotas = s.get("gotas", [])
        n = max(1, len(gotas)); ini = e["t0"] + .4; fin = max(ini + 1.5, tv + .3)
        tg = [ini + (fin - ini) * k / n for k in range(n)]
        nivel = sum(_io((t - x - .35) / .3) for x in tg) / n * .92
        if t > tr - .1: nivel = .92 + .08 * _io((t - tr + .1) / .4)
        vx, vy0, vy1, vw0, vw1 = CX + 70, 420, 1010, 400, 310          # vaso: borde arriba más ancho
        vaso = skia.Path.Polygon([(vx - vw0 / 2, vy0), (vx + vw0 / 2, vy0), (vx + vw1 / 2, vy1), (vx - vw1 / 2, vy1)], True)
        _sombra(c, vx, vy1 + 10, 190, 22, .5)
        c.drawPath(vaso, relleno("#BFD4FF", .10))
        if nivel > 0:
            ly = vy1 - (vy1 - vy0) * nivel; ola = 8 * math.sin(t * 4)
            c.save(); c.clipPath(vaso, doAntiAlias=True)
            liq = skia.Path(); liq.moveTo(vx - 300, ly + ola)
            for k in range(13): liq.lineTo(vx - 300 + 50 * k, ly + 8 * math.sin(t * 4 + k * .9))
            liq.lineTo(vx + 300, vy1 + 20); liq.lineTo(vx - 300, vy1 + 20); liq.close()
            c.drawPath(liq, _p(_lin(ly, vy1, ["#7AB8FF", "#2A6AE8", "#1A3A9A"], .9)))
            for k in range(6):
                ph = (t * .4 + k / 6) % 1; bx = vx - 100 + 40 * k
                by = vy1 - 20 - (vy1 - ly - 30) * ph
                if by > ly + 10: c.drawCircle(bx + 10 * math.sin(t * 3 + k), by, 6 + 3 * (k % 2), trazo("#FFFFFF", 2, .5))
            c.restore()
        # gotas con su icono
        for k, (tp, t0g) in enumerate(zip(gotas, tg)):
            if t < t0g: continue
            u = TI.clamp((t - t0g) / .45)
            if u < 1:
                gx = vx - 120 + 60 * k; gy = 120 + (vy1 - (vy1 - vy0) * max(nivel, .05) - 120) * u * u
                _icono(c, tp, gx, gy, .38, t, 1.0)
            else:
                _icono(c, tp, 160 + 0 * k, 0, 0, t, 0)                             # (nada: ya está dentro)
            ix = 150; iy = 260 + 170 * k
            _icono(c, tp, ix, iy, .5, t, .9 * aparece(t - t0g - .4, .15))
            if t > t0g + .4: c.drawCircle(ix + 95, iy - 60, 20, relleno("#2ED47A", aparece(t - t0g - .4, .15)))
        # el vaso: cristal
        c.drawPath(vaso, trazo("#E6F0FF", 7, .85))
        c.drawLine(vx - vw0 / 2 + 40, vy0 + 40, vx - vw1 / 2 + 40, vy1 - 60, trazo("#FFFFFF", 10, .25))
        # rebosa
        if t > tr - .1:
            a = aparece(t - tr + .1, .15)
            for sx in (-1, 1):
                for k in range(5):
                    ph = ((t - tr) * 1.1 + k / 5) % 1
                    c.drawCircle(vx + sx * (vw0 / 2 + 10 + 40 * ph), vy0 + 10 + 560 * ph * ph, 12 - 6 * ph, relleno("#7AB8FF", a * (1 - ph)))
            c.drawOval(skia.Rect(vx - 330, vy1 - 10, vx + 330, vy1 + 40), relleno("#2A6AE8", .5 * a * _io((t - tr) / .8)))
        # el ojo arriba: al rebosar, ¡TIC!
        tic = _tic(t, tk - .05) if t > tk - .05 else 0
        c.save(); c.translate(0, 0)
        c.drawOval(skia.Rect(vx, 110, vx + 340, 330), _p(_rad(vx + 170, 220, 190, ["#E6A886", "#B87050", "#7A4A3A"], [0, .7, 1], aparece(t - e["t0"], .2))))
        _ojo(c, vx + 170, 225, .46, t, abierto=1.0 if (t + .2) % 2.9 > .15 else .2, tic=tic, mira=(-.6, .5), a=aparece(t - e["t0"], .2))
        c.restore()
        if t > tk - .05 and t - tk < 1.5: self.comic_t(c, "¡TIC!", vx - 200, 230, 84, 8, .7 + .3 * resorte(t - tk, 10, 14), 1 - TI.clamp((t - tk - 1.2) / .3), "#FFE15A")
        _franja(c)

    # ---------------------------------------------------------------- magnesio
    def _bote(c, x, y, s, txt, a=1.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        _sombra(c, 0, 250, 170, 24, .45 * a)
        c.drawRRect(rrc(0, 40, 300, 400, 50), _p(_linx(-150, 150, ["#E8EEF8", "#FFFFFF", "#AEB8CA"], a)))
        c.drawRRect(rrc(0, -195, 260, 80, 20), _p(_linx(-130, 130, ["#2A6AE8", "#6EA0FF", "#163A9E"], a)))
        for k in range(9): c.drawLine(-120 + 30 * k, -230, -120 + 30 * k, -160, trazo("#163A9E", 3, .6 * a))
        c.drawRRect(rrc(0, 60, 300, 190, 12), relleno("#2ED47A", a))
        texto(c, txt, 0, 40, F(900, 44), "#FFFFFF", alfa=a); texto(c, "Mg", 0, 100, F(800, 40), "#0B4A2A", alfa=a)
        c.drawLine(-110, -120, -110, 220, trazo("#FFFFFF", 14, .4 * a))
        c.restore()
    def e_magnesio(self, c, e, t, S):
        s = e["spec"]; tb, td, tm = (_tw(self, e, k) for k in ("bote_word", "dice_word", "demo_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2453D6", "#163A9E", "#0A1E5A"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=7, n=40, col="#BFD4FF")
        u = resorte(t - tb + .25, 7, 9) if t > tb - .25 else 0
        bx, by = CX, 720 + 400 * (1 - u)
        _bote(c, bx, by, .85, s.get("bote_txt", "MAGNESIO"), aparece(t - tb + .25, .15))
        for k in range(3):                                                         # pastillas que saltan
            ph = ((t - tb) * .7 + k / 3) % 1
            if t > tb: c.drawOval(skia.Rect(bx - 200 + 160 * k - 30, 960 - 140 * math.sin(math.pi * ph) - 14, bx - 200 + 160 * k + 30, 960 - 140 * math.sin(math.pi * ph) + 14), relleno("#FFFFFF", .9))
        # rumores
        rs = s.get("rumores", [])
        posr = [(290, 200), (770, 310), (290, 420)]
        for k, r in enumerate(rs):
            tr_ = td + .1 + .35 * k
            if t < tr_: continue
            a = aparece(t - tr_, .15) * (1 - TI.clamp((t - tm + .2) / .3) * .7); uu = resorte(t - tr_, 9, 12)
            x, y = posr[k % 3]
            c.save(); c.translate(x, y); c.scale(.7 + .3 * uu, .7 + .3 * uu)
            w_ = ancho(r, F(800, 30)) + 50
            c.drawRRect(rrc(0, 0, w_, 80, 36), relleno("#FFFFFF", .96 * a))
            c.drawPath(skia.Path.Polygon([(-20, 36), (14, 36), (-34, 70)] if k != 1 else [(20, 36), (-14, 36), (34, 70)], True), relleno("#FFFFFF", .96 * a))
            texto(c, r, 0, 0, F(800, 30), "#14182A", alfa=a)
            c.restore()
        # lupa sobre un estudio y sello
        if t > tm - .7:
            a = aparece(t - tm + .7, .2)
            px, py = 815, 880
            c.save(); c.translate(px, py); c.rotate(6)
            c.drawRRect(rrc(0, 0, 230, 290, 12), relleno("#FFFFFF", a))
            for k in range(8): c.drawLine(-90, -110 + 28 * k, 90 - 40 * (k % 3), -110 + 28 * k, trazo("#9AAFD6", 5, .8 * a))
            c.restore()
            lx = px - 40 + 60 * math.sin((t - tm) * 3); ly = py - 30 + 40 * math.cos((t - tm) * 2.4)
            c.drawCircle(lx, ly, 70, relleno("#FFFFFF", .15 * a)); c.drawCircle(lx, ly, 70, trazo("#20242E", 12, a))
            c.save(); c.translate(lx, ly); c.rotate(-40); c.drawRRect(rrc(0, 120, 28, 100, 12), relleno("#5A3A20", a)); c.restore()
        if t > tm:
            a = aparece(t - tm, .1); sc = 1.6 - .6 * resorte(t - tm, 10, 12)
            c.save(); c.translate(bx, 720); c.rotate(-12); c.scale(sc, sc)
            st = s.get("sello_txt", "NO DEMOSTRADO"); w_ = ancho(st, F(900, 58)) + 60
            c.drawRRect(rrc(0, 0, w_, 110, 16), trazo("#E5322D", 10, a)); c.drawRRect(rrc(0, 0, w_ - 24, 86, 10), trazo("#E5322D", 3, a))
            texto(c, st, 0, 0, F(900, 58), "#E5322D", alfa=a)
            c.restore()
        _franja(c)

    # ---------------------------------------------------------------- se va solo: calendario + remedios
    def e_sevasolo(self, c, e, t, S):
        s = e["spec"]; tso, tdi, tse, tdu, tca, tvi = (_tw(self, e, k) for k in ("solo_word", "dias_word", "semanas_word", "duerme_word", "cafe_word", "vista_word"))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#2A2060", "#17123A", "#08061A"])))
        _polvo(c, t, 0, W, 100, 1150, .6, seed=19, n=50, col="#D9CCFF")
        sube = _io((t - tdu + .3) / .5) if t > tdu - .3 else 0
        cx_, cy_ = CX - 70, 520 - 180 * sube; sc = 1 - .3 * sube
        # días que pasan
        dia = 0.0
        if t > tdi - .2: dia = 1 + 6 * _io((t - tdi + .2) / 1.0)
        if t > tse - .2: dia = 7 + 21 * _io((t - tse + .2) / 1.2)
        temblor = max(0, 1 - dia / 24)
        c.save(); c.translate(cx_, cy_); c.scale(sc, sc)
        c.drawRRect(rrc(8, 14, 430, 420, 30), skia.Paint(AntiAlias=True, Color=color("#000000", .4), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        c.drawRRect(rrc(0, 0, 430, 420, 30), relleno("#FFFFFF"))
        c.drawRRect(rrc(0, -160, 430, 100, 26), relleno("#E5322D")); c.drawRect(skia.Rect(-215, -160, 215, -110), relleno("#E5322D"))
        for sx in (-1, 1): c.drawRRect(rrc(sx * 120, -215, 24, 60, 10), relleno("#5A6478"))
        lab = s.get("dias_txt", "DÍAS")
        texto(c, lab, 0, -160, F(800, 40), "#FFFFFF")
        n = int(dia); fr = dia - n
        texto(c, str(max(1, n + (1 if fr > .5 else 0))), 0, 50, F(900, 170), "#14182A", tnum=True)
        if 0 < fr < 1 and dia < 28:                                                # hoja que se arranca y sale volando
            c.save(); c.translate(160 * fr, 50 - 240 * fr); c.rotate(28 * fr)
            c.drawRRect(rrc(0, 0, 400, 300, 20), relleno("#FFFFFF", .95 * (1 - fr)))
            texto(c, str(max(1, n)), 0, 0, F(900, 170), "#14182A", alfa=1 - fr, tnum=True); c.restore()
        c.restore()
        # ojo pequeño con el temblor que se apaga
        if t > tso - .3:
            a = aparece(t - tso + .3, .2) * (1 - sube)
            ex, ey = 830, 260
            c.drawOval(skia.Rect(ex - 120, ey - 85, ex + 120, ey + 85), _p(_rad(ex, ey, 130, ["#E6A886", "#B87050", "#7A4A3A"], [0, .7, 1], a)))
            _ojo(c, ex, ey, .3, t, abierto=1.0 if (t % 3.1) > .15 else .2, tic=_tic(t, e["t0"]) * temblor, a=a)
            if t > tse - .2: _pill(self, c, s.get("semanas_txt", "UNAS SEMANAS"), cx_, cy_ + 280 * sc, S, aparece(t - tse + .2, .15) * (1 - sube), fondo="#7A1A2A")
        # remedios
        rem = s.get("remedios", []); tr = [tdu, tca, tvi]
        for k, txt in enumerate(rem[:3]):
            if t < tr[k] - .25: continue
            a = aparece(t - tr[k] + .25, .15); u = resorte(t - tr[k] + .25, 8, 10)
            x = 205 + 300 * k; y = 790 - 50 * (1 - u)
            c.drawRRect(rrc(x + 5, y + 10, 262, 330, 30), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
            c.drawRRect(rrc(x, y, 262, 330, 30), _p(_lin(y - 165, y + 165, ["#3A2E7A", "#241A5A"], a)))
            c.drawRRect(rrc(x, y, 262, 330, 30), trazo("#8A78E8", 3, a))
            if k == 0:
                c.drawRRect(rrc(x, y - 20, 200, 70, 20), relleno("#C8D2EA", a)); c.drawRRect(rrc(x - 70, y - 50, 70, 40, 16), relleno("#FFFFFF", a))
                c.drawRRect(rrc(x + 20, y - 40, 150, 40, 14), relleno("#7A6AE8", a))
                texto(c, "Zz", x + 60, y - 110, F(900, 44), "#D9CCFF", alfa=a * (.6 + .4 * math.sin(t * 3)))
            elif k == 1:
                _icono(c, "cafe", x, y - 40, .55, t, a)
                c.drawLine(x + 90, y - 110, x + 90, y - 10, trazo("#2ED47A", 10, a)); c.drawPath(skia.Path.Polygon([(x + 66, y - 30), (x + 114, y - 30), (x + 90, y + 6)], True), relleno("#2ED47A", a))
            else:
                _icono(c, "cerrado", x, y - 40, .9, t, a)
                c.drawArc(skia.Rect(x - 70, y - 140, x + 70, y - 60), 200, 140, False, trazo("#FFE15A", 6, a * .7))
            c.drawRRect(rrc(x, y + 110, 240, 66, 16), relleno("#14102E", .9 * a))
            fnt = F(800, 25 if len(txt) < 12 else 20)
            texto(c, txt, x, y + 110, fnt, "#FFFFFF", alfa=a)
            c.drawCircle(x + 115, y - 145, 26, relleno("#2ED47A", a)); c.drawLine(x + 103, y - 145, x + 112, y - 135, trazo("#FFFFFF", 6, a)); c.drawLine(x + 112, y - 135, x + 128, y - 157, trazo("#FFFFFF", 6, a))
        _franja(c)

    # ---------------------------------------------------------------- al médico si…
    def e_medico(self, c, e, t, S):
        s = e["spec"]; tmd = _tw(self, e, "medico_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#3A1E14", "#24110A", "#0E0604"])))
        _polvo(c, t, 0, W, 100, 1150, .5, seed=29, n=40, col="#FFD9A0")
        u = resorte(t - e["t0"] - .05, 7, 9)
        px, py = CX, 640 + 300 * (1 - u)
        c.save(); c.translate(px, py); c.rotate(-1.5 + .8 * math.sin(t * .8))
        c.drawRRect(rrc(10, 16, 780, 900, 34), skia.Paint(AntiAlias=True, Color=color("#000000", .4), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
        c.drawRRect(rrc(0, 0, 780, 900, 34), _p(_lin(-450, 450, ["#B8865A", "#8A5A32"])))
        c.drawRRect(rrc(0, 20, 720, 820, 16), _p(_lin(-400, 420, ["#FFFFFF", "#F2EEE4"])))
        c.drawRRect(rrc(0, -430, 260, 70, 18), _p(_linx(-130, 130, ["#AEB8CA", "#E8EEF8", "#8A94A8"])))
        # cruz médica
        c.drawRRect(rrc(-270, -300, 90, 90, 18), relleno("#E5322D")); c.drawRect(skia.Rect(-282, -330, -258, -270), relleno("#FFFFFF")); c.drawRect(skia.Rect(-300, -312, -240, -288), relleno("#FFFFFF"))
        texto(c, s.get("titulo_txt", "AL MÉDICO SI…"), 60, -300, F(900, 54), "#14182A", alfa=aparece(t - tmd + .3, .2) if tmd < 1e8 else 1)
        c.drawLine(-320, -230, 320, -230, trazo("#C8D2EA", 3))
        items = s.get("items", [])
        for k, it in enumerate(items):
            tk = self.ta(it["word"], e) - .25
            if t < tk: continue
            a = aparece(t - tk, .15); uu = resorte(t - tk, 8, 10)
            y = -95 + 228 * k; x0 = -50 * (1 - uu)
            c.drawRRect(rrc(x0, y, 660, 196, 24), relleno("#FFF4E0", a)); c.drawRRect(rrc(x0, y, 660, 196, 24), trazo("#F2C14E", 3, a))
            _icono(c, it["tipo"], x0 - 255, y, .8, t, a)
            fnt = F(800, 38 if len(it["txt"]) < 18 else 33)
            texto(c, it["txt"], x0 + 45, y, fnt, "#14182A", alfa=a)
            tri = skia.Path.Polygon([(x0 + 292, y - 50), (x0 + 327, y + 15), (x0 + 257, y + 15)], True)
            sc = .6 + .4 * resorte(t - tk - .25, 10, 12) if t > tk + .25 else 0
            if sc > 0:
                c.save(); c.translate(x0 + 290, y - 15); c.scale(sc, sc); c.translate(-(x0 + 290), -(y - 15))
                c.drawPath(tri, relleno("#F2A21E", a)); texto(c, "!", x0 + 290, y - 6, F(900, 40), "#14182A", alfa=a); c.restore()
        c.restore()
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_parpado(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "parpado":
            if s.get("modo") == "gancho":
                sf(0, "pop", .4)
                if g("tic_word") is not None:
                    for j in range(3): sf(g("tic_word") - .05 + .87 * j, "tictic", 1.0 - .2 * j)
                    sf(g("tic_word") + .05, "zum", .4)
                if g("nadie_word") is not None: sf(g("nadie_word") - .2, "desliz", .6); sf(g("nadie_word") + .3, "pop", .5)
                if g("terremoto_word") is not None: sf(g("terremoto_word") - .1, "terremoto", 1.0); sf(g("terremoto_word") - .1, "pop", .4)
                if g("fuera_word") is not None: sf(g("fuera_word") - .1, "pop", .5); sf(g("fuera_word") + .4, "bajada", .4)
            else:
                if g("tic_word") is not None:
                    for j in range(2): sf(g("tic_word") - .05 + .87 * j, "tictic", .8)
                if g("dormir_word") is not None: sf(g("dormir_word") + .25, "lampara", .9); sf(g("dormir_word") + .5, "zzz", .6)
                if g("nadie_word") is not None: sf(g("nadie_word") - .4, "paso", .5); sf(g("nadie_word") + .1, "paso", .5); sf(g("nadie_word") + .35, "pop", .5)
        if tp == "anillo":
            if g("nombre_word") is not None: sf(g("nombre_word") - .2, "desliz", .6); sf(g("nombre_word") + .05, "sello", .5)
            if g("anillo_word") is not None: sf(g("anillo_word") - .2, "barrido", .7); sf(g("anillo_word") + .7, "destello", .5)
            for k in ("cierra_word", "parpadea_word"):
                if g(k) is not None: sf(g(k) - .1, "parpadeo", .8)
        if tp == "nervio":
            if g("nervio_word") is not None: sf(g("nervio_word") - .2, "electrico", .5); sf(g("nervio_word") + .4, "pop", .4)
            if g("cable_word") is not None: sf(g("cable_word"), "hum", .3)
            if g("chispa_word") is not None:
                for j in range(3): sf(g("chispa_word") - .1 + .33 * j, "chispa", 1.0 - .2 * j)
            if g("trozo_word") is not None:
                for j in range(3): sf(g("trozo_word") + .87 * j, "tictic", .8)
            if g("ojo_word") is not None: sf(g("ojo_word") - .2, "pop", .5)
            if g("abajo_word") is not None: sf(g("abajo_word") - .2, "pop", .6)
        if tp == "sospechosos":
            sf(e["t0"] + .1, "pop", .4)
            for it in s.get("items", []):
                tt = Tw(it["word"]) - .2; sf(tt, "flash", .7)
                extra = {"sueno": "alarma", "estres": "electrico", "cafe": "vapor", "movil": "noti", "vicios": "cristal"}.get(it["tipo"])
                if extra: sf(tt + .25, extra, .45)
        if tp == "vaso":
            gotas = s.get("gotas", []); n = max(1, len(gotas)); ini = e["t0"] + .4; fin = max(ini + 1.5, Tw(s["vaso_word"]) + .3)
            for k in range(len(gotas)): sf(ini + (fin - ini) * k / n + .38, "gota", .9)
            if g("rebosa_word") is not None: sf(g("rebosa_word") - .1, "rebosa", 1.0)
            if g("tic_word") is not None: sf(g("tic_word") - .05, "tictic", 1.0); sf(g("tic_word") + .82, "tictic", .7)
        if tp == "magnesio":
            if g("bote_word") is not None: sf(g("bote_word") - .25, "salto", .6); sf(g("bote_word") + .2, "pop", .4)
            if g("dice_word") is not None:
                for k in range(len(s.get("rumores", []))): sf(g("dice_word") + .1 + .35 * k, "pop", .6)
            if g("demo_word") is not None: sf(g("demo_word") - .7, "desliz", .5); sf(g("demo_word") - .02, "sello", 1.0)
        if tp == "sevasolo":
            if g("solo_word") is not None: sf(g("solo_word") - .3, "destello", .5)
            if g("dias_word") is not None: self.rodillo(g("dias_word") - .2, 1.0)
            if g("semanas_word") is not None: sf(g("semanas_word") - .2, "pagina", .6); self.rodillo(g("semanas_word") + .1, 1.0)
            for k in ("duerme_word", "cafe_word", "vista_word"):
                if g(k) is not None: sf(g(k) - .25, "desliz", .5); sf(g(k) + .05, "pop", .5)
        if tp == "medico":
            sf(e["t0"] + .05, "desliz", .5)
            for it in s.get("items", []):
                tt = Tw(it["word"]) - .25; sf(tt, "pop", .6); sf(tt + .3, "chincheta", .5)

    for k, fn in (("parpado", e_parpado), ("anillo", e_anillo), ("nervio", e_nervio), ("sospechosos", e_sospechosos), ("vaso", e_vaso),
                  ("magnesio", e_magnesio), ("sevasolo", e_sevasolo), ("medico", e_medico)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_parpado)
