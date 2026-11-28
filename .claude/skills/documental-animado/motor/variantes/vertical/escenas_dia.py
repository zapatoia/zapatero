"""Escenas del documental 15 («¿Qué pasaría si siempre fuera de día?»).

Reutiliza el protagonista del 14 (`self.persona_t`). Todas las escenas dibujan su fondo completo, luz con rayos y polvo
en suspensión, y un degradado suave bajo la tipografía para que se lea siempre.
interruptor  cielo de ciudad: el interruptor de la NOCHE; modo apaga (flip_word: la mano lo baja, se hace de día) o enciende
             (vuelve la noche, ventanas que se apagan y «zzz»); reloj_word: esfera de 24 h alrededor del Sol.
cama         dormitorio con ventana al sol: despertador (hora), modo normal / trozos (cabezadas + reloj interno loco, reloj_word) /
             cortinas (cortinas opacas que se cierran en cortina_word y se duerme).
fabrica      cerebro con la fábrica de melatonina: produce con la luna; luz_word: el rayo de sol la para.
animales     bosque de noche: murcielago_word, buho_word, polilla_word, pill_word + pill.
luciernagas  prado al anochecer con luciérnagas que se hablan con destellos; sol_word: se hace de día y no se ven.
corales      arrecife bajo la luna: huevos_word (suelta sincronizada); sin_word (sale el sol: sueltas sueltas, sin cita).
tomatera     tomatera bajo un foco que no se apaga; hojas_word: las hojas amarillean y se manchan.
calor        gráfica de temperatura día/noche que sube y baja; sin_word: se tachan las noches y la curva solo sube.
noruega      mapa con Tromsø y el sol de medianoche dando vueltas sin tocar el horizonte (sol_word).
planeta      la Tierra frente al Sol: gira y se para (cara_word), la Luna con su misma cara (luna_word), noche eterna (eterna_word),
             abrasado/helado (lados_word) y la franja del atardecer (franja_word).
"""
import math
from contextlib import contextmanager

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H, ease = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"], G["ease_io_expo"]
    FNT = {}
    def F(peso, px, fam="Inter"):
        k = (fam, peso, px)
        if k not in FNT: FNT[k] = fuente(fam, peso, px)
        return FNT[k]

    # ---------------------------------------------------------------- sonidos (eventos cortos, suaves; nada en bucle)
    def s_clic():
        d = .12; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t / .006) + .6 * AU._banda(AU._ruido(n, 151), 1500, 6000) * np.exp(-t / .01))
    def s_grillos():
        d = 1.0; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        env = (np.sin(2 * np.pi * 28 * t) > .2).astype(float) * (np.sin(2 * np.pi * 2.2 * t) > -.2)
        return np.sin(2 * np.pi * 4300 * t) * env * np.sin(np.pi * u) ** .7
    def s_pajaros():
        d = 1.0; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n); rng = np.random.default_rng(152)
        for k in range(5):
            a = int((.05 + .17 * k + .03 * rng.random()) * AU.SR); m = int(.09 * AU.SR); tt = t[:m]
            f = 2800 + 1500 * np.sin(np.pi * tt / .09) + 400 * rng.random(); x[a:a + m] += np.sin(2 * np.pi * np.cumsum(f) / AU.SR) * np.sin(np.pi * tt / .09)
        return x
    def s_chillido():
        d = .35; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for k in range(3):
            a = int(k * .1 * AU.SR); m = int(.05 * AU.SR); tt = t[:m]
            x[a:a + m] += np.sin(2 * np.pi * (5200 - 18000 * tt) * tt) * np.sin(np.pi * tt / .05)
        return x
    def s_ulular():
        d = 1.0; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for t0, L, f in ((0, .28, 410), (.38, .5, 380)):
            a = int(t0 * AU.SR); m = int(L * AU.SR); tt = t[:m]
            x[a:a + m] += (np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt)) * np.sin(np.pi * tt / L) ** 1.5 * (1 - .15 * tt / L)
        return x
    def s_aleteo():
        d = .6; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return AU._banda(AU._ruido(n, 153), 300, 2000) * (np.sin(2 * np.pi * 14 * t) > .3) * np.sin(np.pi * t / d)
    def s_cortina():
        d = .8; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 154), 1500, 7000) * np.sin(np.pi * u) ** 1.5 * (1 + .3 * np.sin(2 * np.pi * 9 * u))
    def s_destello2():
        d = .3; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return np.sin(2 * np.pi * 1975 * t) * np.exp(-t / .07) * np.minimum(1, t / .003)
    def s_engr_stop():
        d = .7; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        k = 0; tt = 0.0
        while tt < d - .03:
            a = int(tt * AU.SR); m = 300; x[a:a + m] += AU._banda(AU._ruido(m, 155 + k), 800, 4000) * np.exp(-np.arange(m) / 60)
            k += 1; tt += .04 + .03 * k
        return x
    for nom, fn, db in (("clic", s_clic, -24), ("grillos", s_grillos, -38), ("pajaros", s_pajaros, -34), ("chillido", s_chillido, -33),
                        ("ulular", s_ulular, -29), ("aleteo", s_aleteo, -33), ("cortina", s_cortina, -31), ("destello2", s_destello2, -33),
                        ("engr_stop", s_engr_stop, -29)):
        AU.SFX.setdefault(nom, (fn, db))

    def _io(u): u = TI.clamp(u); return u * u * (3 - 2 * u)
    def _tw(self, e, k): return self.ta(e["spec"][k], e) if e["spec"].get(k) else 1e9
    def _lin(y0, y1, cols, a=1.0, x=0, pos=None):
        return skia.GradientShader.MakeLinear([(x, y0), (x, y1)], [color(k, a) for k in cols], pos)
    def _rad(x, y, r, cols, pos=None, a=1.0):
        return skia.GradientShader.MakeRadial((x, y), max(r, .1), [color(k, a) for k in cols], pos)
    def _p(sh): return skia.Paint(AntiAlias=True, Shader=sh)
    def _mix(a, b, u):
        ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)], float); cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)], float)
        v = ca + (cb - ca) * TI.clamp(u); return "#" + "".join(f"{int(round(q)):02X}" for q in v)
    def _sombra(c, x, y, rx, ry, a):
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), skia.Paint(AntiAlias=True, Color=color("#000000", a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, ry * .7 + 4)))
    def _franja(c):
        """Degradado suave bajo la tipografía (legibilidad en fondos claros)."""
        c.drawRect(skia.Rect(-80, 1040, W + 80, H + 80), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1060), (0, 1300)], [color("#05060C", 0), color("#05060C", .7)])))
    def _pill(self, c, txt, x, y, S, a, fondo="#0B1430", grande=True):
        if a > 0 and txt: self.pildora(c, txt, x, y, S, a, fnt=self.F["pillb"] if grande else self.F["pill"], fondo=fondo)
    def _sol(c, x, y, r, t, a=1.0, rayos=True):
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(x, y, r * 3.2, _p(_rad(x, y, r * 3.2, ["#FFF2B0", "#FFB45C", "#000000"], [0, .25, 1], .55 * a)))
        if rayos:
            for k in range(14):
                an = k * math.pi / 7 + t * .25; L = r * (1.35 + .12 * math.sin(t * 3 + k))
                c.drawLine(x + r * 1.12 * math.cos(an), y + r * 1.12 * math.sin(an), x + L * math.cos(an), y + L * math.sin(an), trazo("#FFE58A", 9, .85 * a))
        c.drawCircle(x, y, r, _p(_rad(x - r * .3, y - r * .3, r * 1.5, ["#FFFFFF", "#FFE58A", "#FFB43A"], [0, .45, 1], a)))
    def _luna(c, x, y, r, a=1.0, t=0.0):
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(x, y, r * 2.6, _p(_rad(x, y, r * 2.6, ["#CFE0FF", "#000000"], None, .35 * a)))
        c.drawCircle(x, y, r, _p(_rad(x - r * .3, y - r * .3, r * 1.4, ["#FFFFFF", "#E6ECF8", "#B8C4DA"], [0, .6, 1], a)))
        for dx, dy, rr in ((-.3, -.2, .18), (.25, .15, .14), (-.05, .38, .1), (.35, -.35, .08)):
            c.drawCircle(x + dx * r, y + dy * r, rr * r, relleno("#A8B4CC", .55 * a))
    def _estrellas(c, t, a, seed=41, n=110, ymax=1100):
        if a <= 0: return
        rng = np.random.default_rng(seed)
        for k in range(n):
            x, y, r = rng.random() * W, rng.random() * ymax, .8 + 2 * rng.random()
            c.drawCircle(x, y, r, relleno("#FFFFFF", a * (.35 + .55 * rng.random()) * (.65 + .35 * math.sin(t * (1 + 2 * rng.random()) + k))))
    def _polvo(c, t, x0, x1, y0, y1, a, seed=5, n=40, col="#FFF6D0"):
        rng = np.random.default_rng(seed)
        for k in range(n):
            x = x0 + (x1 - x0) * ((rng.random() + .02 * t * (rng.random() - .5)) % 1); y = y0 + (y1 - y0) * ((rng.random() - .015 * t * (.5 + rng.random())) % 1)
            c.drawCircle(x, y, 1.2 + 2.4 * rng.random(), relleno(col, a * (.3 + .5 * rng.random()) * (.6 + .4 * math.sin(t * 2 + k))))
    def _rayos(c, pts, t, a, col="#FFF2C0"):
        """Haz de luz volumétrico (polígono con degradado aditivo) + bandas que respiran."""
        with capa(c, modo=skia.BlendMode.kPlus):
            pth = skia.Path.Polygon(pts, True); (x0, y0), (x1, y1) = pts[0], pts[2]
            c.drawPath(pth, _p(skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [color(col, .42 * a), color(col, .0)])))
            for k in range(4):
                f = (k + .5) / 4 + .03 * math.sin(t * .8 + k)
                q = [(pts[0][0] + (pts[1][0] - pts[0][0]) * f, pts[0][1] + (pts[1][1] - pts[0][1]) * f),
                     (pts[3][0] + (pts[2][0] - pts[3][0]) * f, pts[3][1] + (pts[2][1] - pts[3][1]) * f)]
                c.drawLine(q[0][0], q[0][1], q[1][0], q[1][1], skia.Paint(AntiAlias=True, StrokeWidth=26, Color=color(col, .07 * a * (.6 + .4 * math.sin(t * 1.3 + k))),
                                                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))

    # ---------------------------------------------------------------- ciudad + interruptor de la noche
    def _ciudad(c, t, d, apagar=0.0):
        rng = np.random.default_rng(61); x = -40
        for k in range(40):
            if x > W + 40: break
            w = 70 + 70 * rng.random(); h = 180 + 330 * rng.random(); y = 1240 - h
            col = _mix(_mix("#141A36", "#1E2650", rng.random()), _mix("#8FA6C8", "#B9C8DE", rng.random()), d)
            c.drawRect(skia.Rect(x, y, x + w, 1300), relleno(col))
            c.drawRect(skia.Rect(x + w - 10, y, x + w, 1300), relleno("#000000", .18))
            for i in range(int((w - 16) // 22)):
                for j in range(int((h - 30) // 34)):
                    if rng.random() < .45: continue
                    on = 1 - d
                    if apagar > 0 and rng.random() < .9: on *= 1 - TI.clamp(apagar * 2.2 - rng.random() * 1.2)
                    wc = _mix("#FFD27A", "#D8E6F7", d) if on > .02 or d > .5 else "#1A2040"
                    c.drawRect(skia.Rect(x + 10 + i * 22, y + 18 + j * 34, x + 22 + i * 22, y + 36 + j * 34), relleno(wc if d > .5 else "#FFD27A", (.9 * on + .65 * d) if d <= .5 else .7))
            x += w + 6

    def _interruptor(c, x, y, sc, pos, t, a, txt):
        """Placa con palanca; pos 0 = arriba (NOCHE encendida), 1 = abajo."""
        c.save(); c.translate(x, y); c.scale(sc, sc)
        c.drawRRect(rrc(8, 16, 240, 360, 34), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
        c.drawRRect(rrc(0, 0, 240, 360, 34), _p(_lin(-180, 180, ["#FFFFFF", "#E2E7F0", "#C9D0DE"], a)))
        c.drawRRect(rrc(0, 0, 240, 360, 34), trazo("#9AA4B8", 3, a))
        for sy in (-1, 1): c.drawCircle(0, sy * 150, 9, relleno("#AEB8CA", a)); c.drawLine(-6, sy * 150, 6, sy * 150, trazo("#7A8498", 2, a))
        c.drawRRect(rrc(0, 10, 110, 200, 26), _p(_lin(-90, 110, ["#C9D0DE", "#E9EDF4"], a)))
        ang = -18 + 36 * pos; c.save(); c.translate(0, 10); c.rotate(ang)
        c.drawRRect(rrc(0, -40 + 80 * 0, 86, 110, 22), _p(_lin(-95, 15, ["#FFFFFF", "#D8DEEA"], a))); c.drawRRect(rrc(0, -40, 86, 110, 22), trazo("#8A94A8", 2, a))
        c.restore()
        texto(c, txt, 0, -128, F(800, 30), "#1C2340", alfa=a, tracking=.15)
        lc = _mix("#2ED47A", "#FF3B4A", pos); c.drawCircle(0, 140, 10, relleno(lc, a))
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(0, 140, 26, _p(_rad(0, 140, 26, [lc, "#000000"], None, .6 * a)))
        c.restore()

    def _mano(c, x, y, sc, a=1.0):
        """Mano con índice estirado que viene desde la derecha; (x, y) = punta del dedo."""
        P = ("#F8D5B8", "#E6AC86", "#C98763")
        c.save(); c.translate(x, y); c.scale(sc, sc)
        c.drawRRect(rrc(330, 40, 420, 120, 50), _p(_lin(-20, 100, ["#FF8A3D", "#B8401C"], a)))          # manga
        c.drawRRect(rrc(150, 40, 170, 120, 48), _p(_lin(-20, 100, P, a)))
        c.drawRRect(rrc(55, 0, 120, 38, 19), _p(_lin(-19, 19, P, a)))                                  # índice
        for k in range(3): c.drawRRect(rrc(110, 58 + k * 26, 70, 28, 14), _p(_lin(44 + k * 26, 72 + k * 26, P, a)))
        c.drawOval(skia.Rect(2, -12, 30, 12), relleno("#FFE6D6", .8 * a))
        c.restore()

    def e_interruptor(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tf = _tw(self, e, "flip_word"); modo = s.get("modo", "apaga")
        u = _io((t - tf - .05) / .8)
        d = u if modo == "apaga" else 1 - u                       # 0 noche → 1 día
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, [_mix("#070B22", "#3E8EF0", d), _mix("#1B2A5A", "#9CCBF7", d), _mix("#2A2E5A", "#E6F3FF", d)])))
        _estrellas(c, t, 1 - d)
        _luna(c, 790, 260 + 500 * d, 62, 1 - d, t)
        sy = 1250 - 950 * d; sx = 720
        if d > 0: _sol(c, sx, sy, 92, t, d)
        # esfera de 24 h alrededor del sol
        tr = _tw(self, e, "reloj_word")
        if t > tr and d > .5:
            ur = aparece(t - tr, .2); R = 170; sw = 360 * TI.clamp((t - tr) / 1.6)
            for k in range(24):
                an = math.radians(k * 15 - 90); L = 18 if k % 6 == 0 else 9
                c.drawLine(sx + R * math.cos(an), sy + R * math.sin(an), sx + (R + L) * math.cos(an), sy + (R + L) * math.sin(an), trazo("#FFFFFF", 4 if k % 6 == 0 else 2, .9 * ur))
            c.drawArc(skia.Rect(sx - R + 14, sy - R + 14, sx + R - 14, sy + R - 14), -90, sw, False, trazo("#FFE15A", 8, .9 * ur))
            an = math.radians(sw - 90); c.drawCircle(sx + (R - 14) * math.cos(an), sy + (R - 14) * math.sin(an), 10, relleno("#FFFFFF", ur))
            if t - tr > 1.0: _pill(self, c, s.get("reloj_txt", "24 H DE SOL"), sx, sy + R + 60, S, aparece(t - tr - 1.0, .15), fondo="#7A4A05")
        _ciudad(c, t, d, _io((t - tf - 1.0) / 1.6) if modo == "enciende" else 0)
        # zzz de la ciudad dormida
        if modo == "enciende" and t > tf + 1.2:
            for k in range(4):
                ph = ((t - tf) * .45 + k / 4) % 1; x = 150 + k * 210
                texto(c, "z", x + 60 * ph, 900 - 260 * ph, F(800, int(44 + 40 * ph)), "#FFFFFF", alfa=math.sin(math.pi * ph) * aparece(t - tf - 1.2, .3))
        # interruptor + mano
        pos = _io((t - tf) / .12)
        if modo == "enciende": pos = 1 - pos
        a_i = aparece(dt0, .2)
        ix, iy = 300, 560
        _interruptor(c, ix, iy, 1.45, pos, t, a_i, s.get("txt", "NOCHE"))
        hm = TI.clamp((t - tf + .55) / .45) * (1 - TI.clamp((t - tf - .5) / .4))
        if hm > 0:
            ue = _io(hm); px = ix + 20 + 700 * (1 - ue); py = iy + (-90 if modo == "apaga" else 90) + (40 if modo == "apaga" else -40) * pos
            _mano(c, px + 40, py, 1.3, 1.0)
        if 0 < t - tf < .9: self.comic_t(c, "¡CLIC!", ix + 40, iy - 280, 84, -8, .7 + .3 * resorte(t - tf, 10, 14), 1 - TI.clamp((t - tf - .65) / .25), "#FFE15A")
        _franja(c)

    # ---------------------------------------------------------------- dormitorio
    def e_cama(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "normal")
        tc = _tw(self, e, "cortina_word"); uc = _io((t - tc) / .9) if modo == "cortinas" else 0
        luz = 1 - .88 * uc
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, [_mix("#2A2238", "#F2E2C8", luz), _mix("#1A1424", "#D9C2A0", luz)])))
        # papel pintado
        for k in range(12):
            c.drawLine(k * 90, -80, k * 90, 1100, trazo("#000000", 2, .05))
        # ventana
        WX0, WX1, WY0, WY1 = 600, 930, 230, 700
        c.drawRect(skia.Rect(WX0 - 18, WY0 - 18, WX1 + 18, WY1 + 18), relleno(_mix("#3A2E24", "#FFFFFF", luz)))
        c.drawRect(skia.Rect(WX0, WY0, WX1, WY1), _p(_lin(WY0, WY1, ["#4E9AF0", "#BFE3FF"])))
        _sol(c, 800, 360, 52, t, 1.0)
        c.drawRect(skia.Rect(WX0, 600, WX1, WY1), relleno("#7FB86A"))
        for k in range(4): c.drawRect(skia.Rect(WX0 + 20 + k * 80, 560 - 30 * (k % 2), WX0 + 70 + k * 80, 610), relleno("#9FB3C9"))
        c.drawLine((WX0 + WX1) / 2, WY0, (WX0 + WX1) / 2, WY1, trazo("#FFFFFF", 10)); c.drawLine(WX0, (WY0 + WY1) / 2, WX1, (WY0 + WY1) / 2, trazo("#FFFFFF", 10))
        # cortinas opacas
        if modo == "cortinas":
            for sx in (-1, 1):
                cw = (WX1 - WX0) / 2 * (.18 + .86 * uc)
                x0 = WX0 - 30 if sx < 0 else WX1 + 30 - cw; x1 = x0 + cw
                cp = skia.Path(); cp.addRect(skia.Rect(x0, WY0 - 50, x1, WY1 + 60))
                c.drawPath(cp, _p(skia.GradientShader.MakeLinear([(x0, 0), (x1, 0)], [color("#1E2340"), color("#2E3560"), color("#1E2340")], None)))
                for k in range(6):
                    fx = x0 + cw * (k + .5) / 6; c.drawLine(fx, WY0 - 50, fx + 6 * math.sin(t * 2 + k) * (1 - uc), WY1 + 60, trazo("#0E1226", 5, .6))
            c.drawRect(skia.Rect(WX0 - 60, WY0 - 66, WX1 + 60, WY0 - 46), relleno("#3A2E24"))
        # haz de luz que entra (y se estrecha con las cortinas)
        if luz > .15:
            gap = (WX1 - WX0) * (1 - .97 * uc); gx = (WX0 + WX1) / 2
            _rayos(c, [(gx - gap / 2, WY0), (gx + gap / 2, WY0), (gx + gap / 2 - 520, 1200), (gx - gap / 2 - 640, 1200)], t, luz)
            _polvo(c, t, 80, 900, 300, 1150, .8 * luz)
        if modo == "cortinas" and 0 < uc < 1:
            gx = (WX0 + WX1) / 2; c.drawLine(gx, WY0, gx - 560, 1200, trazo("#FFF2C0", 6 * (1 - uc), .8))
        # cama
        bx, by = 330, 1060
        c.drawRRect(rrc(bx - 280, by - 160, 40, 420, 14), _p(_lin(by - 380, by + 60, ["#8A5A32", "#5A3A20"])))
        c.drawRRect(rrc(bx, by + 40, 660, 120, 30), _p(_lin(by - 20, by + 100, ["#F4F6FA", "#C9D0DE"])))
        c.drawRRect(rrc(bx - 200, by - 70, 200, 70, 30), _p(_lin(by - 105, by - 35, ["#FFFFFF", "#D9DEE8"])))
        # protagonista sentado en la cama
        tr = _tw(self, e, "reloj_word"); dorm = modo == "cortinas" and t > tc + .9
        cab = 0.0; cara = s.get("cara", "o")
        if modo == "trozos":
            ph = (t - e["t0"]) % 1.6; cab = 26 * _io(ph / .9) * (1 - _io((ph - 1.2) / .15)) if ph < 1.35 else 0
            cara = "dormido" if 0.5 < ph < 1.3 else "susto" if 1.3 <= ph < 1.6 else "cansado"
        if dorm: cara = "dormido"
        c.save(); c.clipRect(skia.Rect(-100, -100, W + 100, by + 10))
        c.save(); c.translate(bx - 40, by - 40); c.rotate(cab * .3); c.translate(-(bx - 40), -(by - 40))
        self.persona_t(c, bx - 30, by - 80 + cab, 1.35, t, pose="de_pie", cara=cara, a=1.0, sudor=(1.0 if cara == "calor" else 0))
        c.restore(); c.restore()
        c.drawRRect(rrc(bx + 30, by + 20, 700, 170, 40), _p(_lin(by - 50, by + 90, ["#5C8AE6", "#3A5FB8"])))       # manta
        for k in range(5): c.drawLine(bx - 260 + k * 130, by - 50, bx - 230 + k * 130, by + 90, trazo("#2E4E9A", 4, .5))
        if dorm:
            for k in range(3):
                ph = ((t - tc) * .5 + k / 3) % 1
                texto(c, "z", bx + 120 + 90 * ph, by - 330 - 200 * ph, F(800, int(50 + 40 * ph)), "#FFFFFF", alfa=math.sin(math.pi * ph) * aparece(t - tc - .9, .3))
        if modo == "trozos":
            ph = (t - e["t0"]) % 1.6
            if 1.3 <= ph < 1.6: self.comic_t(c, "¡EH!", bx + 160, by - 420, 64, -8, 1.0, 1 - (ph - 1.3) / .3, "#FFFFFF")
        # mesilla con despertador (las 3 de la madrugada… con sol)
        mx, my = 820, by + 20
        c.drawRRect(rrc(mx, my + 60, 220, 200, 16), _p(_lin(my - 40, my + 160, ["#9A6A3A", "#6A4422"])))
        c.drawRRect(rrc(mx, my - 70, 190, 96, 22), _p(_lin(my - 118, my - 22, ["#2A2F44", "#12141E"])))
        hora = s.get("hora", "03:00")
        if modo == "trozos" and t > tr: hora = ["03:00", "11:47", "06:13", "15:02", "04:38", "09:21"][int((t - tr) * 4) % 6]
        texto(c, hora, mx, my - 70, F(800, 54), "#FF5A4E", tnum=True)
        with capa(c, modo=skia.BlendMode.kPlus): c.drawRRect(rrc(mx, my - 70, 180, 70, 16), skia.Paint(AntiAlias=True, Color=color("#FF5A4E", .12), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        if s.get("hora_txt") and modo == "normal": _pill(self, c, s["hora_txt"], mx - 40, my - 160, S, aparece(dt0 - .5, .15), fondo="#8A0E14")
        # reloj interno loco
        if modo == "trozos" and t > tr:
            ur = resorte(t - tr, 8, 10); rx, ry, R = 360, 300, 110 * ur
            c.drawCircle(rx, ry + 8, R + 14, relleno("#000000", .25)); c.drawCircle(rx, ry, R + 12, relleno("#3A2E24")); c.drawCircle(rx, ry, R, _p(_rad(rx - 30, ry - 30, R * 1.4, ["#FFFFFF", "#E9EEF6"])))
            for k in range(12):
                an = k * math.pi / 6; c.drawLine(rx + R * .82 * math.cos(an), ry + R * .82 * math.sin(an), rx + R * .92 * math.cos(an), ry + R * .92 * math.sin(an), trazo("#1C2340", 4))
            a1 = (t - tr) * 7 + 2 * math.sin((t - tr) * 3); a2 = -(t - tr) * 2.3 + math.sin((t - tr) * 5)
            c.drawLine(rx, ry, rx + R * .5 * math.cos(a2), ry + R * .5 * math.sin(a2), trazo("#1C2340", 9)); c.drawLine(rx, ry, rx + R * .78 * math.cos(a1), ry + R * .78 * math.sin(a1), trazo("#E5322D", 5))
            c.drawCircle(rx, ry, 8, relleno("#1C2340"))
            _pill(self, c, s.get("reloj_txt", "RELOJ INTERNO"), rx, ry + R + 50, S, aparece(t - tr - .3, .15), fondo="#1C2340")
        if uc > .2: c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), relleno("#05060E", .45 * _io((uc - .2) / .8)))
        if modo == "cortinas" and t > tc + .5: _pill(self, c, s.get("cortina_txt", "CORTINAS OPACAS"), 760, 820, S, aparece(t - tc - .5, .15), fondo="#1C2340")
        _franja(c)

    # ---------------------------------------------------------------- fábrica de melatonina en el cerebro
    def e_fabrica(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tl = _tw(self, e, "luz_word"); ul = _io((t - tl) / .6)
        tm = _tw(self, e, "melatonina_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, [_mix("#0E1430", "#2A2A4A", ul), _mix("#060A1C", "#1A1A2E", ul)])))
        _estrellas(c, t, .6 * (1 - ul), seed=7, n=60, ymax=500)
        _luna(c, 140, 230, 46, 1 - ul, t)
        # cerebro de perfil
        bx, by = CX, 640; sc = .95 + .05 * resorte(dt0, 6, 8)
        c.save(); c.translate(bx, by); c.scale(sc, sc)
        br = skia.Path(); br.moveTo(-330, 60)
        br.cubicTo(-380, -120, -250, -300, -40, -300); br.cubicTo(150, -320, 330, -220, 350, -40); br.cubicTo(370, 80, 300, 160, 200, 170)
        br.cubicTo(150, 230, 60, 240, 20, 200); br.cubicTo(-80, 250, -260, 220, -330, 60); br.close()
        _sombra(c, 0, 290, 300, 26, .35)
        c.drawPath(br, _p(_rad(-80, -140, 460, ["#FFD0DC", "#F49AB2", "#C2577A"], [0, .6, 1])))
        c.save(); c.clipPath(br, doAntiAlias=True)
        rng = np.random.default_rng(12)
        for k in range(16):                                                     # circunvoluciones
            x0 = -320 + rng.random() * 620; y0 = -280 + rng.random() * 460; g = skia.Path(); g.moveTo(x0, y0)
            for j in range(4): g.quadTo(x0 + 30 * j + 20, y0 + (30 if j % 2 else -30), x0 + 30 * (j + 1) + 20, y0)
            c.drawPath(g, trazo("#B04A6E", 6, .45))
        c.restore()
        c.drawPath(br, trazo("#8A2A4A", 5, .8))
        c.drawPath(skia.Path.Polygon([(40, 190), (90, 190), (110, 330), (60, 340)], True), _p(_lin(190, 340, ["#F49AB2", "#C2577A"])))   # tronco
        # fábrica (glándula) en el centro
        fx, fy = 20, 30; act = 1 - ul
        c.drawRRect(rrc(fx, fy + 30, 210, 120, 12), _p(_lin(fy - 30, fy + 90, ["#6A7488", "#3A4258"])))
        c.drawPath(skia.Path.Polygon([(fx - 105, fy - 30), (fx - 105, fy - 70), (fx - 35, fy - 30), (fx - 35, fy - 70), (fx + 35, fy - 30), (fx + 35, fy - 70), (fx + 105, fy - 30)], True), relleno("#4A5268"))
        c.drawRect(skia.Rect(fx + 60, fy - 150, fx + 90, fy - 30), relleno("#4A5268"))
        for k in range(3):
            c.drawRect(skia.Rect(fx - 80 + k * 55, fy + 10, fx - 50 + k * 55, fy + 40), relleno(_mix("#FFD27A", "#2A3048", ul)))
        # engranaje
        gr = (t - e["t0"]) * 3 * act if t < tl else (tl - e["t0"]) * 3 + 1.2 * (1 - math.exp(-(t - tl) * 3))
        c.save(); c.translate(fx - 75, fy + 75)
        for k in range(8):
            an = gr + k * math.pi / 4; c.drawRect(skia.Rect(-7 + 30 * math.cos(an) - 0, -7 + 30 * math.sin(an), 7 + 30 * math.cos(an), 7 + 30 * math.sin(an)), relleno("#AEB8CA"))
        c.drawCircle(0, 0, 26, relleno("#AEB8CA")); c.drawCircle(0, 0, 9, relleno("#3A4258")); c.restore()
        # humo de «Z» que sale (melatonina)
        for k in range(7):
            ph = ((t - e["t0"]) * .35 + k / 7) % 1
            if t > tl:
                birth = (t - e["t0"]) * .35 + k / 7 - ph
                if (e["t0"] + birth / .35) > tl - .2: continue
            x = fx + 75 + 60 * math.sin(ph * 5 + k) + ph * 120; y = fy - 160 - 380 * ph
            a = math.sin(math.pi * ph)
            c.drawCircle(x, y, 26 + 16 * ph, _p(_rad(x - 6, y - 6, 34 + 16 * ph, ["#E9E0FF", "#B9A6FF"], None, .85 * a)))
            texto(c, "z", x, y + 2, F(800, int(30 + 14 * ph)), "#4A3A9A", alfa=a)
        if t > tm: _pill(self, c, s.get("melatonina_txt", "MELATONINA"), fx + 210, fy - 330, S, aparece(t - tm, .15), fondo="#4A3A9A")
        c.restore()
        # el rayo de sol que la para
        if ul > 0:
            _sol(c, 900, 150, 60, t, ul)
            _rayos(c, [(860, 130), (940, 170), (bx + 70, by + 70), (bx - 30, by + 10)], t, ul)
            if t > tl + .6:
                a = aparece(t - tl - .6, .12); sc2 = .7 + .3 * resorte(t - tl - .6, 9, 12)
                c.save(); c.translate(bx + 20, by + 120); c.scale(sc2, sc2); c.rotate(-8)
                f = F(800, 60); ww = ancho("APAGADA", f) + 50
                c.drawRRect(rrc(0, 0, ww, 96, 14), trazo("#E5322D", 8, a)); texto(c, "APAGADA", 0, 0, f, "#E5322D", alfa=a); c.restore()
        _franja(c)

    # ---------------------------------------------------------------- animales de noche
    def _murcielago(c, x, y, s, t, a):
        c.save(); c.translate(x, y); c.scale(s, s); fl = math.sin(t * 16)
        for sx in (-1, 1):
            w = skia.Path(); w.moveTo(0, 0); w.cubicTo(sx * 40, -40 * fl - 20, sx * 110, -50 * fl - 10, sx * 140, -10 * fl)
            w.lineTo(sx * 115, 10); w.lineTo(sx * 95, 0); w.lineTo(sx * 75, 18); w.lineTo(sx * 55, 6); w.lineTo(sx * 30, 20); w.close()
            c.drawPath(w, relleno("#1A1430", a))
        c.drawOval(skia.Rect(-20, -16, 20, 26), relleno("#2A2040", a))
        for sx in (-1, 1): c.drawPath(skia.Path.Polygon([(sx * 6, -12), (sx * 16, -34), (sx * 18, -8)], True), relleno("#2A2040", a))
        for sx in (-1, 1): c.drawCircle(sx * 7, -2, 3, relleno("#FFE15A", a))
        c.restore()
    def _buho(c, x, y, s, t, a):
        c.save(); c.translate(x, y); c.scale(s, s)
        c.drawOval(skia.Rect(-70, -90, 70, 100), _p(_lin(-90, 100, ["#8A6A4A", "#5A4028"], a)))
        for k in range(5):
            for j in range(3): c.drawArc(skia.Rect(-40 + j * 28, -10 + k * 18, -24 + j * 28, 4 + k * 18), 0, 180, False, trazo("#D9C2A0", 3, .6 * a))
        for sx in (-1, 1):
            c.drawPath(skia.Path.Polygon([(sx * 30, -80), (sx * 58, -118), (sx * 62, -70)], True), relleno("#5A4028", a))
            c.drawCircle(sx * 30, -42, 30, relleno("#F2E2C8", a))
            bl = 1.0 if (t * .6 + sx * .1) % 2.8 > .12 else .1
            c.drawOval(skia.Rect(sx * 30 - 20, -42 - 20 * bl, sx * 30 + 20, -42 + 20 * bl), relleno("#FFB43A", a))
            if bl > .5: c.drawCircle(sx * 30, -42, 10, relleno("#14141E", a)); c.drawCircle(sx * 30 - 4, -46, 4, relleno("#FFFFFF", a))
        c.drawPath(skia.Path.Polygon([(-10, -24), (10, -24), (0, -6)], True), relleno("#E0901A", a))
        for sx in (-1, 0, 1): c.drawLine(sx * 14, 98, sx * 14 + 4, 112, trazo("#E0901A", 5, a))
        c.restore()
    def _polilla(c, x, y, s, t, a, col="#D9C2A0"):
        c.save(); c.translate(x, y); c.scale(s, s); fl = abs(math.sin(t * 20))
        for sx in (-1, 1):
            c.drawOval(skia.Rect(min(0, sx * 46 * (.4 + .6 * fl)), -30, max(0, sx * 46 * (.4 + .6 * fl)), 6), relleno(col, .95 * a))
            c.drawOval(skia.Rect(min(0, sx * 34 * (.4 + .6 * fl)), 0, max(0, sx * 34 * (.4 + .6 * fl)), 26), relleno(_mix(col, "#8A7A60", .3), .95 * a))
        c.drawOval(skia.Rect(-6, -26, 6, 24), relleno("#6A5A40", a))
        for sx in (-1, 1): c.drawLine(0, -24, sx * 14, -44, trazo("#6A5A40", 2, a))
        c.restore()

    def e_animales(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, ["#0A1030", "#1A2450", "#22305A"])))
        _estrellas(c, t, .9, seed=19, n=90, ymax=700)
        _luna(c, 760, 230, 70, 1, t)
        # árboles en silueta
        for k, (tx, th) in enumerate(((60, 820), (240, 700), (900, 760))):
            c.drawRect(skia.Rect(tx - 16, 1240 - th, tx + 16, 1260), relleno("#0A0E22"))
            for j in range(5):
                c.drawCircle(tx + 40 * math.sin(j * 1.9 + k), 1240 - th + j * 70, 110 - j * 10, relleno("#0E1430"))
        c.drawRect(skia.Rect(-80, 1150, W + 80, H + 80), relleno("#060A1C"))
        c.drawLine(80, 620, 470, 640, trazo("#0A0E22", 26))                                   # rama
        # farola con su luz
        lx, ly = 760, 560
        c.drawRect(skia.Rect(lx - 9, ly, lx + 9, 1200), relleno("#1A1F33"))
        c.drawRRect(rrc(lx, ly - 10, 70, 40, 12), relleno("#2A2F44"))
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(lx, ly + 10, 220, _p(_rad(lx, ly + 10, 220, ["#FFE6A0", "#000000"], None, .55)))
            c.drawPath(skia.Path.Polygon([(lx - 30, ly + 10), (lx + 30, ly + 10), (lx + 200, 1200), (lx - 200, 1200)], True), _p(_lin(ly, 1200, ["#FFE6A0", "#000000"], .25)))
        T = lambda k: _tw(self, e, k)
        tb = T("murcielago_word")
        if t > tb - .2:
            u = (t - tb + .2); x = -150 + 520 * u if u < 1.2 else 474 + 160 * math.cos((u - 1.2) * 1.6); y = 360 + 60 * math.sin(u * 3)
            _murcielago(c, x, y, 1.5, t, aparece(u, .1))
        to = T("buho_word")
        if t > to - .1:
            u = resorte(t - to + .1, 8, 10); _buho(c, 330, 560 - 60 * (1 - u) + 4 * math.sin(t * 2), 1.15 * u, t, 1)
        tp = T("polilla_word")
        if t > tp - .1:
            for k in range(3):
                an = (t - tp) * (2.2 + .4 * k) + k * 2.1; _polilla(c, lx + 110 * math.cos(an), ly + 40 + 70 * math.sin(an * 1.3), 1.1 - .15 * k, t + k, aparece(t - tp + .1 - k * .15, .12))
        tpi = T("pill_word")
        if t > tpi: _pill(self, c, s.get("pill", "VIDA NOCTURNA"), CX, 1000, S, aparece(t - tpi, .15), fondo="#3A2A8A")
        _franja(c)

    # ---------------------------------------------------------------- luciérnagas
    def e_luciernagas(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; ts = _tw(self, e, "sol_word"); us = _io((t - ts) / .8)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, [_mix("#141A40", "#5AA6F2", us), _mix("#3A2E5A", "#CDE8FF", us)])))
        _estrellas(c, t, .7 * (1 - us), seed=23, n=70, ymax=600)
        if us > 0: _sol(c, 780, 260, 80, t, us)
        for k, (yy, col) in enumerate(((900, "#1E2A3A"), (980, "#141E2C"))):
            pth = skia.Path(); pth.moveTo(-80, 1300)
            for xx in range(-80, W + 90, 40): pth.lineTo(xx, yy + 30 * math.sin(xx / (120 + 40 * k) + k))
            pth.lineTo(W + 80, 1300); pth.close(); c.drawPath(pth, relleno(_mix(col, ["#5DA852", "#4E9A3A"][k], us)))
        rng = np.random.default_rng(29)
        for k in range(120):                                                    # hierba
            gx = rng.random() * W; gy = 1000 + 200 * rng.random(); h = 30 + 50 * rng.random()
            c.drawLine(gx, gy, gx + 8 * math.sin(t + k), gy - h, trazo(_mix("#0E1622", "#3E8A2A", us), 3))
        # luciérnagas: parejas que se responden
        for k in range(14):
            x = 80 + (k * 137) % 820 + 30 * math.sin(t * .7 + k); y = 520 + (k * 211) % 480 + 24 * math.sin(t * .9 + k * 1.3)
            ph = (t * .8 + (k // 2) * .37 + (k % 2) * .45) % 1.6
            fl = max(0.0, math.sin(math.pi * ph / .35)) if ph < .35 else 0.0
            vis = 1 - .93 * us
            c.drawOval(skia.Rect(x - 14, y - 8, x + 14, y + 8), relleno("#2A2A2A", .9))
            for sx in (-1, 1): c.drawOval(skia.Rect(x - 4 + sx * 8 - 8, y - 18 - 4 * abs(math.sin(t * 25 + k)), x - 4 + sx * 8 + 8, y - 4), relleno("#DDE6FF", .5))
            c.drawCircle(x + 10, y + 3, 9, relleno("#C8E85A", .4 + .6 * fl))
            if fl > 0 and vis > 0:
                with capa(c, modo=skia.BlendMode.kPlus):
                    c.drawCircle(x + 10, y + 3, 90, _p(_rad(x + 10, y + 3, 90, ["#F2FF8A", "#C8E85A", "#000000"], [0, .22, 1], fl * vis)))
            if us > .5 and k % 4 == 0:
                texto(c, "?", x, y - 40 - 6 * math.sin(t * 3 + k), F(800, 36), "#14182A", alfa=(us - .5) * 2)
        if t > ts + .8: _pill(self, c, s.get("pill", "CON SOL, NO SE VEN"), CX, 1000, S, aparece(t - ts - .8, .15), fondo="#7A5A05")
        _franja(c)

    # ---------------------------------------------------------------- corales y la luna
    def e_corales(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; T = lambda k: _tw(self, e, k)
        th, tsn = T("huevos_word"), T("sin_word"); us = _io((t - tsn) / .8)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, [_mix("#0E2A5A", "#1E8AC8", us), _mix("#061430", "#0E4A7A", us)])))
        # superficie con la luna (o el sol) deformada
        for k in range(10):
            yy = 210 + 3 * math.sin(t * 2 + k); c.drawLine(-80 + k * 130, yy, 40 + k * 130, yy + 4 * math.sin(t * 3 + k), trazo("#FFFFFF", 3, .25))
        if us < 1:
            for k in range(6):
                c.drawOval(skia.Rect(760 - 50 + 10 * math.sin(t * 2 + k), 120 + k * 14, 760 + 50 + 10 * math.sin(t * 2.3 + k), 128 + k * 14), relleno("#E6ECF8", .5 * (1 - us) * (1 - k / 7)))
            _luna(c, 760, 100, 44, 1 - us, t)
        if us > 0: _sol(c, 760, 100, 50, t, us)
        with capa(c, modo=skia.BlendMode.kPlus):                                 # cáusticas
            for k in range(7):
                x = (k * 170 + t * 30) % (W + 200) - 100
                c.drawPath(skia.Path.Polygon([(x, 220), (x + 60, 220), (x + 220, 1200), (x + 120, 1200)], True), _p(_lin(220, 1200, ["#BFE8FF", "#000000"], .12 + .06 * math.sin(t + k))))
        # corales
        rng = np.random.default_rng(33); bases = []
        for k in range(9):
            x = 60 + k * 105 + 20 * rng.random(); y = 1100 + 40 * rng.random(); col = ["#FF7A9A", "#FFB45C", "#B97AFF", "#5AD2C8"][k % 4]
            bases.append((x, y - 170))
            if k % 2:
                c.drawOval(skia.Rect(x - 90, y - 150, x + 90, y + 10), _p(_rad(x - 20, y - 90, 140, [_mix(col, "#FFFFFF", .3), col, _mix(col, "#000000", .4)], [0, .5, 1])))
                for j in range(5): c.drawArc(skia.Rect(x - 60 + j * 8, y - 80 + j * 10, x + 60 - j * 8, y - j * 6), 190, 160, False, trazo(_mix(col, "#000000", .3), 3, .6))
            else:
                for j in range(5):
                    an = -math.pi / 2 + (j - 2) * .35; L = 170 + 60 * rng.random(); sw = 3 * math.sin(t * 1.4 + j + k)
                    x2, y2 = x + L * math.cos(an) + sw, y + L * math.sin(an)
                    c.drawLine(x, y, x2, y2, trazo(col, 22)); c.drawCircle(x2, y2, 14, relleno(_mix(col, "#FFFFFF", .3)))
        c.drawRect(skia.Rect(-80, 1130, W + 80, H + 80), _p(_lin(1130, 1300, ["#C9B48A", "#8A7A5A"])))
        # la suelta: todos a la vez con la luna; sin noche, sueltos y desordenados
        for k in range(60):
            bx, by = bases[k % len(bases)]
            if t < tsn:
                t0 = th + .03 * (k % 7); u = t - t0
            else:
                t0 = tsn + .3 + (k * 0.731) % 3.0; u = t - t0
                if k % 3: continue
            if u <= 0: continue
            x = bx + 30 * math.sin(u * 1.5 + k) + (k % 5 - 2) * 8; y = by - 160 * u - 20 * (k % 4)
            if y < 240: continue
            col = ["#FF9AB0", "#FFD27A", "#FFB0E0"][k % 3]
            c.drawCircle(x, y, 9, _p(_rad(x - 3, y - 3, 12, ["#FFFFFF", col], None, .95)))
        if t > th + .4 and t < tsn: _pill(self, c, s.get("pill", "TODOS A LA VEZ"), CX, 330, S, aparece(t - th - .4, .15) * TI.clamp((tsn - t) / .2), fondo="#8A2A5A")
        if t > tsn + .6: _pill(self, c, s.get("pill2", "SIN CITA"), CX, 330, S, aparece(t - tsn - .6, .15), fondo="#3A4462")
        _franja(c)

    # ---------------------------------------------------------------- tomatera bajo un foco que no se apaga
    def e_tomatera(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; th = _tw(self, e, "hojas_word"); uh = _io((t - th) / 1.6)
        tn = _tw(self, e, "noche_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, ["#2A2E3A", "#14161E"])))
        # foco
        lx, ly = CX, 170
        c.drawLine(lx, -80, lx, ly - 40, trazo("#3A3F4A", 6))
        c.drawPath(skia.Path.Polygon([(lx - 90, ly + 20), (lx + 90, ly + 20), (lx + 50, ly - 50), (lx - 50, ly - 50)], True), _p(_lin(ly - 50, ly + 20, ["#5A606E", "#2A2E38"])))
        _rayos(c, [(lx - 80, ly + 20), (lx + 80, ly + 20), (lx + 420, 1150), (lx - 420, 1150)], t, 1.0)
        c.drawOval(skia.Rect(lx - 80, ly + 8, lx + 80, ly + 32), relleno("#FFFBE0"))
        _polvo(c, t, 160, 880, 260, 1100, .7)
        # «siempre encendido»
        if t > tn: _pill(self, c, s.get("pill", "LUZ SIN PARAR"), CX, 290, S, aparece(t - tn, .15), fondo="#7A5A05")
        # maceta
        px, py = CX, 1110
        _sombra(c, px, py + 70, 170, 18, .4)
        c.drawPath(skia.Path.Polygon([(px - 150, py - 90), (px + 150, py - 90), (px + 115, py + 70), (px - 115, py + 70)], True), _p(_lin(py - 90, py + 70, ["#D9774A", "#A04A24"])))
        c.drawRRect(rrc(px, py - 92, 330, 40, 10), _p(_lin(py - 112, py - 72, ["#E8885A", "#B8562C"])))
        # tallo y hojas (amarillean con manchas)
        def hoja(x, y, ang, L, k):
            c.save(); c.translate(x, y); c.rotate(ang)
            g = _mix("#3E9A3A", "#D8C23A", uh * (.6 + .4 * ((k * 37) % 10) / 10))
            for j in range(3):
                lp = skia.Path(); lx0 = L * (.3 + .3 * j); lp.moveTo(lx0, 0); lp.cubicTo(lx0 + 30, -40, lx0 + 70, -30, lx0 + 80, 0); lp.cubicTo(lx0 + 70, 30, lx0 + 30, 40, lx0, 0)
                c.drawPath(lp, relleno(g)); c.drawLine(lx0, 0, lx0 + 76, 0, trazo(_mix(g, "#000000", .3), 2, .6))
                if uh > .3:
                    rng = np.random.default_rng(k * 7 + j)
                    for q in range(3): c.drawCircle(lx0 + 20 + 50 * rng.random(), -14 + 28 * rng.random(), 3 + 5 * rng.random() * uh, relleno("#6A4A1A", .8 * (uh - .3) / .7))
            c.drawLine(0, 0, L * .95, 0, trazo("#2E7A2A", 5)); c.restore()
        sw = 4 * math.sin(t * 1.2)
        c.drawLine(px, py - 90, px + sw, 420, trazo("#2E7A2A", 14))
        for k, (yy, sd) in enumerate(((900, -1), (820, 1), (740, -1), (660, 1), (580, -1), (500, 1))):
            hoja(px + sw * (1 - (yy - 420) / 700), yy, (200 if sd < 0 else -20) + 10 * math.sin(t + k) * (1 - uh * .6) + 25 * uh * (1 if sd > 0 else -1), 150 - 8 * k, k)
        for k, (tx, ty) in enumerate(((px - 120, 780), (px + 110, 700), (px - 90, 620))):
            r = 44 - 4 * k; tcol = _mix("#E5322D", "#C9802A", uh * .5)
            c.drawCircle(tx, ty + r, r, _p(_rad(tx - r * .35, ty + r * .6, r * 1.3, ["#FF8A7A", tcol, "#8A1A1A"], [0, .5, 1])))
            c.drawPath(skia.Path.Polygon([(tx - 16, ty + 4), (tx, ty - 8), (tx + 16, ty + 4), (tx, ty + 12)], True), relleno("#2E7A2A"))
            c.drawOval(skia.Rect(tx - r * .5, ty + r * .3, tx - r * .1, ty + r * .55), relleno("#FFFFFF", .35))
        if t > th + .8: _pill(self, c, s.get("hojas_txt", "HOJAS DAÑADAS"), CX + 200, 980, S, aparece(t - th - .8, .15), fondo="#7A3A05")
        _franja(c)

    # ---------------------------------------------------------------- calor: gráfica día/noche
    def e_calor(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tsn = _tw(self, e, "sin_word"); us = TI.clamp((t - tsn) / 2.6)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, [_mix("#122040", "#5A1A0A", us), _mix("#060A18", "#2A0A04", us)])))
        x0, x1, y0, y1 = 110, 900, 360, 900
        c.drawRRect(rrc((x0 + x1) / 2, (y0 + y1) / 2 + 20, x1 - x0 + 80, y1 - y0 + 160, 30), relleno("#000000", .25))
        c.drawLine(x0, y1, x1, y1, trazo("#FFFFFF", 3, .6)); c.drawLine(x0, y0, x0, y1, trazo("#FFFFFF", 3, .6))
        texto(c, s.get("eje_txt", "TEMPERATURA"), x0 + 10, y0 - 34, F(800, 28), "#C9D3EA", alinear="i", tracking=.15)
        n = 8; dx = (x1 - x0) / n
        for k in range(n):                                                      # iconos sol / luna
            xs, xm = x0 + dx * k + dx * .25, x0 + dx * k + dx * .75
            _sol(c, xs, y1 + 46, 14, t, 1.0, rayos=False)
            _luna(c, xm, y1 + 46, 13, 1.0, t)
            tach = TI.clamp((t - tsn - .15 * k) / .2)
            if tach > 0: c.drawLine(xm - 20, y1 + 66, xm - 20 + 40 * tach, y1 + 26, trazo("#FF3B4A", 6))
        # curva: sube de día y baja de noche; sin noche, solo sube
        pd = TI.clamp(dt0 / 1.8)
        pth = skia.Path(); first = True; base = y1 - 160
        for i in range(0, 241):
            f = i / 240
            if f > pd and t < tsn: break
            xx = x0 + (x1 - x0) * f; cyc = math.sin(2 * math.pi * f * n - math.pi / 2)
            yn = base - 110 * (cyc * .5 + .5)
            ysn = base - 110 * (f * n % 1 if (f * n % 1) < .5 else .5) * 2 * .5 - 330 * f
            fi = f * n; ysn = base - 40 - 330 * (math.floor(fi) + _io((fi % 1) / .5)) / n
            yy = yn + (ysn - yn) * _io(us * 1.4 - f * .4)
            (pth.moveTo if first else pth.lineTo)(xx, yy); first = False
        col = _mix("#FFB45C", "#FF3B2A", us)
        c.drawPath(pth, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=18, Color=color(col, .25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        c.drawPath(pth, trazo(col, 8))
        # termómetro
        tx, ty = 960, 620; fr = .35 + .6 * us
        c.drawRRect(rrc(tx - 40, ty, 50, 360, 25), relleno("#FFFFFF", .9)); c.drawCircle(tx - 40, ty + 200, 42, relleno("#FFFFFF", .9))
        c.drawCircle(tx - 40, ty + 200, 32, relleno("#E5322D")); c.drawRRect(rrc(tx - 40, ty + 170 - 330 * fr / 2, 24, 330 * fr, 12), relleno("#E5322D"))
        if us > 0:                                                              # aire que tiembla de calor
            for k in range(5):
                y = 330 + k * 120; wv = skia.Path(); wv.moveTo(x0, y)
                for xx in range(x0, x1 + 20, 20): wv.lineTo(xx, y + 6 * math.sin(xx / 30 + t * 6 + k))
                c.drawPath(wv, trazo("#FFB45C", 2, .18 * us))
        if t > tsn + 1.2: _pill(self, c, s.get("pill", "SIN NOCHE, NO SE ENFRÍA"), CX, 1040, S, aparece(t - tsn - 1.2, .15), fondo="#8A1A0A")
        _franja(c)

    # ---------------------------------------------------------------- Noruega: sol de medianoche
    def e_noruega(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; G_ = self.geo([16.0, 66.0])
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1240, ["#123A7A", "#0A1E48"])))
        z = .95 + .05 * resorte(dt0, 6, 8); k = 430 / 1100 * z; cen = np.array(G_["pr"](17.0, 66.5))
        P = lambda lon, lat: (lambda q: (CX + (q[0] - cen[0]) * k, 560 - (q[1] - cen[1]) * k))(G_["pr"](lon, lat))
        c.save(); c.translate(CX, 560); c.scale(k, -k); c.translate(-cen[0], -cen[1])
        for pk in ("tierra", "francia"): c.drawPath(G_[pk], relleno("#2A5AB8", .95)); c.drawPath(G_[pk], trazo("#9DB8FF", 1.4 / k, .6))
        tn = _tw(self, e, "norte_word")
        if "578" in G_["ids"]:
            a = aparece(t - tn, .3); c.drawPath(G_["ids"]["578"], relleno("#FFB45C", .85 * a)); c.drawPath(G_["ids"]["578"], trazo("#FFFFFF", 2.5 / k, .9 * a))
        c.restore()
        # círculo polar ártico
        pts = [P(lon, 66.56) for lon in range(-10, 45, 2)]
        pl = trazo("#FFFFFF", 3, .5); pl.setPathEffect(skia.DashPathEffect.Make([14, 10], -t * 20))
        pa = skia.Path(); pa.moveTo(*pts[0])
        for q in pts[1:]: pa.lineTo(*q)
        c.drawPath(pa, pl)
        x, y = P(18.96, 69.65)
        if t > tn + .3:
            a = aparece(t - tn - .3, .12)
            for q in range(2):
                ph = ((t * .9 + q * .5) % 1); c.drawCircle(x, y, 10 + 44 * ph, trazo("#FFFFFF", 3, .55 * (1 - ph) * a))
            c.drawCircle(x, y, 13, relleno("#FFFFFF", a)); c.drawCircle(x, y, 6, relleno("#FF5A3D", a))
            self.pildora(c, s.get("ciudad_txt", "TROMSØ"), x - 30, y - 56, S, a, fnt=self.F["pillb"])
        # ventana: horizonte con el sol dando la vuelta sin ponerse
        ts = _tw(self, e, "sol_word")
        if t > ts:
            a = aparece(t - ts, .2); bx, by, bw, bh = CX, 1010, 640, 230
            c.save(); r = rrc(bx, by, bw, bh, 30); c.drawRRect(r.makeOffset(0, 10), relleno("#000000", .35 * a)); c.clipRRect(r, doAntiAlias=True)
            c.drawRect(skia.Rect(bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2), _p(_lin(by - bh / 2, by + bh / 2, ["#FFB46A", "#FFE2B0"], a)))
            hz = by + 50; c.drawRect(skia.Rect(bx - bw / 2, hz, bx + bw / 2, by + bh / 2), _p(_lin(hz, by + bh / 2, ["#2A4A7A", "#14284A"], a)))
            ang = (t - ts) * 1.6
            sx_, sy_ = bx + 240 * math.cos(ang), hz - 90 - 55 * math.sin(ang)       # nunca baja del horizonte
            for j in range(1, 14):
                aj = ang - j * .08; c.drawCircle(bx + 240 * math.cos(aj), hz - 90 - 55 * math.sin(aj), 22 * (1 - j / 16), relleno("#FFF2B0", .18 * (1 - j / 14) * a))
            _sol(c, sx_, sy_, 26, t, a, rayos=False)
            c.restore()
            c.drawRRect(rrc(bx, by, bw, bh, 30), trazo("#FFFFFF", 3, .5 * a))
            _pill(self, c, s.get("sol_txt", "MAYO → JULIO: EL SOL NO SE PONE"), bx, by - bh / 2 - 36, S, aparece(t - ts - .3, .15), fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- planeta con una cara siempre al Sol
    def e_planeta(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; T = lambda k: _tw(self, e, k)
        tcara, tluna, tet, tlad, tfr = T("cara_word"), T("luna_word"), T("eterna_word"), T("lados_word"), T("franja_word")
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), relleno("#03050E"))
        _estrellas(c, t, .9, seed=47, n=120, ymax=1240)
        # el Sol a la izquierda
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(-260, 640, 900, _p(_rad(-260, 640, 900, ["#FFE6A0", "#FF9A3A", "#000000"], [0, .35, 1], .55)))
        c.drawCircle(-260, 640, 330, _p(_rad(-200, 600, 360, ["#FFFFFF", "#FFE58A", "#FFB43A"], [0, .5, 1])))
        gx, gy, R = 600, 640, 300
        # giro que se frena hasta pararse
        rot = 25 * min(t, tcara) - 25 * e["t0"] + 25 * (1 - math.exp(-(max(0, t - tcara)) * 2)) / 2
        rings = self._mundo_rings(); lon0 = -rot * 3 % 360 - 180; lat0 = 10
        l0, p0 = math.radians(lon0), math.radians(lat0)
        def pr(lon, lat):
            l = np.radians(lon) - l0; p = np.radians(lat)
            x = np.cos(p) * np.sin(l); y = np.cos(p0) * np.sin(p) - np.sin(p0) * np.cos(p) * np.cos(l)
            v = np.sin(p0) * np.sin(p) + np.cos(p0) * np.cos(p) * np.cos(l); return x, y, v
        ue, ul = _io((t - tet) / 1.2), _io((t - tlad) / 1.0)
        c.drawCircle(gx, gy, R, _p(_rad(gx - R * .3, gy - R * .3, R * 1.5, [_mix("#3A78E0", "#E0902A", ul * .6), "#1A4AA8", "#0A1E52"], [0, .55, 1])))
        c.save(); cl = skia.Path(); cl.addCircle(gx, gy, R); c.clipPath(cl, doAntiAlias=True)
        land = skia.Path()
        for cid, rs_ in rings.items():
            for r in rs_:
                X, Y, Vv = pr(r[:, 0], r[:, 1])
                if (Vv > 0).sum() < 2: continue
                nn = np.hypot(X, Y) + 1e-9; Xc = np.where(Vv > 0, X, X / nn); Yc = np.where(Vv > 0, Y, Y / nn)
                land.moveTo(gx + R * Xc[0], gy - R * Yc[0])
                for xx, yy in zip(Xc[1:], Yc[1:]): land.lineTo(gx + R * xx, gy - R * yy)
                land.close()
        c.drawPath(land, relleno(_mix("#5FB36A", "#D8A25A", ul * .8)))
        # lado de noche (derecha) que se hiela
        c.drawRect(skia.Rect(gx, gy - R, gx + R, gy + R), _p(skia.GradientShader.MakeLinear([(gx - 40, 0), (gx + 60, 0)], [color("#000814", 0), color("#000814", .78)])))
        if ue > 0:
            c.drawRect(skia.Rect(gx + 30, gy - R, gx + R, gy + R), relleno("#DDEBFF", .55 * ue))
            rng = np.random.default_rng(3)
            for k in range(40):
                x = gx + 40 + (R - 40) * rng.random(); y = gy - R + 2 * R * rng.random()
                c.drawCircle(x, y, 2 + 2 * rng.random(), relleno("#FFFFFF", ue * (.4 + .6 * math.sin(t * 3 + k) ** 2)))
        if ul > 0:
            c.drawRect(skia.Rect(gx - R, gy - R, gx - 40, gy + R), _p(skia.GradientShader.MakeLinear([(gx - R, 0), (gx - 40, 0)], [color("#FF5A1A", .55 * ul), color("#FF5A1A", 0)])))
        # franja del atardecer
        uf = _io((t - tfr) / .8)
        if uf > 0:
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawRect(skia.Rect(gx - 30, gy - R, gx + 50, gy + R), _p(skia.GradientShader.MakeLinear([(gx - 30, 0), (gx + 50, 0)], [color("#000000", 0), color("#7CFF8A", .55 * uf), color("#000000", 0)], [0, .5, 1])))
            for k in range(6):
                yy = gy - R * .7 + k * R * .28; xx = gx + 10 + 8 * math.sin(k)
                c.drawPath(skia.Path.Polygon([(xx - 12, yy + 12), (xx, yy - 16), (xx + 12, yy + 12)], True), relleno("#2E9A4A", uf))
        c.restore()
        c.drawCircle(gx, gy, R, trazo("#FFFFFF", 2, .35))
        # la Luna, siempre con la misma cara hacia la Tierra
        if t > tluna:
            a = aparece(t - tluna, .2); an = (t - tluna) * 1.2 - 1.0; mx, my = gx + 420 * math.cos(an), gy + 160 * math.sin(an)
            if 40 < mx < 950:
                c.save(); c.translate(mx, my); c.rotate(math.degrees(an) + 180)
                _luna(c, 0, 0, 42, a, t)
                c.drawCircle(-14, -8, 6, relleno("#3A4462", a)); c.drawCircle(-14, 8, 6, relleno("#3A4462", a)); c.drawArc(skia.Rect(-34, -12, -18, 12), 100, 160, False, trazo("#3A4462", 3, a))
                c.restore()
            orb = trazo("#FFFFFF", 2, .25 * a); orb.setPathEffect(skia.DashPathEffect.Make([10, 10], 0))
            c.drawOval(skia.Rect(gx - 420, gy - 160, gx + 420, gy + 160), orb)
        if t > tcara + .3 and t < tlad: _pill(self, c, s.get("cara_txt", "SIEMPRE LA MISMA CARA AL SOL"), gx - 60, 230, S, aparece(t - tcara - .3, .15) * TI.clamp((tlad - t) / .2), fondo="#7A4A05")
        if t > tet + .3: _pill(self, c, s.get("eterna_txt", "NOCHE ETERNA"), gx + 190, gy + R + 60, S, aparece(t - tet - .3, .15), fondo="#1C3A6A")
        if t > tlad: _pill(self, c, s.get("abrasado_txt", "ABRASADO"), gx - 200, 230, S, aparece(t - tlad, .15), fondo="#8A1A0A")
        if t > tlad + .5: _pill(self, c, s.get("helado_txt", "HELADO"), gx + 210, 230, S, aparece(t - tlad - .5, .15), fondo="#1C5A8A")
        if t > tfr + .5: _pill(self, c, s.get("franja_txt", "¿AQUÍ LA VIDA?"), gx, gy - R - 70 + 0, S, aparece(t - tfr - .5, .15), fondo="#1E6A3A")
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_dia(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "interruptor":
            tf = g("flip_word")
            if s.get("modo") == "apaga": sf(e["t0"] + .05, "grillos", .8)
            if tf is not None:
                sf(tf - .5, "desliz", .6); sf(tf, "clic", 1.0); sf(tf + .1, "subida" if s.get("modo") == "apaga" else "bajada", .7)
                if s.get("modo") == "apaga": sf(tf + .8, "pajaros", .9)
                else: sf(tf + .9, "grillos", .8); sf(tf + 1.5, "zzz", .7)
            if g("reloj_word") is not None:
                tr = g("reloj_word")
                for j in range(8): sf(tr + j * .2, "tic", .45)
                sf(tr + 1.65, "ding", .6)
        if tp == "cama":
            m = s.get("modo")
            sf(e["t0"] + .2, "pajaros", .5)
            if m == "trozos":
                k = 0
                while e["t0"] + 1.3 + k * 1.6 < e["t1"] - .2: sf(e["t0"] + 1.3 + k * 1.6, "pop", .5); k += 1
                if g("reloj_word") is not None:
                    for j in range(6): sf(g("reloj_word") + j * .25, "tic", .5)
            if m == "cortinas" and g("cortina_word") is not None: sf(g("cortina_word"), "cortina", 1.0); sf(g("cortina_word") + 1.0, "zzz", .7)
            if m == "normal": sf(e["t0"] + .6, "bip", .5)
        if tp == "fabrica":
            sf(e["t0"] + .3, "engranaje", .6)
            if g("melatonina_word") is not None: sf(g("melatonina_word"), "burbuja", .8)
            if g("luz_word") is not None: sf(g("luz_word"), "destello", .6); sf(g("luz_word") + .2, "engr_stop", 1.0); sf(g("luz_word") + .65, "sello", .7)
        if tp == "animales":
            sf(e["t0"] + .1, "grillos", .7)
            for k, n in (("murcielago_word", "chillido"), ("buho_word", "ulular"), ("polilla_word", "aleteo"), ("pill_word", "pop")):
                if g(k) is not None: sf(g(k), n, .9)
        if tp == "luciernagas":
            sf(e["t0"] + .1, "grillos", .6)
            for j in range(5): sf(e["t0"] + .4 + j * .45, "destello2", .5)
            if g("sol_word") is not None: sf(g("sol_word"), "subida", .6); sf(g("sol_word") + .8, "pop", .5)
        if tp == "corales":
            sf(e["t0"] + .2, "burbuja", .7)
            if g("huevos_word") is not None: sf(g("huevos_word"), "burbuja", 1.0); sf(g("huevos_word") + .4, "destello", .5)
            if g("sin_word") is not None:
                sf(g("sin_word"), "bajada", .6)
                for j in range(3): sf(g("sin_word") + .6 + j * .9, "burbuja", .4)
        if tp == "tomatera":
            sf(e["t0"] + .2, "bip", .4)
            if g("noche_word") is not None: sf(g("noche_word"), "pop", .5)
            if g("hojas_word") is not None: sf(g("hojas_word"), "bajada", .7); sf(g("hojas_word") + .8, "pop", .5)
        if tp == "calor":
            sf(e["t0"] + .2, "rotulador", .6)
            if g("sin_word") is not None:
                for j in range(8): sf(g("sin_word") + .15 * j, "tac", .45)
                sf(g("sin_word") + 1.3, "subida", .8); sf(g("sin_word") + 2.0, "crepita", .7)
        if tp == "noruega":
            if g("norte_word") is not None: sf(g("norte_word"), "pop", .6)
            if g("sol_word") is not None: sf(g("sol_word"), "destello", .6); sf(g("sol_word") + .3, "pop", .4)
        if tp == "planeta":
            for k, n, v in (("cara_word", "bajada", .7), ("luna_word", "destello", .5), ("eterna_word", "viento", .7), ("lados_word", "crepita", .7), ("franja_word", "destello", .7)):
                if g(k) is not None: sf(g(k), n, v)

    for k, fn in (("interruptor", e_interruptor), ("cama", e_cama), ("fabrica", e_fabrica), ("animales", e_animales), ("luciernagas", e_luciernagas),
                  ("corales", e_corales), ("tomatera", e_tomatera), ("calor", e_calor), ("noruega", e_noruega), ("planeta", e_planeta)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_dia)
