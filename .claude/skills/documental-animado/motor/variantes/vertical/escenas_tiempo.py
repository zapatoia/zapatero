"""Escenas del documental 10 (reloj interno): cara, crono, cerebro, cama y buzo, más sonidos de transición variados.

cara     cara grande que mira a cámara: ojos [{word, v 0 cerrado…1 abierto, dur?}] (parpadea sola), pill {word, txt, hasta},
         tachado {word, txt, hasta} (tarjeta con raya roja), bocadillo {word, txt, num}.
crono    cronómetro: inicio_word (+ inicio_fin: al acabar la palabra) → cuenta en tiempo REAL (juego justo), stop_word, stop_txt,
         barra [0, 45] con zonas [{hasta, txt, col}], rotulos [{word, txt, sub, hasta}], comentarios [{word, n, d?}] + comentario_txt,
         modo calor | frio | latido con vel [{word, v}] (aguja que gira sin cifras), etiqueta {word, txt, col}, latido_word,
         fijo (valor quieto) + veredictos [{word, txt, col, rango}].
cerebro  dos hemisferios con pliegues y tres engranajes que engranan; vel [{word, v}].
cama     cabecero, almohada, persona con termómetro (fiebre_word, temp), grito_word/grito, mini crono que va deprisa (crono_word, crono_vel).
buzo     agua con rayos de luz y burbujas, buzo que patalea y cuenta despacio (cuenta_word, cuenta [..]) con mini crono lento.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]

    # ---------------------------------------------------------------- sonidos nuevos
    def s_zum():
        d = .42; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        f = 180 + 900 * u ** 2; x = .5 * np.sin(2 * np.pi * np.cumsum(f) / AU.SR) + .6 * AU._banda(AU._ruido(n, 61), 400, 3000)
        return x * u ** 1.5 * np.minimum(1, (1 - u) / .08)
    def s_barrido():
        d = .38; n = int(d * AU.SR); u = np.linspace(0, 1, n); r = AU._ruido(n, 62); o = np.zeros(n); B = 16
        for k in range(B):
            a, b = k * n // B, (k + 1) * n // B; fc = 3500 - 2600 * (k / B); o[a:b] = AU._banda(r, fc * .7, fc * 1.3)[a:b]
        return o * np.sin(np.pi * u) ** 2
    def s_desliz():
        d = .3; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return (AU._banda(AU._ruido(n, 63), 250, 1600) + .3 * np.sin(2 * np.pi * np.cumsum(140 + 90 * u) / AU.SR)) * np.sin(np.pi * u) ** 1.5
    def s_burbuja():
        d = .12; n = int(d * AU.SR); t = np.arange(n) / AU.SR; f = 500 + 2200 * (t / d) ** 1.5
        return np.sin(2 * np.pi * np.cumsum(f) / AU.SR) * np.exp(-t / .04) * np.minimum(1, t / .003)
    def s_engranaje():
        d = .05; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (AU._banda(AU._ruido(n, 64), 1500, 5000) + .5 * np.sin(2 * np.pi * 820 * t)) * np.exp(-t / .008)
    def s_salida():
        d = .22; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 1760 * t) + .3 * np.sin(2 * np.pi * 3520 * t)) * np.minimum(1, t / .003) * np.minimum(1, (d - t) / .02)
    for nom, fn, db in (("zum", s_zum, -30), ("barrido", s_barrido, -31), ("desliz", s_desliz, -30), ("burbuja", s_burbuja, -30),
                        ("engranaje", s_engranaje, -29), ("salida", s_salida, -25)):
        AU.SFX.setdefault(nom, (fn, db))
    V.SFX_TRANS = dict(whip="whoosh", zoom="zum", mask="barrido", card="desliz")

    # ---------------------------------------------------------------- utilidades
    def _io(u): return u * u * (3 - 2 * u)

    def _keys(self, e, ks, t, campo="v", dd=.7):
        v = float(ks[0][campo])
        for k in ks[1:]:
            u = TI.clamp((t - self.ta(k["word"], e)) / k.get("dur", dd))
            if u <= 0: break
            v += (float(k[campo]) - v) * _io(u)
        return v

    def _fase(self, e, ks, t, t0):
        """Integral de la velocidad desde t0 (vueltas «virtuales» en segundos de esfera)."""
        if t <= t0: return 0.0
        n = max(8, int((t - t0) * 30)); ts = np.linspace(t0, t, n)
        return float(sum(_keys(self, e, ks, x) for x in ts) * (t - t0) / n)

    def _fin_palabra(self, t_ini):
        for p in self.palabras:
            if abs(p["s"] - t_ini) < 1e-3: return p["e"]
        return t_ini + .3

    def _bocadillo(self, c, x, y, txt, num, a, sc=1.0, cola=-1, fs=46):
        if a <= 0: return
        f1, f2 = fuente("Inter", 800, fs), fuente("Inter", 900, fs + 6)
        w1 = ancho(txt, f1); w2 = ancho(num, f2) if num else 0; w = w1 + w2 + (16 if num else 0) + 70; h = fs * 2.1
        c.save(); c.translate(x, y); c.scale(sc, sc); c.rotate(-2 * cola)
        sh = rrc(0, 10, w, h, h * .32)
        c.drawRRect(sh, skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
        p = skia.Path(); p.addRRect(rrc(0, 0, w, h, h * .32))
        tx = -w * .28 * (1 if cola < 0 else -1); p.moveTo(tx - 22, h / 2 - 4); p.lineTo(tx - 44 * (1 if cola < 0 else -1), h / 2 + 46); p.lineTo(tx + 26, h / 2 - 4); p.close()
        c.drawPath(p, relleno("#FBF6EC", a))
        texto(c, txt, -w / 2 + 35, 2, f1, "#14110D", alinear="i", alfa=a)
        if num: texto(c, num, -w / 2 + 35 + w1 + 16, 2, f2, "#E5322D", alinear="i", alfa=a)
        c.restore()

    def _rotulo_sup(self, c, txt, sub, y, a, col="#FFFFFF"):
        if a <= 0: return
        f1 = fuente("Inter", 900, 66); sc = min(1, 860 / ancho(txt, f1))
        c.save(); c.translate(CX, y); c.scale(sc, sc); texto(c, txt, 0, 0, f1, col, alfa=a, sombra=(3, 10, .5)); c.restore()
        if sub: texto(c, sub, CX, y + 70, fuente("Inter", 700, 30), "#B9C6E6", alfa=.9 * a)

    # ================================================================ CARA
    def e_cara(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        v = _keys(self, e, s["ojos"], t, dd=.35)
        ph = (t + .4) % 3.1
        if v > .5 and ph < .15: v *= abs(math.cos(math.pi * ph / .15))
        bob = 6 * math.sin(t * 1.4); cx, cy = CX, 700 + bob; sc = .94 + .06 * resorte(dt0 + .05, 6, 8)
        c.drawCircle(cx, cy, 560, skia.Paint(AntiAlias=True, Color=color("#3D5BC8", .25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 120)))
        c.save(); c.translate(cx, cy); c.scale(sc, sc)
        piel, piel2, pelo, ropa = "#F4C7A1", "#D99A72", "#5A3520", "#E8613C"
        # hombros (se funden abajo)
        hom = skia.Path(); hom.moveTo(-560, 700); hom.cubicTo(-560, 520, -330, 430, 0, 430); hom.cubicTo(330, 430, 560, 520, 560, 700); hom.close()
        c.drawPath(hom, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 430), (0, 640)], [color(ropa), color(ropa, 0)])))
        c.drawRRect(rrc(0, 400, 150, 120, 30), relleno(piel2))
        cuello = skia.Path(); cuello.moveTo(-120, 440); cuello.quadTo(0, 520, 120, 440)
        c.drawPath(cuello, trazo("#000000", 8, .2))
        for sx in (-1, 1):
            c.drawOval(skia.Rect(sx * 360 - 50, -60, sx * 360 + 50, 90), relleno(piel2))
            c.drawArc(skia.Rect(sx * 360 - 26, -20, sx * 360 + 26, 50), -90 if sx > 0 else 90, 180, False, trazo("#8A5A40", 5, .7))
        c.drawOval(skia.Rect(-370, -400, 370, 440), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-90, -120), 520, [color("#FFDDBE"), color(piel), color(piel2)], [0, .55, 1])))
        hp = skia.Path(); hp.moveTo(-372, 40); hp.cubicTo(-400, -330, -170, -450, 20, -440); hp.cubicTo(250, -440, 410, -300, 372, 40)
        hp.cubicTo(340, -120, 250, -190, 120, -200); hp.cubicTo(60, -150, -20, -150, -60, -200); hp.cubicTo(-200, -190, -330, -130, -372, 40); hp.close()
        c.drawPath(hp, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -450), (0, 40)], [color("#7A4A2A"), color(pelo)])))
        c.drawPath(hp, trazo("#2A160C", 4, .5))
        for k in range(5):
            st = skia.Path(); st.moveTo(-200 + k * 90, -380 + 10 * k); st.quadTo(-170 + k * 90, -300, -150 + k * 95, -230)
            c.drawPath(st, trazo("#3A2010", 4, .35))
        # cejas
        lev = 14 * (1 - v)
        for sx in (-1, 1):
            cj = skia.Path(); cj.moveTo(sx * 250, -150 + lev); cj.quadTo(sx * 160, -190 + lev, sx * 70, -165 + lev)
            c.drawPath(cj, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=20, Color=color("#2A160C"), StrokeCap=skia.Paint.kRound_Cap))
        # ojos
        mira = 14 * math.sin(t * .7)
        for sx in (-1, 1):
            ex, ey = sx * 160, -50
            if v > .06:
                h2 = 64 * v
                ojo = skia.Path(); ojo.moveTo(ex - 110, ey); ojo.quadTo(ex, ey - 2 * h2, ex + 110, ey); ojo.quadTo(ex, ey + 2 * h2 * .85, ex - 110, ey); ojo.close()
                c.save(); c.clipPath(ojo, doAntiAlias=True)
                c.drawRect(skia.Rect(ex - 120, ey - 140, ex + 120, ey + 140), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, ey - 70), (0, ey + 40)], [color("#D8DCE6"), color("#FFFFFF")])))
                ix = ex + mira
                c.drawCircle(ix, ey + 4, 54, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((ix, ey + 4), 54, [color("#1E3F7A"), color("#3E7BD9"), color("#1A3A70")], [0, .7, 1])))
                fib = skia.Path()
                for k in range(28):
                    a = 2 * math.pi * k / 28; fib.moveTo(ix + 26 * math.cos(a), ey + 4 + 26 * math.sin(a)); fib.lineTo(ix + 50 * math.cos(a), ey + 4 + 50 * math.sin(a))
                c.drawPath(fib, trazo("#9CC4FF", 2, .35))
                c.drawCircle(ix, ey + 4, 24, relleno("#0C0C12")); c.drawCircle(ix + 16, ey - 14, 11, relleno("#FFFFFF", .95)); c.drawCircle(ix - 14, ey + 18, 5, relleno("#FFFFFF", .7))
                c.restore()
                c.drawPath(ojo, trazo("#1A1410", 9))
                lp = skia.Path(); lp.moveTo(ex - 110, ey); lp.quadTo(ex, ey - 2 * h2, ex + 110, ey)
                c.drawPath(lp, trazo("#1A1410", 14))
            else:
                cl = skia.Path(); cl.moveTo(ex - 100, ey); cl.quadTo(ex, ey + 44, ex + 100, ey)
                c.drawPath(cl, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=12, Color=color("#1A1410"), StrokeCap=skia.Paint.kRound_Cap))
                for k in range(6):
                    u = .15 + .7 * k / 5; x = (1 - u) ** 2 * (ex - 100) + 2 * (1 - u) * u * ex + u * u * (ex + 100); y = (1 - u) ** 2 * ey + 2 * (1 - u) * u * (ey + 44) + u * u * ey
                    c.drawLine(x, y + 4, x + (u - .5) * 30, y + 26, trazo("#1A1410", 5))
        # nariz, mejillas, boca
        nz = skia.Path(); nz.moveTo(-10, 30); nz.quadTo(-40, 150, -20, 170); nz.quadTo(10, 190, 40, 165)
        c.drawPath(nz, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9, Color=color("#1A1410", .85), StrokeCap=skia.Paint.kRound_Cap))
        for sx in (-1, 1): c.drawOval(skia.Rect(sx * 250 - 65, 110, sx * 250 + 65, 190), relleno("#FF8A7A", .45))
        bo = skia.Path(); bo.moveTo(-110, 250); bo.quadTo(0, 320 - 20 * (1 - v), 110, 250)
        c.drawPath(bo, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=11, Color=color("#1A1410"), StrokeCap=skia.Paint.kRound_Cap))
        c.restore()
        # sobrepuestos
        def ventana(q):
            if not q: return 0, 0
            d = t - self.ta(q["word"], e)
            if d <= 0: return 0, d
            a = aparece(d, .12)
            if q.get("hasta"): a *= TI.clamp((self.ta(q["hasta"], e) - .1 - t) / .14)
            return a, d
        a, d = ventana(s.get("pill"))
        if a > 0:
            q = s["pill"]; fk = fuente("Inter", 900, 120); w = ancho(q["txt"], fk) + 90; s2 = .7 + .3 * resorte(d, 9, 12)
            c.save(); c.translate(CX, 1080); c.scale(min(1, 880 / w) * s2, min(1, 880 / w) * s2)
            r_ = rrc(0, 0, w, 190, 46); c.drawRRect(r_, relleno("#0B1A12", .78 * a)); c.drawRRect(r_, trazo("#4ADE80", 5, .7 * a))
            with capa(c, alfa=.7 * a, blur=22): texto(c, q["txt"], 0, 0, fk, "#22C55E")
            texto(c, q["txt"], 0, 0, fk, "#7CF5A6", alfa=a); c.restore()
        a, d = ventana(s.get("tachado"))
        if a > 0:
            q = s["tachado"]; fk = fuente("Inter", 900, 100); w = ancho(q["txt"], fk) + 140; s2 = .7 + .3 * resorte(d, 9, 12)
            c.save(); c.translate(CX, 1080); c.scale(s2, s2)
            r_ = rrc(0, 0, w, 170, 44); c.drawRRect(r_.makeOffset(0, 10) if hasattr(r_, "makeOffset") else r_, skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
            c.drawRRect(r_, relleno("#FBF6EC", a)); texto(c, q["txt"], 0, 4, fk, "#14110D", alfa=a)
            u = TI.cubic_out(TI.clamp((d - .25) / .35))
            if u > 0: c.drawLine(-w / 2 + 50, 30, -w / 2 + 50 + (w - 100) * u, -14, skia.Paint(AntiAlias=True, StrokeWidth=16, Color=color("#EF4423", a), StrokeCap=skia.Paint.kRound_Cap))
            c.restore()
        a, d = ventana(s.get("bocadillo"))
        if a > 0:
            q = s["bocadillo"]; _bocadillo(self, c, CX, 1080, q["txt"], q.get("num", ""), a, .6 + .4 * resorte(d, 9, 12), fs=54)

    # ================================================================ CRONO
    def _dial(self, c, cx, cy, R, frac, col, glow=1.0, cara="#1A2233", digitos=None, mini=False):
        c.drawCircle(cx, cy + 24, R + 30, skia.Paint(AntiAlias=True, Color=color("#000000", .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
        c.drawRRect(rrc(cx, cy - R - 34, R * .28, 56, 14), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, cy - R - 60), (0, cy - R - 6)], [color("#5A6478"), color("#2A3040")])))
        c.drawRRect(rrc(cx, cy - R - 8, R * .16, 26, 8), relleno("#3A4256"))
        c.drawCircle(cx, cy, R + 14, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeSweep(cx, cy, [color(x) for x in ("#4A5468", "#9AA6BC", "#3A4254", "#8C98AE", "#4A5468")])))
        c.drawCircle(cx, cy, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx - R * .3, cy - R * .4), R * 1.4, [color("#2E3A54"), color(cara), color("#0A0E18")], [0, .5, 1])))
        # marcas (las ya recorridas se tiñen del color)
        for k in range(60):
            a = math.radians(-90 + k * 6); big = k % 5 == 0; r0 = R - (40 if big else 22) * (R / 340)
            pasado = k / 60 <= frac
            c.drawLine(cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + (R - 8) * math.cos(a), cy + (R - 8) * math.sin(a),
                       trazo(col if pasado else "#8A94AA", (5 if big else 2.5) * R / 340, .95 if pasado else .55))
        a30 = math.radians(90); c.drawLine(cx, cy + R - 70 * R / 340, cx, cy + R - 14, skia.Paint(AntiAlias=True, StrokeWidth=12 * R / 340, Color=color("#22C55E"), StrokeCap=skia.Paint.kRound_Cap))
        if frac > 0:
            arc = skia.Path(); arc.addArc(skia.Rect(cx - R - 6, cy - R - 6, cx + R + 6, cy + R + 6), -90, 360 * min(frac, .9999))
            c.drawPath(arc, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26 * R / 340, Color=color(col, .35 * glow), StrokeCap=skia.Paint.kRound_Cap,
                                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
            c.drawPath(arc, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10 * R / 340, Color=color(col), StrokeCap=skia.Paint.kRound_Cap))
        c.drawCircle(cx - R * .25, cy - R * .45, R * .7, skia.Paint(AntiAlias=True, Color=color("#FFFFFF", .04)))

    def _aguja(c, cx, cy, R, ang, estela=0.0, col="#FF4A3A"):
        a = math.radians(ang)
        if estela > 0:
            for k in range(1, 9):
                b = math.radians(ang - estela * k * 3.2)
                c.drawLine(cx, cy, cx + (R - 30) * math.cos(b), cy + (R - 30) * math.sin(b), skia.Paint(AntiAlias=True, StrokeWidth=7, Color=color(col, .3 * (1 - k / 9))))
        c.drawLine(cx - 50 * math.cos(a), cy - 50 * math.sin(a), cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a),
                   skia.Paint(AntiAlias=True, StrokeWidth=7, Color=color(col), StrokeCap=skia.Paint.kRound_Cap))
        c.drawCircle(cx, cy, 20, relleno(col)); c.drawCircle(cx, cy, 8, relleno("#FFFFFF"))

    def _digitos(self, c, cx, cy, val, col="#FFFFFF", dec_col="#5AA9FF", esc=1.0, a=1.0, maxw=None):
        """Cifra «SS,d» centrada como grupo; si no cabe en maxw (ancho útil de la esfera) se encoge entera.
        El ancho se mide con «88,8» para que el tamaño no salte al pasar de 9 a 10 s."""
        ent = int(val); dec = int((val - ent) * 10)
        f1, f2 = fuente("Inter", 900, int(220 * esc)), fuente("Inter", 900, int(110 * esc))
        ref = ancho("88", f1) + ancho(",8", f2) + 6 * esc
        k = min(1.0, (maxw or ref) / ref)
        w1, w2 = ancho(str(ent), f1), ancho(f",{dec}", f2); x0 = -(w1 + w2 + 6 * esc) / 2
        c.save(); c.translate(cx, cy); c.scale(k, k)
        with capa(c, alfa=.55 * a, blur=26): texto(c, str(ent), x0, 0, f1, "#000000", alinear="i", tnum=True)
        texto(c, str(ent), x0, 0, f1, col, alinear="i", alfa=a, tnum=True, sombra=(4, 16, .5))
        texto(c, f",{dec}", x0 + w1 + 6 * esc, 40 * esc, f2, dec_col, alinear="i", alfa=a, tnum=True)
        c.restore()

    def e_crono(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo")
        cx, cy, R = CX, 690, 330
        if s.get("barra"): cy, R = 655, 300
        sc = .9 + .1 * resorte(dt0 + .05, 7, 9); c.save(); c.translate(cx, cy); c.scale(sc, sc); c.translate(-cx, -cy)
        # fondos por modo
        rng = np.random.default_rng(21)
        if modo == "calor":
            c.drawCircle(cx, cy, 700, skia.Paint(AntiAlias=True, Color=color("#FF5A1F", .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 160)))
            for k in range(40):
                per = 2 + 2 * rng.random(); ph = ((t + rng.random() * per) % per) / per; x = rng.random() * W + 30 * math.sin(t * 2 + k)
                c.drawCircle(x, 1300 - 1250 * ph, 3 + 5 * rng.random(), relleno("#FFB347", .7 * math.sin(math.pi * ph)))
        elif modo == "frio":
            c.drawCircle(cx, cy, 700, skia.Paint(AntiAlias=True, Color=color("#7CC4FF", .22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 160)))
            for k in range(60):
                per = 4 + 4 * rng.random(); ph = ((t + rng.random() * per) % per) / per; x = rng.random() * W + 40 * math.sin(t + k)
                c.drawCircle(x, -40 + 1350 * ph, 2 + 4 * rng.random(), relleno("#FFFFFF", .75))
            hielo = skia.Path()
            for k in range(10):
                bx = (k % 2) * W + (-1 if k % 2 == 0 else 1) * 10; by = 120 + k * 115; d = 1 if k % 2 == 0 else -1; L = 140 + 60 * rng.random()
                hielo.moveTo(bx, by); hielo.lineTo(bx + d * L, by + 20)
                for j in range(1, 5):
                    px, py = bx + d * L * j / 5, by + 20 * j / 5
                    hielo.moveTo(px, py); hielo.lineTo(px - d * 22, py - 22); hielo.moveTo(px, py); hielo.lineTo(px - d * 22, py + 22)
            c.drawPath(hielo, trazo("#DDEFFF", 3, .55))
        elif modo == "latido":
            c.drawCircle(cx, cy, 700, skia.Paint(AntiAlias=True, Color=color("#E0245E", .28), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 160)))
        # valor del cronómetro
        val = None; parado = False; frac = 0.0; col = "#5AA9FF"; ang = -90.0; estela = 0.0; lab = ""
        if s.get("inicio_word"):
            ti = self.ta(s["inicio_word"], e); t_start = _fin_palabra(self, ti) if s.get("inicio_fin") else ti
            t_stop = self.ta(s["stop_word"], e) if s.get("stop_word") else 1e9
            val = max(0.0, min(t, t_stop) - t_start); parado = t >= t_stop
            frac = (val % 60) / 60; ang = -90 + val * 6
            for z in s.get("zonas", []):
                if val < z["hasta"]: col = z["col"]; lab = z["txt"]; break
            if parado: col = "#FF4A3A"
        elif s.get("vel"):
            f = _fase(self, e, s["vel"], t, e["t0"]); v = _keys(self, e, s["vel"], t)
            ang = -90 + f * 60; frac = ((f * 60) % 360) / 360; estela = min(4, v) if modo else 0
            col = {"calor": "#FF8A3D", "frio": "#9ED3FF", "latido": "#FF5C8A"}.get(modo, "#5AA9FF")
        elif s.get("fijo") is not None:
            val = float(s["fijo"]); frac = val / 60; ang = -90 + val * 6 + 4 * math.sin(t * 2)
            vs = [q for q in s.get("veredictos", []) if q.get("txt") and t >= self.ta(q["word"], e)]
            if vs: col = vs[-1]["col"]
        cara_col = {"frio": "#3A4A66", "calor": "#2A1E22", "latido": "#2A1626"}.get(modo, "#1A2233")
        _dial(self, c, cx, cy, R, frac, col, cara=cara_col)
        if modo == "latido":
            bpm = 1.0 + .8 * (_keys(self, e, s["vel"], t) - 1); pul = max(0, math.sin(t * 2 * math.pi * bpm)) ** 6
            hs = 1 + .1 * pul; c.save(); c.translate(cx, cy - 10); c.scale(hs, hs)
            co = skia.Path(); co.moveTo(0, 150); co.cubicTo(-260, -20, -170, -230, 0, -110); co.cubicTo(170, -230, 260, -20, 0, 150); co.close()
            c.drawPath(co, skia.Paint(AntiAlias=True, Color=color("#FF2D55", .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
            c.drawPath(co, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-60, -80), 260, [color("#FF6B6B"), color("#E0243A"), color("#8A0E22")], [0, .55, 1])))
            c.drawPath(co, trazo("#3A0610", 5, .8)); c.drawOval(skia.Rect(-130, -120, -60, -80), relleno("#FFFFFF", .55)); c.restore()
        _aguja(c, cx, cy, R, ang, estela)
        if val is not None and s.get("inicio_word"):
            _digitos(self, c, cx, cy - 10, val, dec_col=col, maxw=1.25 * R)
            lab_txt = s.get("stop_txt", "STOP") if parado else lab
            if t >= self.ta(s["inicio_word"], e):
                fl = fuente("Inter", 900, 64); kl = min(1.0, 1.2 * R / max(1, ancho(lab_txt, fl)))
                c.save(); c.translate(cx, cy + 150); c.scale(kl, kl); texto(c, lab_txt, 0, 0, fl, col, alfa=1, sombra=(2, 10, .4)); c.restore()
        if s.get("fijo") is not None:
            vs = [q for q in s.get("veredictos", []) if t >= self.ta(q["word"], e)]
            if vs and vs[-1].get("txt"):
                q = vs[-1]; d = t - self.ta(q["word"], e); fk = fuente("Inter", 900, 130); s2 = .7 + .3 * resorte(d, 8, 11)
                c.save(); c.translate(cx, cy); c.scale(s2, s2)
                with capa(c, alfa=.8, blur=24): texto(c, q["txt"], 0, 0, fk, q["col"])
                texto(c, q["txt"], 0, 0, fk, q["col"], alfa=aparece(d, .1)); c.restore()
        c.restore()
        # barra 0–45
        if s.get("barra"):
            b0, b1 = s["barra"]; x0, x1, yb = 70, 930, 1045
            X = lambda v: x0 + (x1 - x0) * (v - b0) / (b1 - b0)
            ant = b0
            for z in s.get("zonas", [{"hasta": 20, "col": "#3B82F6"}, {"hasta": 27, "col": "#38BDF8"}, {"hasta": 31, "col": "#22C55E"}, {"hasta": 35, "col": "#F59E0B"}, {"hasta": 99, "col": "#EF4444"}]):
                h_ = min(z["hasta"], b1); c.drawRect(skia.Rect(X(ant), yb - 12, X(h_), yb + 12), relleno(z["col"], .55)); ant = h_
                if ant >= b1: break
            for q in s.get("veredictos", []):
                if t >= self.ta(q["word"], e):
                    a = aparece(t - self.ta(q["word"], e), .2); r0, r1 = q["rango"]
                    c.drawRect(skia.Rect(X(r0), yb - 40, X(r1), yb + 40), relleno(q["col"], .28 * a)); c.drawRect(skia.Rect(X(r0), yb - 40, X(r1), yb + 40), trazo(q["col"], 3, .8 * a))
            c.drawRect(skia.Rect(x0, yb - 12, x1, yb + 12), trazo("#FFFFFF", 2, .5))
            for v_ in range(int(b0), int(b1) + 1, 10):
                c.drawLine(X(v_), yb - 22, X(v_), yb + 22, trazo("#FFFFFF", 3, .9))
                if v_ != 30: texto(c, str(v_), X(v_), yb + 58, fuente("Inter", 800, 40), "#FFFFFF", alfa=.85)   # el 30 va solo en verde
            c.drawLine(X(30), yb - 36, X(30), yb + 26, skia.Paint(AntiAlias=True, StrokeWidth=7, Color=color("#22C55E")))
            texto(c, "30", X(30), yb + 62, fuente("Inter", 900, 56), "#4ADE80")
            if val is not None and s.get("inicio_word") and t >= self.ta(s["inicio_word"], e):
                xv = X(min(val, b1))
                c.drawCircle(xv, yb, 22, skia.Paint(AntiAlias=True, Color=color("#FFFFFF", .6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
                c.drawCircle(xv, yb, 11, relleno("#FFFFFF"))
                tri = skia.Path(); tri.moveTo(xv - 18, yb - 66); tri.lineTo(xv + 18, yb - 66); tri.lineTo(xv, yb - 38); tri.close(); c.drawPath(tri, relleno("#FFFFFF"))
            for q in s.get("comentarios", []):
                d = t - self.ta(q["word"], e) - q.get("d", 0)
                if d > 0:
                    xv = X(q["n"]); a = aparece(d, .12); r_ = 16 * (.6 + .4 * resorte(d, 10, 12))
                    c.drawCircle(xv, yb, r_ + 5, relleno("#E5322D", a)); c.drawCircle(xv, yb, r_, relleno("#FFFFFF", a))
        # comentarios (bocadillos)
        cs = [q for q in s.get("comentarios", []) if t - self.ta(q["word"], e) - q.get("d", 0) > 0]
        for k, q in enumerate(cs):
            d = t - self.ta(q["word"], e) - q.get("d", 0); n_ = len(s.get("comentarios", []))
            y = 430 + k * (min(130, 470 / max(1, n_ - 1)) if n_ > 2 else 150); x = CX + (-110 if k % 2 == 0 else 110)   # bocadillos por encima de la barra
            _bocadillo(self, c, x, y, s.get("comentario_txt", ""), str(q["n"]), aparece(d, .1), .6 + .4 * resorte(d, 10, 13), cola=-1 if k % 2 == 0 else 1, fs=44)
        # rótulos de arriba y etiqueta
        for q in s.get("rotulos", []):
            d = t - self.ta(q["word"], e)
            if d > 0:
                a = aparece(d, .2)
                if q.get("hasta"): a *= TI.clamp((self.ta(q["hasta"], e) - t) / .15)
                _rotulo_sup(self, c, q["txt"], q.get("sub"), 250, a)
        et = s.get("etiqueta")
        if et and t > self.ta(et["word"], e):
            d = t - self.ta(et["word"], e); fk = fuente("Inter", 900, 96); s2 = .75 + .25 * resorte(d, 8, 11)
            c.save(); c.translate(CX, 1130); c.scale(s2, s2)
            with capa(c, alfa=.8, blur=20): texto(c, et["txt"], 0, 0, fk, et["col"])
            texto(c, et["txt"], 0, 0, fk, et["col"], alfa=aparece(d, .1)); c.restore()
        if modo == "latido":
            ox = (t * 380) % 360; ecg = skia.Path(); first = True
            for k in range(-1, 5):
                bx = k * 360 - ox
                pts = [(bx, 0), (bx + 120, 0), (bx + 140, -18), (bx + 160, 0), (bx + 175, 0), (bx + 190, 40), (bx + 205, -160), (bx + 222, 60), (bx + 240, 0), (bx + 270, -30), (bx + 300, 0), (bx + 360, 0)]
                for (x, y) in pts:
                    if first: ecg.moveTo(x, 1130 + y); first = False
                    else: ecg.lineTo(x, 1130 + y)
            c.drawPath(ecg, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=16, Color=color("#FF5C8A", .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
            c.drawPath(ecg, trazo("#FF8FB0", 5, .95))

    # ================================================================ CEREBRO
    def _engranaje(c, x, y, r, dientes, ang, col1, col2):
        p = skia.Path(); n = dientes * 4
        for k in range(n + 1):
            a = math.radians(ang) + 2 * math.pi * k / n; rr = r + (18 if (k % 4) in (1, 2) else 0)
            (p.moveTo if k == 0 else p.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - r * .3, y - r * .3), r * 1.4, [color(col1), color(col2)])))
        c.drawPath(p, trazo("#0A1226", 6))
        for k in range(5):
            a = math.radians(ang) + 2 * math.pi * k / 5; c.drawCircle(x + r * .55 * math.cos(a), y + r * .55 * math.sin(a), r * .16, relleno("#0E1630", .9))
        c.drawCircle(x, y, r * .22, relleno("#DCE8FF")); c.drawCircle(x, y, r * .11, relleno("#0E1630")); c.drawCircle(x, y, r * .22, trazo("#0A1226", 4))

    def e_cerebro(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; sc = .9 + .1 * resorte(dt0 + .05, 6, 8)
        cx, cy = CX, 650
        c.save(); c.translate(cx, cy); c.scale(sc, sc)
        c.drawCircle(0, 0, 520, skia.Paint(AntiAlias=True, Color=color("#FFB4A0", .18), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 120)))
        c.drawRRect(rrc(0, 340, 150, 180, 40), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 250), (0, 430)], [color("#F2A08A"), color("#C06A5A")])))
        for sx in (-1, 1):
            h = skia.Path(); h.moveTo(sx * 12, -330); h.cubicTo(sx * 300, -360, sx * 470, -200, sx * 450, 40); h.cubicTo(sx * 440, 260, sx * 300, 330, sx * 150, 260)
            h.cubicTo(sx * 80, 230, sx * 30, 300, sx * 12, 280); h.close()
            c.drawPath(h, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((sx * 150, -120), 470, [color("#FFE6DC"), color("#F5B3A2"), color("#D7826F")], [0, .6, 1])))
            c.save(); c.clipPath(h, doAntiAlias=True); rr = np.random.default_rng(3 if sx > 0 else 4); pl = skia.Path()
            for k in range(14):
                x, y = sx * (60 + 360 * rr.random()), -300 + 560 * rr.random(); pl.moveTo(x, y)
                for j in range(4): x += sx * (rr.random() - .3) * 90; y += (rr.random() - .5) * 110; pl.quadTo(x - 30, y + 20, x, y)
            c.drawPath(pl, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=14, Color=color("#C0604E", .45), StrokeCap=skia.Paint.kRound_Cap)); c.restore()
            c.drawPath(h, trazo("#8A3A2E", 5, .6))
        f = _fase(self, e, s["vel"], t, e["t0"]) * 90
        _engranaje(c, -60, 10, 130, 12, f, "#6AA8FF", "#1E4FC2")
        _engranaje(c, 150, -110, 88, 9, -f * 130 / 88 + 10, "#7FB6FF", "#2A5ED0")
        _engranaje(c, 110, 190, 74, 8, -f * 130 / 74 + 6, "#7FB6FF", "#2A5ED0")
        c.restore()

    # ================================================================ CAMA (fiebre)
    def e_cama(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        c.drawRect(skia.Rect(-20, 300, W + 20, 880), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 300), (0, 880)], [color("#B87A48"), color("#8A5530")])))
        for k in range(1, 9): c.drawLine(k * 125, 330, k * 125, 860, trazo("#6A3E20", 4, .5))
        c.drawRect(skia.Rect(-20, 300, W + 20, 880), trazo("#3A2010", 6, .8))
        c.drawOval(skia.Rect(30, 470, 1040, 900), relleno("#F4F1EA")); c.drawOval(skia.Rect(30, 470, 1040, 900), trazo("#2A2018", 6))
        uf = TI.cubic_out(TI.clamp((t - self.ta(s["fiebre_word"], e)) / 1.2)) if s.get("fiebre_word") else 0
        AY, SC = 640, 2.1; self._avatar(c, CX, AY, SC, "#8E6BE0", "#4A2A18", largo=True)
        for sx in (-1, 1): c.drawOval(skia.Rect(CX + sx * 36 * SC - 22, AY + 18 * SC, CX + sx * 36 * SC + 22, AY + 30 * SC), relleno("#FF4A3A", .45 * uf))
        if uf > 0:
            dy = (t * 40) % 60; c.drawCircle(CX - 45 * SC, AY - 30 * SC + dy, 11, relleno("#9ED8FF", .8 * uf))
        # termómetro
        c.save(); c.translate(CX + 8, AY + 38 * SC); c.rotate(-30)
        c.drawRRect(rrc(150, 0, 300, 34, 17), relleno("#FFFFFF", .95)); c.drawRRect(rrc(150, 0, 300, 34, 17), trazo("#2A2018", 4))
        for k in range(12): c.drawLine(40 + k * 22, -8, 40 + k * 22, 2, trazo("#2A2018", 2, .7))
        c.drawRRect(rrc(20 + 130 * (.25 + .75 * uf), 0, 260 * (.25 + .75 * uf), 12, 6), relleno("#E5322D"))
        c.drawCircle(0, 0, 30, relleno("#E5322D")); c.drawCircle(0, 0, 30, trazo("#2A2018", 4)); c.restore()
        if uf > .3 and s.get("temp"):
            self.pildora(c, s["temp"], CX + 320, 400, S, TI.clamp((uf - .3) / .3), fnt=fuente("Inter", 800, 44), fondo="#5A1010")
        # manta
        c.drawRect(skia.Rect(-20, 860, W + 20, 940), relleno("#F4F1EA")); c.drawLine(-20, 860, W + 20, 850, trazo("#2A2018", 6))
        c.drawRect(skia.Rect(-20, 940, W + 20, H + 20), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 940), (0, 1700)], [color("#4A7FD6"), color("#1E3E8A"), color("#0C1838")], [0, .5, 1])))
        for k in range(9):
            c.drawLine(k * 140 - 20, 940, k * 140 + 30, H, trazo("#9EC0FF", 6, .25)); c.drawLine(-20, 1010 + k * 120, W + 20, 1000 + k * 120, trazo("#9EC0FF", 6, .2))
        # mini crono que va deprisa
        if s.get("crono_word") and t > self.ta(s["crono_word"], e) - .3:
            tc = self.ta(s["crono_word"], e); val = max(0, t - tc) * s.get("crono_vel", 1.5) * 12
            a = aparece(t - tc + .3, .2); c.save(); c.translate(CX, 1040); s2 = .6 + .4 * resorte(t - tc + .3, 8, 10); c.scale(s2, s2); c.translate(-CX, -1040)
            _dial(self, c, CX, 1040, 115, (val % 60) / 60, "#FF8A3D"); _aguja(c, CX, 1040, 115, -90 + val * 6, 2.0, "#FF8A3D"); c.restore()
        if s.get("grito_word"):
            d = t - self.ta(s["grito_word"], e)
            if d > 0: _bocadillo(self, c, 290, 380, s["grito"], "", aparece(d, .1), .6 + .4 * resorte(d, 10, 13), cola=-1, fs=58)

    # ================================================================ BUZO (frío)
    def e_buzo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        c.drawRect(skia.Rect(-20, -20, W + 20, H + 20), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, H)], [color("#3FA0E6"), color("#145CA8"), color("#06204A")], [0, .45, 1])))
        for k in range(6):
            x = 80 + k * 190 + 40 * math.sin(t * .5 + k); p = skia.Path(); p.moveTo(x, 150); p.lineTo(x + 90, 150); p.lineTo(x - 120, 1500); p.lineTo(x - 220, 1500); p.close()
            c.drawPath(p, relleno("#BFE6FF", .07 + .04 * math.sin(t * 1.3 + k)))
        ola = skia.Path(); ola.moveTo(-20, 0)
        for k in range(0, 13): ola.lineTo(k * 90 - 20, 150 + 30 * math.sin(k * 1.7 + t * 1.5) * (1 if k % 2 else -1))
        ola.lineTo(W + 20, 0); ola.close(); c.drawPath(ola, relleno("#9FB4C8", .9))
        rb = np.random.default_rng(31)
        for k in range(26):
            per = 3 + 3 * rb.random(); ph = ((t + rb.random() * per) % per) / per; x = rb.random() * W + 20 * math.sin(t * 2 + k); y = 1450 - 1250 * ph; r = 8 + 18 * rb.random()
            c.drawCircle(x, y, r, trazo("#E6F6FF", 3, .7 * math.sin(math.pi * ph))); c.drawCircle(x - r * .3, y - r * .3, r * .22, relleno("#FFFFFF", .6 * math.sin(math.pi * ph)))
        # buzo
        bx, by = CX - 130, 600 + 14 * math.sin(t * 1.2); pat = 12 * math.sin(t * 3)
        c.save(); c.translate(bx, by); c.scale(.88, .88)
        for sx, ph in ((-1, 0), (1, math.pi)):
            c.save(); c.translate(sx * 45, 250); c.rotate(pat * math.sin(t * 3 + ph) / 4)
            c.drawRRect(rrc(0, 130, 54, 260, 20), relleno("#1C2238")); c.drawPath(skia.Path.Polygon([(-50, 250), (50, 250), (70, 380), (-60, 360)], True), relleno("#FFC82E"))
            c.drawPath(skia.Path.Polygon([(-50, 250), (50, 250), (70, 380), (-60, 360)], True), trazo("#8A6A0A", 3)); c.restore()
        c.drawRRect(rrc(-150, 40, 70, 260, 26), relleno("#D8DCE6")); c.drawRRect(rrc(-150, 40, 70, 260, 26), trazo("#6A7080", 3))
        c.drawRRect(rrc(0, 60, 250, 330, 70), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-120, 0), (120, 0)], [color("#2A3150"), color("#151A2E")])))
        c.drawRRect(rrc(0, 40, 180, 16, 8), relleno("#FFC82E"))
        for sx in (-1, 1):
            c.save(); c.translate(sx * 120, -40); c.rotate(sx * (20 + 6 * math.sin(t * 1.5)))
            c.drawRRect(rrc(0, 110, 52, 230, 24), relleno("#1C2238")); c.restore()
        c.drawCircle(0, -200, 120, relleno("#151A2E"))
        c.drawCircle(0, -175, 86, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-20, -200), 90, [color("#FFD9B8"), color("#E2A57A")])))
        c.drawRRect(rrc(0, -205, 190, 92, 34), relleno("#BFE3F0", .75)); c.drawRRect(rrc(0, -205, 190, 92, 34), trazo("#FFC82E", 10))
        for sx in (-1, 1): c.drawCircle(sx * 40, -205, 11, relleno("#2A3A4A"))
        c.drawCircle(-10, -120, 30, relleno("#2A3150")); rg = skia.Path(); rg.moveTo(15, -120); rg.quadTo(140, -110, 120, 40); c.drawPath(rg, trazo("#2A3150", 12))
        c.restore()
        # cuenta lenta y mini crono lento
        if s.get("cuenta_word"):
            tc = self.ta(s["cuenta_word"], e)
            for k, txt in enumerate(s.get("cuenta", [])):
                d = t - tc - k * 1.1
                if d > 0:
                    a = aparece(d, .15) * TI.clamp((1.6 - d) / .3); y = 360 - 60 * d
                    texto(c, txt, CX + 60 + k * 90, y, fuente("Inter", 900, 70), "#FFFFFF", alfa=a, sombra=(2, 10, .5))
        cxm, cym = CX + 255, 860; val = max(0, t - e["t0"]) * .45
        _dial(self, c, cxm, cym, 150, (val % 60) / 60, "#9ED3FF"); _aguja(c, cxm, cym, 150, -90 + val * 6, .6, "#FF4A3A")
        _digitos(self, c, cxm, cym - 4, val, dec_col="#9ED3FF", esc=.42, maxw=1.2 * 150)

    # ---------------------------------------------------------------- efectos
    def efectos_tiempo(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]
        if tp == "cara":
            for k in s["ojos"][1:]: pon(self.ta(k["word"], e), "parpadeo", 1.0)
            if s.get("pill"): pon(self.ta(s["pill"]["word"], e), "pop", .7)
            if s.get("tachado"): pon(self.ta(s["tachado"]["word"], e), "pop", .6); self.sfx(TI.f_de_t(self.ta(s["tachado"]["word"], e) + .3), "sello", .6)
            if s.get("bocadillo"): pon(self.ta(s["bocadillo"]["word"], e), "pop", .7)
        if tp == "crono":
            if s.get("inicio_word"):
                ti = self.ta(s["inicio_word"], e); ts = _fin_palabra(self, ti) if s.get("inicio_fin") else ti
                self.sfx(TI.f_de_t(ts + .01), "salida", 1.0)                       # pitido de salida (luego silencio: no da pistas)
            if s.get("stop_word"): pon(self.ta(s["stop_word"], e), "golpe", .7)
            for k, q in enumerate(s.get("comentarios", [])):
                self.sfx(TI.f_de_t(self.ta(q["word"], e) + q.get("d", 0) + .01), f"rama{min(10, 3 + k)}", .9)
            if s.get("vel"):
                ks = s["vel"]; t0 = e["t0"] + .1; tf = (e.get("t1") or t0 + 3) - .1; x = t0
                while x < tf:                                                       # tic-tac al ritmo de la aguja
                    v = _keys(self, e, ks, x); self.sfx(TI.f_de_t(x), "tic" if int(x * 10) % 2 else "tac", .55)
                    x += max(.11, .5 / max(v, .1))
            if s.get("etiqueta"): pon(self.ta(s["etiqueta"]["word"], e), "destello", .7)
            if s.get("latido_word"):
                tl_ = self.ta(s["latido_word"], e)
                for j in range(4): self.sfx(TI.f_de_t(tl_ + j * .55), "latido", 1.0)
            for q in s.get("veredictos", []):
                if q.get("txt"): pon(self.ta(q["word"], e), "golpe", .5)
        if tp == "cerebro":
            ks = s["vel"]; x = e["t0"] + .2; tf = (e.get("t1") or x + 3) - .1
            while x < tf:
                v = _keys(self, e, ks, x); self.sfx(TI.f_de_t(x), "engranaje", .7); x += max(.11, .45 / max(v, .1))
        if tp == "cama":
            if s.get("fiebre_word"): self.sfx(TI.f_de_t(self.ta(s["fiebre_word"], e)), "subida", 1.0)
            if s.get("grito_word"): pon(self.ta(s["grito_word"], e), "pop", .8)
            if s.get("crono_word"):
                x = self.ta(s["crono_word"], e)
                for j in range(10): self.sfx(TI.f_de_t(x + j * .12), "tic", .6)
        if tp == "buzo":
            rb = np.random.default_rng(5); x = e["t0"] + .3
            while x < (e.get("t1") or x + 3) - .3: self.sfx(TI.f_de_t(x), "burbuja", .6 + .4 * rb.random()); x += .35 + .5 * rb.random()
            if s.get("cuenta_word"):
                for k in range(len(s.get("cuenta", []))): self.sfx(TI.f_de_t(self.ta(s["cuenta_word"], e) + k * 1.1), "tac", 1.0)

    V.e_cara = e_cara; V.e_crono = e_crono; V.e_cerebro = e_cerebro; V.e_cama = e_cama; V.e_buzo = e_buzo
    for k in ("cara", "crono", "cerebro", "cama", "buzo"): setattr(V, "efectos_" + k, efectos_tiempo)
