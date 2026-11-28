"""Escenas del documental 16 («La partida que nadie ha jugado jamás»).

partida   el protagonista detrás de un tablero en perspectiva; mueve_word: el peón blanco avanza dos casillas (¡TOC!);
          modo "pierde": dama negra que da mate (mate_word), el rey blanco cae y el protagonista pone cara de susto.
rejilla   mosaico infinito de tableros que se aleja (desde/hasta = tableros de ancho, word, dur) con contador que rueda
          (valor_desde → valor) y rótulo; destaca: un tablero dorado en el centro que brilla.
tablero   tablero visto desde arriba; blancas_word / negras_word: puntos de las 20 jugadas posibles; modo "medio":
          posición de medio juego con contador de jugadas (jugadas_word, jugadas).
ritmo     pantallas que escupen partidas (20 millones al día) y calendario de años que rueda (anios_word, anios).
piramide  línea del tiempo de 9.500 años con la pirámide (piramide_word) a mitad.
ceros     un 1 con 120 ceros (partidas_word) frente a un 1 con 80 ceros (atomos_word); mas_word: las partidas aplastan.
"""
import math

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
    CLARA, OSCURA, MARCO = "#EFE3C8", "#9A6B45", "#3A2416"

    # ---------------------------------------------------------------- sonidos
    def s_toc():
        d = .18; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 620 * t) + .5 * np.sin(2 * np.pi * 1450 * t)) * np.exp(-t / .025) + .3 * AU._banda(AU._ruido(n, 161), 1000, 5000) * np.exp(-t / .008)
    def s_cascada():
        d = .9; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n); rng = np.random.default_rng(162)
        for k in range(26):
            a = int((k / 26) ** 1.3 * (d - .1) * AU.SR); m = int(.05 * AU.SR); tt = t[:m]
            x[a:a + m] += np.sin(2 * np.pi * (700 + 900 * rng.random()) * tt) * np.exp(-tt / .012) * (1 - .5 * k / 26)
        return x
    def s_caerey():
        d = .5; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for t0, v in ((0, 1), (.12, .6), (.22, .35), (.29, .2)):
            a = int(t0 * AU.SR); m = int(.08 * AU.SR); tt = t[:m]; x[a:a + m] += v * np.sin(2 * np.pi * 520 * tt) * np.exp(-tt / .02)
        return x
    for nom, fn, db in (("toc", s_toc, -23), ("cascada", s_cascada, -31), ("caerey", s_caerey, -25)):
        AU.SFX.setdefault(nom, (fn, db))

    def _io(u): u = TI.clamp(u); return u * u * (3 - 2 * u)
    def _tw(self, e, k): return self.ta(e["spec"][k], e) if e["spec"].get(k) else 1e9
    def _lin(y0, y1, cols, a=1.0, x=0, pos=None): return skia.GradientShader.MakeLinear([(x, y0), (x, y1)], [color(k, a) for k in cols], pos)
    def _rad(x, y, r, cols, pos=None, a=1.0): return skia.GradientShader.MakeRadial((x, y), max(r, .1), [color(k, a) for k in cols], pos)
    def _p(sh): return skia.Paint(AntiAlias=True, Shader=sh)
    def _franja(c):
        c.drawRect(skia.Rect(-80, 1040, W + 80, H + 80), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1060), (0, 1300)], [color("#05060C", 0), color("#05060C", .72)])))
    def _fondo(c, t, a="#141A30", b="#070A16"):
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, 1300, [a, b])))
        rng = np.random.default_rng(71)
        for k in range(40):
            x = (rng.random() * W + t * (4 + 6 * rng.random())) % W; y = (rng.random() * 1200 - t * 3 * rng.random()) % 1200
            c.drawCircle(x, y, 1.2 + 2 * rng.random(), relleno("#C9A86A", .12 + .15 * rng.random()))
    def _fmt(v): return f"{int(round(v)):,}".replace(",", ".")

    # ---------------------------------------------------------------- piezas (siluetas propias)
    def pieza(c, tipo, x, y, s, blanca, a=1.0, rot=0.0):
        """(x, y) = base de la pieza; s = alto en px."""
        if a <= 0: return
        f1, f2, bo = (("#FFFFFF", "#D9CCB0", "#5A4630") if blanca else ("#4A4A58", "#15151E", "#05050A"))
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s / 100, s / 100)
        sh = _p(skia.GradientShader.MakeLinear([(-30, 0), (30, 0)], [color(f1, a), color(f2, a)]))
        st = trazo(bo, 3, .55 * a)
        def dib(p): c.drawPath(p, sh); c.drawPath(p, st)
        base = skia.Path(); base.addRRect(rrc(0, -6, 64, 14, 6)); dib(base)
        if tipo == "p":
            b = skia.Path(); b.moveTo(-20, -12); b.cubicTo(-14, -30, -10, -42, -8, -52); b.lineTo(8, -52); b.cubicTo(10, -42, 14, -30, 20, -12); b.close(); dib(b)
            h = skia.Path(); h.addCircle(0, -62, 15); dib(h)
        elif tipo == "t":
            b = skia.Path(); b.addRect(skia.Rect(-20, -64, 20, -12)); dib(b)
            cr = skia.Path(); cr.moveTo(-26, -64); cr.lineTo(-26, -88); cr.lineTo(-15, -88); cr.lineTo(-15, -78); cr.lineTo(-5, -78); cr.lineTo(-5, -88)
            cr.lineTo(5, -88); cr.lineTo(5, -78); cr.lineTo(15, -78); cr.lineTo(15, -88); cr.lineTo(26, -88); cr.lineTo(26, -64); cr.close(); dib(cr)
        elif tipo == "a":
            b = skia.Path(); b.moveTo(-18, -12); b.cubicTo(-12, -30, -8, -40, -6, -46); b.lineTo(6, -46); b.cubicTo(8, -40, 12, -30, 18, -12); b.close(); dib(b)
            m = skia.Path(); m.moveTo(0, -94); m.cubicTo(22, -80, 22, -52, 0, -46); m.cubicTo(-22, -52, -22, -80, 0, -94); dib(m)
            c.drawLine(-6, -78, 8, -64, trazo(bo, 4, .7 * a)); c.drawCircle(0, -98, 5, sh)
        elif tipo == "c":
            k = skia.Path(); k.moveTo(-22, -12); k.cubicTo(-24, -40, -10, -60, -14, -74); k.cubicTo(-10, -92, 10, -96, 22, -80)
            k.lineTo(30, -58); k.cubicTo(32, -50, 24, -46, 16, -52); k.lineTo(8, -58); k.cubicTo(6, -44, 22, -30, 22, -12); k.close(); dib(k)
            c.drawCircle(8, -76, 3.5, relleno(bo, a)); c.drawPath(skia.Path.Polygon([(-8, -88), (-2, -100), (2, -86)], True), sh)
        elif tipo in ("d", "r"):
            b = skia.Path(); b.moveTo(-22, -12); b.cubicTo(-14, -36, -12, -56, -16, -70); b.lineTo(16, -70); b.cubicTo(12, -56, 14, -36, 22, -12); b.close(); dib(b)
            if tipo == "d":
                cr = skia.Path(); cr.moveTo(-20, -70)
                for j in range(5): cr.lineTo(-20 + j * 10 + 5, -92); cr.lineTo(-20 + (j + 1) * 10, -76)
                cr.close(); dib(cr)
                for j in range(5): c.drawCircle(-15 + j * 10 - 0, -95, 4, sh)
            else:
                c.drawRRect(rrc(0, -76, 34, 14, 5), sh); c.drawRect(skia.Rect(-4, -110, 4, -82), sh); c.drawRect(skia.Rect(-12, -102, 12, -94), sh)
        c.restore()

    INI = {}
    for i, tp in enumerate("tcadract"):
        INI[(i, 0)] = (tp, False); INI[(i, 1)] = ("p", False); INI[(i, 6)] = ("p", True); INI[(i, 7)] = (tp, True)

    # ---------------------------------------------------------------- tablero visto desde arriba
    def tablero(c, x, y, L, piezas, t, a=1.0, marco=True, destacado=0.0):
        s = L / 8
        if marco:
            c.drawRRect(rrc(x, y + 14, L + 60, L + 60, 26), skia.Paint(AntiAlias=True, Color=color("#000000", .45 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
            c.drawRRect(rrc(x, y, L + 56, L + 56, 24), _p(_lin(y - L / 2, y + L / 2, ["#6A4428", MARCO], a)))
            c.drawRRect(rrc(x, y, L + 56, L + 56, 24), trazo("#C9A86A", 3, .6 * a))
        for i in range(8):
            for j in range(8):
                col = CLARA if (i + j) % 2 == 0 else OSCURA
                c.drawRect(skia.Rect(x - L / 2 + i * s, y - L / 2 + j * s, x - L / 2 + (i + 1) * s, y - L / 2 + (j + 1) * s), relleno(col, a))
        c.drawRect(skia.Rect(x - L / 2, y - L / 2, x + L / 2, y + L / 2), _p(_lin(y - L / 2, y + L / 2, ["#FFFFFF", "#000000"], .08 * a)))
        for (i, j), (tp, bl) in piezas.items():
            pieza(c, tp, x - L / 2 + (i + .5) * s, y - L / 2 + (j + .86) * s, s * .9, bl, a)

    # imagen de un mosaico de 2×2 tableros (para la rejilla: se pinta como textura, sirve para millones)
    _MOS = {}
    def mosaico():
        if "img" in _MOS: return _MOS["img"]
        N = 512; srf = skia.Surface(N, N); cv = srf.getCanvas(); cv.clear(color("#0A0D1A"))
        rng = np.random.default_rng(5)
        for q in range(4):
            ox, oy = (q % 2) * 256, (q // 2) * 256
            cv.drawRRect(rrc(ox + 128, oy + 128, 232, 232, 14), relleno("#5A3A22"))
            L = 208; s = L / 8; x0, y0 = ox + 128 - L / 2, oy + 128 - L / 2
            for i in range(8):
                for j in range(8): cv.drawRect(skia.Rect(x0 + i * s, y0 + j * s, x0 + (i + 1) * s, y0 + (j + 1) * s), relleno(CLARA if (i + j) % 2 == 0 else OSCURA))
            pz = dict(INI)
            for _ in range(2 + q):                                              # cada tablero, una apertura distinta
                i = int(rng.integers(8)); j0 = 6 if rng.random() < .5 else 1
                if (i, j0) in pz:
                    tp, bl = pz.pop((i, j0)); pz[(i, j0 + (-1 - int(rng.integers(2)) if bl else 1 + int(rng.integers(2))))] = (tp, bl)
            for (i, j), (tp, bl) in pz.items(): pieza(cv, tp, x0 + (i + .5) * s, y0 + (j + .86) * s, s * .9, bl)
        _MOS["img"] = srf.makeImageSnapshot().withDefaultMipmaps(); return _MOS["img"]

    # ---------------------------------------------------------------- partida (protagonista + tablero en perspectiva)
    def _persp(u, v):
        """u, v en 0..1 (v = 0 lejos) → pantalla; devuelve x, y y escala."""
        y0, y1, w0, w1 = 650, 1150, 560, 1000
        vv = v ** 1.15; y = y0 + (y1 - y0) * vv; w = w0 + (w1 - w0) * vv
        return CX + (u - .5) * w, y, w / 8

    def e_partida(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "mueve")
        _fondo(c, t)
        with capa(c, modo=skia.BlendMode.kPlus):                                # foco sobre la mesa
            c.drawCircle(CX, 560, 700, _p(_rad(CX, 560, 700, ["#FFE6B0", "#000000"], [0, 1], .22)))
        # protagonista detrás del tablero
        tm = _tw(self, e, "mueve_word"); tmate = _tw(self, e, "mate_word")
        cara = s.get("cara", "feliz")
        if modo == "pierde": cara = "susto" if t > tmate + .3 else "o"
        c.save(); c.clipRect(skia.Rect(-100, -100, W + 100, 680))
        self.persona_t(c, CX, 560 + 6 * math.sin(t * 1.5), 1.45, t, pose="de_pie", cara=cara, a=1.0)
        c.restore()
        # mesa
        c.drawPath(skia.Path.Polygon([(-80, 640), (W + 80, 640), (W + 80, 1300), (-80, 1300)], True), _p(_lin(640, 1300, ["#6A4428", "#2A180C"])))
        for k in range(9): c.drawLine(-80, 660 + k * 70, W + 80, 670 + k * 70, trazo("#000000", 3, .12))
        # tablero en perspectiva
        q = [_persp(0, 0), _persp(1, 0), _persp(1, 1), _persp(0, 1)]
        mp = skia.Path.Polygon([(q[0][0] - 30, q[0][1] - 18), (q[1][0] + 30, q[1][1] - 18), (q[2][0] + 46, q[2][1] + 30), (q[3][0] - 46, q[3][1] + 30)], True)
        c.drawPath(mp, _p(_lin(620, 1190, ["#7A4C2C", MARCO]))); c.drawPath(mp, trazo("#C9A86A", 3, .6))
        for i in range(8):
            for j in range(8):
                p00, p10, p11, p01 = _persp(i / 8, j / 8), _persp((i + 1) / 8, j / 8), _persp((i + 1) / 8, (j + 1) / 8), _persp(i / 8, (j + 1) / 8)
                c.drawPath(skia.Path.Polygon([p00[:2], p10[:2], p11[:2], p01[:2]], True), relleno(CLARA if (i + j) % 2 == 0 else OSCURA))
        # piezas: blancas lejos (las del protagonista), negras cerca
        pz = {}
        for i, tp in enumerate("tcadract"):
            pz[(i, 0)] = (tp, True); pz[(i, 1)] = ("p", True); pz[(i, 6)] = ("p", False); pz[(i, 7)] = (tp, False)
        anim = None
        if modo == "mueve":
            u = _io((t - tm + .15) / .45)
            pz.pop((4, 1)); anim = ("p", True, 4, 1 + 2 * u, -60 * math.sin(math.pi * u))
        else:
            pz.pop((4, 6)); pz[(4, 4)] = ("p", False)
            pz.pop((5, 1)); pz[(5, 2)] = ("p", True); pz.pop((6, 1)); pz[(6, 3)] = ("p", True)
            pz.pop((3, 7)); u = _io((t - tmate + .2) / .5)
            anim = ("d", False, 3 + 4 * u, 7 - 4 * u, -50 * math.sin(math.pi * u))                 # dama a h4: mate del loco
        orden = sorted(pz.items(), key=lambda kv: kv[0][1])
        rey_cae = TI.clamp((t - tmate - .45) / .4) if modo == "pierde" else 0
        for (i, j), (tp, bl) in orden:
            x, y, sq = _persp((i + .5) / 8, (j + .82) / 8)
            rot = 0
            if modo == "pierde" and (i, j) == (4, 0): rot = -85 * _io(rey_cae)
            pieza(c, tp, x, y, sq * 1.05, bl, 1.0, rot)
        if anim:
            tp, bl, ai, aj, lift = anim; x, y, sq = _persp((ai + .5) / 8, (aj + .82) / 8)
            c.drawOval(skia.Rect(x - sq * .4, y - sq * .12, x + sq * .4, y + sq * .12), relleno("#000000", .3))
            pieza(c, tp, x, y + lift, sq * 1.05, bl, 1.0)
        if modo == "mueve" and 0 < t - tm - .3 < .8:
            self.comic_t(c, "¡TOC!", CX + 250, 560, 80, -8, .7 + .3 * resorte(t - tm - .3, 10, 14), 1 - TI.clamp((t - tm - .85) / .25), "#FFE15A")
        if modo == "pierde" and t > tmate + .5:
            self.pildora(c, s.get("mate_txt", "JAQUE MATE"), CX, 220, S, aparece(t - tmate - .5, .15), fnt=self.F["pillb"], fondo="#8A0E14")
            if t - tmate < 1.6: self.comic_t(c, "¡PLOF!", CX + 220, 700, 70, -8, .7 + .3 * resorte(t - tmate - .7, 10, 14), aparece(t - tmate - .7, .1) * (1 - TI.clamp((t - tmate - 1.4) / .2)), "#FFFFFF")
        _franja(c)

    # ---------------------------------------------------------------- rejilla infinita de tableros
    def e_rejilla(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; tw = _tw(self, e, "word") if s.get("word") else e["t0"]
        u = ease(TI.clamp((t - tw) / s.get("dur", 2.0))) if t > tw else 0
        n0, n1 = s.get("desde", 1.0), s.get("hasta", 20.0)
        n = math.exp(math.log(n0) + (math.log(n1) - math.log(n0)) * u) * (1 + .01 * dt0)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), relleno("#0A0D1A"))
        cell = 1080 / n; img = mosaico(); k = cell * 2 / 512              # el mosaico tiene 2 tableros de lado
        cx, cy = CX, 660
        m = skia.Matrix(); m.setScale(k, k); m.postTranslate(cx - cell / 2 - cell * math.floor(0), cy - cell / 2)
        sh = img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), m)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), skia.Paint(Shader=sh))
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), skia.Paint(Shader=skia.GradientShader.MakeRadial((cx, cy), 1150, [color("#05060C", 0), color("#05060C", .6)], [.45, 1])))
        if s.get("destaca"):
            ud = _io((t - (_tw(self, e, "destaca_word") if s.get("destaca_word") else e["t0"])) / .6)
            L = cell * .9
            if ud > 0:
                with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(cx, cy, max(L, 40) * 2.2, _p(_rad(cx, cy, max(L, 40) * 2.2, ["#FFD24A", "#000000"], None, .3 * ud)))
                c.drawRRect(rrc(cx, cy, L + 10, L + 10, 8), trazo("#FFD24A", max(4, L * .04), ud)); c.drawRRect(rrc(cx, cy, L, L, 4), relleno("#FFE08A", .18 * ud))
                for q in range(2):
                    ph = ((t * .9 + q * .5) % 1); c.drawCircle(cx, cy, max(L, 30) * (.8 + 1.6 * ph), trazo("#FFD24A", 4, .8 * (1 - ph) * ud))
        # contador
        if s.get("valor") is not None:
            tv = _tw(self, e, "valor_word") if s.get("valor_word") else tw
            uv = TI.cubic_out(TI.clamp((t - tv) / s.get("dur_valor", 1.4))) if t > tv else 0
            v0, v1 = s.get("valor_desde", 1), s["valor"]
            v = math.exp(math.log(v0) + (math.log(v1) - math.log(v0)) * uv) if uv < 1 else v1
            a = aparece(t - tv + .1, .15)
            if a > 0:
                txt = _fmt(v); f = F(800, 120)
                if ancho(txt, f) > 800: f = F(800, int(120 * 800 / ancho(txt, f)))
                w = ancho(txt, f) + 90; sc = .85 + .15 * resorte(t - tv + .1, 8, 10)
                c.save(); c.translate(cx, cy); c.scale(sc, sc)
                c.drawRRect(rrc(0, 14, w, 190, 60), relleno("#000000", .5 * a)); c.drawRRect(rrc(0, 0, w, 190, 60), _p(_lin(-95, 95, ["#FFFBF0", "#EFE3C8"], a)))
                with capa(c, alfa=a, blur=(3 if 0 < uv < 1 else 0)): texto(c, txt, 0, 4, f, "#141A30", tnum=True)
                c.restore()
        if s.get("label"):
            tl = _tw(self, e, "label_word") if s.get("label_word") else e["t0"] + .3
            self.pildora(c, s["label"], cx, 260, S, aparece(t - tl, .15), fnt=self.F["pillb"], fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- tablero con las 20 jugadas / medio juego
    def e_tablero(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; _fondo(c, t)
        L = 760; x, y = CX, 650; sq = L / 8
        modo = s.get("modo", "inicio")
        if modo == "inicio":
            tablero(c, x, y, L, INI, t)
            def punto(i, j, a):
                if a <= 0: return
                px, py = x - L / 2 + (i + .5) * sq, y - L / 2 + (j + .5) * sq
                c.drawCircle(px, py, 22 * min(1, a * 1.3), relleno("#2F6BFF" if j >= 4 else "#E5322D", .85))
                c.drawCircle(px, py, 22 * min(1, a * 1.3), trazo("#FFFFFF", 3, .8 * a))
            for bando, w_, filas, cab in (("blancas_word", None, (5, 4), ((1, 7, 0, 5), (1, 7, 2, 5), (6, 7, 5, 5), (6, 7, 7, 5))),
                                          ("negras_word", None, (2, 3), ((1, 0, 0, 2), (1, 0, 2, 2), (6, 0, 5, 2), (6, 0, 7, 2)))):
                tb = _tw(self, e, bando)
                if t < tb: continue
                destinos = [(i, f) for f in filas for i in range(8)] + [(a3, b3) for (_, _, a3, b3) in cab]
                for k, (i, j) in enumerate(destinos): punto(i, j, TI.clamp((t - tb - k * .04) / .15))
                nvis = sum(1 for k in range(len(destinos)) if t > tb + k * .04)
                a = aparece(t - tb, .12)
                self.pildora(c, f"{nvis} OPCIONES", x, y - L / 2 - 80 if bando == "blancas_word" else y + L / 2 + 80, S, a, fnt=F(800, 44),
                             fondo="#2F6BFF" if bando == "blancas_word" else "#B3121C")
        else:
            pz = {(4, 7): ("r", True), (3, 7): ("t", True), (2, 6): ("p", True), (1, 6): ("p", True), (0, 6): ("p", True), (5, 6): ("p", True),
                  (6, 6): ("p", True), (7, 6): ("p", True), (1, 4): ("d", True), (4, 0): ("r", False), (7, 0): ("t", False), (5, 0): ("a", False),
                  (3, 1): ("t", False), (0, 1): ("p", False), (5, 1): ("p", False), (6, 1): ("p", False), (7, 1): ("p", False), (4, 2): ("d", False), (5, 2): ("c", False)}
            tablero(c, x, y, L, pz, t)
            tj = _tw(self, e, "jugadas_word"); uj = TI.cubic_out(TI.clamp((t - tj + .2) / 1.0)) if t > tj - .2 else 0
            n = int(round(s.get("jugadas", 40) * uj))
            if t > tj - .3:
                a = aparece(t - tj + .3, .15)
                c.save(); c.translate(x, y + L / 2 + 90); c.drawRRect(rrc(0, 0, 440, 110, 40), _p(_lin(-55, 55, ["#1C2340", "#070B1A"], .95 * a)))
                c.drawRRect(rrc(0, 0, 440, 110, 40), trazo("#FFD24A", 3, a)); texto(c, f"JUGADA {n}", 0, 0, F(800, 56), "#FFFFFF", alfa=a, tnum=True); c.restore()
        _franja(c)

    # ---------------------------------------------------------------- ritmo: 20 millones al día y años que pasan
    def e_ritmo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; _fondo(c, t, "#122A3A", "#06121C")
        ta = _tw(self, e, "anios_word"); ua = _io((t - ta + .2) / .5)
        # pantallas (móvil y portátil) que escupen partidas
        if ua < 1:
            a = 1 - ua
            for k, (x, y, w, h, r) in enumerate(((330, 560, 420, 280, 18), (760, 620, 180, 330, 30))):
                c.drawRRect(rrc(x, y + 10, w + 20, h + 20, r), relleno("#000000", .4 * a)); c.drawRRect(rrc(x, y, w + 20, h + 20, r), relleno("#2A2F44", a))
                c.drawRRect(rrc(x, y, w, h, r * .6), _p(_lin(y - h / 2, y + h / 2, ["#1E3A5A", "#0E1E30"], a)))
                tablero(c, x, y, min(w, h) * .7, INI, t, a, marco=False)
            c.drawRRect(rrc(330, 720, 520, 26, 10), relleno("#3A3F54", a))
            img = mosaico()
            for k in range(26):                                                 # partidas que salen volando
                ph = ((t - e["t0"]) * .6 + k / 26) % 1; an = -math.pi / 2 + (k % 7 - 3) * .35
                x = 520 + 600 * ph * math.cos(an) * .7; y = 560 + 700 * ph * math.sin(an) * .8 + 400 * ph * ph
                sz = 40 + 50 * ph
                c.drawImageRect(img, skia.Rect(0, 0, 256, 256), skia.Rect(x - sz / 2, y - sz / 2, x + sz / 2, y + sz / 2), skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=a * math.sin(math.pi * ph)))
            self.pildora(c, s.get("dia_txt", "≈ 20 MILLONES DE PARTIDAS AL DÍA"), CX, 990, S, a * aparece(dt0 - .3, .15), fnt=self.F["pillb"], fondo="#1E6A8A")
        if ua > 0:
            n = s.get("anios", 12); ud = TI.clamp((t - ta) / 1.8); an_ = max(1, int(1 + (n - 1) * TI.cubic_out(ud)))
            x, y = CX, 600; sc = .8 + .2 * resorte(t - ta + .2, 8, 10)
            c.save(); c.translate(x, y); c.scale(sc, sc)
            for k in range(4): c.drawRRect(rrc(8 * k, 10 + 10 * k, 520, 560, 30), relleno("#D9CDB0", ua))
            c.drawRRect(rrc(0, 0, 520, 560, 30), _p(_lin(-280, 280, ["#FFFBF0", "#EFE3C8"], ua)))
            c.drawRRect(rrc(0, -215, 520, 130, 30), relleno("#9A6B45", ua)); c.drawRect(skia.Rect(-260, -200, 260, -150), relleno("#9A6B45", ua))
            texto(c, "AÑO", 0, -215, F(800, 64), "#FFFFFF", alfa=ua)
            with capa(c, alfa=ua, blur=(3 if 0 < ud < 1 else 0)): texto(c, str(an_), 0, 70, F(800, 250), "#141A30", tnum=True)
            c.restore()
            if 0 < ud < 1:                                                       # hoja que vuela
                ph = (ud * (n - 1)) % 1; c.save(); c.translate(x + 380 * ph, y - 200 * ph); c.rotate(35 * ph)
                c.drawRRect(rrc(0, 40, 520, 430, 26), relleno("#FFFBF0", 1 - ph)); c.restore()
            if ud >= 1: self.pildora(c, s.get("anios_txt", "CASI 12 AÑOS SIN PARAR"), CX, 990, S, aparece(t - ta - 1.8, .15), fnt=self.F["pillb"], fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- pirámide y línea del tiempo
    def e_piramide(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; _fondo(c, t, "#2A1A0E", "#0E0804")
        tp = _tw(self, e, "piramide_word")
        x0, x1, yb = 90, 930, 980
        u = _io(dt0 / 1.0)
        c.drawRect(skia.Rect(-80, yb, W + 80, 1300), _p(_lin(yb, 1300, ["#C99A5A", "#7A5A2A"])))           # arena
        c.drawLine(x0, yb + 40, x0 + (x1 - x0) * u, yb + 40, trazo("#EFE3C8", 5))
        for k in range(20):
            xx = x0 + (x1 - x0) * k / 19
            if xx <= x0 + (x1 - x0) * u: c.drawLine(xx, yb + 28, xx, yb + 52, trazo("#EFE3C8", 3 if k % 5 == 0 else 2))
        texto(c, "HACE 9.500 AÑOS", x0, yb + 90, F(800, 28), "#EFE3C8", alinear="i", alfa=u)
        texto(c, "HOY", x1, yb + 90, F(800, 30), "#FFD24A", alinear="d", alfa=u)
        uh = _io((dt0 - .3) / 1.4)
        c.drawRRect(rrc(x0 + (x1 - x0) * uh / 2, 330, (x1 - x0) * uh, 70, 35), _p(skia.GradientShader.MakeLinear([(x0, 0), (x1, 0)], [color("#2F6BFF"), color("#6EA0FF")])))
        img = mosaico()
        c.drawImageRect(img, skia.Rect(0, 0, 256, 256), skia.Rect(x0 + (x1 - x0) * uh - 55, 275, x0 + (x1 - x0) * uh + 55, 385), skia.SamplingOptions(skia.FilterMode.kLinear))
        self.pildora(c, s.get("ajedrez_txt", "9.500 AÑOS PROBANDO PARTIDAS"), CX, 240, S, aparece(dt0 - .4, .15), fnt=self.F["pillb"], fondo="#2F6BFF")
        if t > tp - .2:
            ux = _io((t - tp + .2) / .7); px = x0 + (x1 - x0) * (5000 / 9500); hgt = 360 * resorte(t - tp + .2, 7, 9)
            c.drawPath(skia.Path.Polygon([(px - 260, yb + 4), (px, yb + 4 - hgt), (px + 260, yb + 4)], True), _p(_lin(yb - hgt, yb, ["#F2C27A", "#C98A3A"])))
            c.drawPath(skia.Path.Polygon([(px, yb + 4 - hgt), (px + 260, yb + 4), (px + 50, yb + 4)], True), relleno("#000000", .2))
            for k in range(1, 8): c.drawLine(px - 260 * (1 - k / 8), yb + 4 - hgt * k / 8, px + 260 * (1 - k / 8), yb + 4 - hgt * k / 8, trazo("#8A5A2A", 2, .5))
            c.drawRRect(rrc(px + (x1 - px) * ux / 2, 450, (x1 - px) * ux, 50, 25), relleno("#FFB45C", .95))
            self.pildora(c, s.get("piramide_txt", "PIRÁMIDES: ≈ 4.500 AÑOS"), (px + x1) / 2, 520, S, aparece(t - tp - .4, .15), fnt=self.F["pillb"], fondo="#8A5A2A")
        with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(860, 700, 260, _p(_rad(860, 700, 260, ["#FFB45C", "#000000"], None, .4)))
        c.drawCircle(860, 700, 60, _p(_rad(845, 685, 80, ["#FFF2B0", "#FFB43A"])))
        _franja(c)

    # ---------------------------------------------------------------- 1 con 120 ceros contra 1 con 80
    def _bloque(c, x, y, n, cols, t0, t, dig, a=1.0, col="#EFE3C8", sc=1.0):
        f = F(800, int(40 * sc)); dx, dy = 36 * sc, 46 * sc
        tot = n + 1; filas = math.ceil(tot / cols)
        for k in range(tot):
            if t < t0 + k * dig: break
            i, j = k % cols, k // cols; xx = x - (cols - 1) * dx / 2 + i * dx; yy = y - (filas - 1) * dy / 2 + j * dy
            u = TI.clamp((t - t0 - k * dig) / .12)
            texto(c, "1" if k == 0 else "0", xx, yy + 8 * (1 - u), f, "#FFD24A" if k == 0 else col, alfa=a * u)

    def e_ceros(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; _fondo(c, t, "#10142A", "#05060E")
        tpa, tat, tmas = _tw(self, e, "partidas_word"), _tw(self, e, "atomos_word"), _tw(self, e, "mas_word")
        um = _io((t - tmas) / .8)
        # partidas: 1 con 120 ceros
        if t > tpa - .1:
            img = mosaico(); a = aparece(t - tpa + .1, .15)
            c.drawImageRect(img, skia.Rect(0, 0, 256, 256), skia.Rect(90, 205, 160, 275), skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=a))
            texto(c, s.get("partidas_txt", "PARTIDAS POSIBLES"), 180, 240, F(800, 40), "#FFFFFF", alinear="i", alfa=a)
            sc = 1 + .12 * um
            with capa(c, modo=skia.BlendMode.kPlus):
                if um > 0: c.drawCircle(CX, 480, 420, _p(_rad(CX, 480, 420, ["#FFD24A", "#000000"], None, .25 * um)))
            _bloque(c, CX, 480 + 20 * um, 120, 17, tpa, t, .012, 1.0, sc=sc)
        if t > tat - .1:
            a = aparece(t - tat + .1, .15) * (1 - .5 * um); yb = 910 + 40 * um
            ax, ay = 140, 740 + 40 * um
            for k in range(3):
                c.save(); c.translate(ax, ay); c.rotate(k * 60 + t * 40); c.drawOval(skia.Rect(-46, -16, 46, 16), trazo("#6EA0FF", 3, a)); c.restore()
            c.drawCircle(ax, ay, 12, relleno("#FFB45C", a))
            texto(c, s.get("atomos_txt", "ÁTOMOS DEL UNIVERSO"), 200, ay, F(800, 40), "#FFFFFF", alinear="i", alfa=a)
            _bloque(c, CX, yb, 80, 17, tat, t, .012, a, col="#9DB8FF", sc=1 - .25 * um)
        if t > tmas + .6:
            self.pildora(c, s.get("mas_txt", "MUCHÍSIMAS MÁS PARTIDAS QUE ÁTOMOS"), CX, 1010 + 40 * um, S, aparece(t - tmas - .6, .15), fnt=self.F["pillb"], fondo="#7A4A05")
        _franja(c)

    # ---------------------------------------------------------------- efectos
    def efectos_ajedrez(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        g = lambda k: Tw(s[k]) if s.get(k) else None
        if tp == "partida":
            if g("mueve_word") is not None: sf(g("mueve_word") - .15, "whoosh", .4); sf(g("mueve_word") + .3, "toc", 1.0)
            if g("mate_word") is not None: sf(g("mate_word") - .2, "whoosh", .5); sf(g("mate_word") + .3, "toc", 1.0); sf(g("mate_word") + .5, "caerey", 1.0); sf(g("mate_word") + .55, "sello", .7)
        if tp == "rejilla":
            tw = g("word") if s.get("word") else e["t0"]
            sf(tw, "zum", .7); sf(tw + .3, "cascada", .9)
            if s.get("valor") is not None: self.rodillo(g("valor_word") if s.get("valor_word") else tw, s.get("dur_valor", 1.4))
            if s.get("destaca"): sf(g("destaca_word") if s.get("destaca_word") else e["t0"], "destello", .8)
            if s.get("label"): sf((g("label_word") if s.get("label_word") else e["t0"] + .3), "pop", .5)
        if tp == "tablero":
            for k in ("blancas_word", "negras_word"):
                tb = g(k)
                if tb is not None:
                    for j in range(0, 20, 2): sf(tb + j * .04, "pop", .35)
            if s.get("modo") == "medio":
                sf(e["t0"] + .3, "toc", .7)
                if g("jugadas_word") is not None: self.rodillo(g("jugadas_word") - .2, 1.0)
        if tp == "ritmo":
            sf(e["t0"] + .2, "cascada", .8); sf(e["t0"] + 1.0, "cascada", .6)
            if g("anios_word") is not None:
                ta = g("anios_word")
                for j in range(11): sf(ta + 1.8 * (j + .5) / 11, "arranca", .6)
                sf(ta + 1.85, "sello", .7)
        if tp == "piramide":
            sf(e["t0"] + .3, "subida", .7)
            if g("piramide_word") is not None: sf(g("piramide_word"), "golpe", .6); sf(g("piramide_word") + .4, "pop", .4)
        if tp == "ceros":
            for k in ("partidas_word", "atomos_word"):
                t0 = g(k)
                if t0 is not None:
                    for j in range(10): sf(t0 + j * .14, "tic", .45)
            if g("mas_word") is not None: sf(g("mas_word"), "subida", .8); sf(g("mas_word") + .6, "pop", .5)

    for k, fn in (("partida", e_partida), ("rejilla", e_rejilla), ("tablero", e_tablero), ("ritmo", e_ritmo), ("piramide", e_piramide), ("ceros", e_ceros)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_ajedrez)
