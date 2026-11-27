"""Escenas cotidianas de la variante vertical (documental 09): ojo, reloj de 24 h, batería y despertador digital.

ojo      parpado [{word, v (0 cerrado … 1 abierto), dur?}], movil_word (reflejo del móvil en la pupila), rojo_word (venitas rojas,
         ojeras), dormir_word (ojo cerrado en calma + «z» que suben), titulos [{word, txt, sub}]. Parpadea solo y cabecea de sueño.
reloj    esfera de 24 h: noche [desde, hasta] (estrellas y luna), porciones [{word, desde, hasta, txt, col, extra?: [d, h], ya?}],
         aguja [{word, h, dur?}] (tic-tac al moverse), tuyas {word, desde, hasta, txt, ya?} (porción dorada), atenuar_word,
         mover {word, desde, hasta} (la porción dorada viaja a otra hora del día).
bateria  etiqueta, niveles [{word, v %, hora "HH:MM", dur?}] (líquido con ola y burbujas; color según nivel), aviso_word (batería
         baja que parpadea), ayer {word, txt}.
digital  horas [{word, h "HH:MM", dur?}] (dígitos de 7 segmentos que corren), alarma_word (parpadeo + pitidos); móvil encendido en la cama.
Efectos propios: tic-tac, bajada/subida de batería con rodillo, bip de batería baja, clac de dígitos, alarma, vibración, parpadeo, «z».
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]
    CY = 700.0
    ORO, ORO2 = "#F2C14E", "#FFE7A3"

    # ---------------------------------------------------------------- sonidos
    def _tono(f0, d, dc, arm=((1, 1),), ataque=.003):
        def s():
            n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
            for m, a in arm: x += a * np.sin(2 * np.pi * f0 * m * t)
            return x * np.exp(-t / dc) * np.minimum(1, t / ataque)
        return s
    def s_bajada():
        d = .7; n = int(d * AU.SR); u = np.linspace(0, 1, n); f = 900 - 620 * u ** .8
        return np.sin(2 * np.pi * np.cumsum(f) / AU.SR) * np.sin(np.pi * u) ** 1.3
    def s_alarma():
        d = 1.1; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for k in range(4):
            a = int(k * .26 * AU.SR); m = min(n - a, int(.14 * AU.SR)); tt = np.arange(m) / AU.SR
            x[a:a + m] += (np.sin(2 * np.pi * 2093 * tt) + .3 * np.sin(2 * np.pi * 4186 * tt)) * np.minimum(1, tt / .004) * np.minimum(1, (.14 - tt) / .01)
        return x
    def s_vibra():
        d = .62; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for t0 in (0, .34):
            a = int(t0 * AU.SR); m = min(n - a, int(.24 * AU.SR)); tt = np.arange(m) / AU.SR
            x[a:a + m] += np.sign(np.sin(2 * np.pi * 165 * tt)) * .6 * np.sin(np.pi * tt / .24) ** .5
        return AU._bajos(x, 900)
    def s_parpadeo():
        d = .16; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 51), 500, 2500) * np.sin(np.pi * u) ** 2
    def s_zzz():
        d = 1.2; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        f = 220 + 25 * np.sin(2 * np.pi * 1.2 * t)
        return (np.sin(2 * np.pi * np.cumsum(f) / AU.SR) + .3 * np.sin(4 * np.pi * np.cumsum(f) / AU.SR)) * np.sin(np.pi * t / d) ** 2
    for nom, fn, db in (("tac", _tono(1250, .035, .007), -31), ("bip", _tono(1568, .16, .05, ((1, 1), (2, .25))), -27), ("bajada", s_bajada, -30),
                        ("alarma", s_alarma, -27), ("vibra", s_vibra, -26), ("parpadeo", s_parpadeo, -33), ("zzz", s_zzz, -31)):
        AU.SFX.setdefault(nom, (fn, db))

    # ---------------------------------------------------------------- utilidades
    def _keys(self, e, ks, campo, t, defecto_dur=.7, conv=float):
        """Interpola valores por palabras clave: [{word, <campo>, dur?}] → valor en t (y si se está moviendo)."""
        v = conv(ks[0][campo]); mov = False
        for k in ks[1:]:
            tk = self.ta(k["word"], e); d = k.get("dur", defecto_dur)
            u = TI.clamp((t - tk) / d)
            if u <= 0: break
            if u < 1: mov = True
            v = v + (conv(k[campo]) - v) * _io(u)
        return v, mov

    def _io(u): return u * u * (3 - 2 * u)
    def _hm(s): h, m = s.split(":"); return int(h) * 60 + int(m)
    def _tt(self, w, e): return -99.0 if w == "@ya" else self.ta(w, e)

    def _titulo(self, c, s, e, t, S, y=300):
        tts = [q for q in s.get("titulos", []) if t >= self.ta(q["word"], e) - .05]
        if not tts: return
        q = tts[-1]; dt = t - self.ta(q["word"], e); a = aparece(dt + .05, .18)
        fk = self.F["keyserif"]; w = ancho(q["txt"], fk); esc = min(1.0, 840 / w) * (.92 + .08 * resorte(dt, 8, 10))
        c.save(); c.translate(CX, y + 16 * (1 - resorte(dt, 8, 10))); c.scale(esc, esc)
        with capa(c, alfa=.5 * a, blur=22): texto(c, q["txt"], 0, 0, fk, "#000000")
        texto(c, q["txt"], 0, 0, fk, "#FFF4E6", alfa=a, sombra=(3, 10, .5)); c.restore()
        if q.get("sub"):
            sub = " ".join(q["sub"]); fs = self.F["etq"]; ws = ancho(sub, fs) * .62
            c.save(); c.translate(CX, y + 92); c.scale(.62, .62); texto(c, sub, 0, 0, fs, ORO, alfa=aparece(dt - .15, .2), sombra=(2, 8, .5)); c.restore()

    # ================================================================ OJO
    def e_ojo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        # piel a pantalla completa (degradado cálido + ojeras abajo, más oscuro donde va el texto)
        sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [color("#5A3A2C"), color("#B07A5A"), color("#9A6450"), color("#3A2630"), color("#140C14")],
                                            [0, .22, .5, .66, .8])
        c.drawRect(skia.Rect(-60, -60, W + 60, H + 60), skia.Paint(Shader=sh))
        rng = np.random.default_rng(3)
        poros = skia.Path()
        for _ in range(700): poros.addCircle(float(rng.random() * W), float(rng.random() * 1250), float(.6 + rng.random() * 1.4))
        c.drawPath(poros, relleno("#3A2418", .10))
        v, _ = _keys(self, e, s["parpado"], "v", t)
        ur = TI.cubic_out(TI.clamp((t - self.ta(s["rojo_word"], e)) / .5)) if s.get("rojo_word") else 0
        dormir = s.get("dormir_word") and t > self.ta(s["dormir_word"], e)
        # cabeceo de sueño y parpadeos automáticos
        if v < .8 and not dormir: v = max(0, v + .05 * math.sin(t * 1.7))
        if v > .35 and not dormir:
            ph = (t + .7) % 3.4
            if ph < .16: v *= abs(math.cos(math.pi * ph / .16))
        cx, cy = CX, CY + 90
        up = 60 - 430 * v ** .8; lo = 60 + 190 * TI.clamp(v * 2.4); hw = 405
        # ceja (se levanta al abrir)
        by = cy - 330 - 40 * v
        ceja = skia.Path(); ceja.moveTo(cx - 470, by + 60); ceja.cubicTo(cx - 250, by - 40, cx + 150, by - 60, cx + 470, by + 10)
        for k in range(26):
            o = (k - 13) * 2.2
            c.save(); c.translate(o * .7, o); c.drawPath(ceja, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.5, Color=color("#1E120C", .5))); c.restore()
        # ojera
        c.drawOval(skia.Rect(cx - 380, cy + 150, cx + 380, cy + 420), skia.Paint(AntiAlias=True, Color=color("#4A2450", .25 + .35 * ur),
                                                                                  MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 50)))
        # pliegue del párpado
        pl = skia.Path(); pl.moveTo(cx - hw, cy); pl.quadTo(cx, cy - 470, cx + hw, cy)
        c.drawPath(pl, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=14, Color=color("#3A2016", .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
        ojo = skia.Path(); ojo.moveTo(cx - hw, cy); ojo.quadTo(cx, cy + up * 2, cx + hw, cy); ojo.quadTo(cx, cy + lo * 2 - 0, cx - hw, cy); ojo.close()
        if up < lo - 4:
            c.save(); c.clipPath(ojo, doAntiAlias=True)
            c.drawRect(skia.Rect(cx - hw, cy - 450, cx + hw, cy + 450), skia.Paint(Shader=skia.GradientShader.MakeRadial((cx, cy), 460, [color("#FFF8F2"), color("#F2D6CC"), color("#D9A9A0")], [0, .6, 1])))
            if ur > 0:   # venitas
                vr = np.random.default_rng(7); pv = skia.Path()
                for k in range(16):
                    sx = -1 if k % 2 else 1; x0 = cx + sx * hw * .98; y0 = cy + (vr.random() - .5) * 120; pv.moveTo(x0, y0)
                    x, y = x0, y0
                    for _ in range(4):
                        x -= sx * (40 + 50 * vr.random()); y += (vr.random() - .5) * 60; pv.lineTo(x, y)
                c.drawPath(pv, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color=color("#C8242A", .8 * ur)))
            ix, iy, R = cx + 10 * math.sin(t * .6), cy + 15, 205
            c.drawCircle(ix, iy, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((ix, iy), R, [color("#3A2410"), color("#9A6A2A"), color("#C8923E"), color("#5A3814")], [0, .4, .8, 1])))
            fib = skia.Path(); fr = np.random.default_rng(5)
            for k in range(150):
                a = 2 * math.pi * k / 150 + fr.random() * .03; r0 = 90 + 10 * fr.random(); r1 = R * (.75 + .25 * fr.random())
                fib.moveTo(ix + r0 * math.cos(a), iy + r0 * math.sin(a)); fib.lineTo(ix + r1 * math.cos(a), iy + r1 * math.sin(a))
            c.drawPath(fib, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6, Color=color("#F7D29A", .35)))
            c.drawCircle(ix, iy, R, trazo("#2A1606", 10, .9))
            pr = 88 - 10 * ur
            c.drawCircle(ix, iy, pr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((ix - 20, iy - 20), pr, [color("#1A1A22"), color("#050508")])))
            c.drawOval(skia.Rect(ix - 140, iy - 100, ix - 70, iy - 58), relleno("#FFFFFF", .75))
            if s.get("movil_word") and t > self.ta(s["movil_word"], e) - .01:
                am = aparece(t - self.ta(s["movil_word"], e), .3); fl = .85 + .15 * math.sin(t * 7.3) * math.sin(t * 2.1)
                c.save(); c.translate(ix + 85, iy - 85); c.rotate(14)
                c.drawRRect(rrc(0, 0, 74, 128, 12), skia.Paint(AntiAlias=True, Color=color("#A8E8FF", .35 * am * fl), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
                c.drawRRect(rrc(0, 0, 74, 128, 12), relleno("#1A1626", .95 * am))
                scr = skia.GradientShader.MakeLinear([(0, -55), (0, 55)], [color("#9B7BE0", am), color("#7FE3F0", am), color("#E0749B", am)], [0, (t * .4) % 1, 1])
                c.drawRRect(rrc(0, 0, 62, 114, 8), skia.Paint(AntiAlias=True, Shader=scr, Alphaf=fl))
                for k in range(3): c.drawRRect(rrc(-8, -36 + k * 30 - (t * 40) % 30, 40, 6, 3), relleno("#FFFFFF", .6 * am))
                c.restore()
            # sombra del párpado sobre el globo
            c.drawPath(ojo, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=60, Color=color("#3A1E16", .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20)))
            c.restore()
        # pestañas superiores (siguen la curva del párpado)
        def bez(u, ctrl):
            x = (1 - u) ** 2 * (cx - hw) + 2 * (1 - u) * u * cx + u * u * (cx + hw)
            y = (1 - u) ** 2 * cy + 2 * (1 - u) * u * (cy + ctrl * 2) + u * u * cy
            return x, y
        pest = skia.Path()
        for k in range(58):
            u = .04 + .92 * k / 57; x, y = bez(u, up); dirx = (u - .5) * 1.6
            L = 70 + 35 * math.sin(math.pi * u)
            if dormir or v < .08:
                pest.moveTo(x, y); pest.quadTo(x + dirx * 20, y + L * .5, x + dirx * 40, y + L * .85)
            else:
                pest.moveTo(x, y); pest.quadTo(x + dirx * 25, y - L * .6, x + dirx * 55 + 8, y - L)
        c.drawPath(pest, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4, Color=color("#120A08"), StrokeCap=skia.Paint.kRound_Cap))
        c.drawPath(_curva(cx, cy, hw, up), trazo("#1A0E0A", 7, .95))
        if up < lo - 4:
            inf = skia.Path()
            for k in range(30):
                u = .1 + .8 * k / 29; x, y = bez(u, lo); inf.moveTo(x, y + 4); inf.lineTo(x + (u - .5) * 14, y + 22)
            c.drawPath(inf, trazo("#2A1812", 2, .7)); c.drawPath(_curva(cx, cy, hw, lo), trazo("#8A5A4A", 3, .6))
        if dormir:
            dz = t - self.ta(s["dormir_word"], e)
            for k in range(3):
                ph = (dz * .45 + k / 3) % 1; a = math.sin(math.pi * ph) * aparece(dz - .3, .4)
                fz = fuente("Inter", 800, int(60 + 50 * ph)); texto(c, "z", cx + 200 + 120 * ph + 30 * math.sin(ph * 6), cy - 200 - 380 * ph, fz, "#FFF4E6", alfa=a, sombra=(2, 8, .4))
        _titulo(self, c, s, e, t, S, y=230)

    def _curva(cx, cy, hw, ctrl):
        p = skia.Path(); p.moveTo(cx - hw, cy); p.quadTo(cx, cy + ctrl * 2, cx + hw, cy); return p

    # ================================================================ RELOJ 24 h
    def _ang(h): return -90 + h * 15

    def _cuña(c, cx, cy, r0, r1, h0, h1, paint):
        if h1 - h0 <= 1e-3: return
        a0, a1 = _ang(h0), _ang(h1); p = skia.Path()
        p.arcTo(skia.Rect(cx - r1, cy - r1, cx + r1, cy + r1), a0, a1 - a0, True)
        p.arcTo(skia.Rect(cx - r0, cy - r0, cx + r0, cy + r0), a1, a0 - a1, False); p.close()
        c.drawPath(p, paint); return p

    def e_reloj(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        sc = .86 + .14 * resorte(dt0 + .05, 7, 9) + .006 * math.sin(t * 1.3)
        cx, cy, R = CX, CY, 380 * sc
        ua = TI.cubic_out(TI.clamp((t - self.ta(s["atenuar_word"], e)) / .5)) if s.get("atenuar_word") else 0
        # sombra y bisel dorado
        c.drawCircle(cx, cy + 26, R + 46, skia.Paint(AntiAlias=True, Color=color("#000000", .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
        c.drawCircle(cx, cy, R + 44, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeSweep(cx, cy, [color(x) for x in ("#B8893E", "#F7DFA0", "#9A6E2A", "#E9C77A", "#B8893E")])))
        c.drawCircle(cx, cy, R + 14, relleno("#6E4E1E", .6))
        c.drawCircle(cx, cy, R + 10, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx - 80, cy - 120), R * 1.3, [color("#F6EEDC"), color("#D9CCB0")])))
        # noche
        n0, n1 = s.get("noche", [0, 7])
        pn = _cuña(c, cx, cy, 78 * sc, R - 6, n0, n1, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx + 120, cy - 160), R, [color("#2A3A8A"), color("#101A4A")])))
        if pn:
            c.save(); c.clipPath(pn, doAntiAlias=True); rr = np.random.default_rng(4)
            for k in range(46):
                a = math.radians(_ang(n0 + (n1 - n0) * rr.random())); r = (110 + (R - 130) * rr.random())
                tw = .5 + .5 * math.sin(t * (2 + 3 * rr.random()) + k)
                c.drawCircle(cx + r * math.cos(a), cy + r * math.sin(a), 1.5 + 2.5 * rr.random(), relleno("#FFFFFF", .35 + .55 * tw))
            am = math.radians(_ang((n0 + n1) / 2)); mx, my = cx + .62 * R * math.cos(am), cy + .62 * R * math.sin(am)
            c.drawCircle(mx, my, 70, skia.Paint(AntiAlias=True, Color=color("#FFF2C8", .25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
            c.drawCircle(mx, my, 44, relleno("#FFF2C8")); c.drawCircle(mx + 20, my - 12, 40, relleno("#16226A"))
            c.restore()
        # porciones
        etqs = []
        for q in s.get("porciones", []):
            tq = -99 if q.get("ya") else self.ta(q["word"], e); dq = t - tq
            if dq <= -.02: continue
            u = TI.cubic_out(TI.clamp(dq / .45)); al = 1 - .62 * ua
            for (d, hh) in [(q["desde"], q["hasta"])] + ([tuple(q["extra"])] if q.get("extra") else []):
                h1 = d + (hh - d) * u; r1 = (R - 6) * (.9 + .1 * resorte(dq, 9, 12))
                sh = skia.GradientShader.MakeRadial((cx, cy), R, [color(q["col"], al), color(_osc(q["col"]), al)], [.25, 1])
                p = _cuña(c, cx, cy, 78 * sc, r1, d, h1, skia.Paint(AntiAlias=True, Shader=sh))
                if p is not None and u > .2: c.drawPath(p, trazo("#FFFFFF", 3, .55 * al))
            if q.get("txt") and dq > .1:
                am = math.radians(_ang((q["desde"] + q["hasta"]) / 2)); rr_ = .64 * R if q["hasta"] - q["desde"] > 1.5 else .86 * R
                etqs.append((q["txt"], cx + rr_ * math.cos(am), cy + rr_ * math.sin(am), q["col"], aparece(dq - .1, .15) * (1 - ua)))
        # porción dorada (tuyas), que puede viajar
        tu = s.get("tuyas")
        if tu:
            tq = -99 if tu.get("ya") else self.ta(tu["word"], e); dq = t - tq
            if dq > -.02:
                d, hh = tu["desde"], tu["hasta"]
                mv = s.get("mover")
                if mv:
                    um = _io(TI.clamp((t - self.ta(mv["word"], e)) / 1.1)); d = d + (mv["desde"] - d) * um; hh = hh + (mv["hasta"] - hh) * um
                u = TI.cubic_out(TI.clamp(dq / .45)); h1 = d + (hh - d) * u
                pop = 26 * ua + 14 * (_io(TI.clamp((t - self.ta(mv["word"], e)) / 1.1)) if mv else 0); am = math.radians(_ang((d + hh) / 2))
                ox, oy = pop * math.cos(am), pop * math.sin(am)
                pul = .5 + .5 * math.sin(t * 4)
                c.save(); c.translate(ox, oy)
                sh = skia.GradientShader.MakeRadial((cx + .6 * R * math.cos(am), cy + .6 * R * math.sin(am)), R * .7, [color("#FFF0A8"), color("#F2B630"), color("#B8801A")], [0, .5, 1])
                p = _cuña(c, cx, cy, 78 * sc, (R - 6) * (1 + .03 * ua), d, h1, skia.Paint(AntiAlias=True, Shader=sh))
                if p is not None:
                    c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=16, Color=color(ORO2, .25 + .25 * pul),
                                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
                    c.drawPath(p, trazo("#FFF6D0", 3, .9))
                c.restore()
                if tu.get("txt") and dq > .15:
                    fk = fuente("Inter", 900, 96); a = aparece(dq - .15, .15); s2 = .7 + .3 * resorte(dq - .15, 8, 10)
                    yy = cy - R - 105
                    c.save(); c.translate(cx, yy); c.scale(s2, s2)
                    r_ = rrc(0, 4, ancho(tu["txt"], fk) + 80, 140, 34); c.drawRRect(r_, relleno("#141B33", .82 * a)); c.drawRRect(r_, trazo(ORO, 2, .5 * a))
                    with capa(c, alfa=.6 * a, blur=18): texto(c, tu["txt"], 0, 0, fk, ORO)
                    texto(c, tu["txt"], 0, 0, fk, "#FFD45C", alfa=a); c.restore()
        # marcas de horas
        for h in range(24):
            a = math.radians(_ang(h)); big = h % 6 == 0; r0 = R - (34 if big else 20)
            c.drawLine(cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + (R - 4) * math.cos(a), cy + (R - 4) * math.sin(a), trazo("#2A1E10", 6 if big else 3, .85))
        # aguja
        if s.get("aguja"):
            h, _ = _keys(self, e, s["aguja"], "h", t, 1.0)
            a = math.radians(_ang(h)); L = R - 40
            sh = skia.Path(); sh.moveTo(cx - 14 * math.sin(-a) * 0 + 12 * math.cos(a + math.pi / 2), cy + 12 * math.sin(a + math.pi / 2))
            ag = skia.Path(); ag.moveTo(cx + 13 * math.cos(a + math.pi / 2), cy + 13 * math.sin(a + math.pi / 2)); ag.lineTo(cx + L * math.cos(a), cy + L * math.sin(a))
            ag.lineTo(cx + 13 * math.cos(a - math.pi / 2), cy + 13 * math.sin(a - math.pi / 2)); ag.lineTo(cx - 40 * math.cos(a), cy - 40 * math.sin(a)); ag.close()
            c.save(); c.translate(6, 10); c.drawPath(ag, skia.Paint(AntiAlias=True, Color=color("#000000", .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))); c.restore()
            c.drawPath(ag, relleno("#1E1A16"))
            c.drawLine(cx + (L - 60) * math.cos(a), cy + (L - 60) * math.sin(a), cx + L * math.cos(a), cy + L * math.sin(a), skia.Paint(AntiAlias=True, StrokeWidth=9, Color=color("#E5322D"), StrokeCap=skia.Paint.kRound_Cap))
        c.drawCircle(cx, cy, 78 * sc, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx - 20, cy - 20), 80 * sc, [color("#FBF4E2"), color("#D8CBB0")])))
        c.drawCircle(cx, cy, 24, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx - 7, cy - 7), 26, [color("#FFF0C0"), color("#A87A2A")])))
        for txt, x, y, col, a in etqs:
            if a > 0: self.pildora(c, txt, x, y, S, a, fnt=self.F["pillb"], fondo="#0B1430", col=_cla(col))
        _titulo(self, c, s, e, t, S, y=210)

    def _osc(hx):
        v = [int(hx[i:i + 2], 16) for i in (1, 3, 5)]; return "#" + "".join(f"{int(x * .62):02X}" for x in v)
    def _cla(hx):
        v = [int(hx[i:i + 2], 16) for i in (1, 3, 5)]; return "#" + "".join(f"{int(x + (255 - x) * .45):02X}" for x in v)

    # ================================================================ BATERÍA
    def e_bateria(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ks = s["niveles"]; v, mov = _keys(self, e, ks, "v", t, 1.2)
        hm, _ = _keys(self, e, [dict(k, m=_hm(k["hora"])) for k in ks], "m", t, 1.2)
        aw = s.get("aviso_word"); aviso = aw and t > self.ta(aw, e)
        col = "#EF4444" if v < 15 else ("#F5B83D" if v < 60 else "#34D399")
        sc = .9 + .1 * resorte(dt0 + .05, 7, 9); cx, cy, bw, bh = CX, CY + 20, 430 * sc, 760 * sc
        # resplandor del color
        c.drawOval(skia.Rect(cx - 360, cy + bh / 2 - 80, cx + 360, cy + bh / 2 + 170), skia.Paint(AntiAlias=True, Color=color(col, .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 60)))
        c.drawRRect(rrc(cx, cy - bh / 2 - 30, 180 * sc, 70, 16), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(cx - 90, 0), (cx + 90, 0)], [color("#6E737C"), color("#D8DCE2"), color("#7E838C")], [0, .45, 1])))
        cuerpo = rrc(cx, cy, bw, bh, 70 * sc)
        c.drawRRect(cuerpo.makeOffset(0, 18) if hasattr(cuerpo, "makeOffset") else cuerpo, skia.Paint(AntiAlias=True, Color=color("#000000", .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
        c.drawRRect(cuerpo, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(cx - bw / 2, 0), (cx + bw / 2, 0)], [color("#2A2D34"), color("#16181D"), color("#22252C")])))
        iw, ih = bw - 56, bh - 56; inner = rrc(cx, cy, iw, ih, 48 * sc)
        c.drawRRect(inner, relleno("#0D0E12", .9))
        # líquido con ola y burbujas
        lvl = cy + ih / 2 - ih * max(0.0, v) / 100
        c.save(); c.clipRRect(inner, doAntiAlias=True)
        ola = skia.Path(); ola.moveTo(cx - iw / 2, cy + ih / 2 + 5)
        amp = 6 + (10 if mov else 0)
        for k in range(0, 41):
            x = cx - iw / 2 + iw * k / 40; ola.lineTo(x, lvl + amp * math.sin(k * .5 + t * 4.2) * .6 + 3 * math.sin(k * 1.3 - t * 3))
        ola.lineTo(cx + iw / 2, cy + ih / 2 + 5); ola.close()
        c.drawPath(ola, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, lvl), (0, cy + ih / 2)], [color(_cla(col)), color(col), color(_osc(col))], [0, .3, 1])))
        rb = np.random.default_rng(12)
        for k in range(18):
            per = 1.6 + 2 * rb.random(); ph = ((t + rb.random() * per) % per) / per; by = cy + ih / 2 - (cy + ih / 2 - lvl) * ph
            if by > lvl + 6: c.drawCircle(cx - iw / 2 + 30 + (iw - 60) * rb.random() + 6 * math.sin(t * 3 + k), by, 3 + 6 * rb.random(), relleno("#FFFFFF", .35 * (1 - ph)))
        c.restore()
        # brillo de cristal
        c.drawRRect(rrc(cx - iw / 2 + 34, cy - 40, 22, ih * .6, 11), relleno("#FFFFFF", .10))
        if aviso:
            bl = .5 + .5 * math.cos((t - self.ta(aw, e)) * 2 * math.pi * 1.6)
            c.drawRRect(cuerpo, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Color=color("#EF4444", .9 * bl)))
        else: c.drawRRect(cuerpo, trazo("#8A8F99", 3, .7))
        # cifra, etiqueta y hora
        txt = f"{int(round(v))}%"; fk = fuente("Inter", 900, 160)
        if ancho(txt, fk) > iw - 50: fk = fuente("Inter", 900, int(160 * (iw - 50) / ancho(txt, fk)))
        texto(c, txt, cx, cy - 60, fk, "#FFFFFF", tnum=True, sombra=(4, 14, .5))
        if s.get("etiqueta"):
            fe = self.F["etq"]; w_ = ancho(s["etiqueta"], fe) + 60; r_ = rrc(cx, cy + 90, w_, 82, 18)
            c.drawRRect(r_, relleno("#0B0C10", .85)); c.drawRRect(r_, trazo("#FFFFFF", 2.5, .7)); texto(c, s["etiqueta"], cx, cy + 90, fe, "#FFFFFF")
        fh = fuente("Inter", 800, 88); hs = f"{int(hm) // 60 % 24:02d}:{int(hm) % 60:02d}"; r_ = rrc(cx, cy + 230, 300, 116, 26)
        c.drawRRect(r_, relleno("#0B0C10", .9));
        with capa(c, alfa=.5, blur=14): texto(c, hs, cx, cy + 230, fh, "#FFD98A", tnum=True)
        texto(c, hs, cx, cy + 230, fh, "#FFE6A8", tnum=True)
        if s.get("ayer"):
            dy = t - self.ta(s["ayer"]["word"], e)
            if dy > 0:
                a = aparece(dy, .15)
                self.pildora(c, s["ayer"]["txt"], cx, cy - ih / 2 + 70 - 16 * (1 - resorte(dy, 9, 12)), S, a, fnt=self.F["item"], fondo="#0B0C10")

    # ================================================================ DESPERTADOR DIGITAL
    SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcfgd"}

    def _digito(c, ch, x, y, w, h, on, off):
        g = 16; L = {"a": (x + g, y, x + w - g, y), "d": (x + g, y + h, x + w - g, y + h), "g": (x + g, y + h / 2, x + w - g, y + h / 2),
                     "f": (x, y + g, x, y + h / 2 - g), "b": (x + w, y + g, x + w, y + h / 2 - g), "e": (x, y + h / 2 + g, x, y + h - g), "c": (x + w, y + h / 2 + g, x + w, y + h - g)}
        for k, (x0, y0, x1, y1) in L.items():
            c.drawLine(x0, y0, x1, y1, on if k in SEG.get(ch, "") else off)

    def e_digital(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ks = s["horas"]; m = _hm(ks[0]["h"])
        for k in ks[1:]:
            tk = self.ta(k["word"], e); u = TI.clamp((t - tk) / k.get("dur", 1.0))
            if u <= 0: break
            dm = (_hm(k["h"]) - m) % 1440; m = m + dm * _io(u)
            if u >= 1: m = _hm(k["h"])
        hs = f"{int(m) // 60 % 24:02d}{int(m) % 60:02d}"
        al = s.get("alarma_word"); ta_ = self.ta(al, e) if al else 1e9
        blink = 1.0 if t < ta_ + .8 else (1.0 if int((t - ta_) * 4) % 2 == 0 else .25)
        shake = 6 * math.sin(t * 60) * TI.clamp(1 - abs(t - ta_ - 1.2) / .6) if t > ta_ + .6 else 0
        # habitación: ventana y mesilla
        c.drawRect(skia.Rect(60, 140, 420, 640), trazo("#5A6AB8", 6, .18)); c.drawLine(240, 140, 240, 640, trazo("#5A6AB8", 6, .18)); c.drawLine(60, 390, 420, 390, trazo("#5A6AB8", 6, .18))
        c.drawRect(skia.Rect(-20, 760, W + 20, 800), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 760), (0, 800)], [color("#5A3A26"), color("#2A1A10")])))
        # cama
        cama = skia.Path(); cama.moveTo(-40, 1220); cama.cubicTo(200, 960, 800, 940, W + 40, 1060); cama.lineTo(W + 40, H + 40); cama.lineTo(-40, H + 40); cama.close()
        c.drawPath(cama, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 950), (0, 1500)], [color("#3D5BC8"), color("#16245A"), color("#070B1E")], [0, .45, 1])))
        for k in range(3): c.drawLine(80 + k * 300, 1150 + k * 20, 330 + k * 300, 1110 + k * 20, trazo("#0E1840", 10, .5))
        # móvil encendido sobre la cama
        px, py = CX, 1040; fl = .8 + .2 * math.sin(t * 5.1) * math.sin(t * 1.7)
        c.drawOval(skia.Rect(px - 330, py - 160, px + 330, py + 160), skia.Paint(AntiAlias=True, Color=color("#C9A8FF", .28 * fl), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 60)))
        c.save(); c.translate(px, py); c.rotate(-6)
        c.drawRRect(rrc(0, 0, 400, 200, 34), relleno("#1A1A22")); c.drawRRect(rrc(0, 0, 400, 200, 34), trazo("#8A8FA0", 3, .8))
        c.save(); c.clipRRect(rrc(0, 0, 376, 176, 24), doAntiAlias=True)
        off = (t * 160) % 376
        for k in range(-1, 3):
            x0 = -188 + k * 188 - off % 188
            hue = ["#E0749B", "#7FE3F0", "#9B7BE0", "#F5B83D"][(k + int(t * 160 // 188)) % 4]
            c.drawRect(skia.Rect(x0, -90, x0 + 186, 90), skia.Paint(Shader=skia.GradientShader.MakeRadial((x0 + 93, 0), 140, [color("#FFFFFF", .9), color(hue)], [0, .6])))
        c.restore()
        texto(c, f"{hs[:2]}:{hs[2:]}", 150, -50, self.F["mini"], "#FFFFFF", alfa=.9); c.restore()
        # reloj
        c.save(); c.translate(shake, 0)
        caja = rrc(CX, 600, 840, 330, 54)
        c.drawRRect(caja.makeOffset(0, 18) if hasattr(caja, "makeOffset") else caja, skia.Paint(AntiAlias=True, Color=color("#000000", .55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
        c.drawRRect(caja, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 435), (0, 765)], [color("#3A3D46"), color("#1A1C22")])))
        c.drawRRect(caja, trazo("#6A6F7C", 3, .7)); c.drawRRect(rrc(CX, 600, 760, 260, 30), relleno("#120607"))
        on = skia.Paint(AntiAlias=True, StrokeWidth=22, Color=color("#FF3B2E", blink), StrokeCap=skia.Paint.kRound_Cap)
        glow = skia.Paint(AntiAlias=True, StrokeWidth=40, Color=color("#FF3B2E", .35 * blink), StrokeCap=skia.Paint.kRound_Cap, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        off_ = skia.Paint(AntiAlias=True, StrokeWidth=22, Color=color("#3A0A08", .55), StrokeCap=skia.Paint.kRound_Cap)
        xs = [CX - 330, CX - 175, CX + 45, CX + 200]
        for pnt, of in ((glow, None), (on, off_)):
            for ch, x in zip(hs, xs):
                _digito(c, ch, x, 500, 110, 200, pnt, of if of is not None else skia.Paint(Color=0))
        for yy in (560, 640): c.drawCircle(CX - 32, yy, 13, relleno("#FF3B2E", blink))
        c.restore()
        if s.get("tachar_word"):                                         # aspa roja que se traza sobre el reloj
            u = TI.clamp((t - self.ta(s["tachar_word"], e)) / .45)
            if u > 0:
                p_ = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=30, Color=color("#E5322D"), StrokeCap=skia.Paint.kRound_Cap)
                g_ = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=60, Color=color("#E5322D", .35), StrokeCap=skia.Paint.kRound_Cap,
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16))
                u1, u2 = TI.cubic_out(TI.clamp(u * 2)), TI.cubic_out(TI.clamp(u * 2 - 1))
                for pp in (g_, p_):
                    c.drawLine(CX - 360, 420, CX - 360 + 720 * u1, 420 + 360 * u1, pp)
                    if u2 > 0: c.drawLine(CX + 360, 420, CX + 360 - 720 * u2, 420 + 360 * u2, pp)
        _titulo(self, c, s, e, t, S, y=250)

    # ---------------------------------------------------------------- efectos
    def efectos_cotidianas(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]
        if tp == "ojo":
            ks = s["parpado"]
            for k in ks[1:]: pon(self.ta(k["word"], e), "parpadeo", .9)
            if s.get("movil_word"): self.sfx(TI.f_de_t(max(0, self.ta(s["movil_word"], e) + .05)), "vibra", .9)
            if s.get("rojo_word"): self.sfx(TI.f_de_t(self.ta(s["rojo_word"], e) + .02), "golpe", .7)
            if s.get("dormir_word"): self.sfx(TI.f_de_t(self.ta(s["dormir_word"], e) + .6), "zzz", 1.0)
            for q in s.get("titulos", []): pon(self.ta(q["word"], e), "destello", .5)
        if tp == "reloj":
            for k, q in enumerate(s.get("porciones", [])):
                if not q.get("ya"): self.sfx(TI.f_de_t(self.ta(q["word"], e) + .03), f"rama{min(10, 2 + 2 * k)}", .9)
            tu = s.get("tuyas")
            if tu and not tu.get("ya"): pon(self.ta(tu["word"], e) + .08, "destello", .9); self.sfx(TI.f_de_t(self.ta(tu["word"], e) + .2), "campana", .6)
            if s.get("atenuar_word"): pon(self.ta(s["atenuar_word"], e), "whoosh", .5)
            if s.get("mover"): pon(self.ta(s["mover"]["word"], e), "subida", .9); self.sfx(TI.f_de_t(self.ta(s["mover"]["word"], e) + 1.15), "destello", .7)
            ks = s.get("aguja", [])
            for k in ks[1:]:
                tk = self.ta(k["word"], e); d = k.get("dur", 1.0); j = 0; x = tk + .02
                while x < tk + d:
                    self.sfx(TI.f_de_t(x), "tic" if j % 2 == 0 else "tac", .8); x += .13; j += 1
        if tp == "bateria":
            ks = s["niveles"]
            for k in ks[1:]:
                tk = self.ta(k["word"], e); d = k.get("dur", 1.2); sube = k["v"] > 0 and ks[ks.index(k) - 1]["v"] < k["v"]
                self.sfx(TI.f_de_t(tk), "subida" if sube else "bajada", 1.0); self.rodillo(tk, d)
            if s.get("aviso_word"):
                for j in range(3): self.sfx(TI.f_de_t(self.ta(s["aviso_word"], e) + j * .62), "bip", .9)
            if s.get("ayer"): pon(self.ta(s["ayer"]["word"], e), "pop", .5)
        if tp == "digital":
            ks = s["horas"]
            for k in ks[1:]:
                tk = self.ta(k["word"], e); d = k.get("dur", 1.0); x = tk + .02
                while x < tk + d: self.sfx(TI.f_de_t(x), "tic", .6); x += .12
                self.sfx(TI.f_de_t(tk + d + .02), "clac", .8)
            if s.get("alarma_word"): self.sfx(TI.f_de_t(self.ta(s["alarma_word"], e) + .85), "alarma", 1.0)
            if s.get("tachar_word"):
                tx = self.ta(s["tachar_word"], e); self.sfx(TI.f_de_t(tx + .02), "sello", .5); self.sfx(TI.f_de_t(tx + .25), "sello", .5)
            for q in s.get("titulos", []): pon(self.ta(q["word"], e), "pop", .4)
            self.sfx(TI.f_de_t(e["t0"] + .3), "vibra", .6)

    V.e_ojo = e_ojo; V.e_reloj = e_reloj; V.e_bateria = e_bateria; V.e_digital = e_digital
    for k in ("ojo", "reloj", "bateria", "digital"): setattr(V, "efectos_" + k, efectos_cotidianas)
