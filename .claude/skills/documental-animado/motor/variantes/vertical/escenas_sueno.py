"""Escenas del documental 13 («¿Qué pasaría si dejases de dormir a propósito?»).

Comunes a todas (campo `hud` en la escena): {desde, hasta, word, dur} → contador «HORAS DESPIERTO» arriba que rueda, y
PÁRPADOS de cansancio que van cerrando la pantalla según las horas (y parpadeos). `parpados: false` los quita.
insomne     cara ilustrada: ojos [{word, v}], ojeras, palillos_word (palillos que sujetan los párpados), caen_word (se caen y se duerme),
            bolsa_word (bolsa de basura esperando) + bolsa_txt.
calendario  calendario de taco: anio, word (empieza a arrancar hojas) hasta `dias`, dur, sello_txt.
conducir    carretera en perspectiva, coche que hace eses (eses_word), alcoholímetro que sube a valor (word) con label.
neuronas    cerebro de luces: apaga_word (zonas que se apagan), micro_word (la pantalla se va a negro un instante: microsueño).
limpieza    cerebro con residuos: duerme_word (ola azul que limpia), acumula_word (los residuos vuelven y se amontonan).
alucina     habitación a oscuras: la pared respira, el reloj se derrite, sombra_word (silueta en la puerta), ojos_word (ojos en la oscuridad).
recuerdos   cabeza de perfil: fotos que salen y se deshacen (memoria_word), vapor de enfado (enfado_word).
dormir      cama + ventana día/noche que gira + contador de horas de sueño (word, valor_h, valor_m).
capitulo    móvil con «Siguiente episodio en 5…» y dedo que pulsa (pulsa_word).
Efectos: palillos (clac), hojas arrancadas, motor/derrape, glitch, ola, susurro, vapor, latido lento, notificación.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"]
    PIEL = ("#F6D2B4", "#E3A983", "#C98A66")

    # ---------------------------------------------------------------- sonidos
    def s_glitch():
        d = .45; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n); rng = np.random.default_rng(81)
        for k in range(9):
            a = int(rng.random() * (n - 2000)); m = int((.01 + .03 * rng.random()) * AU.SR)
            x[a:a + m] += np.sign(np.sin(2 * np.pi * (200 + 1800 * rng.random()) * t[:m])) * (.5 + .5 * rng.random())
        return AU._banda(x, 150, 6000) * np.exp(-t / .3)
    def s_ola():
        d = 1.0; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 82), 200, 2500) * np.sin(np.pi * u) ** 1.5 * (1 + .4 * np.sin(2 * np.pi * 5 * u))
    def s_susurro():
        d = 1.1; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        x = AU._banda(AU._ruido(n, 83), 2000, 7000) * (.5 + .5 * np.sin(2 * np.pi * 6 * t) ** 2)
        return x * np.sin(np.pi * u) ** 2
    def s_motor():
        d = 1.2; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        f = 70 + 25 * np.sin(2 * np.pi * .8 * t); ph = np.cumsum(f) / AU.SR
        x = AU._bajos(np.sign(np.sin(2 * np.pi * ph)) * .6 + .4 * AU._ruido(n, 84), 900)
        return x * np.sin(np.pi * u) ** .8
    def s_vapor():
        d = .7; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 85), 3000, 9000) * np.sin(np.pi * u) ** .7 * (1 - u) ** .5
    def s_arranca():
        d = .2; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 86), 900, 5000) * (u ** .2) * (1 - u) ** 3 * (1 + np.sign(np.sin(2 * np.pi * 60 * u)) * .3)
    def s_noti():
        d = .35; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for t0, f in ((0, 1318), (.11, 1760)):
            k = int(t0 * AU.SR); tt = t[:n - k]; x[k:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / .08)
        return x
    for nom, fn, db in (("glitch", s_glitch, -26), ("ola", s_ola, -31), ("susurro", s_susurro, -33), ("motor", s_motor, -31),
                        ("vapor", s_vapor, -33), ("arranca", s_arranca, -29), ("noti", s_noti, -27)):
        AU.SFX.setdefault(nom, (fn, db))

    def _io(u): return u * u * (3 - 2 * u)
    def _tw(self, e, w): return self.ta(w, e) if w else 1e9
    def _sombra(c, x, y, rx, ry, a):
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), skia.Paint(AntiAlias=True, Color=color("#000000", a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, ry * .7 + 4)))
    def _piel(y0, y1, a=1.0):
        return skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [color(PIEL[0], a), color(PIEL[1], a), color(PIEL[2], a)])

    # ---------------------------------------------------------------- HUD de horas + párpados (común)
    def horas(self, e, t):
        h = e["spec"].get("hud")
        if not h: return None
        tw = self.ta(h["word"], e) if h.get("word") else e["t0"]; d = h.get("dur", 1.0)
        u = TI.cubic_out(TI.clamp((t - tw) / d)) if t > tw else 0
        return h["desde"] + (h["hasta"] - h["desde"]) * u, (0 < t - tw < d)

    def capa_hud(self, c, e, t, S):
        """Contador «HORA X · DESPIERTO». Si la escena abre un hito (`hud.capitulo`), aparece GRANDE en el centro sobre un velo,
        rueda hasta la nueva hora y vuela a su sitio arriba. (Sin párpados: el usuario no los quiere.)"""
        r = horas(self, e, t)
        if r is None: return
        hv, rodando = r; h = e["spec"]["hud"]; dt0 = t - e["t0"]
        x0, y0, sc = CX, 205, 1.0
        if h.get("capitulo"):
            uf = _io(TI.clamp((dt0 - h.get("grande", 1.0)) / .45))
            if uf < 1:
                c.drawRect(skia.Rect(-60, -60, W + 60, 1240), relleno("#05060E", .62 * (1 - uf)))
            x0, y0, sc = CX, 650 + (205 - 650) * uf, 2.3 + (1 - 2.3) * uf
            if uf < 1:
                sc *= .85 + .15 * resorte(dt0 + .05, 8, 11)
        a = aparece(dt0 + .05, .15); txt = f"{int(round(hv))} H"
        f1 = fuente("Inter", 800, 44); f2 = fuente("Inter", 700, 24)
        c.save(); c.translate(x0, y0); c.scale(sc, sc)
        w = 330; col = "#FF6A5A" if hv >= 17 else "#9DB8FF"
        c.drawRRect(rrc(0, 0, w, 92, 46), relleno("#0B0B14", .88 * a)); c.drawRRect(rrc(0, 0, w, 92, 46), trazo(col, 2.5, .9 * a))
        if rodando:
            with capa(c, modo=skia.BlendMode.kPlus): c.drawRRect(rrc(0, 0, w + 10, 102, 51), skia.Paint(AntiAlias=True, Color=color(col, .25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        ix = -w / 2 + 50
        c.drawCircle(ix, 0, 24, trazo("#FFFFFF", 3.5, a)); ang = t * (14 if rodando else 3)
        c.drawLine(ix, 0, ix + 15 * math.cos(ang), 15 * math.sin(ang), trazo("#FFFFFF", 3.5, a)); c.drawLine(ix, 0, ix + 10 * math.cos(ang / 12), 10 * math.sin(ang / 12), trazo("#FFFFFF", 4, a))
        with capa(c, alfa=a, blur=(3 if rodando else 0)): texto(c, txt, 30, -14, f1, "#FF6A5A" if hv >= 17 else "#FFFFFF", tnum=True)
        texto(c, "DESPIERTO", 30, 24, f2, "#C9D3EA", alfa=a)
        c.restore()

    # ---------------------------------------------------------------- cara ilustrada
    def _cara(c, x, y, s, t, ojos=1.0, ojeras=0.0, enfado=0.0, palillos=0.0, venas=0.0, caen=0.0, a=1.0, mirar=0.0, sudor=0.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        _sombra(c, 0, 300, 230, 30, .3 * a)
        # cuello y jersey
        c.drawRRect(rrc(0, 250, 150, 140, 40), skia.Paint(AntiAlias=True, Shader=_piel(200, 320, a)))
        c.drawRRect(rrc(0, 360, 420, 160, 80), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 300), (0, 440)], [color("#4F6BD8", a), color("#2C3E9A", a)])))
        # orejas
        for sx in (-1, 1): c.drawOval(skia.Rect(sx * 190 - 34, -30, sx * 190 + 34, 70), skia.Paint(AntiAlias=True, Shader=_piel(-30, 70, a)))
        # cabeza
        c.drawOval(skia.Rect(-190, -230, 190, 240), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-50, -60), 300, [color(PIEL[0], a), color(PIEL[1], a), color(PIEL[2], a)], [0, .6, 1])))
        # pelo despeinado
        pel = skia.Path(); pel.moveTo(-200, -20); pel.cubicTo(-220, -200, -80, -280, 20, -262)
        pel.cubicTo(140, -270, 230, -180, 200, -20); pel.lineTo(170, -110)
        for k in range(9):
            xx = 150 - k * 40; pel.lineTo(xx, -150 - 30 * (k % 2) - 10 * math.sin(t * 2 + k)); pel.lineTo(xx - 20, -120)
        pel.lineTo(-170, -110); pel.close()
        c.drawPath(pel, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -270), (0, -100)], [color("#4A2E1E", a), color("#2A1810", a)])))
        for k in range(3):
            pm = skia.Path(); pm.moveTo(-30 + k * 40, -262); pm.quadTo(-10 + k * 45, -320 - 10 * math.sin(t * 3 + k), 20 + k * 40, -300)
            c.drawPath(pm, trazo("#3A2418", 6, a))
        # ojos
        for sx in (-1, 1):
            ex, ey = sx * 85, -10
            if ojeras > 0:
                c.drawOval(skia.Rect(ex - 70, ey + 18, ex + 70, ey + 70), skia.Paint(AntiAlias=True, Color=color("#6A3A70", .55 * ojeras * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
            ojo = skia.Path(); ojo.addOval(skia.Rect(ex - 58, ey - 40, ex + 58, ey + 40))
            c.save(); c.clipPath(ojo, doAntiAlias=True)
            c.drawRect(skia.Rect(ex - 60, ey - 42, ex + 60, ey + 42), relleno("#FFFFFF", a))
            if venas > 0:
                rv = np.random.default_rng(3 + sx); pv = skia.Path()
                for k in range(8):
                    x0 = ex + sx * 58 * (1 if k % 2 else -1); yy = ey + (rv.random() - .5) * 40; pv.moveTo(x0, yy)
                    pv.lineTo(x0 - (1 if k % 2 else -1) * sx * (20 + 20 * rv.random()), yy + (rv.random() - .5) * 20)
                c.drawPath(pv, trazo("#D2323C", 2, .8 * venas * a))
            ix = ex + 5 * math.sin(t * .7) + 22 * mirar
            c.drawCircle(ix, ey + 4, 27, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((ix, ey + 4), 27, [color("#5A3A1A", a), color("#8A5A2A", a), color("#3A2410", a)], [0, .7, 1])))
            c.drawCircle(ix, ey + 4, 13, relleno("#0A0A10", a)); c.drawCircle(ix - 9, ey - 6, 6, relleno("#FFFFFF", .9 * a))
            # párpado superior (piel) según apertura
            cierre = 1 - ojos
            if cierre > 0:
                c.drawRect(skia.Rect(ex - 62, ey - 44, ex + 62, ey - 44 + 88 * cierre), relleno(PIEL[1], a))
                c.drawLine(ex - 58, ey - 44 + 88 * cierre, ex + 58, ey - 44 + 88 * cierre, trazo("#7A4A30", 4, a))
            c.restore()
            c.drawOval(skia.Rect(ex - 58, ey - 40, ex + 58, ey + 40), trazo("#7A4A30", 3, .7 * a))
            # ceja
            by = ey - 70 - 6 * ojos
            c.drawLine(ex - 55, by - sx * 14 * enfado * (-1) + 0, ex + 55, by + sx * 14 * enfado, skia.Paint(AntiAlias=True, StrokeWidth=13, Color=color("#3A2418", a), StrokeCap=skia.Paint.kRound_Cap))
            # palillos que sujetan los párpados
            if palillos > 0:
                ca = caen; py = ey - 44 + 88 * (1 - max(ojos, .62)) - 260 * (1 - _io(min(1, palillos)))
                ap = a * (1 - TI.clamp((caen - .6) / .4))
                for dx in (-26, 24):
                    if ap <= 0: break
                    c.save(); c.translate(ex + dx + 30 * ca * sx, py + 400 * ca * ca); c.rotate(4 * sx + 120 * ca * sx)
                    c.drawRRect(rrc(0, 40, 9, 92, 4), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-4, 0), (4, 0)], [color("#F2DDB0", ap), color("#C9A86A", ap)])))
                    c.restore()
        if sudor > 0:   # gota de sudor
            g = skia.Path(); g.moveTo(170, -120); g.cubicTo(150, -80, 150, -50, 170, -45); g.cubicTo(190, -50, 190, -80, 170, -120)
            c.drawPath(g, relleno("#9FDCFF", .9 * sudor * a)); c.drawCircle(164, -64, 5, relleno("#FFFFFF", .8 * sudor * a))
        # nariz y boca
        n_ = skia.Path(); n_.moveTo(-6, 20); n_.quadTo(-26, 80, 0, 88); n_.quadTo(16, 90, 22, 80); c.drawPath(n_, trazo("#B07050", 4, .8 * a))
        if enfado > .3: c.drawArc(skia.Rect(-55, 130, 55, 180), 200, 140, False, trazo("#8A3A2A", 6, a))
        else: c.drawArc(skia.Rect(-45, 105, 45, 150), 20, 140, False, trazo("#8A3A2A", 6, a))
        c.restore()

    def e_insomne(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        ov = s.get("ojos", [{"word": "@0", "v": 1}]); ojos = ov[0]["v"]
        for k in ov[1:]:
            u = TI.clamp((t - self.ta(k["word"], e)) / k.get("dur", .4)); ojos += (k["v"] - ojos) * _io(u)
        # cabeceo de sueño
        cab = 0.0 if not s.get("cabecea") else 8 * max(0, math.sin(t * 1.3)) ** 4
        tp, tc = _tw(self, e, s.get("palillos_word")), _tw(self, e, s.get("caen_word"))
        pal = TI.clamp((t - tp) / .35); caen = TI.clamp((t - tc) / .6)
        if caen > 0: ojos = ojos * (1 - _io(TI.clamp((t - tc - .2) / .5)))
        elif pal > .6: ojos = max(ojos, .95)
        if ojos > .3 and pal <= 0:
            ph = (t + .4) % 2.6
            if ph < .14: ojos *= abs(math.cos(math.pi * ph / .14))
        # taza de café humeante
        tx, ty = CX + 330, 1020
        c.drawRRect(rrc(tx, ty, 150, 140, 22), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(tx - 75, 0), (tx + 75, 0)], [color("#FFFFFF"), color("#D9DEE8")])))
        c.drawArc(skia.Rect(tx + 50, ty - 40, tx + 120, ty + 30), -90, 180, False, trazo("#D9DEE8", 16))
        c.drawOval(skia.Rect(tx - 68, ty - 80, tx + 68, ty - 56), relleno("#5A3418"))
        for k in range(3):
            ph = (t * .5 + k / 3) % 1; sp = skia.Path(); x0 = tx - 30 + k * 30
            sp.moveTo(x0, ty - 90 - 160 * ph); sp.cubicTo(x0 + 20, ty - 120 - 160 * ph, x0 - 20, ty - 150 - 160 * ph, x0 + 6, ty - 190 - 160 * ph)
            c.drawPath(sp, trazo("#FFFFFF", 6, .35 * math.sin(math.pi * ph)))
        _cara(c, CX - 40, 640 + cab, 1.32, t, ojos, s.get("ojeras", .6), s.get("enfado", 0), pal, s.get("venas", 0), caen, aparece(dt0 + .1, .2))
        if pal > 0 and t - tp < 1.2:
            dd = t - tp; f = fuente("Inter", 800, 96); sc = .6 + .4 * resorte(dd, 10, 14)
            c.save(); c.translate(CX - 40, 300); c.rotate(-7); c.scale(sc, sc)
            texto(c, "¡CLAC!", 5, 8, f, "#14182A", alfa=1 - TI.clamp((dd - .8) / .4)); texto(c, "¡CLAC!", 0, 0, f, "#FFE15A", alfa=1 - TI.clamp((dd - .8) / .4)); c.restore()
        if caen > .5:
            dz = t - tc - .4
            for k in range(3):
                ph = (dz * .45 + k / 3) % 1; texto(c, "z", CX + 160 + 100 * ph, 380 - 220 * ph, fuente("Inter", 800, int(56 + 46 * ph)), "#FFFFFF", alfa=math.sin(math.pi * ph) * aparece(dz, .3))
        tb = _tw(self, e, s.get("bolsa_word"))
        if t > tb:   # bolsa de basura esperando
            u = resorte(t - tb, 7, 9); bx, by = CX - 330, 1030 + 200 * (1 - u)
            b = skia.Path(); b.moveTo(bx - 80, by + 70); b.cubicTo(bx - 110, by - 20, bx - 60, by - 80, bx - 15, by - 90); b.lineTo(bx - 30, by - 130)
            b.lineTo(bx + 30, by - 130); b.lineTo(bx + 15, by - 90); b.cubicTo(bx + 60, by - 80, bx + 110, by - 20, bx + 80, by + 70); b.close()
            c.drawPath(b, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(bx - 100, 0), (bx + 100, 0)], [color("#3A3F4A"), color("#1A1D24")])))
            c.drawLine(bx - 40, by - 40, bx - 10, by + 40, trazo("#5A6070", 3, .7))
            if s.get("bolsa_txt"): self.pildora(c, s["bolsa_txt"], CX - 240, 880, S, aparece(t - tb - .3, .15), fnt=self.F["pillb"], fondo="#0C1630")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- calendario de taco 1964
    def e_calendario(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tw = self.ta(s["word"], e); dias = s.get("dias", 11); d = s.get("dur", 2.0)
        u = TI.clamp((t - tw) / d) if t > tw else 0
        d0 = s.get("desde_dia", 1)
        hoja = d0 + int((dias - d0) * _io(u) + 1e-6) if t > tw else d0
        x, y, w, h = CX, 700, 560, 640
        _sombra(c, x + 20, y + h / 2 + 10, w * .55, 26, .4)
        # base y pila de hojas
        for k in range(6): c.drawRRect(rrc(x + 3 * k, y + 6 * k, w, h, 22), relleno("#E9E2D2", 1))
        c.drawRRect(rrc(x, y, w, h, 22), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y - h / 2), (0, y + h / 2)], [color("#FFFDF7"), color("#F1EADB")])))
        c.drawRRect(rrc(x, y - h / 2 + 70, w, 140, 0), relleno("#D23A2E")); c.drawRRect(rrc(x, y - h / 2 + 30, w, 60, 22), relleno("#D23A2E"))
        texto(c, s.get("anio", "1964"), x, y - h / 2 + 90, fuente("Inter", 800, 70), "#FFFFFF")
        for k in range(5): c.drawCircle(x - 200 + k * 100, y - h / 2 + 6, 16, trazo("#8A8F9A", 6))
        texto(c, "DÍA", x, y - 40, fuente("Inter", 800, 48), "#8A8F9A")
        texto(c, str(hoja), x, y + 120, fuente("Inter", 800, 260), "#14182A", tnum=True)
        # hoja que se arranca y vuela
        if 0 < u < 1:
            ph = ((dias - d0) * _io(u)) % 1
            c.save(); c.translate(x + 300 * ph, y - 200 * ph - 120 * ph * ph); c.rotate(40 * ph)
            c.drawRRect(rrc(0, 70, w, h - 140, 18), relleno("#FFFDF7", 1 - ph)); texto(c, str(max(1, hoja - 1)), 0, 120, fuente("Inter", 800, 200), "#14182A", alfa=1 - ph)
            c.restore()
        if hoja >= dias and s.get("sello_txt"):
            ds = t - tw - d
            if ds > 0:
                sc = 1.6 - .6 * TI.clamp(resorte(ds, 10, 14)); c.save(); c.translate(x + 170, y + 230); c.rotate(-12); c.scale(sc, sc)
                f = fuente("Inter", 800, 46); ww = ancho(s["sello_txt"], f) + 50
                c.drawRRect(rrc(0, 0, ww, 84, 12), trazo("#D23A2E", 7, aparece(ds, .07))); texto(c, s["sello_txt"], 0, 0, f, "#D23A2E", alfa=aparece(ds, .07)); c.restore()
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- conducir con 17 h despierto
    def e_conducir(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; te = _tw(self, e, s.get("eses_word")); hz = 600
        c.drawRect(skia.Rect(-40, -40, W + 40, hz), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, hz)], [color("#0E1430"), color("#3A3A6A"), color("#E08A5A")], [0, .7, 1])))
        for k in range(30):
            rng = np.random.default_rng(k); c.drawCircle(float(rng.random() * W), float(rng.random() * 400), 1.5, relleno("#FFFFFF", .5 + .4 * math.sin(t * 2 + k)))
        c.drawRect(skia.Rect(-40, hz, W + 40, 1260), relleno("#1E2A1E"))
        road = skia.Path.Polygon([(CX - 30, hz), (CX + 30, hz), (CX + 620, 1260), (CX - 620, 1260)], True)
        c.drawPath(road, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, hz), (0, 1260)], [color("#2A2A32"), color("#3E3E48")])))
        for k in range(12):   # rayas que vienen hacia ti
            q = ((k / 12) + t * .55) % 1; q2 = q + .035; ya, yb = hz + (1260 - hz) * q ** 2, hz + (1260 - hz) * q2 ** 2
            wa, wb = 2 + 14 * q ** 2, 2 + 14 * q2 ** 2
            c.drawPath(skia.Path.Polygon([(CX - wa, ya), (CX + wa, ya), (CX + wb, yb), (CX - wb, yb)], True), relleno("#F2D35A", .9))
        for sx in (-1, 1): c.drawLine(CX + sx * 30, hz, CX + sx * 600, 1260, trazo("#FFFFFF", 6, .8))
        # faros de frente que pasan y señales en el arcén
        for k in range(2):
            q = ((t * .35 + k * .5) % 1); yy = 600 + (1200 - 600) * q ** 2; xx = CX + 30 + 520 * q ** 2
            for dx in (-1, 1): c.drawCircle(xx + dx * (6 + 40 * q ** 2), yy, 3 + 16 * q ** 2, skia.Paint(AntiAlias=True, Color=color("#FFF6D0", .9), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3 + 10 * q)))
        for k in range(3):
            q = ((t * .3 + k / 3) % 1); yy = 600 + 600 * q ** 2; xx = CX - 40 - 620 * q ** 2; hh = 10 + 150 * q ** 2
            c.drawLine(xx, yy, xx, yy - hh, trazo("#9AA0AA", 2 + 5 * q, .9)); c.drawCircle(xx, yy - hh, 6 + 40 * q ** 2, relleno("#E5322D", .95)); c.drawCircle(xx, yy - hh, 4 + 30 * q ** 2, relleno("#FFFFFF", .95))
        ue = TI.clamp((t - te) / .6) * (1 + .7 * TI.clamp((t - _tw(self, e, s.get("eses2_word"))) / .6))   # más eses con el doble
        cx_ = CX + ue * (170 * math.sin((t - te) * 2.2) + 40 * math.sin((t - te) * 5.1)); rot = ue * 7 * math.cos((t - te) * 2.2)
        c.save(); c.translate(cx_, 1000); c.rotate(rot)
        _sombra(c, 0, 120, 230, 24, .5)
        body = skia.Path(); body.moveTo(-210, 100); body.lineTo(-200, -20); body.cubicTo(-190, -60, -150, -70, -120, -72); body.lineTo(-90, -170)
        body.lineTo(90, -170); body.lineTo(120, -72); body.cubicTo(150, -70, 190, -60, 200, -20); body.lineTo(210, 100); body.close()
        c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -170), (0, 100)], [color("#E2464A"), color("#B5222A"), color("#6E1016")], [0, .6, 1])))
        c.drawPath(skia.Path.Polygon([(-78, -158), (78, -158), (100, -84), (-100, -84)], True), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -158), (0, -84)], [color("#9FB8E8"), color("#2A3A5A")])))
        for sx in (-1, 1):
            c.drawRRect(rrc(sx * 150, -20, 80, 34, 10), relleno("#FF2A2A")); c.drawRRect(rrc(sx * 150, -20, 80, 34, 10), skia.Paint(AntiAlias=True, Color=color("#FF4A3A", .6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
            c.drawRRect(rrc(sx * 165, 110, 70, 50, 12), relleno("#111116"))
        c.drawRRect(rrc(0, 40, 140, 40, 6), relleno("#F2F2F2")); c.restore()
        # alcoholímetro
        st = s.get("medidor")
        if st:
            pasos = st.get("pasos") or [dict(word=st["word"], valor=st["valor"], label=st.get("label", ""))]
            v = float(st.get("desde", 0)); lab = pasos[0].get("label", ""); dv = -1; fin = False
            for q in pasos:
                tq = self.ta(q["word"], e)
                if t > tq:
                    u = TI.cubic_out(TI.clamp((t - tq) / 1.0)); v = v + (q["valor"] - v) * u; lab = q.get("label", lab); dv = t - tq; fin = u >= 1
            st = dict(st, valor=v if fin else 1e9, label=lab)
            a = aparece(dt0 - .2, .2); mx, my = CX, 440
            c.drawRRect(rrc(mx, my, 520, 210, 40), relleno("#121826", .92 * a)); c.drawRRect(rrc(mx, my, 520, 210, 40), trazo("#5A6A8A", 3, a))
            c.drawRRect(rrc(mx, my - 20, 440, 110, 18), relleno("#0A2A1E", a))
            col = "#FF5A4A" if v >= .499 else "#5AF2A0"
            with capa(c, alfa=a, blur=10): texto(c, f"{v:.2f}".replace(".", ",") + " g/l", mx, my - 20, fuente("Inter", 800, 80), col, tnum=True)
            texto(c, f"{v:.2f}".replace(".", ",") + " g/l", mx, my - 20, fuente("Inter", 800, 80), col, alfa=a, tnum=True)
            texto(c, st.get("label", ""), mx, my + 70, fuente("Inter", 800, 30), "#C9D3EA", alfa=a)
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- cerebro de luces
    def _cerebro_path(cx, cy, s):
        p = skia.Path(); p.moveTo(cx - 330 * s, cy + 60 * s)
        p.cubicTo(cx - 380 * s, cy - 120 * s, cx - 250 * s, cy - 300 * s, cx - 60 * s, cy - 290 * s)
        p.cubicTo(cx + 120 * s, cy - 330 * s, cx + 340 * s, cy - 220 * s, cx + 350 * s, cy - 20 * s)
        p.cubicTo(cx + 360 * s, cy + 120 * s, cx + 260 * s, cy + 200 * s, cx + 120 * s, cy + 190 * s)
        p.cubicTo(cx + 60 * s, cy + 280 * s, cx - 40 * s, cy + 270 * s, cx - 60 * s, cy + 190 * s)
        p.cubicTo(cx - 200 * s, cy + 220 * s, cx - 310 * s, cy + 170 * s, cx - 330 * s, cy + 60 * s); p.close()
        return p

    def e_neuronas(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; ta_, tm = _tw(self, e, s.get("apaga_word")), _tw(self, e, s.get("micro_word"))
        cx, cy = CX, 680; br = _cerebro_path(cx, cy, 1.25)
        c.drawPath(br, skia.Paint(AntiAlias=True, Color=color("#6EA0FF", .25), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
        c.drawPath(br, relleno("#0E1838", .95)); c.drawPath(br, trazo("#6EA0FF", 4, .7))
        rng = np.random.default_rng(21); N = 150
        pts = []
        while len(pts) < N:
            x, y = cx + (rng.random() - .5) * 860, cy + (rng.random() - .5) * 600
            if br.contains(x, y): pts.append((x, y))
        zonas = [(cx - 200, cy - 80), (cx + 170, cy - 140), (cx + 40, cy + 120)]
        ua = TI.clamp((t - ta_) / 1.2)
        def apag(x, y):
            v = 0.0
            for k, (zx, zy) in enumerate(zonas):
                uk = TI.clamp((t - ta_ - k * .45) / .6) * (.85 + .15 * math.sin(t * 3 + k))
                d = math.hypot(x - zx, y - zy); v = max(v, uk * TI.clamp(1 - (d - 90) / 70))
            return v
        c.save(); c.clipPath(br, doAntiAlias=True)
        for i in range(N):
            x, y = pts[i]
            for j in (i * 7 % N, i * 13 % N):
                x2, y2 = pts[j]
                if math.hypot(x2 - x, y2 - y) < 130:
                    off = max(apag(x, y), apag(x2, y2))
                    c.drawLine(x, y, x2, y2, trazo("#6EA0FF", 1.6, .35 * (1 - off)))
                    ph = (t * .8 + i * .13) % 1
                    if off < .5: c.drawCircle(x + (x2 - x) * ph, y + (y2 - y) * ph, 3, relleno("#BFE0FF", .8 * (1 - off)))
        for i, (x, y) in enumerate(pts):
            off = apag(x, y); fl = .6 + .4 * math.sin(t * 5 + i)
            c.drawCircle(x, y, 6, relleno("#FFE7A3" if off < .5 else "#3A4058", (.95 * fl) if off < .5 else .7))
            if off < .3: c.drawCircle(x, y, 14, skia.Paint(AntiAlias=True, Color=color("#FFE7A3", .25 * fl * (1 - off)), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
        for k, (zx, zy) in enumerate(zonas):
            uk = TI.clamp((t - ta_ - k * .45) / .6)
            if uk > 0: c.drawCircle(zx, zy, 150, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((zx, zy), 150, [color("#000000", .75 * uk), color("#000000", 0)])))
        c.restore()
        if ua > 0:
            for k, (zx, zy) in enumerate(zonas):
                uk = TI.clamp((t - ta_ - k * .45) / .6)
                if uk > 0: texto(c, "zz", zx + 40, zy - 30 - 10 * math.sin(t * 2 + k), fuente("Inter", 800, 44), "#9DB8FF", alfa=uk * .9)
            self.pildora(c, s.get("apaga_txt", "NEURONAS APAGADAS"), CX, 1110, S, ua, fnt=self.F["pillb"], fondo="#0C1630")
        capa_hud(self, c, e, t, S)
        # microsueño: la pantalla se va a negro y vuelve con un glitch
        dm = t - tm
        if 0 < dm < .75:
            k = 1.0 if dm < .5 else 1 - (dm - .5) / .25
            c.drawRect(skia.Rect(-60, -60, W + 60, 1240), relleno("#000000", k))
            if .45 < dm < .75:
                rng2 = np.random.default_rng(int(dm * 60))
                for j in range(6):
                    yy = rng2.random() * 1200; c.drawRect(skia.Rect(-60, yy, W + 60, yy + 8 + 30 * rng2.random()), relleno("#6EA0FF" if j % 2 else "#FF4A6A", .5))
            if dm < .5: texto(c, "…", CX, 640, fuente("Inter", 800, 120), "#3A3A4A", alfa=k)

    # ---------------------------------------------------------------- limpieza del cerebro
    def e_limpieza(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; td, tac = _tw(self, e, s.get("duerme_word")), _tw(self, e, s.get("acumula_word"))
        cx, cy = CX, 660; br = _cerebro_path(cx, cy, 1.2)
        gris = TI.clamp((t - tac) / 1.5)
        c.drawPath(br, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx - 80, cy - 120), 520, [color("#F7B7C0"), color("#E58A9A"), color("#B85A6E")])))
        if gris > 0: c.drawPath(br, relleno("#6A6470", .55 * gris))
        # pliegues
        c.save(); c.clipPath(br, doAntiAlias=True)
        for k in range(9):
            pg = skia.Path(); y0 = cy - 260 + k * 60; pg.moveTo(cx - 420, y0)
            for x in range(-420, 430, 60): pg.lineTo(cx + x, y0 + 22 * math.sin(x * .03 + k * 1.7))
            c.drawPath(pg, trazo("#B85A6E", 5, .5))
        # residuos
        rng = np.random.default_rng(31); ola = TI.clamp((t - td) / 1.4); fx = cx - 450 + 980 * _io(ola) if t > td else -1e9
        n_base = 40 + int(80 * gris)
        for k in range(n_base):
            x, y = cx + (rng.random() - .5) * 760, cy + (rng.random() - .5) * 520
            if not br.contains(x, y): continue
            vuelve = k >= 40 or (t > tac + (k % 40) * .02)
            if x < fx and not (t > tac and vuelve): continue
            r = 9 + 9 * rng.random(); bob = 3 * math.sin(t * 2 + k)
            c.drawCircle(x, y + bob, r, relleno("#C9A23A", .9)); c.drawCircle(x - r * .3, y + bob - r * .3, r * .35, relleno("#F2D88A", .8))
        # ola de líquido limpiador
        if 0 < ola < 1:
            c.drawRect(skia.Rect(fx - 160, cy - 400, fx + 30, cy + 400), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(fx - 160, 0), (fx + 30, 0)], [color("#4FC3FF", 0), color("#4FC3FF", .65)])))
            for k in range(10): c.drawCircle(fx - 20 - (k * 37 % 120), cy - 280 + k * 60, 8, trazo("#FFFFFF", 2, .7))
        c.restore()
        c.drawPath(br, trazo("#8A3A50", 4, .8))
        if t > td: self.pildora(c, s.get("duerme_txt", "DURMIENDO: LIMPIEZA"), CX, 1080, S, aparece(t - td, .15) * (1 - TI.clamp((t - tac) / .2)), fnt=self.F["pillb"], fondo="#1F7AB8")
        if t > tac: self.pildora(c, s.get("acumula_txt", "SIN DORMIR: SE ACUMULA"), CX, 1080, S, aparece(t - tac - .1, .15), fnt=self.F["pillb"], fondo="#8A6A1A")
        # luna / sol
        lx, ly = CX + 320, 330
        if t > td and t < tac:
            a1 = skia.Path(); a1.addCircle(lx, ly, 46); a2 = skia.Path(); a2.addCircle(lx + 22, ly - 14, 42)
            c.drawPath(skia.Op(a1, a2, skia.PathOp.kDifference_PathOp), relleno("#F2C14E"))
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- alucinaciones
    def e_alucina(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; ts, to = _tw(self, e, s.get("sombra_word")), _tw(self, e, s.get("ojos_word"))
        k = TI.clamp(dt0 / 3)
        # pared que respira (rayas onduladas)
        c.drawRect(skia.Rect(-40, -40, W + 40, 1000), relleno("#1A1630"))
        for j in range(16):
            p = skia.Path(); x0 = 40 + j * 64; p.moveTo(x0, 120)
            for y in range(120, 1000, 30): p.lineTo(x0 + (8 + 22 * k) * math.sin(y * .02 + t * 2 + j * .4), y)
            c.drawPath(p, trazo("#3A2F6A", 10, .9))
        c.drawRect(skia.Rect(-40, 1000, W + 40, 1260), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1000), (0, 1260)], [color("#2A2040"), color("#120E20")])))
        # puerta con luz
        dx, dy = CX - 230, 640
        c.drawRect(skia.Rect(dx - 140, dy - 300, dx + 140, 1000), relleno("#0A0810"))
        c.drawPath(skia.Path.Polygon([(dx - 140, 1000), (dx + 140, 1000), (dx + 260, 1260), (dx - 260, 1260)], True), relleno("#FFE7A3", .10))
        c.drawRect(skia.Rect(dx - 140, dy - 300, dx + 140, 1000), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(dx, dy - 300), (dx, 1000)], [color("#FFE7A3", .25), color("#FFB45C", .45)])))
        if t > ts:   # silueta en la puerta
            us = TI.clamp((t - ts) / .8); a = us * (.85 + .15 * math.sin(t * 7))
            c.drawCircle(dx, dy - 150, 52, relleno("#000000", a)); c.drawRRect(rrc(dx, dy + 40, 150, 330, 70), relleno("#000000", a))
            c.drawRRect(rrc(dx, dy + 290, 120, 200, 30), relleno("#000000", a))
        # reloj que se derrite
        rx, ry = CX + 220, 400; mel = k
        rel = skia.Path(); rel.moveTo(rx - 110, ry - 40); rel.cubicTo(rx - 110, ry - 140, rx + 110, ry - 140, rx + 110, ry - 40)
        rel.cubicTo(rx + 110, ry + 40 + 160 * mel, rx + 40, ry + 60 + 260 * mel, rx + 10, ry + 80 + 300 * mel); rel.cubicTo(rx - 20, ry + 60 + 200 * mel, rx - 110, ry + 60 + 60 * mel, rx - 110, ry - 40); rel.close()
        c.drawPath(rel, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(rx, ry - 140), (rx, ry + 300)], [color("#F2D35A"), color("#C9902A")])))
        c.drawCircle(rx, ry - 50, 80, relleno("#FFF8E6"))
        for q in range(12):
            an = 2 * math.pi * q / 12; c.drawLine(rx + 66 * math.cos(an), ry - 50 + 66 * math.sin(an) * (1 + .3 * mel), rx + 74 * math.cos(an), ry - 50 + 74 * math.sin(an) * (1 + .3 * mel), trazo("#3A2A1A", 3))
        for an, L in ((t * 2.5, 60), (t * .4, 44)): c.drawLine(rx, ry - 50, rx + L * math.cos(an), ry - 50 + L * math.sin(an) * (1 + .5 * mel), trazo("#3A2A1A", 5))
        # ojos en la oscuridad
        if t > to:
            for j, (ox, oy) in enumerate(((CX + 280, 820), (CX - 40, 300), (CX + 120, 940))):
                ua = TI.clamp((t - to - j * .3) / .3); bl = 1 if (t * .8 + j * .37) % 1 > .06 else .1
                for sx in (-1, 1):
                    c.drawOval(skia.Rect(ox + sx * 24 - 14, oy - 7 * bl, ox + sx * 24 + 14, oy + 7 * bl), relleno("#FFE15A", ua))
                    c.drawOval(skia.Rect(ox + sx * 24 - 14, oy - 7 * bl, ox + sx * 24 + 14, oy + 7 * bl), skia.Paint(AntiAlias=True, Color=color("#FFE15A", .5 * ua), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        if s.get("pill") and t > ts: self.pildora(c, s["pill"], CX, 1120, S, aparece(t - ts, .15), fnt=self.F["pillb"], fondo="#5A2A8A")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- recuerdos que se van + enfado
    def e_recuerdos(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tm, te = _tw(self, e, s.get("memoria_word")), _tw(self, e, s.get("enfado_word"))
        cx, cy = CX - 60, 700; enf = TI.clamp((t - te) / .5)
        c.save(); c.translate(CX, 700); c.scale(1.3, 1.3); c.translate(-CX, -700)
        # cabeza de perfil
        hp = skia.Path(); hp.moveTo(cx - 60, cy + 330); hp.lineTo(cx - 60, cy + 180); hp.cubicTo(cx - 230, cy + 120, cx - 260, cy - 140, cx - 100, cy - 250)
        hp.cubicTo(cx + 40, cy - 330, cx + 260, cy - 230, cx + 250, cy - 40); hp.lineTo(cx + 300, cy + 40); hp.lineTo(cx + 250, cy + 70)
        hp.cubicTo(cx + 260, cy + 130, cx + 220, cy + 170, cx + 150, cy + 160); hp.lineTo(cx + 140, cy + 330); hp.close()
        col_a, col_b = ("#E58A6A", "#B5422A") if enf > .5 else ("#9DB8FF", "#4F6BD8")
        c.drawPath(hp, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, cy - 300), (0, cy + 330)], [color(col_a), color(col_b)])))
        if enf > 0: c.drawPath(hp, relleno("#FF3A2A", .25 * enf * (.7 + .3 * math.sin(t * 9))))
        # fotos (recuerdos) que salen de la cabeza y se deshacen
        if t > tm:
            for j in range(5):
                ph = ((t - tm) * .5 + j / 5) % 1
                if t - tm < j * .25: continue
                px_, py_ = cx + 40 + 330 * ph + 40 * math.sin(j * 2), cy - 120 - 380 * ph + 60 * math.sin(j * 1.3)
                a = 1 - ph
                c.save(); c.translate(px_, py_); c.rotate(-15 + 30 * math.sin(j * 1.7) + 40 * ph)
                c.drawRect(skia.Rect(-70, -80, 70, 80), relleno("#FFFFFF", a)); c.drawRect(skia.Rect(-58, -68, 58, 40), relleno(("#7FC8F8", "#F2B33D", "#2FBF71", "#E5322D", "#8B5CF6")[j], a))
                c.drawCircle(-20, -30, 16, relleno("#FFFFFF", .7 * a))
                c.restore()
                rng = np.random.default_rng(j)
                for q in range(8):   # se deshacen en píxeles
                    c.drawRect(skia.Rect(px_ + 90 * ph * (rng.random() - .2), py_ - 60 * ph * rng.random(), px_ + 90 * ph * (rng.random() - .2) + 10, py_ - 60 * ph * rng.random() + 10), relleno("#FFFFFF", .6 * ph * a))
        if enf > 0:   # vapor de enfado (dentro de la escala)
            for j in range(4):
                ph = ((t - te) * .9 + j / 4) % 1; vx = cx + 60 + (j - 1.5) * 60; vy = cy - 300 - 180 * ph
                c.drawCircle(vx + 20 * math.sin(t * 3 + j), vy, 26 + 30 * ph, relleno("#FFFFFF", .5 * (1 - ph) * enf))
        c.restore()
        if t > tm: self.pildora(c, s.get("memoria_txt", "MEMORIA"), CX, 1100, S, aparece(t - tm, .15) * (1 - enf), fnt=self.F["pillb"], fondo="#4F6BD8")
        if enf > 0: self.pildora(c, s.get("enfado_txt", "IRRITABLE"), CX, 1100, S, enf, fnt=self.F["pillb"], fondo="#E5322D")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- dormir para recuperarse
    def e_dormir(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tw = self.ta(s["word"], e); dv = t - tw
        u = TI.cubic_out(TI.clamp(dv / 1.6)) if dv > 0 else 0
        mins = (s["valor_h"] * 60 + s.get("valor_m", 0)) * u
        # ventana con ciclo día/noche que gira deprisa mientras corre el contador
        wx, wy = CX + 250, 590; ang = (mins / 720.0) * 2 * math.pi
        c.save(); pth = skia.Path(); pth.addRRect(rrc(wx, wy, 300, 300, 26)); c.clipPath(pth, doAntiAlias=True)
        dia = .5 + .5 * math.cos(ang)
        c.drawRect(skia.Rect(wx - 150, wy - 150, wx + 150, wy + 150), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, wy - 150), (0, wy + 150)], [color("#0E1430" if dia < .5 else "#7FC8F8"), color("#3A3A6A" if dia < .5 else "#D9F1FF")])))
        sx, sy = wx + 110 * math.sin(ang), wy + 110 * math.cos(ang)
        c.drawCircle(sx, sy, 34, relleno("#FFE15A")); c.drawCircle(wx - 110 * math.sin(ang), wy - 110 * math.cos(ang), 30, relleno("#F2F2F2"))
        c.restore(); c.drawRRect(rrc(wx, wy, 300, 300, 26), trazo("#8A6A4A", 12)); c.drawLine(wx, wy - 150, wx, wy + 150, trazo("#8A6A4A", 8)); c.drawLine(wx - 150, wy, wx + 150, wy, trazo("#8A6A4A", 8))
        # cama con la persona dormida
        by = 930
        c.drawRRect(rrc(CX, by + 120, 880, 120, 20), relleno("#5A3A2A")); c.drawRRect(rrc(CX - 410, by - 40, 60, 380, 16), relleno("#6A4A36"))
        c.drawRRect(rrc(CX - 220, by - 30, 300, 120, 50), relleno("#F2EEF8"))
        hx, hy = CX - 210, by - 95
        c.drawCircle(hx, hy, 92, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((hx - 20, hy - 30), 110, [color(PIEL[0]), color(PIEL[1])])))
        pel = skia.Path(); pel.addArc(skia.Rect(hx - 96, hy - 100, hx + 96, hy + 80), 180, 180); c.drawPath(pel, relleno("#3A2418"))
        for ex in (-32, 32): c.drawArc(skia.Rect(hx + ex - 16, hy - 4, hx + ex + 16, hy + 16), 10, 160, False, trazo("#3A2418", 4))
        c.drawArc(skia.Rect(hx - 20, hy + 36, hx + 20, hy + 60), 20, 140, False, trazo("#8A4A3A", 4))
        m = skia.Path(); m.moveTo(CX - 370, by + 70); m.cubicTo(CX - 200, by - 30 + 8 * math.sin(t * 1.2), CX + 150, by - 10, CX + 440, by + 30); m.lineTo(CX + 440, by + 150); m.lineTo(CX - 370, by + 150); m.close()
        c.drawPath(m, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, by - 30), (0, by + 150)], [color("#7FC8F8"), color("#3A86C8")])))
        for k in range(3):
            ph = (t * .45 + k / 3) % 1; texto(c, "z", hx + 120 + 90 * ph, hy - 140 - 200 * ph, fuente("Inter", 800, int(50 + 40 * ph)), "#FFFFFF", alfa=math.sin(math.pi * ph))
        # contador de sueño
        if dv > -.1:
            a = aparece(dv + .1, .15); h_, m_ = divmod(int(round(mins)), 60)
            c.drawRRect(rrc(CX, 300, 560, 190, 36), relleno("#0B1530", .85 * a)); c.drawRRect(rrc(CX, 300, 560, 190, 36), trazo("#9DB8FF", 2.5, .6 * a))
            with capa(c, alfa=a, blur=(4 if 0 < dv < 1.6 else 0)): texto(c, f"{h_} h {m_:02d} min", CX, 280, fuente("Inter", 800, 92), "#FFFFFF", tnum=True)
            texto(c, s.get("label", "DURMIENDO SEGUIDO"), CX, 355, fuente("Inter", 800, 32), "#9DB8FF", alfa=a)

    # ---------------------------------------------------------------- «un capítulo más»
    def e_capitulo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tp = _tw(self, e, s.get("pulsa_word"))
        px, py, pw, ph_ = CX, 650, 560, 1000
        _sombra(c, px + 20, py + ph_ / 2, 280, 30, .5)
        c.drawRRect(rrc(px, py, pw, ph_, 70), relleno("#0C0C12")); c.drawRRect(rrc(px, py, pw - 30, ph_ - 30, 56), relleno("#14141E"))
        c.drawRRect(rrc(px, py - ph_ / 2 + 40, 140, 30, 15), relleno("#0C0C12"))
        # miniatura del siguiente episodio
        c.drawRRect(rrc(px, py - 160, 480, 300, 24), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(px - 240, 0), (px + 240, 0)], [color("#8B5CF6"), color("#E5322D")])))
        c.drawPath(skia.Path.Polygon([(px - 30, py - 210), (px - 30, py - 110), (px + 50, py - 160)], True), relleno("#FFFFFF", .9))
        texto(c, s.get("titulo", "Episodio 7"), px, py + 40, fuente("Inter", 800, 44), "#FFFFFF")
        n = max(0, 5 - int(max(0, dt0 - .4) / .55))
        texto(c, f"Siguiente episodio en {n}…", px, py + 110, fuente("Inter", 600, 34), "#B9C0D6")
        # anillo de cuenta atrás + botón
        bx, by = px, py + 260; uc = TI.clamp((dt0 - .4) / 2.75)
        c.drawRRect(rrc(bx, by, 380, 100, 50), relleno("#FFFFFF" if t < tp else "#2FBF71"))
        texto(c, "VER AHORA" if t < tp else "▶ REPRODUCIENDO", bx, by, fuente("Inter", 800, 36), "#14141E" if t < tp else "#FFFFFF")
        c.drawArc(skia.Rect(bx - 205, by - 65, bx + 205, by + 65), -90, 360 * uc, False, trazo("#E5322D", 6, .8))
        # dedo
        if t > tp - .6:
            u = TI.clamp((t - tp + .6) / .6); fx, fy = bx + 60, by + 80 + 300 * (1 - _io(u))
            c.save(); c.translate(fx, fy); c.rotate(-15)
            c.drawRRect(rrc(0, 120, 90, 260, 45), skia.Paint(AntiAlias=True, Shader=_piel(0, 260))); c.drawOval(skia.Rect(-26, 0, 26, 50), relleno("#FBE5D4"))
            c.restore()
            if t > tp:
                dp = t - tp; c.drawCircle(bx + 50, by, 40 + 160 * dp, trazo("#FFFFFF", 4, max(0, .8 - dp)))
        capa_hud(self, c, e, t, S)


    # ---------------------------------------------------------------- hora 16: se acaba el día
    def e_atardecer(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tn, tm = _tw(self, e, s.get("noche_word")), _tw(self, e, s.get("luna_word"))
        un = TI.clamp((t - tn + .3) / 1.6)
        def mix(a_, b_, u):
            ca, cb = color(a_), color(b_)
            return skia.Color(int(skia.ColorGetR(ca) + (skia.ColorGetR(cb) - skia.ColorGetR(ca)) * u), int(skia.ColorGetG(ca) + (skia.ColorGetG(cb) - skia.ColorGetG(ca)) * u), int(skia.ColorGetB(ca) + (skia.ColorGetB(cb) - skia.ColorGetB(ca)) * u))
        c.drawRect(skia.Rect(-40, -40, W + 40, 1240), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1100)], [mix("#F28A5A", "#0B1030", un), mix("#FFC27A", "#2A2A60", un), mix("#FFE2B0", "#4A3A6A", un)], [0, .6, 1])))
        for k in range(50):
            rng = np.random.default_rng(100 + k); c.drawCircle(float(rng.random() * W), float(rng.random() * 600), 1.6, relleno("#FFFFFF", un * (.5 + .4 * math.sin(t * 2 + k))))
        sy = 520 + 520 * _io(un); c.drawCircle(CX + 160, sy, 110, skia.Paint(AntiAlias=True, Color=color("#FFD27A", 1 - .3 * un), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30))); c.drawCircle(CX + 160, sy, 80, relleno("#FFE7A3"))
        if t > tm:   # luna que sube
            um = resorte(t - tm, 4, 6); mx, my = CX - 220, 560 - 220 * um
            a1 = skia.Path(); a1.addCircle(mx, my, 70); a2 = skia.Path(); a2.addCircle(mx + 32, my - 20, 64)
            c.drawPath(skia.Op(a1, a2, skia.PathOp.kDifference_PathOp), relleno("#FFF2C4")); c.drawCircle(mx, my, 110, skia.Paint(AntiAlias=True, Color=color("#FFF2C4", .18), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
        rng = np.random.default_rng(7); x = -20
        while x < W:
            bw = 90 + rng.random() * 90; bh = 220 + rng.random() * 330; top = 1180 - bh
            c.drawRect(skia.Rect(x, top, x + bw - 6, 1240), relleno("#1A1A2E" if un > .5 else "#3A2A3E"))
            for wy in range(int(top + 20), 1160, 46):
                for wx in range(int(x + 14), int(x + bw - 30), 34):
                    k = (wx * 7 + wy * 13) % 100 / 100
                    if un > k * .9: c.drawRect(skia.Rect(wx, wy, wx + 18, wy + 26), relleno("#FFD27A", .9 * min(1, (un - k * .9) * 4) * (0 if (wx + wy) % 5 == 0 and t > tm + 1 else 1)))
            x += bw
        if t > tm:   # tu ventana sigue encendida, con brillo
            c.drawRect(skia.Rect(CX + 40, 900, CX + 120, 980), skia.Paint(AntiAlias=True, Color=color("#FFE7A3", .7), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20)))
            self.pildora(c, s.get("tu_txt", "TÚ SIGUES DESPIERTO"), CX, 1060, S, aparece(t - tm, .15), fnt=self.F["pillb"], fondo="#E5322D")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- hambre
    def _comida(c, tipo, x, y, s, a):
        c.save(); c.translate(x, y); c.scale(s, s)
        if tipo == "burger":
            c.drawArc(skia.Rect(-60, -50, 60, 30), 180, 180, True, relleno("#E8A04A", a)); c.drawRect(skia.Rect(-62, -12, 62, 0), relleno("#5AC04A", a))
            c.drawRRect(rrc(0, 8, 124, 18, 8), relleno("#6A3A1A", a)); c.drawRect(skia.Rect(-58, 16, 58, 24), relleno("#F2C14E", a)); c.drawRRect(rrc(0, 34, 118, 20, 8), relleno("#E8A04A", a))
            for k in range(5): c.drawCircle(-30 + k * 15, -30 + (k % 2) * 6, 3, relleno("#FFF2C4", a))
        elif tipo == "donut":
            c.drawCircle(0, 0, 55, relleno("#E8A04A", a)); c.drawCircle(0, -4, 48, relleno("#F27AB0", a)); c.drawCircle(0, 0, 18, relleno("#00000000", 0))
            c.drawCircle(0, 0, 18, relleno("#14141E", a))
            for k in range(8):
                an = k * .8; c.drawLine(30 * math.cos(an), 30 * math.sin(an) - 4, 38 * math.cos(an), 38 * math.sin(an) - 4, trazo(("#FFE15A", "#6EA0FF", "#FFFFFF")[k % 3], 4, a))
        else:
            c.drawPath(skia.Path.Polygon([(0, 60), (-55, -50), (55, -50)], True), relleno("#F2C14E", a)); c.drawRRect(rrc(0, -54, 120, 18, 8), relleno("#D9893A", a))
            for (px, py) in ((-15, -20), (14, -10), (0, 20)): c.drawCircle(px, py, 9, relleno("#D2323C", a))
        c.restore()

    def e_hambre(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; th = _tw(self, e, s.get("hambre_word"))
        uh = TI.clamp((t - th) / .5); cx, cy = CX, 700
        shake = 10 * uh * math.sin(t * 40) * (.5 + .5 * math.sin(t * 3))
        # estómago
        st = skia.Path(); st.moveTo(cx - 40, cy - 300); st.lineTo(cx - 40, cy - 200)
        st.cubicTo(cx - 40, cy - 150, cx - 250, cy - 170, cx - 250, cy + 10)
        st.cubicTo(cx - 250, cy + 190, cx - 80, cy + 260, cx + 60, cy + 220)
        st.cubicTo(cx + 160, cy + 190, cx + 210, cy + 120, cx + 260, cy + 130); st.lineTo(cx + 275, cy + 70)
        st.cubicTo(cx + 200, cy + 60, cx + 150, cy + 110, cx + 80, cy + 120)
        st.cubicTo(cx - 40, cy + 130, cx - 120, cy + 60, cx - 110, cy - 30)
        st.cubicTo(cx - 100, cy - 110, cx + 20, cy - 150, cx + 20, cy - 200); st.lineTo(cx + 20, cy - 300); st.close()
        c.save(); c.translate(shake, 0)
        c.drawPath(st, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx - 120, cy + 20), 330, [color("#FFC2CF"), color("#F27A95"), color("#C2456A")])))
        c.save(); c.clipPath(st, doAntiAlias=True)
        for k in range(6):   # pliegues internos
            pg = skia.Path(); pg.moveTo(cx - 230, cy - 20 + k * 40); pg.cubicTo(cx - 160, cy - 60 + k * 45, cx - 60, cy + 40 + k * 30, cx + 60, cy + 120 + k * 20)
            c.drawPath(pg, trazo("#C2456A", 4, .35))
        c.drawOval(skia.Rect(cx - 220, cy - 80, cx - 150, cy + 60), relleno("#FFFFFF", .18)); c.restore()
        c.drawPath(st, trazo("#8A2A4A", 5, .8))
        c.restore()
        if uh > 0:   # GRRR y ondas
            for k in range(3):
                r = 300 + ((t * 220 + k * 70) % 210); c.drawArc(skia.Rect(cx - r, cy - r * .8, cx + r, cy + r * .8), -40, 80, False, trazo("#FFFFFF", 5, .35 * (1 - (r - 300) / 210) * uh))
                c.drawArc(skia.Rect(cx - r, cy - r * .8, cx + r, cy + r * .8), 140, 80, False, trazo("#FFFFFF", 5, .35 * (1 - (r - 300) / 210) * uh))
            f = fuente("Inter", 800, 90); sc = .7 + .3 * resorte(t - th, 10, 14)
            c.save(); c.translate(cx + 30, 330); c.rotate(-6 + 3 * math.sin(t * 20)); c.scale(sc, sc)
            texto(c, "GRRR…", 5, 8, f, "#14182A", alfa=uh); texto(c, "GRRR…", 0, 0, f, "#FFE15A", alfa=uh); c.restore()
            for k, tp in enumerate(("burger", "donut", "pizza", "burger", "donut")):
                an = t * .9 + k * 2 * math.pi / 5; R_ = 360
                _comida(c, tp, cx + R_ * math.cos(an), cy + R_ * .75 * math.sin(an), .9 + .1 * math.sin(t * 3 + k), TI.clamp((t - th - k * .12) / .3))
            self.pildora(c, s.get("hambre_txt", "HORMONA DEL HAMBRE ▲"), CX, 1100, S, uh, fnt=self.F["pillb"], fondo="#C2456A")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- paranoia (hora 72)
    def e_paranoia(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tc = _tw(self, e, s.get("cree_word"))
        uc = TI.clamp((t - tc) / .5)
        # ojos que vigilan desde la oscuridad
        for j, (ox, oy) in enumerate(((CX - 330, 420), (CX + 330, 470), (CX - 360, 900), (CX + 360, 860), (CX, 330))):
            ua = TI.clamp((t - tc - j * .18) / .3); bl = 1 if (t * .7 + j * .29) % 1 > .07 else .1
            look = -1 if ox > CX else 1
            for sx in (-1, 1):
                c.drawOval(skia.Rect(ox + sx * 26 - 20, oy - 12 * bl, ox + sx * 26 + 20, oy + 12 * bl), relleno("#FFFFFF", .9 * ua))
                c.drawCircle(ox + sx * 26 + look * 8, oy, 7 * bl, relleno("#14141E", ua))
        mir = math.sin(t * 2.6) if uc > 0 else 0
        _cara(c, CX, 720, 1.05, t, .95, .9, .3, 0, .7, 0, aparece(dt0 + .1, .2), mirar=mir, sudor=uc)
        if uc > 0:   # bocadillo de pensamiento
            bx, by = CX + 160, 330; sc = .6 + .4 * resorte(t - tc, 8, 11)
            for k, (dx, dy, r) in enumerate(((-120, 140, 14), (-80, 100, 22))): c.drawCircle(bx + dx, by + dy + 60, r * sc, relleno("#FFFFFF", .95 * uc))
            c.save(); c.translate(bx, by); c.scale(sc, sc)
            c.drawRRect(rrc(0, 0, 400, 130, 65), relleno("#FFFFFF", .95 * uc))
            texto(c, s.get("idea_txt", "¿ME VIGILAN?"), 0, 0, fuente("Inter", 800, 46), "#14182A", alfa=uc); c.restore()
            self.pildora(c, s.get("pill", "IDEAS FALSAS"), CX, 1100, S, uc, fnt=self.F["pillb"], fondo="#5A2A8A")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- efectos
    def efectos_sueno(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; T = lambda w: self.ta(w, e)
        h = s.get("hud")
        if h and h.get("word"): self.rodillo(T(h["word"]), h.get("dur", 1.0))
        if h and h.get("capitulo"):   # entrada de capítulo: golpe de reloj + vuelo al sitio
            self.sfx(TI.f_de_t(e["t0"] + .12), "ding", .7); self.sfx(TI.f_de_t(e["t0"] + h.get("grande", 1.0)), "whoosh", .45)
        if tp == "atardecer":
            if s.get("noche_word"): self.sfx(TI.f_de_t(T(s["noche_word"])), "bajada", .7)
            if s.get("luna_word"): self.sfx(TI.f_de_t(T(s["luna_word"])), "campana", .45)
            for j in range(6): self.sfx(TI.f_de_t(T(s["noche_word"]) + .4 + j * .2), "tic", .35) if s.get("noche_word") else None
        if tp == "hambre" and s.get("hambre_word"):
            th = T(s["hambre_word"]); self.sfx(TI.f_de_t(th), "vibra", 1.0); self.sfx(TI.f_de_t(th + .7), "vibra", .7)
            for j in range(5): self.sfx(TI.f_de_t(th + .1 + j * .12), "pop", .3)
        if tp == "paranoia" and s.get("cree_word"):
            tc = T(s["cree_word"]); self.sfx(TI.f_de_t(tc), "susurro", 1.0); self.sfx(TI.f_de_t(tc + .9), "susurro", .7)
            for j in range(5): self.sfx(TI.f_de_t(tc + j * .18), "parpadeo", .5)
        if tp == "insomne":
            if s.get("palillos_word"): self.sfx(TI.f_de_t(T(s["palillos_word"]) + .3), "clac", 1.0); self.sfx(TI.f_de_t(T(s["palillos_word"]) + .42), "clac", .8)
            if s.get("caen_word"): self.sfx(TI.f_de_t(T(s["caen_word"]) + .45), "clac", .7); self.sfx(TI.f_de_t(T(s["caen_word"]) + .8), "zzz", .9)
            if s.get("bolsa_word"): pon(T(s["bolsa_word"]), "pop", .5)
            for k in s.get("ojos", [])[1:]: self.sfx(TI.f_de_t(T(k["word"])), "parpadeo", .7)
        if tp == "calendario":
            tw = T(s["word"]); d = s.get("dur", 2.0); n = s.get("dias", 11) - 1
            for j in range(n): self.sfx(TI.f_de_t(tw + d * (j + .5) / n), "arranca", .7)
            if s.get("sello_txt"): self.sfx(TI.f_de_t(tw + d + .05), "sello", .8)
        if tp == "conducir":
            self.sfx(TI.f_de_t(e["t0"] + .2), "motor", .8)
            if s.get("eses_word"): self.sfx(TI.f_de_t(T(s["eses_word"])), "motor", .9)
            if s.get("medidor"):
                for q in (s["medidor"].get("pasos") or [s["medidor"]]): self.rodillo(T(q["word"]), 1.0); self.sfx(TI.f_de_t(T(q["word"]) + 1.0), "bip", .8)
            if s.get("eses2_word"): self.sfx(TI.f_de_t(T(s["eses2_word"])), "motor", 1.0)
        if tp == "neuronas":
            if s.get("apaga_word"):
                for j in range(3): self.sfx(TI.f_de_t(T(s["apaga_word"]) + j * .45), "bajada", .5)
            if s.get("micro_word"): self.sfx(TI.f_de_t(T(s["micro_word"]) + .45), "glitch", 1.0)
        if tp == "limpieza":
            if s.get("duerme_word"): self.sfx(TI.f_de_t(T(s["duerme_word"])), "ola", 1.0)
            if s.get("acumula_word"):
                for j in range(5): self.sfx(TI.f_de_t(T(s["acumula_word"]) + j * .22), "pop", .3)
        if tp == "alucina":
            if s.get("sombra_word"): self.sfx(TI.f_de_t(T(s["sombra_word"])), "susurro", 1.0)
            if s.get("ojos_word"):
                for j in range(3): self.sfx(TI.f_de_t(T(s["ojos_word"]) + j * .3), "parpadeo", .6)
        if tp == "recuerdos":
            if s.get("memoria_word"):
                for j in range(4): self.sfx(TI.f_de_t(T(s["memoria_word"]) + j * .3), "destello", .35)
            if s.get("enfado_word"): self.sfx(TI.f_de_t(T(s["enfado_word"])), "vapor", 1.0)
        if tp == "dormir":
            self.sfx(TI.f_de_t(e["t0"] + .3), "zzz", .8); self.rodillo(T(s["word"]), 1.6); self.sfx(TI.f_de_t(T(s["word"]) + 1.65), "campana", .5)
        if tp == "capitulo":
            self.sfx(TI.f_de_t(e["t0"] + .25), "noti", .8)
            if s.get("pulsa_word"): self.sfx(TI.f_de_t(T(s["pulsa_word"])), "tecla", .9)

    for k, fn in (("atardecer", e_atardecer), ("hambre", e_hambre), ("paranoia", e_paranoia), ("insomne", e_insomne), ("calendario", e_calendario), ("conducir", e_conducir), ("neuronas", e_neuronas), ("limpieza", e_limpieza),
                  ("alucina", e_alucina), ("recuerdos", e_recuerdos), ("dormir", e_dormir), ("capitulo", e_capitulo)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_sueno)
