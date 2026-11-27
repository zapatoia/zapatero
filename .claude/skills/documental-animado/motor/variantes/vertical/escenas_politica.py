"""Escenas de política / explicador de programas (documental 11): urna, programa, cita, nomina, expedientes, promesas.

urna        papeleta {word, txt, col, txt_col} que cae por la ranura; pill {txt, word?}; superficie nueva «rojo».
programa    libros [{word, anio, sub, col}] (portadas que se abren y se apilan), extra {word, txt} (tarjeta «REALIDAD»),
            contador {word, hasta, label, dur} (un solo libro que pasa hojas mientras corre el número de páginas).
cita        anio, pag, txt (cita literal), marca_word (rotulador que subraya), hoy {word, valor, desde, decimales, prefijo,
            sufijo, label, nota, dur} (la tarjeta sube y debajo rueda la cifra de hoy).
nomina      ejemplo de nómina: sube_word (sueldo +10 %), precios_word (+10 %), irpf_word (el IRPF crece más), final_word (sello).
expedientes fichas [{word, nombre, rol, nota, estado, estado_word, col}] con sello que cae.
promesas    pill, filas [{word, icono (casa|maletin|familia|hucha|irpf), perfil, txt, marca (ok|aviso)}].
Efectos: papeleta que cae, hojas que pasan, rotulador, sello, rodillo de cifras, pops y campana.
"""
import math

import numpy as np
import skia


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H, SUP, TX = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"], G["SUP"], G["TX"]
    SUP.setdefault("rojo", dict(a="#B3121C", b="#3A0509", txt="#FFFFFF", sub="#FFD6D6", acc="#FFFFFF", tierra="#7A0A10", borde="#FF9A9A", grid=False))
    PAPEL, TINTA, GRIS = "#FBF7EE", "#14182A", "#6B7183"

    # ---------------------------------------------------------------- sonidos
    def s_hoja():
        d = .22; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        x = AU._banda(AU._ruido(n, 61), 1200, 6500) * (u ** .3) * (1 - u) ** 2.2 * 3
        return x
    def s_rotu():
        d = .42; n = int(d * AU.SR); u = np.linspace(0, 1, n); t = np.arange(n) / AU.SR
        x = AU._banda(AU._ruido(n, 62), 2500, 7000) * (.7 + .3 * np.sin(2 * np.pi * 23 * t))
        return x * np.sin(np.pi * u) ** .6
    def s_caida():
        d = .3; n = int(d * AU.SR); t = np.arange(n) / AU.SR
        x = np.sin(2 * np.pi * (140 - 60 * t / d) * t) * np.exp(-t / .06) + .4 * AU._banda(AU._ruido(n, 63), 300, 2000) * np.exp(-t / .03)
        return AU._bajos(x, 1500)
    for nom, fn, db in (("hoja", s_hoja, -33), ("rotulador", s_rotu, -36), ("caida", s_caida, -27)):
        AU.SFX.setdefault(nom, (fn, db))

    def _io(u): return u * u * (3 - 2 * u)
    def _sombra(c, r, a=.3, dy=14, bl=18):
        c.drawRRect(r.makeOffset(0, dy) if hasattr(r, "makeOffset") else r, skia.Paint(AntiAlias=True, Color=color("#000000", a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, bl)))
    def _ajusta(txt, fam, peso, px, maxw):
        f = fuente(fam, peso, px); w = ancho(txt, f)
        return f if w <= maxw else fuente(fam, peso, max(10, int(px * maxw / w)))
    def _papel(c, r, a=1.0, col=PAPEL):
        """Hoja de papel con degradado suave y grano."""
        _sombra(c, r, .28 * a)
        rect = r.rect() if hasattr(r, "rect") else r
        c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, rect.top()), (0, rect.bottom())], [color(col, a), color("#EFE7D6", a)])))
        rng = np.random.default_rng(int(rect.left() + rect.top()) % 997)
        g = skia.Path()
        for _ in range(160): g.addCircle(float(rect.left() + rng.random() * rect.width()), float(rect.top() + rng.random() * rect.height()), .9)
        c.save(); c.clipRRect(r, doAntiAlias=True); c.drawPath(g, relleno("#8A7A5A", .10 * a)); c.restore()
        c.drawRRect(r, trazo("#FFFFFF", 1.5, .6 * a))

    def _rodar(self, e, t, h, desde=0.0):
        """Valor que rueda desde `desde` hasta h['valor'] tras h['word'] (cubic out), y la velocidad para el desenfoque."""
        tw = self.ta(h["word"], e); dd = h.get("dur", .9); dt = t - tw
        u = TI.cubic_out(TI.clamp(dt / dd)) if dt > 0 else 0
        v = h.get("desde", desde) + (h["valor"] - h.get("desde", desde)) * u
        vel = (1 - TI.clamp(dt / dd)) ** 2 if 0 < dt < dd else 0
        return v, vel, dt
    def _fmt(v, h):
        dec = h.get("decimales", 0)
        s = f"{v:.{dec}f}".replace(".", ",") if dec else f"{int(round(v)):,}".replace(",", ".")
        return h.get("prefijo", "") + s + h.get("sufijo", "")

    # ================================================================ URNA
    def _urna(c, cx, cy, t, a, carga=0):
        w, h, dz = 600, 430, 150          # frente y profundidad (perspectiva desde arriba)
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2 + 60, cy + h / 2 + 60
        # sombra en el suelo
        c.drawOval(skia.Rect(x0 - 40, y1 - 20, x1 + 70, y1 + 60), skia.Paint(AntiAlias=True, Color=color("#000000", .4 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
        top = skia.Path.Polygon([(x0, y0), (x1, y0), (x1 + dz * .45, y0 - dz * .55), (x0 + dz * .45, y0 - dz * .55)], True)
        lado = skia.Path.Polygon([(x1, y0), (x1 + dz * .45, y0 - dz * .55), (x1 + dz * .45, y1 - dz * .55), (x1, y1)], True)
        # papeletas dentro (se ven a través del cristal)
        rng = np.random.default_rng(4)
        c.save(); c.clipRect(skia.Rect(x0 + 6, y0 + 6, x1 - 6, y1 - 6), doAntiAlias=True)
        for k in range(14 + int(carga)):
            px_ = x0 + 40 + rng.random() * (w - 80); py_ = y1 - 40 - rng.random() * 110 - (k // 5) * 18
            c.save(); c.translate(px_, py_); c.rotate(float(rng.random() * 70 - 35))
            c.drawRect(skia.Rect(-60, -38, 60, 38), relleno("#FFFFFF", .55 * a)); c.drawRect(skia.Rect(-60, -38, 60, 38), trazo("#9AA6C0", 1.2, .5 * a))
            c.restore()
        c.restore()
        # cristal: lado, frente y tapa
        c.drawPath(lado, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x1, 0), (x1 + dz * .45, 0)], [color("#DDE6F7", .20 * a), color("#9FB1D6", .10 * a)])))
        c.drawRect(skia.Rect(x0, y0, x1, y1), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [color("#FFFFFF", .22 * a), color("#C9D6F0", .08 * a), color("#FFFFFF", .16 * a)], [0, .55, 1])))
        c.drawPath(top, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y0 - dz * .55), (0, y0)], [color("#3A3F52", .95 * a), color("#22263A", .95 * a)])))
        # reflejo que se desliza despacio
        rx = x0 + ((t * .12) % 1.6 - .3) * w
        c.save(); c.clipRect(skia.Rect(x0, y0, x1, y1), doAntiAlias=True)
        c.drawPath(skia.Path.Polygon([(rx, y0), (rx + 60, y0), (rx - 120, y1), (rx - 180, y1)], True), relleno("#FFFFFF", .10 * a)); c.restore()
        for pth in (lado, top): c.drawPath(pth, trazo("#FFFFFF", 2.5, .55 * a))
        c.drawRect(skia.Rect(x0, y0, x1, y1), trazo("#FFFFFF", 3, .7 * a))
        # ranura
        sx, sy = cx + dz * .22, y0 - dz * .27
        c.drawRRect(rrc(sx, sy, 300, 22, 11), relleno("#05060C", a)); c.drawRRect(rrc(sx, sy + 3, 300, 22, 11), trazo("#5A6178", 2, .6 * a))
        # precinto
        c.drawRect(skia.Rect(cx - 70, y0 + 28, cx + 70, y0 + 48), relleno("#E5322D", .85 * a))
        return sx, sy

    def _papeleta(c, x, y, rot, p, a, esc=1.0):
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(esc, esc)
        r = skia.Rect(-150, -100, 150, 100)
        c.drawRect(r.makeOffset(10, 16), skia.Paint(AntiAlias=True, Color=color("#000000", .3 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        c.drawRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -100), (0, 100)], [color(p.get("col", "#E30613"), a), color(p.get("col2", p.get("col", "#C8000F")), a)])))
        c.drawRect(skia.Rect(-136, -86, 136, 86), trazo(p.get("txt_col", "#FFFFFF"), 2, .35 * a))
        f = _ajusta(p["txt"], "Inter", 800, 96, 250)
        texto(c, p["txt"], 0, -6 if p.get("sub") else 0, f, p.get("txt_col", "#FFFFFF"), alfa=a)
        if p.get("sub"): texto(c, p["sub"], 0, 62, fuente("Inter", 700, 26), p.get("txt_col", "#FFFFFF"), alfa=.8 * a)
        c.restore()

    def e_urna(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; a = aparece(dt0 + .05, .2)
        cy = 760 + 30 * (1 - resorte(dt0 + .05, 7, 9))
        p = s["papeleta"]; tc = self.ta(p["word"], e); u = TI.clamp((t - tc) / .55)
        sx, sy = _urna(c, CX, cy, t, a, carga=0)
        # papeleta: flota arriba balanceándose y cae por la ranura
        fx = sx; fy0 = 395 + 10 * math.sin(t * 2.2)
        y = fy0 + (sy + 120 - fy0) * (u ** 2.2); rot = (1 - u) * 6 * math.sin(t * 1.7)
        esc = 1 - .15 * u
        if u < 1:
            c.save()
            if u > 0: c.clipRect(skia.Rect(0, 0, W, sy + 2))
            _papeleta(c, fx, y, rot, p, a * (1 - TI.clamp((u - .92) / .08)), esc)
            c.restore()
        else:
            dz = t - tc - .55
            if dz < .6:    # destello en la ranura al entrar
                with capa(c, modo=skia.BlendMode.kPlus):
                    c.drawOval(skia.Rect(sx - 220, sy - 40, sx + 220, sy + 40), skia.Paint(AntiAlias=True, Color=color("#FFE7A3", .6 * (1 - dz / .6)), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
        if s.get("pill"):
            q = s["pill"]; dp = t - (self.ta(q["word"], e) if q.get("word") else e["t0"])
            if dp > 0: self.pildora(c, q["txt"], CX, 200 + 20 * (1 - resorte(dp, 9, 12)), S, aparece(dp, .15), fnt=self.F["pillb"])

    # ================================================================ PROGRAMA (libros)
    def _libro(c, x, y, w, h, col, anio, sub, a, abre=1.0, hojas=0.0, t=0):
        """Libro cerrado en 3/4: lomo, canto de páginas y portada que se abre (abre 0→1 = portada de canto → de frente)."""
        dz = 34
        # canto de páginas (derecha y abajo)
        canto = skia.Path.Polygon([(x + w / 2, y - h / 2), (x + w / 2 + dz, y - h / 2 + dz * .5), (x + w / 2 + dz, y + h / 2 + dz * .5), (x + w / 2, y + h / 2)], True)
        base = skia.Path.Polygon([(x - w / 2, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2 + dz, y + h / 2 + dz * .5), (x - w / 2 + dz, y + h / 2 + dz * .5)], True)
        c.drawOval(skia.Rect(x - w / 2 - 20, y + h / 2 - 10, x + w / 2 + 60, y + h / 2 + 50), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20)))
        for pth in (canto, base): c.drawPath(pth, relleno("#F4EEDF", a))
        for k in range(12):
            q = k / 12
            c.drawLine(x + w / 2 + dz * q, y - h / 2 + dz * .5 * q + 4, x + w / 2 + dz * q, y + h / 2 + dz * .5 * q - 2, trazo("#C9BFA6", 1, .7 * a))
        # páginas que pasan (por encima del bloque, desde el lomo)
        if hojas > 0:
            for k in range(3):
                ph = (hojas * 3 + k / 3) % 1; sxp = math.cos(math.pi * ph)
                pg = skia.Path.Polygon([(x - w / 2, y - h / 2 + 6), (x - w / 2 + w * sxp, y - h / 2 + 6 - 30 * math.sin(math.pi * ph)), (x - w / 2 + w * sxp, y + h / 2 - 6 - 30 * math.sin(math.pi * ph)), (x - w / 2, y + h / 2 - 6)], True)
                c.drawPath(pg, relleno("#FFFDF6" if sxp > 0 else "#E9E1CC", .95 * a)); c.drawPath(pg, trazo("#BDB196", 1.2, .6 * a))
                for r_ in range(6):
                    yy = y - h / 2 + 60 + r_ * (h - 120) / 6
                    c.drawLine(x - w / 2 + 30 * (1 if sxp > 0 else -1) * abs(sxp) + (0 if sxp > 0 else w * sxp), yy, x - w / 2 + w * sxp * .85, yy - 20 * math.sin(math.pi * ph), trazo("#9A9384", 3, .25 * a * abs(sxp)))
        # portada
        sx = max(.02, abre)
        c.save(); c.translate(x - w / 2, y); c.scale(sx, 1)
        r = skia.Rect(0, -h / 2, w, h / 2)
        c.drawRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -h / 2), (w, h / 2)], [color(col, a), color(col, a)], [0, 1])))
        c.drawRect(r, relleno("#000000", .0))
        c.drawRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -h / 2), (w, h / 2)], [color("#FFFFFF", .16 * a), color("#000000", .25 * a)])))
        c.drawRect(skia.Rect(0, -h / 2, 26, h / 2), relleno("#000000", .22 * a))
        c.restore()
        if abre > .5:
            al = a * TI.clamp((abre - .5) * 2)
            texto(c, "PROGRAMA", x + 10, y - h * .30, fuente("Inter", 800, int(w * .115)), "#FFFFFF", alfa=.9 * al)
            texto(c, "ELECTORAL", x + 10, y - h * .30 + w * .13, fuente("Inter", 600, int(w * .075)), "#FFFFFF", alfa=.75 * al)
            texto(c, anio, x + 10, y + h * .08, _ajusta(anio, "Inter", 800, int(w * .34), w * .8), "#FFFFFF", alfa=al, sombra=(3, 10, .35))
            if sub: texto(c, sub, x + 10, y + h * .34, fuente("Inter", 700, int(w * .075)), "#FFFFFF", alfa=.85 * al)

    def e_programa(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        libros = s.get("libros", [])
        if s.get("pill"): self.pildora(c, s["pill"], CX, 215, S, aparece(dt0, .15), fnt=self.F["pillb"], fondo="#0C1630")
        if s.get("contador"):     # un solo libro grande que pasa hojas mientras corre el contador
            q = s["contador"]; L = libros[0]; dl = t - (self.ta(L["word"], e) if L.get("word") else e["t0"])
            ab = TI.clamp(resorte(dl + .05, 7, 9))
            v, vel, dtc = _rodar(self, e, t, dict(word=q["word"], valor=q["hasta"], desde=1, dur=q.get("dur", 1.4)))
            hojas = (t - self.ta(q["word"], e)) * 1.2 if 0 < dtc < q.get("dur", 1.4) + .1 else 0
            _libro(c, CX - 10, 560, 440, 580, L["col"], L["anio"], L.get("sub", ""), aparece(dl + .05, .2), ab, hojas, t)
            if dtc > -.1:
                a = aparece(dtc + .1, .15); txt = str(int(round(v)))
                c.save(); c.translate(CX, 1010); sc = .9 + .1 * resorte(dtc + .1, 8, 11); c.scale(sc, sc)
                with capa(c, alfa=a, blur=min(6, vel * 10)): texto(c, txt, 0, 0, fuente("Inter", 800, 170), S["txt"], tnum=True)
                c.restore(); texto(c, q.get("label", "PÁGINAS"), CX, 1125, self.F["unit"], S["acc"], alfa=a)
            return
        n = len(libros); xs = [CX - 215, CX + 215] if n == 2 else [CX]
        for k, L in enumerate(libros):
            dl = t - self.ta(L["word"], e)
            if dl < -.05: continue
            ab = TI.clamp(resorte(dl + .05, 7, 9)); y = 600 + 40 * (1 - resorte(dl + .05, 7, 9))
            hojas = 0
            _libro(c, xs[k] - 15, y, 340, 460, L["col"], L["anio"], L.get("sub", ""), aparece(dl + .05, .15), ab, hojas, t)
        x = s.get("extra")
        if x:
            dx = t - self.ta(x["word"], e)
            if dx > 0:
                a = aparece(dx, .15); sc = .8 + .2 * resorte(dx, 8, 11)
                c.save(); c.translate(CX, 1010); c.scale(sc, sc)
                f = fuente("Inter", 800, 44); w = ancho(x["txt"], f) + 150
                r = rrc(0, 0, w, 100, 50); _sombra(c, r, .3 * a)
                c.drawRRect(r, relleno("#2FBF71", a)); c.drawRRect(r, trazo("#FFFFFF", 2, .5 * a))
                texto(c, x["txt"], 28, 0, f, "#FFFFFF", alfa=a)
                # icono de gráfica
                for i, hh in enumerate((18, 30, 44)): c.drawRect(skia.Rect(-w / 2 + 34 + i * 16, 22 - hh, -w / 2 + 46 + i * 16, 22), relleno("#FFFFFF", a))
                c.restore()
                # flechas desde los libros
                u = TI.cubic_out(TI.clamp(dx / .4))
                for xb in xs:
                    c.drawLine(xb, 860, xb + (CX - xb) * .85 * u, 860 + 90 * u, trazo(S["acc"], 5, .7 * a))

    # ================================================================ CITA (programa de entonces → hoy)
    def e_cita(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; h = s.get("hoy")
        th = self.ta(h["word"], e) if h else 1e9; uh = TI.cubic_out(TI.clamp((t - th + .1) / .5))
        # tarjeta de papel con la cita
        fq = fuente("InstrumentSerif", 400, 74); esp = ancho(" ", fq)
        ws = s["txt"].split(); filas = TX.partir_lineas(ws, fq, 700, esp)
        hq = 150 + 84 * len(filas) + 40
        cy = 600 - 250 * uh + 30 * (1 - resorte(dt0 + .05, 7, 9)); esc = 1 - .14 * uh
        a = aparece(dt0 + .05, .2)
        c.save(); c.translate(CX, cy); c.scale(esc, esc); c.rotate(-1.2 * (1 - uh))
        r = rrc(0, 0, 860, hq, 26); _papel(c, r, a)
        # cabecera: «PROGRAMA PSOE 2019 · pág. 53»
        y0 = -hq / 2 + 62
        c.drawRRect(rrc(-370, y0, 46, 60, 6), relleno(s.get("col", "#E30613"), a))
        texto(c, s.get("cabecera", "PROGRAMA " + s["anio"]), -330, y0 - 12, fuente("Inter", 800, 30), TINTA, alinear="i", alfa=a)
        texto(c, s.get("pag", ""), -330, y0 + 22, fuente("Inter", 600, 26), GRIS, alinear="i", alfa=a)
        c.drawLine(-380, y0 + 50, 380, y0 + 50, trazo("#CFC6B2", 2, a))
        # rotulador
        tm = self.ta(s["marca_word"], e) if s.get("marca_word") else 1e9
        yq = y0 + 120
        for fi, fila in enumerate(filas):
            txt = " ".join(ws[j] for j in fila); wl = ancho(txt, fq); yy = yq + fi * 84
            um = TI.clamp((t - tm - fi * .28) / .32)
            if um > 0:
                c.drawRect(skia.Rect(-wl / 2 - 10, yy - 6, -wl / 2 - 10 + (wl + 20) * TI.cubic_out(um), yy + 34), relleno("#FFE15A", .75 * a))
            texto(c, txt, 0, yy, fq, TINTA, alfa=a)
        # comillas grandes
        texto(c, "“", -390, yq - 30, fuente("InstrumentSerif", 400, 160), s.get("col", "#E30613"), alfa=.5 * a)
        c.restore()
        # sello del año
        dz = dt0 - .25
        if dz > 0:
            sc = 1.6 - .6 * TI.clamp(resorte(dz, 10, 14)); al = aparece(dz, .08)
            c.save(); c.translate(CX + 330, cy - hq / 2 * esc + 10); c.rotate(-10); c.scale(sc, sc)
            c.drawRRect(rrc(0, 0, 200, 74, 12), trazo(s.get("col", "#E30613"), 5, .9 * al))
            texto(c, s["anio"], 0, 0, fuente("Inter", 800, 50), s.get("col", "#E30613"), alfa=.9 * al)
            c.restore()
        # HOY
        if h and t > th - .1:
            v, vel, dt = _rodar(self, e, t, h)
            ah = aparece(dt + .1, .15)
            self.pildora(c, "HOY", CX, 770 + 20 * (1 - resorte(dt + .1, 9, 12)), S, ah, fnt=fuente("Inter", 800, 38), fondo="#E5322D")
            txt = _fmt(v, h); f = _ajusta(_fmt(h["valor"], h), "Inter", 800, 210, 820)
            c.save(); c.translate(CX, 935); sc = .9 + .1 * resorte(dt + .1, 8, 11); c.scale(sc, sc)
            with capa(c, alfa=ah, blur=min(6, vel * 10)): texto(c, txt, 0, 0, f, S["txt"], tnum=True, sombra=(4, 14, .35))
            c.restore()
            if h.get("label"): texto(c, h["label"], CX, 1070, _ajusta(h["label"], "Inter", 700, 44, 840), S["acc"], alfa=aparece(dt - .2, .2))
            if h.get("nota"):
                dn = t - self.ta(h.get("nota_word", h["word"]), e) - .5
                if dn > 0: self.pildora(c, h["nota"], CX, 1160, S, aparece(dn, .15), fnt=self.F["nota"])

    # ================================================================ NÓMINA (ejemplo)
    def e_nomina(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]
        def u_(k, d=.7):
            w = s.get(k)
            return TI.cubic_out(TI.clamp((t - self.ta(w, e)) / d)) if w else 0
        us, up, ui, uf = u_("sube_word"), u_("precios_word", .5), u_("irpf_word", .8), u_("final_word", .3)
        self.pildora(c, s.get("pill", "EJEMPLO"), CX, 215, S, aparece(dt0, .15), fnt=self.F["pillb"], fondo="#0C1630")
        base, hmax, w = 1090, 520, 300
        cols = [(CX - 190, "ANTES", 1.0, .16, 0), (CX + 190, "DESPUÉS", 1.0 + .10 * us, .16 + .09 * ui, 1)]
        for x, lab, k, pi, j in cols:
            a = aparece(dt0 - .15 * j, .2)
            hh = hmax * k / 1.1; top = base - hh
            r = skia.Rect(x - w / 2, top, x + w / 2, base)
            c.drawRect(r.makeOffset(0, 16), skia.Paint(AntiAlias=True, Color=color("#000000", .3 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
            hi = hh * pi
            c.drawRect(skia.Rect(x - w / 2, top + hi, x + w / 2, base), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - w / 2, 0), (x + w / 2, 0)], [color("#4F86FF", a), color("#2453D6", a)])))
            c.drawRect(skia.Rect(x - w / 2, top, x + w / 2, top + hi), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - w / 2, 0), (x + w / 2, 0)], [color("#FF5A52", a), color("#C81E1E", a)])))
            c.drawRect(r, trazo("#FFFFFF", 2, .35 * a))
            texto(c, "IRPF", x, top + hi / 2, fuente("Inter", 800, 40), "#FFFFFF", alfa=a)
            texto(c, "TE QUEDA", x, top + hi + (base - top - hi) / 2, fuente("Inter", 800, 34), "#FFFFFF", alfa=.9 * a)
            texto(c, lab, x, base + 46, self.F["pillb"], S["sub"], alfa=a)
            if j == 1 and ui > 0:     # la franja roja crece y brilla
                with capa(c, modo=skia.BlendMode.kPlus):
                    c.drawRect(skia.Rect(x - w / 2 - 6, top - 6, x + w / 2 + 6, top + hi + 6), skia.Paint(AntiAlias=True, Color=color("#FF5A52", .35 * math.sin(math.pi * min(1, ui)) + .1 * ui), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
                texto(c, "▲", x + w / 2 - 34, top + hi / 2, fuente("Inter", 800, 34), "#FFFFFF", alfa=ui)
        # etiquetas en fila, arriba
        def chip(txt, y, col, u):
            if u <= 0: return
            self.pildora(c, txt, CX, y + 18 * (1 - resorte(u * .7, 9, 12)), S, min(1, u * 3), fnt=fuente("Inter", 800, 40), fondo=col)
        chip("SUELDO  +10 %", 300, "#2453D6", us)
        chip("PRECIOS  +10 %", 385, "#8B5CF6", up)
        chip("IRPF  SUBE MÁS DEL 10 %", 470, "#E5322D", ui)
        if uf > 0:
            sc = 1.5 - .5 * uf; c.save(); c.translate(CX, 780); c.rotate(-8); c.scale(sc, sc)
            f = fuente("Inter", 800, 56); txt = s.get("final_txt", "NO ERES MÁS RICO"); wt = ancho(txt, f) + 60
            c.drawRRect(rrc(0, 0, wt, 116, 16), relleno("#0B1530", .8 * uf)); c.drawRRect(rrc(0, 0, wt, 116, 16), trazo("#FF5A52", 7, uf))
            texto(c, txt, 0, 0, f, "#FF5A52", alfa=uf); c.restore()

    # ================================================================ EXPEDIENTES (causas)
    def e_expedientes(self, c, e, t, S):
        s = e["spec"]; fs = s["fichas"]; n = len(fs); hh = 270; y0 = 660 - (n - 1) * hh / 2
        for i, f in enumerate(fs):
            dt = t - self.ta(f["word"], e)
            if dt < -.1: continue
            a = aparece(dt + .1, .15); x = CX + 80 * (1 - resorte(dt + .1, 8, 11)); y = y0 + i * hh
            # pestaña de carpeta
            c.drawRRect(rrc(x - 330, y - 118, 180, 40, 10), relleno("#D9B36A", a))
            r = rrc(x, y, 860, 230, 20); _papel(c, r, a, "#F6E7C4")
            col = f.get("col", "#E5322D")
            c.drawRect(skia.Rect(x - 430, y - 115, x - 418, y + 115), relleno(col, a))
            texto(c, f["nombre"], x - 395, y - 42, _ajusta(f["nombre"], "Inter", 800, 60, 470), TINTA, alinear="i", alfa=a)
            if f.get("rol"): texto(c, f["rol"], x - 395, y + 14, fuente("Inter", 700, 28), GRIS, alinear="i", alfa=a)
            if f.get("nota"): texto(c, f["nota"], x - 395, y + 62, _ajusta(f["nota"], "Inter", 600, 28, 470), "#4A5068", alinear="i", alfa=a)
            ds = t - self.ta(f.get("estado_word", f["word"]), e) - .05
            if ds > 0:
                sc = 1.7 - .7 * TI.clamp(resorte(ds, 10, 14)); al = aparece(ds, .07)
                lineas = f["estado"].split("\n")
                fnt = fuente("Inter", 800, 38); wmax = max(ancho(l, fnt) for l in lineas)
                k = min(1.0, 270 / wmax)
                c.save(); c.translate(x + 270, y); c.rotate(-9); c.scale(sc * k, sc * k)
                bh = 60 + 46 * len(lineas); bw = wmax + 50
                c.drawRRect(rrc(0, 0, bw, bh, 14), trazo(col, 7, .92 * al)); c.drawRRect(rrc(0, 0, bw - 20, bh - 20, 8), trazo(col, 2.5, .7 * al))
                for j, l in enumerate(lineas): texto(c, l, 0, (j - (len(lineas) - 1) / 2) * 46, fnt, col, alfa=.92 * al)
                c.restore()

    # ================================================================ PROMESAS (por perfil)
    def _icono(c, tipo, x, y, a, col="#2F6BFF"):
        c.drawCircle(x, y, 44, relleno(col, .14 * a)); p = relleno(col, a); st = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=color(col, a), StrokeJoin=skia.Paint.kRound_Join)
        if tipo == "casa":
            c.drawPath(skia.Path.Polygon([(x - 26, y - 2), (x, y - 26), (x + 26, y - 2)], True), p); c.drawRect(skia.Rect(x - 19, y - 4, x + 19, y + 24), p)
            c.drawRect(skia.Rect(x - 6, y + 8, x + 6, y + 24), relleno("#FFFFFF", a))
        elif tipo == "maletin":
            c.drawRRect(rrc(x, y + 6, 54, 38, 6), p); c.drawRRect(rrc(x, y - 18, 22, 14, 4), st)
        elif tipo == "familia":
            for dx, r_, hh in ((-12, 10, 30), (14, 7, 20)):
                c.drawCircle(x + dx, y - hh / 2 - r_ + 2, r_, p); c.drawRRect(rrc(x + dx, y + 12 - (30 - hh) / 2 + 4, r_ * 2.2, hh, r_), p)
        elif tipo == "hucha":
            c.drawOval(skia.Rect(x - 26, y - 16, x + 24, y + 20), p); c.drawCircle(x + 26, y, 7, p)
            c.drawRect(skia.Rect(x - 18, y + 16, x - 10, y + 26), p); c.drawRect(skia.Rect(x + 8, y + 16, x + 16, y + 26), p)
            c.drawRect(skia.Rect(x - 8, y - 22, x + 8, y - 17), relleno("#FFFFFF", a)); c.drawCircle(x, y - 34, 8, relleno("#F2C14E", a))
        elif tipo == "irpf":
            c.drawRRect(rrc(x, y, 40, 52, 5), p); texto(c, "%", x, y + 2, fuente("Inter", 800, 30), "#FFFFFF", alfa=a)

    def e_promesas(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; fs = s["filas"]; n = len(fs); hh = 190; y0 = 660 - (n - 1) * hh / 2
        if s.get("pill"): self.pildora(c, s["pill"], CX, y0 - 140, S, aparece(dt0, .15), fnt=self.F["pillb"], fondo="#0C1630")
        for i, f in enumerate(fs):
            dt = t - self.ta(f["word"], e)
            if dt <= -.05: continue
            a = aparece(dt + .05, .15); x = CX + 70 * (1 - resorte(dt + .05, 8, 11)); y = y0 + i * hh
            aviso = f.get("marca") == "aviso"
            r = rrc(x, y, 860, 166, 26); _sombra(c, r, .18 * a)
            c.drawRRect(r, relleno("#FFFFFF", .95 * a)); c.drawRRect(r, trazo("#F2B33D" if aviso else "#9AAFD6", 3 if aviso else 2, .7 * a))
            _icono(c, f.get("icono", "casa"), x - 360, y, a, "#E08A00" if aviso else "#2F6BFF")
            texto(c, f["perfil"], x - 296, y - 34, fuente("Inter", 800, 28), "#E08A00" if aviso else "#2F6BFF", alinear="i", alfa=a)
            texto(c, f["txt"], x - 296, y + 18, _ajusta(f["txt"], "Inter", 800, 46, 600), TINTA, alinear="i", alfa=a)
            if f.get("sub"): pass
            cx_, cy_ = x + 375, y; u = TI.clamp((dt - .35) / .25)
            if aviso:
                c.drawCircle(cx_, cy_, 30, relleno("#F2B33D", .2 * a))
                if u > 0: texto(c, "!", cx_, cy_, fuente("Inter", 800, 46), "#E08A00", alfa=u)
            else:
                c.drawCircle(cx_, cy_, 30, relleno("#2FBF71", .16 * a))
                if u > 0:
                    pth = skia.Path(); pth.moveTo(cx_ - 15, cy_ + 1); pth.lineTo(cx_ - 4, cy_ + 13)
                    pth.lineTo(cx_ - 4 + 22 * TI.clamp(u * 1.4 - .4), cy_ + 13 - 28 * TI.clamp(u * 1.4 - .4))
                    c.drawPath(pth, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color=color("#2FBF71"), StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join))

    # ---------------------------------------------------------------- efectos
    def efectos_politica(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]
        if tp == "urna":
            tc = self.ta(s["papeleta"]["word"], e)
            self.sfx(TI.f_de_t(max(0, tc + .05)), "whoosh", .35); self.sfx(TI.f_de_t(tc + .55), "caida", 1.0)
            if s.get("pill") and s["pill"].get("word"): pon(self.ta(s["pill"]["word"], e), "pop", .4)
            if s.get("campana"): self.sfx(TI.f_de_t(tc + .75), "campana", .55)
        if tp == "programa":
            for L in s.get("libros", []):
                if L.get("word"):
                    tl = self.ta(L["word"], e)
                    for j in range(3): self.sfx(TI.f_de_t(tl + .02 + j * .2), "hoja", .8)
            if s.get("extra"): pon(self.ta(s["extra"]["word"], e), "pop", .45)
            if s.get("contador"):
                q = s["contador"]; tq = self.ta(q["word"], e); d = q.get("dur", 1.4)
                x = tq
                while x < tq + d: self.sfx(TI.f_de_t(x), "hoja", .55); x += .28
                self.rodillo(tq, d)
        if tp == "cita":
            self.sfx(TI.f_de_t(e["t0"] + .3), "sello", .45)
            if s.get("marca_word"): self.sfx(TI.f_de_t(self.ta(s["marca_word"], e) + .02), "rotulador", .9)
            h = s.get("hoy")
            if h:
                th = self.ta(h["word"], e); pon(th, "whoosh", .4); self.rodillo(th, h.get("dur", .9))
                if h.get("nota"): pon(self.ta(h.get("nota_word", h["word"]), e) + .5, "pop", .35)
        if tp == "nomina":
            for k, nom in (("sube_word", "subida"), ("precios_word", "pop"), ("irpf_word", "subida")):
                if s.get(k): self.sfx(TI.f_de_t(self.ta(s[k], e) + .02), nom, .8)
            if s.get("final_word"): pon(self.ta(s["final_word"], e) + .05, "sello", .6)
        if tp == "expedientes":
            for f in s["fichas"]:
                pon(self.ta(f["word"], e), "hoja", .7)
                self.sfx(TI.f_de_t(self.ta(f.get("estado_word", f["word"]), e) + .12), "sello", .65)
        if tp == "promesas":
            for f in s["filas"]:
                tf = self.ta(f["word"], e); pon(tf, "pop", .4)
                if libre(tf + .38, tf + .6): self.sfx(TI.f_de_t(tf + .38), "sello" if f.get("marca") == "aviso" else "tic", .45)

    V.e_urna = e_urna; V.e_programa = e_programa; V.e_cita = e_cita; V.e_nomina = e_nomina
    V.e_expedientes = e_expedientes; V.e_promesas = e_promesas
    for k in ("urna", "programa", "cita", "nomina", "expedientes", "promesas"): setattr(V, "efectos_" + k, efectos_politica)
