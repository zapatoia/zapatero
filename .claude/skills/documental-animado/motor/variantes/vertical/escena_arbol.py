"""Escena `arbol` de la variante vertical: árbol genealógico que se duplica por generaciones (documental 08).

guion.json → lineas[].escena (tipo "arbol"), todo opcional salvo `gens`:
  gens        [{word, g, d?, ya?}]  generaciones visibles; crece (o encoge) al llegar a la palabra (+d s). `ya`: ya estaba al entrar.
  contador    true → cifra 2^g arriba con odómetro + `etq` ("GENERACIÓN {g} · HACIA {anio}", anio = anio_base − anios_gen·g)
  etiquetas   [{g, txt}] píldora junto a la fila g mientras es la más alta
  rojo_word / rojo_fin / rojo_txt   las filas altas se desbordan y se ponen rojas (no cabe tanta gente)
  pareja_word / pareja_txt          una pareja de la fila 3 se ilumina y un antepasado repetido aparece dos veces más arriba
  caminos_word                      el mismo antepasado en varias casillas de la última fila; sus caminos hasta ti se encienden
  red_word (red_ya)                 las filas altas se cierran sobre pocos puntos: el árbol se vuelve una red (rombo)
  rey_word / rayo_word              corona en la cúspide de la red y rayo de luz hasta ti
  vecino_word / cruce_word          segunda persona con su árbol (violeta); sus antepasados se cruzan con los tuyos
  chat_word / chat_txt / chat_sub   bocadillo de mensaje entre los dos
  titulos     [{word, txt, sub}]    titular serif arriba con subtítulo espaciado
Efectos: nota que sube por cada generación, rodillo de tics en el contador, destello, golpe, campana, mensaje.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU = G["resorte"], G["aparece"], G["CX"], G["AU"]
    ORO, ORO2, ROJO, VIOLETA, BLANCO = "#F2C14E", "#FFE7A3", "#FF5A4E", "#A99BFF", "#FFFFFF"
    YTOP, YRAIZ = 450.0, 960.0

    # ---------------------------------------------------------------- sonidos nuevos (se registran sin tocar los existentes)
    def _nota(f0):
        def s():
            d = .55; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
            for m, a, dc in ((1, 1, .22), (2, .3, .12), (3, .1, .06)): x += a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t / dc)
            return x * np.minimum(1, t / .003)
        return s
    PENTA = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 2093.0]
    for k, f0 in enumerate(PENTA): AU.SFX.setdefault(f"rama{k}", (_nota(f0), -31))

    def s_campana():
        d = 1.4; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for m, a, dc in ((1, 1, .9), (2.76, .45, .5), (5.4, .22, .25), (8.9, .1, .12)): x += a * np.sin(2 * np.pi * 392 * m * t) * np.exp(-t / dc)
        return x * np.minimum(1, t / .004)
    def s_mensaje():
        d = .32; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n)
        for f0, t0 in ((1175, 0), (1568, .11)):
            k = int(t0 * AU.SR); tt = t[:n - k]; x[k:] += np.sin(2 * np.pi * f0 * tt) * np.exp(-tt / .06) * np.minimum(1, tt / .002)
        return x
    def s_subida():
        d = .6; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        f = 260 + 520 * u ** 1.5; x = np.sin(2 * np.pi * np.cumsum(f) / AU.SR) * .5 + .5 * AU._banda(AU._ruido(n, 31), 700, 3000)
        return x * np.sin(np.pi * u) ** 1.2
    def s_clac():
        d = .05; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        return (np.sin(2 * np.pi * 1300 * t) + .5 * AU._banda(AU._ruido(n, 41), 2000, 6000)) * np.exp(-t / .01)
    AU.SFX.setdefault("campana", (s_campana, -30)); AU.SFX.setdefault("mensaje", (s_mensaje, -26))
    AU.SFX.setdefault("subida", (s_subida, -32)); AU.SFX.setdefault("clac", (s_clac, -27))

    # ---------------------------------------------------------------- tiempo de las generaciones
    def _eventos(self, e):
        ev = []
        for k in e["spec"]["gens"]:
            t = -99.0 if k.get("ya") else self.ta(k["word"], e) + k.get("d", 0)
            ev.append((t, k["g"]))
        ev.sort(key=lambda x: x[0]); return ev

    def _estado(self, e, t):
        """→ G actual, Gv (escala suave), prog[g] (0..1 de cada fila), t_ultimo cambio."""
        ev = _eventos(self, e); g0 = 0; gv = None; prog = {}
        alta, baja = {}, {}
        for te, g in ev:
            if te > t: break
            for r in range(g0 + 1, g + 1): alta[r] = te; baja.pop(r, None)
            for r in range(g + 1, g0 + 1): baja[r] = te
            g0 = g
        for r in range(1, 13):
            if r in alta and r <= g0: prog[r] = TI.clamp((t - alta[r]) / .55)
            elif r in baja: prog[r] = 1 - TI.clamp((t - baja[r]) / .45)
            else: prog[r] = 0.0
        prev = None
        for te, g in ev:
            tgt = max(3.4, g)
            if prev is None: gv = tgt; prev = tgt; continue
            u = TI.cubic_out(TI.clamp((t - te) / .8)) if t > te else 0
            gv += (tgt - prev) * u; prev = tgt
        return g0, gv or 4, prog

    def _gmax(self, e):
        return max(k["g"] for k in e["spec"]["gens"])

    # ---------------------------------------------------------------- geometría
    def _filas(self, e, t, cx, gv, gtop, esc=1.0, ytop=YTOP, yraiz=YRAIZ):
        s = e["spec"]
        ur = self._u(s, "rojo_word", e, t, .7, fin="rojo_fin")
        un = self._u(s, "red_word", e, t, 1.1) if not s.get("red_ya") else 1.0
        P = {0: np.array([[cx, yraiz]])}
        for g in range(1, gtop + 1):
            f = g / gv
            y = yraiz - (yraiz - ytop) * f ** .9
            hw = (95 + 345 * f ** .95) * esc
            if ur > 0 and g > 4: hw *= 1 + 1.1 * ur * ((g - 4) / max(1, gtop - 4)) ** 1.3
            n = 2 ** g; xs = cx + hw * (((np.arange(n) + .5) / n) * 2 - 1)
            if un > 0 and g >= 3 and gtop > 3:
                k = max(1, int(round(6 * (1 - (g - 3) / (gtop - 3)) ** 1.2))) if g > 3 else 6
                hk = (95 + 345 * (3 / gv) ** .95) * 1.55 * esc * (1 - (g - 3) / (gtop - 3 + .6)) ** .9
                i = np.arange(n); slot = ((i * k) // n + (i % 3 == 1) * (g % 2) - (i % 5 == 3)) % k
                xc = cx + (hk * ((slot + .5) / k * 2 - 1) if k > 1 else 0 * slot)
                xs = xs + (xc - xs) * TI.cubic_out(un)
            P[g] = np.stack([xs, np.full(n, y)], 1)
        return P

    def _u(self, s, clave, e, t, d, fin=None):
        w = s.get(clave)
        if not w: return 0.0
        u = TI.cubic_out(TI.clamp((t - self.ta(w, e)) / d))
        if fin and s.get(fin): u *= 1 - TI.cubic_out(TI.clamp((t - self.ta(s[fin], e)) / .6))
        return u

    def _mezcla(a, b, u):
        ca, cb = np.array(color(a), float), np.array(color(b), float)
        return int(ca + (cb - ca) * u)

    # ---------------------------------------------------------------- dibujo de piezas
    def _ramas(self, c, P, prog, gtop, col_fn, alfa=1.0, brillo=True, grosor=1.0):
        for g in range(1, gtop + 1):
            pg = prog.get(g, 1.0)
            if pg <= 0: continue
            hijos = P[g - 1][np.arange(2 ** g) // 2]; pad = P[g]
            fin = hijos + (pad - hijos) * TI.cubic_out(pg)
            path = skia.Path()
            for (x0, y0), (x1, y1) in zip(hijos, fin): path.moveTo(x0, y0); path.lineTo(x1, y1)
            col = col_fn(g); lw = max(.55, 2.4 - .2 * g) * grosor; al = alfa * max(.35, 1 - .06 * g)
            if brillo and g <= 7:
                c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=lw * 4, Color=color(col, .16 * al),
                                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
            c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=lw, Color=color(col, al)))
            # nodos
            if pg > .6:
                an = TI.clamp((pg - .6) / .4) * alfa
                r = max(1.1, 7.5 - .75 * g); pts = P[g]
                if 2 ** g <= 128:
                    halo = skia.Paint(AntiAlias=True, Color=color(col, .35 * an), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 1.6))
                    for x, y in pts: c.drawCircle(x, y, r * 2.2, halo)
                pn = skia.Path()
                for x, y in pts: pn.addCircle(x, y, r * (.9 if 2 ** g > 128 else 1))
                c.drawPath(pn, relleno(ORO2 if col == ORO else col, .95 * an))

    def _avatar(self, c, x, y, sc, ropa, pelo, largo=False, a=1.0, boca=0.0):
        """Busto con volumen: hombros con degradado que se funde abajo, cuello, cabeza con luz, pelo, ojos y sonrisa."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.scale(sc, sc)
        piel, piel2 = "#E2A57A", "#B9764F"
        if largo:   # melena detrás
            p = skia.Path(); p.addRRect(rrc(0, 28, 150, 170, 60))
            c.drawPath(p, relleno(pelo, a))
        # hombros
        hom = skia.Path(); hom.moveTo(-125, 150); hom.cubicTo(-125, 85, -70, 62, 0, 62); hom.cubicTo(70, 62, 125, 85, 125, 150); hom.close()
        c.drawPath(hom, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 62), (0, 150)], [color(ropa, a), color(ropa, 0)])))
        cap = skia.Path(); cap.moveTo(-58, 70); cap.quadTo(0, 112, 58, 70)
        c.drawPath(cap, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color=color("#000000", .18 * a)))
        # cuello
        c.drawRRect(rrc(0, 52, 34, 40, 10), relleno(piel2, a))
        # cabeza
        c.drawCircle(-56, 0, 12, relleno(piel2, a)); c.drawCircle(56, 0, 12, relleno(piel2, a))
        c.drawOval(skia.Rect(-56, -66, 56, 62), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-16, -24), 90, [color(piel, a), color(piel2, a)])))
        # pelo
        hp = skia.Path(); hp.moveTo(-60, 2); hp.cubicTo(-66, -60, -30, -78, 0, -76); hp.cubicTo(36, -78, 68, -58, 60, 2)
        hp.cubicTo(52, -24, 40, -34, 22, -36); hp.lineTo(16, -26); hp.lineTo(4, -36); hp.lineTo(-8, -25); hp.lineTo(-18, -36); hp.cubicTo(-40, -34, -54, -22, -60, 2); hp.close()
        c.drawPath(hp, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -78), (0, 0)], [color(pelo, a), color("#2A1A10", a)])))
        if largo:
            for sx in (-1, 1):
                lp = skia.Path(); lp.moveTo(sx * 60, -6); lp.cubicTo(sx * 70, 40, sx * 66, 80, sx * 62, 110); lp.lineTo(sx * 44, 106); lp.cubicTo(sx * 50, 60, sx * 52, 30, sx * 46, -10); lp.close()
                c.drawPath(lp, relleno(pelo, a))
        # cara
        for sx in (-1, 1):
            c.drawOval(skia.Rect(sx * 22 - 6, 4, sx * 22 + 6, 15), relleno("#2B1B14", a))
            c.drawCircle(sx * 22 + 2, 7, 1.8, relleno(BLANCO, .9 * a))
            c.drawLine(sx * 22 - 9, -7, sx * 22 + 9, -9 if sx < 0 else -7, trazo("#4A2E1E", 3, .8 * a))
        sm = skia.Path(); sm.moveTo(-14, 34); sm.quadTo(0, 44 + 8 * boca, 14, 34)
        c.drawPath(sm, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2, Color=color("#6B3524", a), StrokeCap=skia.Paint.kRound_Cap))
        c.restore()

    def _corona(self, c, x, y, sc, a):
        if a <= 0: return
        c.save(); c.translate(x, y); c.scale(sc, sc)
        c.drawCircle(0, 0, 120, skia.Paint(AntiAlias=True, Color=color(ORO, .28 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
        p = skia.Path(); p.moveTo(-80, 40); p.lineTo(-86, -30); p.lineTo(-48, 6); p.lineTo(-26, -50); p.lineTo(0, 0); p.lineTo(26, -50)
        p.lineTo(48, 6); p.lineTo(86, -30); p.lineTo(80, 40); p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -50), (0, 40)], [color("#FFF0B8", a), color("#C98A1A", a)])))
        c.drawPath(p, trazo("#7A4E08", 2.5, .7 * a))
        c.drawRRect(rrc(0, 36, 172, 22, 8), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 25), (0, 47)], [color("#FFE08A", a), color("#A86E10", a)])))
        for k, (jx, col) in enumerate(((-56, "#D63A3A"), (-18, "#2F6BFF"), (18, "#2FBF71"), (56, "#D63A3A"))):
            c.drawCircle(jx, 36, 7, relleno(col, a)); c.drawCircle(jx - 2, 34, 2.2, relleno(BLANCO, .8 * a))
        for jx, jy in ((-86, -30), (-26, -50), (26, -50), (86, -30)): c.drawCircle(jx, jy, 7, relleno("#FFF4CC", a))
        c.restore()

    def _titulo(self, c, s, e, t, S):
        tts = [q for q in s.get("titulos", []) if t >= self.ta(q["word"], e) - .05]
        if not tts: return
        q = tts[-1]; dt = t - self.ta(q["word"], e)
        a = aparece(dt + .05, .18)
        sig = [x for x in s.get("titulos", []) if self.ta(x["word"], e) > self.ta(q["word"], e)]
        if sig: a *= TI.clamp((self.ta(sig[0]["word"], e) - .08 - t) / .12)
        fk = self.F["keyserif"]; w = ancho(q["txt"], fk); esc = min(1.0, 820 / w) * (.92 + .08 * resorte(dt, 8, 10))
        c.save(); c.translate(CX, 290 + 16 * (1 - resorte(dt, 8, 10))); c.scale(esc, esc)
        with capa(c, alfa=.45 * a, blur=20): texto(c, q["txt"], 0, 0, fk, ORO)
        texto(c, q["txt"], 0, 0, fk, "#F4E9D2", alfa=a, sombra=(3, 10, .4)); c.restore()
        if q.get("sub"): texto(c, " ".join(q["sub"]), CX, 375, self.F["mini2"], S["sub"], alfa=.85 * aparece(dt - .12, .2))

    # ---------------------------------------------------------------- escena
    def e_arbol(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        G0, gv, prog = _estado(self, e, t); gtop = max([g for g in range(1, 13) if prog.get(g, 0) > 0] or [0])
        gtop = max(gtop, 1)
        ur = self._u(s, "rojo_word", e, t, .7, fin="rojo_fin"); un = 1.0 if s.get("red_ya") else self._u(s, "red_word", e, t, 1.1)
        uv = self._u(s, "vecino_word", e, t, .9)
        cx_yo = CX - 215 * uv
        esc = 1 - .42 * uv
        P = _filas(self, e, t, cx_yo, gv, gtop, esc, ytop=s.get("ytop", YTOP))
        def col_fn(g):
            cg = ORO
            if ur > 0 and g > 4: cg = _hex(_lerp(ORO, ROJO, ur * min(1, (g - 4) / 2)))
            return cg
        # vecino: árbol violeta que se cruza con el tuyo
        if uv > 0:
            cx_v = CX + 215 + 200 * (1 - uv); gv2 = 4
            Pv = _filas(self, e, t, cx_v, gv2, min(gtop, 4), esc)
            uc = self._u(s, "cruce_word", e, t, 1.0)
            if uc > 0 and 4 in Pv and 4 in P:
                orden = np.random.default_rng(8).permutation(len(P[4]))[:len(Pv[4])]
                Pv[4] = Pv[4] + (P[4][orden] - Pv[4]) * uc
                if 3 in Pv and 3 in P:
                    orden3 = np.random.default_rng(9).permutation(len(P[3]))[:4]
                    Pv[3][::2] = Pv[3][::2] + (P[3][orden3] - Pv[3][::2]) * uc * .0
            self._ramas(c, Pv, {g: TI.clamp((t - self.ta(s["vecino_word"], e)) / .5 - (g - 1) * .35) for g in range(1, 5)}, min(gtop, 4), lambda g: VIOLETA, uv)
        self._ramas(c, P, prog, gtop, col_fn)
        # chispas: puntos de luz que suben por las ramas (el árbol nunca está quieto)
        if gtop >= 2:
            rng = np.random.default_rng(17); halo = skia.Paint(AntiAlias=True, Color=color(ORO2, .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
            for q in range(14):
                per = 2.2 + 1.4 * rng.random(); ph = ((t + rng.random() * per) % per) / per; j = int(rng.integers(0, 2 ** gtop))
                m = ph * gtop; g = int(m); f = m - g
                if g >= gtop or prog.get(g + 1, 0) < 1: continue
                a0 = P[g][j >> (gtop - g)]; a1 = P[g + 1][j >> (gtop - g - 1)]; x, y = a0 + (a1 - a0) * f
                al = math.sin(math.pi * ph); halo.setAlphaf(.5 * al); c.drawCircle(x, y, 7, halo); c.drawCircle(x, y, 2.4, relleno(BLANCO, .9 * al))
        # pareja: dos nodos de la fila 3 + el mismo antepasado dos veces en la fila 5
        fcm = 1 - self._u(s, "caminos_word", e, t, .35)
        up = self._u(s, "pareja_word", e, t, .5) * (1 - un) * fcm
        if up > 0 and gtop >= 5:
            for i in (2, 3):
                x, y = P[3][i]; c.drawCircle(x, y, 22, skia.Paint(AntiAlias=True, Color=color(BLANCO, .55 * up), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
                c.drawCircle(x, y, 9, relleno(BLANCO, up))
            mx = (P[3][2][0] + P[3][3][0]) / 2
            self.pildora(c, s.get("pareja_txt", ""), mx, P[3][2][1] + 52, S, up, fnt=self.F["lab"], fondo="#0B1430")
            ua = TI.clamp((t - self.ta(s["pareja_word"], e) - .6) / .5) * (1 - un) * fcm
            if ua > 0:
                a_, b_ = P[5][9], P[5][13]
                for x, y in (a_, b_):
                    pul = .8 + .2 * math.sin(t * 9)
                    c.drawCircle(x, y, 20, skia.Paint(AntiAlias=True, Color=color(ROJO, .6 * ua * pul), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
                    c.drawCircle(x, y, 8, relleno(ROJO, ua))
                arc = skia.Path(); arc.moveTo(*a_); arc.quadTo((a_[0] + b_[0]) / 2, a_[1] - 90, *b_)
                pa = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color=color(ROJO, .9 * ua)); pa.setPathEffect(skia.DashPathEffect.Make([10, 8], -t * 40))
                c.drawPath(arc, pa)
        # caminos: el mismo antepasado en varias casillas de la fila alta
        ucm = self._u(s, "caminos_word", e, t, .4)
        if ucm > 0 and gtop >= 5:
            gt = gtop; n = 2 ** gt; sel = [int(n * q) for q in (.04, .2, .37, .55, .71, .9)]
            for k, j in enumerate(sel):
                uk = TI.clamp((t - self.ta(s["caminos_word"], e) - .12 * k) / .7)
                if uk <= 0: continue
                cad = [P[g][j >> (gt - g)] for g in range(gt, -1, -1)]
                path = skia.Path(); path.moveTo(*cad[0])
                L = len(cad) - 1; m = uk * L
                for q in range(1, L + 1):
                    if q <= m: path.lineTo(*cad[q])
                    else:
                        f = m - (q - 1); x = cad[q - 1] + (cad[q] - cad[q - 1]) * f; path.lineTo(*x); break
                c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9, Color=color(BLANCO, .25 * ucm),
                                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
                c.drawPath(path, trazo(BLANCO, 2.6, .9 * ucm))
                x, y = cad[0]
                c.drawCircle(x, y, 22, skia.Paint(AntiAlias=True, Color=color(ROJO, .55 * ucm), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
                c.drawCircle(x, y, 9, relleno("#FFD0C8", ucm))
        # rojo: aviso
        if ur > .05 and s.get("rojo_txt"):
            self.pildora(c, s["rojo_txt"], CX, 330, S, ur, fnt=self.F["pillb"], fondo="#5A1010")
        # cúspide: corona y rayo
        if s.get("rey_word") and gtop >= 4:
            ap = P[gtop][0]; uk = TI.clamp((t - self.ta(s["rey_word"], e)) / .6)
            if uk > 0:
                sc = .8 * (.6 + .4 * resorte(t - self.ta(s["rey_word"], e), 7, 9))
                self._corona(c, ap[0], ap[1] - 70, sc, uk)
            if s.get("rayo_word"):
                ury = TI.clamp((t - self.ta(s["rayo_word"], e)) / 1.1)
                if ury > 0:
                    j = 2 ** gtop // 3; cad = [P[g][j >> (gtop - g)] for g in range(gtop, -1, -1)]
                    L = len(cad) - 1; m = TI.cubic_out(ury) * L; path = skia.Path(); path.moveTo(*cad[0]); cab = cad[0]
                    for q in range(1, L + 1):
                        if q <= m: path.lineTo(*cad[q]); cab = cad[q]
                        else:
                            cab = cad[q - 1] + (cad[q] - cad[q - 1]) * (m - q + 1); path.lineTo(*cab); break
                    c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=22, Color=color(ORO2, .35),
                                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
                    c.drawPath(path, trazo(BLANCO, 4, .95))
                    c.drawCircle(cab[0], cab[1], 16, skia.Paint(AntiAlias=True, Color=color(BLANCO, .9), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
        # etiquetas de fila
        for q in s.get("etiquetas", []):
            g = q["g"]
            if g > gtop or prog.get(g, 0) <= 0: continue
            a = TI.clamp((prog[g] - .5) / .3) * (1 - prog.get(g + 1, 0))
            if a > 0:
                xl = P[g][0][0] - 40; self.pildora(c, q["txt"], xl - 70, P[g][0][1], S, a, fnt=self.F["lab"], fondo="#0B1430", col=ORO2, alinear="d")
        # personas
        sc0 = .95 * (1 - .15 * uv); bo = .6 if s.get("chat_word") and t > self.ta(s["chat_word"], e) else 0
        self._avatar(c, cx_yo, 1036, sc0, "#2BA59B", "#6B4426", a=aparece(dt0 + .3, .2), boca=bo)
        if uv > 0: self._avatar(c, CX + 215 + 200 * (1 - uv), 1036, sc0, "#7C62E6", "#3A2416", largo=True, a=uv, boca=bo)
        # bocadillo
        if s.get("chat_word"):
            dc = t - self.ta(s["chat_word"], e)
            if dc > 0:
                a = aparece(dc, .12); scb = .6 + .4 * resorte(dc, 10, 13); fb = self.F["etq"]; wb = ancho(s["chat_txt"], fb) + 70
                c.save(); c.translate(CX + 40, 900); c.scale(scb, scb)
                r = rrc(0, 0, wb, 118, 26)
                c.drawRRect(r.makeOffset(0, 10) if hasattr(r, "makeOffset") else r, skia.Paint(AntiAlias=True, Color=color("#000000", .3 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
                c.drawRRect(r, relleno("#FFC94D", a))
                texto(c, s["chat_txt"], 0, -12, fb, "#1A1206", alfa=a)
                sub = s.get("chat_sub", ""); nck = sub.count("✓"); sub = sub.replace("✓", "").strip()
                if sub:
                    fs = self.F["mini"]; xs = wb / 2 - 30 - nck * 14; texto(c, sub, xs - 8, 34, fs, "#5A4416", alinear="d", alfa=a)
                    for k in range(nck):
                        x0 = xs + k * 12; p = skia.Path(); p.moveTo(x0, 33); p.lineTo(x0 + 5, 38); p.lineTo(x0 + 13, 27)
                        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.6, Color=color("#2F6BFF", a), StrokeCap=skia.Paint.kRound_Cap))
                c.restore()
        # contador arriba
        if s.get("contador"):
            ev = [x for x in _eventos(self, e) if x[0] <= t]; v = 1; va = 1
            for te, g in ev:
                u = TI.cubic_out(TI.clamp((t - te) / .5)); v = va + (2 ** g - va) * u; va = 2 ** g
            a = aparece(dt0, .2) if ev else 0
            if a > 0:
                txt = f"{int(round(v)):,}".replace(",", "."); fk = fuente("Inter", 800, 150)
                with capa(c, alfa=.4 * a, blur=18): texto(c, txt, CX, 255, fk, ORO, tnum=True)
                texto(c, txt, CX, 255, fk, "#F4E9D2", alfa=a, tnum=True, sombra=(3, 10, .4))
                g = ev[-1][1]; etq = s.get("etq", "").format(g=g, anio=_redondo(s.get("anio_base", 2026) - s.get("anios_gen", 30) * g))
                texto(c, " ".join(etq), CX, 360, self.F["mini2"], S["sub"], alfa=.85 * a)
        self._titulo(c, s, e, t, S)

    # ---------------------------------------------------------------- efectos de sonido
    def efectos_arbol(self, e, pon, libre):
        s = e["spec"]; ev = [x for x in _eventos(self, e) if x[0] > -50]
        g0 = max([g for te, g in _eventos(self, e) if te <= -50] or [0])
        for te, g in ev:
            if g > g0:
                for r in range(g0 + 1, g + 1):
                    self.sfx(TI.f_de_t(max(0, te + .02 + .12 * (r - g0 - 1))), f"rama{min(10, r - 1)}", .9)
                if s.get("contador") and g >= 3:
                    for j in range(3 + (g >= 6)): self.sfx(TI.f_de_t(te + .14 + j * .11), "tic", .5)
            g0 = g
        if s.get("contador") and ev: self.sfx(TI.f_de_t(max(0, ev[0][0] - .06)), "pop", .5)
        for clave, nombre, vol, extra in (("rojo_word", "golpe", .6, 0), ("pareja_word", "destello", .8, .05), ("caminos_word", "destello", .7, 0),
                                          ("red_word", "whoosh", .8, 0), ("rey_word", "campana", 1.0, 0), ("rayo_word", "subida", .9, 0),
                                          ("vecino_word", "pop", .6, .05), ("cruce_word", "whoosh", .6, 0), ("chat_word", "mensaje", 1.0, 0)):
            w = s.get(clave)
            if w and not (clave == "red_word" and s.get("red_ya")): pon(self.ta(w, e) + extra, nombre, vol)
        if s.get("pareja_word"): self.sfx(TI.f_de_t(self.ta(s["pareja_word"], e) + .65), "pop", .5)
        if s.get("red_word") and not s.get("red_ya"): self.sfx(TI.f_de_t(self.ta(s["red_word"], e) + .9), "golpe", .45)
        if s.get("caminos_word"):
            for k in range(6): self.sfx(TI.f_de_t(self.ta(s["caminos_word"], e) + .12 * k + .7), "tic", .55)
        for q in s.get("titulos", []): pon(self.ta(q["word"], e), "pop", .3)

    def rodillo(self, t0, dur):
        """Odómetro: tics que empiezan rápidos y frenan, y un «clac» al parar (separados ≥ 0,11 s para la mezcla)."""
        t = t0 + .02; k = 0
        while t < t0 + dur - .05:
            self.sfx(TI.f_de_t(t), "tic", .75 - .3 * (t - t0) / dur); k += 1
            t += .11 + .16 * ((t - t0) / dur) ** 2
        self.sfx(TI.f_de_t(t0 + dur + .02), "clac", .8)

    def _lerp(a, b, u):
        ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)], float); cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)], float)
        return ca + (cb - ca) * u
    def _hex(v): return "#" + "".join(f"{int(round(x)):02X}" for x in v)
    def _redondo(a): return int(round(a / 10.0) * 10)

    V.e_arbol = e_arbol; V._ramas = _ramas; V._avatar = _avatar; V._corona = _corona; V._titulo = _titulo; V._u = _u
    V.efectos_arbol = efectos_arbol; V.rodillo = rodillo
