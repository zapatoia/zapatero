"""Escenas del documental 14 («¿Y si cayeras por un agujero que atraviesa la Tierra?»).

Física: caída por un túnel recto Madrid → antípoda, sin aire, con la densidad real de la Tierra (modelo PREM).
La tabla `estado(t)` da profundidad (km recorridos) y velocidad (km/h) para t en segundos: 38 min 9 s de punta a punta.

Comunes (campo `hud` en la escena): {desde, hasta, word, dur, capitulo, grande} → cronómetro de la caída arriba (tiempo, km, km/h).
  Con `capitulo` el cronómetro sale GRANDE en el centro, rueda y vuela a su sitio; el fondo se DESENFOCA de verdad
  (blur que sube y baja con curva suave, regla del usuario: nada de velos de golpe). `modo: "aire"` → contador de horas.
superficie  corte del suelo con cielo: modo salto (agujero_word, linea_word, salta en «saltas»), salida (asoma_word, agarra_word,
            oveja_word + oveja_txt) y cierre (pulgar_word, aire_word: mejillas infladas). cartel = texto del poste.
globo       globo terráqueo que gira de Madrid a su antípoda (madrid_word, gira_word, weber_word, madrid_txt, weber_txt).
corte       la Tierra partida por la mitad con el túnel: tunel_word, regla_word/regla_txt, crono_word, aviso_word/aviso_txt,
            punto {desde, hasta, word, dur} (subida que frena), yoyo_word (va y viene), reloj_word/reloj_txt.
tunel       el protagonista cae por el túnel; capa (tierra, roca, granito, moho, manto, nucleo, interno, centro, aire), vel (px/s),
            cara (susto, o, feliz, calor, mejillas), pose (cae, estrella, paraca), pj [x, y, escala], extras [{tipo, word, hasta, …}]:
            f1, avion, mina, taladro, calendario, termometro, crono, moho, caramelo, campo, brujula, gravedad, pluton, sol,
            velocimetro, cero, flechas, viento, dias, atrapado.
capa        la corteza con montañas, mares y ciudades (montes_word, mares_word, ciudad_word, capa_word) y la manzana (manzana_word).
mapa_es     España con Madrid → Barcelona en un destello (word) y cronómetro (crono_txt).
"""
import math
from contextlib import contextmanager

import numpy as np
import skia


# ---------------------------------------------------------------- física (PREM, sin aire)
def _tabla():
    R = 6371e3; N = 40000; rs = np.linspace(0, R, N + 1); dr = rs[1] - rs[0]; x = rs / R; rk = rs / 1e3
    rho = np.select([rk < 1221.5, rk < 3480, rk < 5701, rk < 5771, rk < 5971, rk < 6151, rk < 6346.6, rk < 6356],
                    [13.0885 - 8.8381 * x ** 2, 12.5815 - 1.2638 * x - 3.6426 * x ** 2 - 5.5281 * x ** 3,
                     7.9565 - 6.4761 * x + 5.5283 * x ** 2 - 3.0807 * x ** 3, 5.3197 - 1.4836 * x, 11.2494 - 8.0298 * x,
                     7.1089 - 3.8045 * x, 2.6910 + 0.6924 * x, 2.9 + 0 * x], 2.6 + 0 * x) * 1000
    M = np.cumsum(4 * np.pi * rs ** 2 * rho) * dr; g = 6.674e-11 * M / np.maximum(rs, 1) ** 2; g[0] = 0
    pot = np.concatenate(([0.0], np.cumsum(((g[1:] + g[:-1]) / 2 * dr)[::-1])))[::-1]
    v = np.sqrt(2 * pot)
    tc = np.concatenate(([0.0], np.cumsum((dr / ((v[1:] + v[:-1]) / 2))[::-1])))[::-1]
    return tc[::-1], ((R - rs) / 1e3)[::-1], (v * 3.6)[::-1]
_TS, _DEP, _VEL = _tabla()
TC = float(_TS[-1])                       # ≈ 1144 s al centro


def estado(ts):
    """t (s) → (km recorridos, km/h)."""
    ts = max(0.0, min(2 * TC, ts))
    if ts <= TC: return float(np.interp(ts, _TS, _DEP)), float(np.interp(ts, _TS, _VEL))
    q = 2 * TC - ts
    return 2 * 6371 - float(np.interp(q, _TS, _DEP)), float(np.interp(q, _TS, _VEL))


def instalar(V, G):
    TI, texto, ancho, fuente, color, capa, relleno, trazo, rrc = (G[k] for k in ("TI", "texto", "ancho", "fuente", "color", "capa", "relleno", "trazo", "rrc"))
    resorte, aparece, CX, AU, W, H, path_de, ease = G["resorte"], G["aparece"], G["CX"], G["AU"], G["W"], G["H"], G["path_de"], G["ease_io_expo"]
    G["SUP"].setdefault("magma", dict(a="#3A1206", b="#120402", txt="#FFFFFF", sub="#FFD9B0", acc="#FFE15A", tierra="#4A1A0A", borde="#FF8A3D", grid=False))
    PIEL = ("#F8D5B8", "#E6AC86", "#C98763")
    SUDA = ("#FF8A3D", "#F2622B", "#B8401C")     # sudadera naranja
    VAQ = ("#4F79C9", "#2F539E", "#1D3670")
    FNT = {}
    def F(peso, px, fam="Inter"):
        k = (fam, peso, px)
        if k not in FNT: FNT[k] = fuente(fam, peso, px)
        return FNT[k]

    # ---------------------------------------------------------------- sonidos (eventos cortos, nada en bucle)
    def s_viento():
        d = 1.0; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 141), 300, 3000) * np.sin(np.pi * u) ** 1.2 * (1 + .35 * np.sin(2 * np.pi * 3.3 * u))
    def s_burbuja():
        d = .5; n = int(d * AU.SR); t = np.arange(n) / AU.SR; x = np.zeros(n); rng = np.random.default_rng(142)
        for k in range(6):
            a = int(rng.random() * (n - 4000)); m = 3500; tt = t[:m]; f0 = 180 + 260 * rng.random()
            x[a:a + m] += np.sin(2 * np.pi * (f0 + 900 * tt) * tt) * np.exp(-tt / .03)
        return AU._bajos(x, 1800)
    def s_crepita():
        d = .6; n = int(d * AU.SR); x = np.zeros(n); rng = np.random.default_rng(143)
        for k in range(40):
            a = int(rng.random() * (n - 300)); x[a:a + 200] += (rng.random() - .5) * 2 * np.exp(-np.arange(200) / 30)
        return AU._banda(x, 800, 7000) * np.sin(np.pi * np.linspace(0, 1, n)) ** .5
    def s_rumor():
        d = .9; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._bajos(AU._ruido(n, 144), 160) * np.sin(np.pi * u) ** 1.5
    def s_hum():
        d = .8; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        return (np.sin(2 * np.pi * 110 * t) + .5 * np.sin(2 * np.pi * 220 * t) + .25 * np.sin(2 * np.pi * 330 * t)) * np.sin(np.pi * u) ** 2 * (1 + .2 * np.sin(2 * np.pi * 7 * t))
    def s_balido():
        d = .75; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        f = 410 + 30 * np.sin(2 * np.pi * 7.5 * t) - 60 * u; ph = np.cumsum(f) / AU.SR
        x = sum(np.sin(2 * np.pi * k * ph) / k ** .8 for k in range(1, 9))
        x = AU._banda(x, 500, 3500) * (1 + .6 * np.sign(np.sin(2 * np.pi * 7.5 * t)) * .3)
        return x * np.minimum(1, t / .04) * (1 - u) ** .6
    def s_taladro():
        d = .7; n = int(d * AU.SR); t = np.arange(n) / AU.SR; u = t / d
        return AU._banda(np.sign(np.sin(2 * np.pi * 95 * t)) * .5 + .5 * AU._ruido(n, 145), 200, 2500) * np.sin(np.pi * u) ** .6
    def s_aliento():
        d = .55; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._banda(AU._ruido(n, 146), 400, 3000) * u ** 1.5 * (1 - u) ** .3
    def s_chuf():
        d = .25; n = int(d * AU.SR); u = np.linspace(0, 1, n)
        return AU._bajos(AU._ruido(n, 147), 900) * (1 - u) ** 3
    for nom, fn, db in (("viento", s_viento, -30), ("burbuja", s_burbuja, -29), ("crepita", s_crepita, -32), ("rumor", s_rumor, -26),
                        ("hum", s_hum, -33), ("balido", s_balido, -27), ("taladro", s_taladro, -31), ("aliento", s_aliento, -31), ("chuf", s_chuf, -25)):
        AU.SFX.setdefault(nom, (fn, db))

    def _io(u): u = TI.clamp(u); return u * u * (3 - 2 * u)
    def _tw(self, e, w): return self.ta(w, e) if w else 1e9
    def _sombra(c, x, y, rx, ry, a):
        c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), skia.Paint(AntiAlias=True, Color=color("#000000", a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, ry * .7 + 4)))
    def _lin(y0, y1, cols, a=1.0, x=0):
        return skia.GradientShader.MakeLinear([(x, y0), (x, y1)], [color(k, a) for k in cols])
    def _rad(x, y, r, cols, pos=None, a=1.0):
        return skia.GradientShader.MakeRadial((x, y), max(r, .1), [color(k, a) for k in cols], pos)
    def _p(sh): return skia.Paint(AntiAlias=True, Shader=sh)
    def _comic(c, txt, x, y, px, rot, sc, a, col="#FFE15A"):
        if a <= 0: return
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
        f = F(800, px); texto(c, txt, 6, 9, f, "#14182A", alfa=a); texto(c, txt, 0, 0, f, col, alfa=a); c.restore()
    def _vis(self, e, t, x):
        """Visibilidad de un extra: entra en su palabra (resorte) y sale en `hasta` (fundido)."""
        tw = self.ta(x["word"], e) if x.get("word") else e["t0"]
        dt = t - tw
        if dt < -.05: return 0.0, dt
        a = aparece(dt + .05, .15)
        if x.get("hasta"):
            th = self.ta(x["hasta"], e) - .1; a *= TI.clamp((th - t) / .18)
        return a, dt

    # ---------------------------------------------------------------- desenfoque real del fondo en los capítulos
    def _sigma_cap(self, e, t):
        h = e["spec"].get("hud") or {}
        if not h.get("capitulo"): return 0.0
        dt0 = t - e["t0"]; gr = h.get("grande", 1.05)
        sube = _io(dt0 / .35); baja = 1 - _io((dt0 - gr) / .55)
        return 14.0 * sube * baja

    @contextmanager
    def _mundo(self, c, e, t):
        s = _sigma_cap(self, e, t)
        if s > .3:
            c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(s, s)))
            yield
            c.restore()
            c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), relleno("#05060E", .22 * s / 14))   # oscurecido con la MISMA curva suave
        else:
            yield

    # ---------------------------------------------------------------- HUD: cronómetro de la caída
    def _fmt_t(ts):
        ts = int(round(ts)); return f"{ts // 60}:{ts % 60:02d}"
    def _fmt_n(v):
        if v < 10: return f"{v:.1f}".replace(".", ",")
        return f"{int(round(v)):,}".replace(",", ".")

    def hud_t(self, e, t):
        h = e["spec"].get("hud")
        if not h: return None
        tw = self.ta(h["word"], e) if h.get("word") else e["t0"]; d = h.get("dur", 1.0)
        u = TI.cubic_out(TI.clamp((t - tw) / d)) if t > tw else 0
        return h["desde"] + (h["hasta"] - h["desde"]) * u, (0 < t - tw < d)

    def capa_hud(self, c, e, t, S):
        r = hud_t(self, e, t)
        if r is None: return
        ts, rodando = r; h = e["spec"]["hud"]; dt0 = t - e["t0"]; ts = min(ts, 2 * TC)
        x0, y0, sc = CX, 205, 1.0
        if h.get("capitulo"):
            gr = h.get("grande", 1.05); uf = _io((dt0 - gr) / .45)
            x0, y0, sc = CX, 640 + (205 - 640) * uf, 1.6 + (1 - 1.6) * uf
            if uf < 1: sc *= .86 + .14 * resorte(dt0 + .05, 8, 11)
        a = aparece(dt0 + .05, .15)
        aire = h.get("modo") == "aire"
        if aire:
            hh = e["spec"].get("hud_horas", {}); twh = self.ta(hh["word"], e) if hh.get("word") else 1e9
            uh = TI.cubic_out(TI.clamp((t - twh) / hh.get("dur", 3))) if t > twh else 0
            horas = hh.get("hasta", 32) * uh; rodando = 0 < t - twh < hh.get("dur", 3)
            grande = f"{int(horas)} H"; l1, l2 = "CON AIRE", "200 KM/H"
        else:
            km, v = estado(ts); grande = _fmt_t(ts)
            l1 = f"{_fmt_n(km)} KM"; l2 = f"{_fmt_n(v)} KM/H"
        c.save(); c.translate(x0, y0); c.scale(sc, sc)
        w, hgt = 520, 104; col = "#FFB45C"
        c.drawRRect(rrc(0, 8, w, hgt, 52), skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
        c.drawRRect(rrc(0, 0, w, hgt, 52), _p(_lin(-52, 52, ["#1A1F33", "#0A0C16"], .92 * a)))
        c.drawRRect(rrc(0, 0, w, hgt, 52), trazo(col, 2.5, .9 * a))
        if rodando:
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawRRect(rrc(0, 0, w + 10, hgt + 10, 57), skia.Paint(AntiAlias=True, Color=color(col, .22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        # icono: cronómetro / reloj
        ix = -w / 2 + 56
        c.drawCircle(ix, 4, 27, trazo("#FFFFFF", 4, a)); c.drawRRect(rrc(ix, -30, 14, 9, 3), relleno("#FFFFFF", a))
        ang = -math.pi / 2 + (t * (16 if rodando else 2.5))
        c.drawLine(ix, 4, ix + 18 * math.cos(ang), 4 + 18 * math.sin(ang), trazo(col, 4, a))
        with capa(c, alfa=a, blur=(2.5 if rodando else 0)):
            texto(c, grande, ix + 44, 2, F(800, 58), "#FFFFFF", alinear="i", tnum=True)
        c.drawLine(52, -30, 52, 34, trazo("#FFFFFF", 2, .25 * a))
        texto(c, l1, 72, -16, F(800, 30), col, alinear="i", alfa=a, tnum=True)
        texto(c, l2, 72, 22, F(700, 26), "#C9D3EA", alinear="i", alfa=a, tnum=True)
        c.restore()

    # ---------------------------------------------------------------- protagonista
    def _ojo(c, x, y, r, mira, abre=1.0, a=1.0):
        c.drawOval(skia.Rect(x - r, y - r * 1.15 * abre, x + r, y + r * 1.15 * abre), relleno("#FFFFFF", a))
        if abre > .25:
            c.drawCircle(x + mira[0] * r * .35, y + mira[1] * r * .35, r * .55, relleno("#2A1A12", a))
            c.drawCircle(x + mira[0] * r * .35 - r * .2, y + mira[1] * r * .35 - r * .22, r * .18, relleno("#FFFFFF", a))
        c.drawOval(skia.Rect(x - r, y - r * 1.15 * abre, x + r, y + r * 1.15 * abre), trazo("#5A3A28", 2.5, .6 * a))

    def _cabeza(c, t, cara, viento, a, sudor=0.0):
        """Cabeza en (0, -175). viento 0–1: pelo y cejas hacia arriba."""
        hy = -175
        # pelo de detrás (mechones que el aire levanta)
        for k in range(7):
            ang = -math.pi / 2 + (k - 3) * .32; L = 46 + 50 * viento + 10 * math.sin(t * 13 + k * 1.7) * viento
            bx, by = 58 * math.cos(ang), hy + 58 * math.sin(ang)
            ex, ey = bx + L * math.cos(ang - .08 * math.sin(t * 9 + k)), by + L * math.sin(ang) - L * .6 * viento
            pm = skia.Path(); pm.moveTo(bx - 16, by); pm.quadTo((bx + ex) / 2 - 8, (by + ey) / 2, ex, ey); pm.quadTo((bx + ex) / 2 + 10, (by + ey) / 2, bx + 16, by); pm.close()
            c.drawPath(pm, _p(_lin(by, ey, ["#3A2418", "#5A3A26"], a)))
        for sx in (-1, 1):                                                       # orejas
            c.drawOval(skia.Rect(sx * 70 - 15, hy - 14, sx * 70 + 15, hy + 22), _p(_lin(hy - 14, hy + 22, PIEL, a)))
        c.drawOval(skia.Rect(-70, hy - 74, 70, hy + 70), _p(_rad(-22, hy - 26, 110, PIEL, [0, .6, 1], a)))
        # flequillo
        fl = skia.Path(); fl.moveTo(-66, hy - 18); fl.cubicTo(-70, hy - 92, 70, hy - 98, 66, hy - 18)
        for k in range(6):
            xx = 54 - k * 22; fl.lineTo(xx - 6, hy - 38 - 14 * (k % 2) - 16 * viento); fl.lineTo(xx - 14, hy - 30)
        fl.close(); c.drawPath(fl, _p(_lin(hy - 96, hy - 20, ["#5A3A26", "#3A2418"], a)))
        c.drawOval(skia.Rect(-40, hy - 86, 6, hy - 70), relleno("#FFFFFF", .12 * a))
        # cara
        mira = (.15 * math.sin(t * 1.3), -.35 * viento)
        abre = 1.0
        if cara in ("feliz", "sonrisa") and (t % 3.1) < .12: abre = .2
        if cara == "cansado": abre = .42 + .08 * math.sin(t * 1.7)
        if cara == "dormido": abre = .06
        if cara in ("cansado", "dormido"):
            for sx in (-1, 1): c.drawOval(skia.Rect(sx * 28 - 20, hy + 8, sx * 28 + 20, hy + 24), relleno("#8A4A7A", .35 * a))
        r_ojo = 17 if cara != "susto" else 19
        for sx in (-1, 1): _ojo(c, sx * 28, hy - 4, r_ojo, mira, abre, a)
        ceja = 14 if cara in ("susto", "o") else (6 if cara == "feliz" else 10)
        for sx in (-1, 1):
            c.drawLine(sx * 14, hy - 30 - ceja - 4 * viento, sx * 42, hy - 28 - ceja - (6 if cara == "calor" else 0) * sx * 0 - 2 * viento,
                       skia.Paint(AntiAlias=True, StrokeWidth=7, Color=color("#3A2418", a), StrokeCap=skia.Paint.kRound_Cap))
        # mejillas
        mej = .35 if cara != "mejillas" else .0
        for sx in (-1, 1): c.drawCircle(sx * 44, hy + 20, 12, relleno("#FF7A7A", mej * a))
        my = hy + 38
        if cara == "susto":
            c.drawOval(skia.Rect(-17, my - 14, 17, my + 22 + 3 * math.sin(t * 20)), relleno("#5A1E1E", a)); c.drawOval(skia.Rect(-10, my + 8, 10, my + 20), relleno("#E0646E", a))
        elif cara == "o":
            c.drawOval(skia.Rect(-11, my - 8, 11, my + 14), relleno("#5A1E1E", a))
        elif cara == "feliz":
            pb = skia.Path(); pb.moveTo(-26, my - 6); pb.quadTo(0, my + 30, 26, my - 6); pb.close(); c.drawPath(pb, relleno("#5A1E1E", a))
            c.drawRect(skia.Rect(-18, my - 6, 18, my), relleno("#FFFFFF", a))
        elif cara == "calor":
            pb = skia.Path(); pb.moveTo(-22, my + 4)
            for k in range(5): pb.quadTo(-22 + k * 11 + 5.5, my + 4 + (6 if k % 2 else -6), -22 + (k + 1) * 11, my + 4)
            c.drawPath(pb, trazo("#5A1E1E", 5, a)); sudor = max(sudor, 1.0)
        elif cara == "mejillas":
            for sx in (-1, 1): c.drawCircle(sx * 40, hy + 26, 24, _p(_rad(sx * 34, hy + 18, 30, ["#FFC0A8", "#F29A82"], None, a)))
            c.drawLine(-10, my + 2, 10, my + 2, trazo("#5A1E1E", 5, a))
        elif cara == "cansado":
            c.drawLine(-16, my + 2, 16, my + 4, trazo("#5A1E1E", 5, a))
        elif cara == "dormido":
            c.drawOval(skia.Rect(-7, my - 2, 7, my + 10), relleno("#5A1E1E", a))
        else:
            c.drawArc(skia.Rect(-20, my - 12, 20, my + 10), 20, 140, False, trazo("#5A1E1E", 5, a))
        if sudor > 0:
            for k, (sx, yy) in enumerate(((1, -40), (-1, -20))):
                ph = (t * .8 + k * .5) % 1; gy = hy + yy + 40 * ph
                gpt = skia.Path(); gx = sx * 62; gpt.moveTo(gx, gy - 14); gpt.cubicTo(gx - 9, gy - 2, gx - 9, gy + 8, gx, gy + 8); gpt.cubicTo(gx + 9, gy + 8, gx + 9, gy - 2, gx, gy - 14)
                c.drawPath(gpt, relleno("#9FDCFF", .9 * sudor * a * math.sin(math.pi * ph)))

    def _miembro(c, x0, y0, a1, l1, a2, l2, grosor, cols, a, mano=None, pie=None):
        """Brazo/pierna con dos segmentos (ángulos absolutos en grados, 0 = abajo)."""
        r1, r2 = math.radians(a1), math.radians(a2)
        x1, y1 = x0 + l1 * math.sin(r1), y0 + l1 * math.cos(r1)
        x2, y2 = x1 + l2 * math.sin(r2), y1 + l2 * math.cos(r2)
        for (xa, ya, xb, yb, g) in ((x0, y0, x1, y1, grosor), (x1, y1, x2, y2, grosor * .9)):
            c.drawLine(xa, ya, xb, yb, skia.Paint(AntiAlias=True, StrokeWidth=g, StrokeCap=skia.Paint.kRound_Cap, Color=color(cols[1], a)))
            c.drawLine(xa - g * .18, ya, xb - g * .18, yb, skia.Paint(AntiAlias=True, StrokeWidth=g * .35, StrokeCap=skia.Paint.kRound_Cap, Color=color(cols[0], .55 * a)))
        if mano:
            c.drawCircle(x2, y2, grosor * .62, _p(_rad(x2 - 4, y2 - 4, grosor * .8, PIEL, [0, .6, 1], a)))
            if mano == "pulgar":
                c.drawRRect(rrc(x2 + 2, y2 - grosor * .9, grosor * .34, grosor * .8, grosor * .17), relleno(PIEL[1], a))
        if pie:
            ang = math.atan2(y2 - y1, x2 - x1)
            c.save(); c.translate(x2, y2); c.rotate(math.degrees(ang) - 90 + pie)
            c.drawRRect(rrc(8, 10, 58, 30, 14), relleno("#F4F6FA", a)); c.drawRRect(rrc(8, 20, 60, 10, 5), relleno("#C9CFDB", a))
            c.drawLine(-6, 2, 22, 2, trazo("#FF6A3D", 3, a)); c.restore()
        return x2, y2

    def persona(self, c, x, y, s, t, pose="cae", cara="o", viento=1.0, a=1.0, sudor=0.0, rot=0.0):
        """Protagonista: chaval con sudadera naranja, vaqueros y zapatillas. (x, y) = cintura."""
        if a <= 0: return
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
        w8 = lambda k, f=1.0: math.sin(t * (7 + k) * f + k * 1.3)
        if pose in ("cae", "estrella", "paraca"):
            if pose == "cae":
                bl = [(-150 + 10 * w8(1), 70, -175 + 18 * w8(2), 66), (150 + 10 * w8(3), 70, 175 + 18 * w8(4), 66)]
                pl = [(-30 + 10 * w8(5, .7), 80, 10 + 25 * w8(6, .7), 74), (30 + 10 * w8(7, .7), 80, -10 + 25 * w8(8, .7), 74)]
            elif pose == "estrella":
                q = .25 * math.sin(t * 1.4)
                bl = [(-105 + 6 * q, 74, -120 + 8 * q, 66), (105 - 6 * q, 74, 120 - 8 * q, 66)]
                pl = [(-38 + 4 * q, 84, -30, 76), (38 - 4 * q, 84, 30, 76)]
            else:   # paracaidista: codos arriba, piernas atrás
                bl = [(-110 + 6 * w8(1, .5), 70, -175 + 8 * w8(2, .5), 62), (110 + 6 * w8(3, .5), 70, 175 + 8 * w8(4, .5), 62)]
                pl = [(-30, 76, -95 + 10 * w8(5, .5), 66), (30, 76, 95 + 10 * w8(6, .5), 66)]
            # sombra de volumen
            for sx, (a1, l1, a2, l2) in zip((-1, 1), pl):
                _miembro(c, sx * 26, 40, a1, l1, a2, l2, 46, VAQ, a, pie=0)
            # cuerpo
            c.drawRRect(rrc(0, -40, 150, 176, 56), _p(_lin(-128, 48, SUDA, a)))
            c.drawRRect(rrc(-28, -46, 40, 150, 20), relleno("#FFFFFF", .10 * a))
            c.drawRRect(rrc(0, 26, 110, 40, 16), relleno(SUDA[2], .55 * a))                 # bolsillo canguro
            for sx in (-1, 1):                                                              # cordones al viento
                pc = skia.Path(); pc.moveTo(sx * 16, -108); pc.quadTo(sx * (20 + 10 * w8(9 + sx)), -150 - 30 * viento, sx * (12 + 14 * w8(11 + sx)), -170 - 40 * viento)
                c.drawPath(pc, trazo("#FFFFFF", 4, .9 * a))
            c.drawRRect(rrc(0, 46, 150, 20, 10), relleno(VAQ[1], a))                       # cintura del vaquero
            for sx, (a1, l1, a2, l2) in zip((-1, 1), bl):
                _miembro(c, sx * 62, -100, a1, l1, a2, l2, 38, SUDA, a, mano=True)
            _cabeza(c, t, cara, viento, a, sudor)
        else:   # de pie / pulgar / agachado
            ag = 1.0 if pose == "agacha" else 0.0
            for sx in (-1, 1):
                _miembro(c, sx * 26, 40, sx * (8 + 30 * ag), 100 - 10 * ag, -sx * (4 + 40 * ag), 96 - 10 * ag, 46, VAQ, a, pie=sx * 0)
            c.drawRRect(rrc(0, -40, 150, 176, 56), _p(_lin(-128, 48, SUDA, a)))
            c.drawRRect(rrc(-28, -46, 40, 150, 20), relleno("#FFFFFF", .10 * a))
            c.drawRRect(rrc(0, 26, 110, 40, 16), relleno(SUDA[2], .55 * a))
            for sx in (-1, 1):
                c.drawLine(sx * 16, -108, sx * 18, -60, trazo("#FFFFFF", 4, .9 * a))
            c.drawRRect(rrc(0, 46, 150, 20, 10), relleno(VAQ[1], a))
            if pose == "pulgar":
                _miembro(c, -62, -100, 20, 86, 10, 76, 38, SUDA, a, mano=True)
                _miembro(c, 62, -100, -60, 80, -175, 62, 38, SUDA, a, mano="pulgar")
            else:
                for sx in (-1, 1): _miembro(c, sx * 62, -100, sx * (16 + 30 * ag), 86, sx * (6 + 50 * ag), 76, 38, SUDA, a, mano=True)
            _cabeza(c, t, cara, 0.0, a, sudor)
        c.restore()

    def oveja(c, x, y, s, t, a=1.0, paso=0.0):
        c.save(); c.translate(x, y); c.scale(s, s)
        _sombra(c, 0, 92, 110, 14, .3 * a)
        for k, lx in enumerate((-60, -30, 30, 60)):
            sw = 10 * math.sin(paso * 9 + k * math.pi)
            c.drawRRect(rrc(lx + sw * .3, 62, 16, 60, 7), relleno("#2A2A30", a))
        rng = np.random.default_rng(9)
        for k in range(16):
            ax = -80 + 160 * rng.random(); ay = -30 + 60 * rng.random()
            c.drawCircle(ax, ay + 4, 34, relleno("#D9D9DE", a))
        for k in range(16):
            ax = -80 + 160 * rng.random(); ay = -34 + 56 * rng.random()
            c.drawCircle(ax, ay, 32, _p(_rad(ax - 10, ay - 12, 40, ["#FFFFFF", "#ECECF2"], None, a)))
        # cabeza
        hx, hy = -112, -22 + 3 * math.sin(t * 2)
        c.drawOval(skia.Rect(hx - 34, hy - 40, hx + 30, hy + 42), _p(_lin(hy - 40, hy + 42, ["#3A3A44", "#1E1E26"], a)))
        for sx in (-1, 1): c.drawOval(skia.Rect(hx - 6 + sx * 34 - 18, hy - 30, hx - 6 + sx * 34 + 18, hy - 14), relleno("#2A2A32", a))
        c.drawCircle(hx - 12, hy - 8, 8, relleno("#FFFFFF", a)); c.drawCircle(hx - 14, hy - 8, 4, relleno("#111111", a))
        c.drawCircle(hx + 10, hy - 8, 8, relleno("#FFFFFF", a)); c.drawCircle(hx + 8, hy - 8, 4, relleno("#111111", a))
        for k in range(4): c.drawCircle(hx - 14 + k * 12, hy - 42, 12, relleno("#FFFFFF", a))
        c.restore()

    # ---------------------------------------------------------------- superficie (salto, salida, cierre)
    def e_superficie(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; modo = s.get("modo", "salto"); T = lambda k: _tw(self, e, s.get(k))
        GY = 800; HX, HW = 610, 330; SC = 1.12                                             # suelo, centro y ancho del agujero
        nz = modo == "salida"
        with _mundo(self, c, e, t):
            # cielo
            c.drawRect(skia.Rect(-80, -80, W + 80, GY + 10), _p(_lin(0, GY, ["#4E8FEA", "#9CC8F7", "#E6F2FF"] if not nz else ["#3F86D6", "#8FC3F2", "#E9F6FF"])))
            sx_, sy_ = 830, 300
            c.drawCircle(sx_, sy_, 150, _p(_rad(sx_, sy_, 150, ["#FFF6C9", "#FFF6C9", "#FFF6C9"], None, .0)))
            c.drawCircle(sx_, sy_, 120, _p(_rad(sx_, sy_, 120, ["#FFFBE0", "#FFE58A", "#FFE58A"], [0, .55, 1], .35)))
            c.drawCircle(sx_, sy_, 56, _p(_rad(sx_ - 14, sy_ - 14, 70, ["#FFFFFF", "#FFE58A"])))
            for k in range(3):                                                  # nubes que se desplazan
                nx = (120 + k * 360 + t * (14 + 6 * k)) % (W + 400) - 200; ny = 170 + 90 * k
                for dx, dy, r in ((0, 0, 46), (44, -16, 56), (96, 0, 44), (50, 14, 50)):
                    c.drawCircle(nx + dx, ny + dy, r, relleno("#FFFFFF", .85))
            # colinas / horizonte
            if nz:
                for k, (yy, col) in enumerate(((GY - 120, "#7FBF6A"), (GY - 60, "#5DA852"))):
                    pth = skia.Path(); pth.moveTo(-80, GY + 10)
                    for xx in range(-80, W + 90, 40): pth.lineTo(xx, yy + 50 * math.sin(xx / (160 + 60 * k) + k * 2))
                    pth.lineTo(W + 80, GY + 10); pth.close(); c.drawPath(pth, relleno(col))
            else:
                pth = skia.Path(); pth.moveTo(-80, GY + 10)
                for xx in range(-80, W + 90, 30): pth.lineTo(xx, GY - 70 - 30 * math.sin(xx / 90) - 18 * math.sin(xx / 37))
                pth.lineTo(W + 80, GY + 10); pth.close(); c.drawPath(pth, relleno("#B9A27A"))
                for k in range(9):                                              # olivos
                    ox = 60 + k * 115 + 20 * (k % 2); oy = GY - 40 - 20 * (k % 3)
                    c.drawRect(skia.Rect(ox - 3, oy, ox + 3, oy + 26), relleno("#6A4A2A")); c.drawOval(skia.Rect(ox - 26, oy - 26, ox + 26, oy + 6), relleno("#6E8A4A"))
            # subsuelo por capas
            capas = [("#6B4A2E", 0), ("#5A3C24", 90), ("#4A3220", 220), ("#3B281A", 380), ("#2C1E14", 540)]
            for col, dy in capas:
                c.drawRect(skia.Rect(-80, GY + dy, W + 80, H + 80), relleno(col))
                wv = skia.Path(); wv.moveTo(-80, GY + dy)
                for xx in range(-80, W + 90, 40): wv.lineTo(xx, GY + dy + 6 * math.sin(xx / 70 + dy))
                c.drawPath(wv, trazo("#000000", 3, .15))
            rng = np.random.default_rng(14)
            for k in range(70):                                                 # piedras
                px_, py_ = rng.random() * W, GY + 30 + rng.random() * 760; r_ = 5 + 12 * rng.random()
                c.drawOval(skia.Rect(px_ - r_, py_ - r_ * .7, px_ + r_, py_ + r_ * .7), relleno("#8A6A4A" if k % 3 else "#A88A6A", .55))
            c.drawRect(skia.Rect(-80, GY - 8, W + 80, GY + 22), _p(_lin(GY - 8, GY + 22, ["#7CCB5A", "#4E9A3A"] if nz else ["#9CC15A", "#6F9A3A"])))
            for k in range(90):
                gx = k * 12 + (k % 3) * 2; c.drawLine(gx, GY - 4, gx + 3 * math.sin(t * 2 + k), GY - 16 - 6 * (k % 4), trazo("#4E9A3A" if nz else "#7EA34A", 3))
            # agujero: se abre en `agujero_word` (o ya abierto)
            ta = T("agujero_word"); ua = 1.0 if modo != "salto" else _io((t - ta) / .5)
            if ua > 0:
                hw = HW * ua; prof = (H + 80 - GY) * (1.0 if modo != "salto" else _io((t - ta - .15) / .7))
                c.drawRect(skia.Rect(HX - hw / 2, GY + 6, HX + hw / 2, GY + 6 + prof), _p(_lin(GY, GY + prof, ["#14100C", "#050403"])))
                for sx in (-1, 1):                                              # bordes con luz rasante
                    c.drawRect(skia.Rect(HX + sx * hw / 2 - (14 if sx > 0 else 0), GY + 6, HX + sx * hw / 2 + (0 if sx > 0 else 14), GY + 6 + prof), relleno("#000000", .45))
                c.drawOval(skia.Rect(HX - hw / 2 - 8, GY - 16, HX + hw / 2 + 8, GY + 22), relleno("#2A1E14"))
                c.drawOval(skia.Rect(HX - hw / 2, GY - 10, HX + hw / 2, GY + 18), _p(_lin(GY - 10, GY + 18, ["#000000", "#100A06"])))
                if modo == "salto" and 0 < t - ta < 1.0:                       # polvo al abrirse
                    for k in range(14):
                        ph = (t - ta) / 1.0; an = math.pi + k / 13 * math.pi
                        c.drawCircle(HX + math.cos(an) * (hw / 2 + 60 * ph), GY - 10 + math.sin(an) * 90 * ph, 10 + 18 * ph, relleno("#C9A27E", .5 * (1 - ph)))
            # línea discontinua: «atraviesa la Tierra»
            tl = T("linea_word")
            if t > tl:
                u = _io((t - tl) / .8); pl = trazo("#FFE15A", 6, .9); pl.setPathEffect(skia.DashPathEffect.Make([26, 18], -t * 120))
                c.drawLine(HX, GY + 30, HX, GY + 30 + (H - GY) * u, pl)
                ay = GY + 30 + (1236 - GY - 30) * u
                c.drawPath(skia.Path.Polygon([(HX - 22, ay - 30), (HX + 22, ay - 30), (HX, ay + 4)], True), relleno("#FFE15A", .9))
            # cartel
            cx_, cy_ = (170 if nz else 870), GY
            c.drawRect(skia.Rect(cx_ - 7, cy_ - 170, cx_ + 7, cy_), _p(_lin(0, 0, ["#8A5A32", "#5A3A20"])))
            f = F(800, 30); txt = s.get("cartel", ""); ww = ancho(txt, f) + 40
            c.save(); c.translate(cx_ - 30, cy_ - 150); c.rotate(-3)
            pc = skia.Path.Polygon([(-ww / 2, -30), (ww / 2 - 10, -30), (ww / 2 + 16, 0), (ww / 2 - 10, 30), (-ww / 2, 30)], True)
            c.drawPath(pc, _p(_lin(-30, 30, ["#C98A52", "#9A6232"]))); c.drawPath(pc, trazo("#5A3A20", 3))
            texto(c, txt, 0, 0, f, "#FFF4E0"); c.restore()
            # personaje
            BASE = GY - 250 * SC
            if modo == "salto":
                tj = self.ta(s.get("salta_word", "saltas"), e); dj = t - tj + .25
                if dj < 0:
                    persona(self, c, 250, BASE, SC, t, pose="de_pie", cara="o" if t > ta else "sonrisa")
                elif dj < .2:
                    persona(self, c, 250, BASE + 26 * _io(dj / .2), SC, t, pose="agacha", cara="feliz")
                else:
                    u = dj - .2; p_ = TI.clamp(u / .45)
                    xj = 250 + (HX - 250) * _io(p_); yj = BASE - 120 * math.sin(math.pi * p_)
                    if u > .45: yj = BASE + .5 * 7000 * (u - .45) ** 2
                    clip = u > .3
                    if clip:
                        cl = skia.Path(); cl.addRect(skia.Rect(-100, -100, W + 100, GY + 4)); cl.addRect(skia.Rect(HX - HW / 2 + 4, GY, HX + HW / 2 - 4, H + 100))
                        c.save(); c.clipPath(cl, doAntiAlias=True)
                    persona(self, c, xj, yj, SC, t, pose="cae", cara="susto", viento=TI.clamp(u / .4))
                    if clip: c.restore()
                    _comic(c, "¡FIUUU!", HX + 170, GY - 330, 92, -8, .7 + .3 * resorte(u, 10, 14), TI.clamp(1 - (u - .9) / .3))
            elif modo == "salida":
                tas = T("asoma_word"); u = _io((t - tas + .1) / .9)
                yh = GY + 60 + 700 * (1 - u) ** 2                       # sube frenando hasta velocidad cero
                tg = T("agarra_word"); ug = _io((t - tg) / .3)
                c.save(); c.clipRect(skia.Rect(-100, -100, W + 100, GY + 4))
                persona(self, c, HX, yh, SC, t, pose="estrella" if ug < .5 else "de_pie", cara="o" if ug < .5 else "feliz", viento=.4 * (1 - u))
                c.restore()
                if ug > 0:                                                      # manos agarradas al borde
                    for sx in (-1, 1):
                        hx_ = HX + sx * (HW / 2 + 10); hy_ = GY - 6
                        c.drawCircle(hx_, hy_ - 30 * (1 - ug), 26, _p(_rad(hx_ - 6, hy_ - 6, 34, PIEL, [0, .6, 1], ug)))
                    if t - tg < .6: _comic(c, "¡TAC!", HX - 200, GY - 120, 60, -6, .8 + .2 * resorte(t - tg, 10, 14), 1 - TI.clamp((t - tg - .4) / .2), "#FFFFFF")
                to = T("oveja_word")
                if t > to - .6:
                    uo = _io((t - to + .6) / 1.0); ox = W + 160 - (W + 160 - 830) * uo
                    oveja(c, ox, GY - 70, .9, t, 1.0, paso=(t - to) if uo < 1 else 0)
                    if t > to + .3 and s.get("oveja_txt"):
                        dd = t - to - .3; sc_ = .6 + .4 * resorte(dd, 9, 12)
                        c.save(); c.translate(760, GY - 290); c.scale(sc_, sc_)
                        c.drawRRect(rrc(0, 0, 250, 100, 50), relleno("#FFFFFF", .96)); c.drawPath(skia.Path.Polygon([(30, 40), (70, 40), (50, 90)], True), relleno("#FFFFFF", .96))
                        texto(c, s["oveja_txt"], 0, 0, F(800, 48), "#14182A"); c.restore()
            else:   # cierre: de pie al borde, pulgar arriba y aguanta el aire
                tp, tai = T("pulgar_word"), T("aire_word")
                pose = "pulgar" if t > tp else "de_pie"; cara = "mejillas" if t > tai else ("feliz" if t > tp else "o")
                c.save()
                if t > tai:
                    sc_ = 1 + .04 * resorte(t - tai, 8, 9) - .04
                else: sc_ = 1
                persona(self, c, 280, BASE, SC * sc_, t, pose=pose, cara=cara)
                c.restore()
                if t > tai:
                    self.pildora(c, s.get("aire_txt", "TÚNEL SIN AIRE ✓"), HX, GY + 110, S, aparece(t - tai, .15), fnt=self.F["pillb"], fondo="#1E6A3A")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- globo (Madrid → antípoda)
    def _ortho(lon0, lat0, R, gx, gy):
        l0, p0 = math.radians(lon0), math.radians(lat0)
        def pr(lon, lat):
            l = np.radians(lon) - l0; p = np.radians(lat)
            x = np.cos(p) * np.sin(l); y = np.cos(p0) * np.sin(p) - np.sin(p0) * np.cos(p) * np.cos(l)
            vis = np.sin(p0) * np.sin(p) + np.cos(p0) * np.cos(p) * np.cos(l)
            return x, y, vis
        return pr

    def e_globo(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; T = lambda k: _tw(self, e, s.get(k))
        rings = self._mundo_rings()
        gx, gy, R = CX, 660, 390 * (.94 + .06 * resorte(dt0, 6, 8))
        M = (-3.70, 40.42); Wb = (176.30, -40.42)
        tg = T("gira_word"); u = ease(TI.clamp((t - tg) / 1.8)) if t > tg else 0
        lon0 = M[0] - 8 + 3 * dt0 * (1 - u) + (Wb[0] - M[0] + 8) * u; lat0 = M[1] - 8 + (Wb[1] - M[1] + 16) * u
        pr = _ortho(lon0, lat0, R, gx, gy)
        # estrellas
        rng = np.random.default_rng(31)
        for k in range(90):
            c.drawCircle(rng.random() * W, rng.random() * 1300, .8 + 1.8 * rng.random(), relleno("#FFFFFF", (.25 + .5 * rng.random()) * (.7 + .3 * math.sin(t * 2 + k))))
        # atmósfera
        c.drawCircle(gx, gy, R * 1.1, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx, gy), R * 1.1, [color("#5C96FF", .0), color("#5C96FF", .0), color("#5C96FF", .45), color("#5C96FF", 0)], [0, .86, .91, 1])))
        c.drawCircle(gx, gy, R, _p(_rad(gx - R * .35, gy - R * .4, R * 1.6, ["#3A78E0", "#1A4AA8", "#0A1E52"], [0, .55, 1])))
        # tierra firme (puntos ocultos proyectados al borde)
        def path_pais(rs_):
            pth = skia.Path(); alguno = False
            for r in rs_:
                X, Y, Vv = pr(r[:, 0], r[:, 1])
                if (Vv > 0).sum() < 2: continue
                n = np.hypot(X, Y) + 1e-9; Xc = np.where(Vv > 0, X, X / n); Yc = np.where(Vv > 0, Y, Y / n)
                pth.moveTo(gx + R * Xc[0], gy - R * Yc[0])
                for xx, yy in zip(Xc[1:], Yc[1:]): pth.lineTo(gx + R * xx, gy - R * yy)
                pth.close(); alguno = True
            return pth if alguno else None
        c.save(); cl = skia.Path(); cl.addCircle(gx, gy, R); c.clipPath(cl, doAntiAlias=True)
        for cid, rs_ in rings.items():
            p_ = path_pais(rs_)
            if p_ is None: continue
            col = "#5FB36A"
            c.drawPath(p_, _p(_rad(gx - R * .3, gy - R * .35, R * 1.5, ["#8FD28A", "#4E9A52", "#2E6A3A"], [0, .6, 1])))
            c.drawPath(p_, trazo("#1E4A2A", 1.2, .5))
        for cid, wk, colr in (("724", "madrid_word", "#FFB45C"), ("554", "weber_word", "#FFB45C")):
            if t > T(wk) and cid in rings:
                p_ = path_pais(rings[cid])
                if p_ is not None: c.drawPath(p_, relleno(colr, .85 * aparece(t - T(wk), .3))); c.drawPath(p_, trazo("#FFFFFF", 2, .8))
        # sombra del terminador + brillo
        c.drawCircle(gx, gy, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx - R * .45, gy - R * .5), R * 2.1, [color("#000000", 0), color("#000000", .05), color("#000000", .55)], [0, .55, 1])))
        c.drawOval(skia.Rect(gx - R * .62, gy - R * .78, gx - R * .05, gy - R * .42), relleno("#FFFFFF", .08))
        c.restore()
        c.drawCircle(gx, gy, R, trazo("#BFD6FF", 2, .45))
        # pines
        for (lon, lat), wk, tk in ((M, "madrid_word", "madrid_txt"), (Wb, "weber_word", "weber_txt")):
            if t <= T(wk): continue
            X, Y, Vv = pr(np.array([lon]), np.array([lat]))
            if Vv[0] <= 0.05: continue
            x, y = gx + R * float(X[0]), gy - R * float(Y[0]); dt = t - T(wk); a = aparece(dt, .12) * TI.clamp(float(Vv[0]) / .25)
            for q in range(2):
                ph = ((t * .9 + q * .5) % 1); c.drawCircle(x, y, 10 + 44 * ph, trazo("#FFFFFF", 3, .55 * (1 - ph) * a))
            sc = resorte(dt, 10, 14); c.drawCircle(x, y, 14 * sc, relleno("#FFFFFF", a)); c.drawCircle(x, y, 7 * sc, relleno("#FF5A3D", a))
            self.pildora(c, s.get(tk, ""), x, y - 62 * sc, S, a, fnt=self.F["pillb"])
        # el túnel: línea que se hunde desde Madrid hacia el centro (antes de girar)
        tm = T("madrid_word")
        if tm < t < tg + .5:
            X, Y, Vv = pr(np.array([M[0]]), np.array([M[1]])); x, y = gx + R * float(X[0]), gy - R * float(Y[0])
            u2 = _io((t - tm - .3) / .6) * (1 - _io((t - tg) / .4))
            pl = trazo("#FFE15A", 5, .85 * u2); pl.setPathEffect(skia.DashPathEffect.Make([18, 12], -t * 80))
            c.drawLine(x, y, x + (gx - x) * u2, y + (gy - y) * u2, pl)

    # ---------------------------------------------------------------- corte de la Tierra
    CAPAS = [(1.0, ["#8A6A4A", "#6A4A30"]), (.985, ["#FF8A3D", "#C2401C", "#7A1E0E"]), (.546, ["#FFD24A", "#FF9A2A", "#E0601A"]), (.192, ["#FFFFFF", "#FFF2B0", "#FFD24A"])]

    def _tierra_corte(c, gx, gy, R, t, a=1.0):
        c.drawCircle(gx, gy, R * 1.06, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx, gy), R * 1.06, [color("#FF8A3D", .0), color("#FF8A3D", .0), color("#FF8A3D", .25 * a), color("#FF8A3D", 0)], [0, .9, .94, 1])))
        c.drawCircle(gx, gy, R, _p(_lin(gy - R, gy + R, ["#3A78E0", "#2A5AB8"], a)))
        for k, (fr, cols) in enumerate(CAPAS):
            r = R * fr * (.985 if k == 0 else 1)
            if k == 0: c.drawCircle(gx, gy, R * .995, _p(_lin(gy - R, gy + R, ["#8A6A4A", "#5A3A24"], a))); continue
            c.drawCircle(gx, gy, r, _p(_rad(gx, gy, r, cols[::-1] if len(cols) == 3 else cols, None, a)))
            c.drawCircle(gx, gy, r, trazo("#000000", 2, .18 * a))
        # textura: grumos del manto que giran despacio
        rng = np.random.default_rng(55)
        for k in range(46):
            an = rng.random() * 6.28 + t * .05 * (1 if k % 2 else -1); rr = R * (.6 + .36 * rng.random())
            c.drawCircle(gx + rr * math.cos(an), gy + rr * math.sin(an), R * (.015 + .03 * rng.random()), relleno("#FFB45C", .18 * a))
        with capa(c, modo=skia.BlendMode.kPlus):
            c.drawCircle(gx, gy, R * .3, _p(_rad(gx, gy, R * .3, ["#FFFFFF", "#FFD24A", "#000000"], [0, .4, 1], .35 * a * (.85 + .15 * math.sin(t * 3)))))
        c.drawCircle(gx, gy, R, trazo("#FFFFFF", 2, .3 * a))

    def e_corte(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; T = lambda k: _tw(self, e, s.get(k))
        gx, gy, R = CX, 700, 410 * (.95 + .05 * resorte(dt0, 6, 8))
        with _mundo(self, c, e, t):
            rng = np.random.default_rng(32)
            for k in range(70):
                c.drawCircle(rng.random() * W, rng.random() * 1300, .8 + 1.6 * rng.random(), relleno("#FFFFFF", (.2 + .4 * rng.random()) * (.7 + .3 * math.sin(t * 2 + k))))
            _tierra_corte(c, gx, gy, R, t)
            # túnel
            tt_ = T("tunel_word"); ut = 1.0 if not s.get("tunel_word") else _io((t - tt_) / .7)
            if ut > 0:
                c.drawRect(skia.Rect(gx - 9, gy - R, gx + 9, gy - R + 2 * R * ut), relleno("#0A0604", .92))
                c.drawRect(skia.Rect(gx - 9, gy - R, gx + 9, gy - R + 2 * R * ut), trazo("#FFE15A", 2, .55))
            for txt, yy, k in ((s.get("arriba_txt"), gy - R, "a"), (s.get("abajo_txt"), gy + R, "b")):
                if not txt: continue
                c.drawCircle(gx, yy, 10, relleno("#FFFFFF", aparece(dt0, .2)))
                self.pildora(c, txt, gx + 40, yy, S, aparece(dt0 - .1, .2), fnt=self.F["pillb"], alinear="i")
            # regla
            tr = T("regla_word")
            if t > tr:
                u = _io((t - tr) / .6); xr = gx - R - 0 + 0
                xr = gx - 70; lp = trazo("#FFE15A", 4, .95)
                c.drawLine(xr, gy - R, xr, gy - R + 2 * R * u, lp)
                for yy in (gy - R, gy - R + 2 * R * u): c.drawLine(xr - 16, yy, xr + 16, yy, lp)
                if u > .5: self.pildora(c, s.get("regla_txt", ""), xr - 20, gy - 40, S, aparece(t - tr - .4, .15), fnt=self.F["pillb"], fondo="#3A2A05", alinear="d")
            # cronómetro con interrogante
            tc = T("crono_word")
            if t > tc:
                dd = t - tc; sc = .6 + .4 * resorte(dd, 9, 12); a = aparece(dd, .12)
                c.save(); c.translate(gx + 230, gy + 40); c.scale(sc, sc)
                c.drawCircle(0, 0, 96, _p(_lin(-96, 96, ["#FFFFFF", "#D9DEE8"], a))); c.drawCircle(0, 0, 96, trazo("#14182A", 6, a))
                c.drawRRect(rrc(0, -108, 30, 22, 6), relleno("#14182A", a)); c.drawLine(0, 0, 60 * math.cos(-1.57 + dd * 6), 60 * math.sin(-1.57 + dd * 6), trazo("#E5322D", 7, a))
                texto(c, "?", 0, 46, F(800, 50), "#14182A", alfa=a)
                c.restore()
            ta = T("aviso_word")
            if t > ta:
                dd = t - ta; sc = .6 + .4 * resorte(dd, 9, 12); a = aparece(dd, .12) * (.8 + .2 * math.sin(t * 8))
                c.save(); c.translate(CX, 200); c.scale(sc, sc)
                self.pildora(c, "⚠ " + s.get("aviso_txt", ""), 0, 0, S, a, fnt=self.F["pillb"], fondo="#B3121C"); c.restore()
            # punto que viaja (subida) / yoyó
            pt = s.get("punto"); yo = s.get("yoyo_word")
            def bolita(fr, a=1.0, estela=None):
                y = gy - R + 2 * R * fr
                if estela is not None:
                    for k in range(1, 10):
                        y2 = gy - R + 2 * R * estela(k); c.drawCircle(gx, y2, 18 * (1 - k * .08), relleno("#FFE15A", .12 * (1 - k / 10) * a))
                with capa(c, alfa=.6 * a, blur=10): c.drawCircle(gx, y, 26, relleno("#FFE15A"))
                c.drawCircle(gx, y, 20, _p(_rad(gx - 6, y - 6, 26, ["#FFFFFF", "#FF8A3D"], None, a)))
                persona(self, c, gx + 68, y - 6, .2, t, pose="estrella", cara="feliz", a=a)
            if pt:
                tw_ = T("punto_word") if False else self.ta(pt["word"], e); d = pt.get("dur", 2)
                q = lambda tt: TI.clamp((tt - tw_) / d)
                ts_ = lambda tt: TC + TC * q(tt)
                fr = lambda tt: estado(ts_(tt))[0] / 12742 if tt > tw_ else pt["desde"]
                bolita(fr(t), 1.0, estela=lambda k: fr(t - k * .05))
                if t > tw_:
                    v = estado(ts_(t))[1]
                    for k in range(3):                                          # flechas de frenado
                        yy = gy + R * .3 + k * 34; al = .8 * (v / 36000) * aparece(t - tw_, .2)
                        c.drawPath(skia.Path.Polygon([(gx - 120, yy), (gx - 90, yy - 22), (gx - 60, yy)], False), trazo("#FFFFFF", 5, al))
            elif yo:
                ty = T("yoyo_word"); per = s.get("periodo", 3.0)
                if t > ty:
                    fr = lambda tt: .5 - .5 * math.cos(2 * math.pi * max(0, tt - ty) / per)
                    bolita(fr(t), 1.0, estela=lambda k: fr(t - k * .04))
                    for txt, k in ((s.get("arriba_txt"), 0), (s.get("abajo_txt"), 1)):
                        pass
                else:
                    bolita(1.0)
                trl = T("reloj_word")
                if t > trl:
                    self.pildora(c, "↕ IDA Y VUELTA · " + s.get("reloj_txt", ""), CX, 1190, S, aparece(t - trl, .15), fnt=self.F["pillb"], fondo="#3A2A05")
        capa_hud(self, c, e, t, S)

    # ---------------------------------------------------------------- túnel: paredes por capas
    PAL = {
        "tierra": dict(fondo=("#4A3220", "#2C1E14"), banda=["#6B4A2E", "#7A5634", "#5A3C24", "#8A6440"], piedra="#A88A6A", luz="#FFD9A0", veta="#3A281A"),
        "roca": dict(fondo=("#3A3430", "#1E1A18"), banda=["#5A524A", "#6A6058", "#4A423C", "#7A6E62"], piedra="#9A8E80", luz="#FFE2B0", veta="#2A2420"),
        "granito": dict(fondo=("#4A3A3A", "#241A1A"), banda=["#7A6262", "#8A7070", "#6A5252", "#9A8080"], piedra="#D8C8C0", luz="#FFD0A0", veta="#3A2A2A"),
        "moho": dict(fondo=("#2A2222", "#141010"), banda=["#3E3434", "#4A3E3A", "#342A28", "#52443E"], piedra="#7A6A62", luz="#FF9A5A", veta="#1A1414"),
        "manto": dict(fondo=("#5A1A0E", "#2A0A06"), banda=["#8A2A12", "#A0361A", "#7A220E", "#B4461E"], piedra="#E0602A", luz="#FFB060", veta="#FFB045"),
        "nucleo": dict(fondo=("#8A3A0A", "#4A1A04"), banda=["#FF9A2A", "#FFB43A", "#F2801E", "#FFC24A"], piedra="#FFE08A", luz="#FFF0B0", veta="#FFE680"),
        "interno": dict(fondo=("#A86A1A", "#5A3208"), banda=["#E8A83A", "#F2C25A", "#D08A22", "#FFD87A"], piedra="#FFFFFF", luz="#FFFFFF", veta="#FFFFFF"),
        "centro": dict(fondo=("#D88A2A", "#8A4A0A"), banda=["#FFD87A", "#FFE9A8", "#F2B84A", "#FFF2C8"], piedra="#FFFFFF", luz="#FFFFFF", veta="#FFFFFF"),
        "aire": dict(fondo=("#4A3A3A", "#241A1A"), banda=["#7A6262", "#8A7070", "#6A5252", "#9A8080"], piedra="#D8C8C0", luz="#FFD0A0", veta="#3A2A2A"),
    }
    WL, WR = 210, 830                                                           # bordes del hueco

    def _pared(c, capa_, x0, x1, scroll, t, prof=1.0, lado=-1):
        P = PAL[capa_]; per = 1400
        c.save(); c.clipRect(skia.Rect(x0, -100, x1, H + 100))
        c.drawRect(skia.Rect(x0, -100, x1, H + 100), _p(_lin(0, H, list(P["fondo"]))))
        rng = np.random.default_rng(100 + (0 if lado < 0 else 7))
        # bandas (estratos) inclinadas
        for k in range(14):
            y = (k * 100 + 37 * rng.random() - scroll) % per - 100; hb = 40 + 60 * rng.random(); col = P["banda"][k % 4]
            pth = skia.Path(); pth.moveTo(x0, y); amp = 14 + 10 * rng.random(); ph = rng.random() * 6
            for xx in range(int(x0), int(x1) + 30, 30): pth.lineTo(xx, y + amp * math.sin(xx / 90 + ph) + (xx - x0) * .08 * lado)
            for xx in range(int(x1), int(x0) - 30, -30): pth.lineTo(xx, y + hb + amp * math.sin(xx / 90 + ph) + (xx - x0) * .08 * lado)
            pth.close(); c.drawPath(pth, relleno(col, .9))
            if capa_ in ("manto", "nucleo", "interno", "centro"):
                c.drawPath(pth, trazo(P["veta"], 2.5, .35 + .25 * math.sin(t * 3 + k)))
        # piedras / cristales / burbujas
        for k in range(34):
            px_ = x0 + (x1 - x0) * rng.random(); py_ = (rng.random() * per - scroll * (1 + .1 * rng.random())) % per - 100; r_ = 6 + 22 * rng.random()
            if capa_ == "nucleo":
                c.drawCircle(px_, py_, r_ * .6, trazo("#FFF6C8", 2.5, .6)); continue
            if capa_ in ("interno", "centro"):
                hx = skia.Path()
                for j in range(6):
                    an = j * math.pi / 3 + k; (hx.moveTo if j == 0 else hx.lineTo)(px_ + r_ * math.cos(an), py_ + r_ * math.sin(an))
                hx.close(); c.drawPath(hx, relleno("#FFFFFF", .35)); c.drawPath(hx, trazo("#FFF2B0", 2, .6)); continue
            pp = skia.Path()
            for j in range(6):
                an = j * math.pi / 3 + rng.random() * .6; rr = r_ * (.7 + .5 * rng.random()); (pp.moveTo if j == 0 else pp.lineTo)(px_ + rr * math.cos(an), py_ + rr * .75 * math.sin(an))
            pp.close(); c.drawPath(pp, relleno(P["piedra"], .55)); c.drawPath(pp, trazo("#000000", 1.5, .2))
        if capa_ == "granito":                                                  # moteado del granito
            for k in range(160):
                px_ = x0 + (x1 - x0) * rng.random(); py_ = (rng.random() * per - scroll) % per - 100
                c.drawCircle(px_, py_, 2 + 3 * rng.random(), relleno(("#1A1414", "#F2E6E0", "#C98A8A")[k % 3], .7))
        if capa_ == "tierra":                                                   # raíces y fósiles
            for k in range(5):
                fx = x0 + (x1 - x0) * (.2 + .6 * rng.random()); fy = (rng.random() * per - scroll) % per - 100
                sp = skia.Path(); sp.moveTo(fx, fy)
                for j in range(30): an = j * .45; rr = 2 + j * .9; sp.lineTo(fx + rr * math.cos(an), fy + rr * math.sin(an))
                c.drawPath(sp, trazo("#E9D7B8", 3, .55))
        if capa_ == "manto":                                                    # grietas que brillan
            with capa(c, modo=skia.BlendMode.kPlus):
                for k in range(8):
                    gx_ = x0 + (x1 - x0) * rng.random(); gy_ = (rng.random() * per - scroll) % per - 100
                    gp = skia.Path(); gp.moveTo(gx_, gy_)
                    for j in range(6): gp.lineTo(gx_ + 30 * math.sin(j * 1.7 + k), gy_ + j * 30)
                    c.drawPath(gp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=color("#FF7A2A", .5 + .3 * math.sin(t * 4 + k)), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
        if capa_ == "nucleo":                                                   # olas de metal líquido
            for k in range(9):
                y = (k * 160 - scroll * .5) % per - 100; wv = skia.Path(); wv.moveTo(x0, y)
                for xx in range(int(x0), int(x1) + 20, 20): wv.lineTo(xx, y + 18 * math.sin(xx / 50 + t * 5 + k))
                c.drawPath(wv, trazo("#FFF2B0", 4, .5))
        c.restore()
        # cara interior de la pared (volumen): sombra hacia el hueco + filo de luz
        ex = x1 if lado < 0 else x0
        g0, g1 = (ex - 70, ex) if lado < 0 else (ex + 70, ex)
        c.drawRect(skia.Rect(min(g0, g1), -100, max(g0, g1), H + 100), skia.Paint(Shader=skia.GradientShader.MakeLinear([(g0, 0), (g1, 0)], [color("#000000", 0), color("#000000", .45)])))
        c.drawLine(ex, -100, ex, H + 100, trazo(P["luz"], 3, .55))

    def _fondo_tunel(self, c, e, t, capa_, vel):
        P = PAL[capa_]; scroll = vel * (t - e["t0"])
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, list(P["fondo"]))))
        # pared del fondo (más oscura y más lenta: paralaje)
        with capa(c, alfa=.55):
            _pared(c, capa_, WL - 10, WR + 10, scroll * .45, t, lado=1)
        c.drawRect(skia.Rect(WL, -80, WR, H + 80), skia.Paint(Shader=skia.GradientShader.MakeLinear([(WL, 0), (WR, 0)], [color("#000000", .55), color("#000000", .25), color("#000000", .55)], [0, .5, 1])))
        # resplandor de lo que viene debajo
        glow = {"tierra": "#000000", "roca": "#000000", "granito": "#FF6A2A", "moho": "#FF6A2A", "manto": "#FF9A3A", "nucleo": "#FFE08A", "interno": "#FFFFFF", "centro": "#FFFFFF", "aire": "#FF6A2A"}[capa_]
        ga = {"tierra": 0, "roca": 0, "granito": .12, "moho": .3, "manto": .4, "nucleo": .5, "interno": .6, "centro": .8, "aire": .15}[capa_]
        if ga:
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawRect(skia.Rect(-80, 300, W + 80, H + 80), _p(_rad(CX, 1500, 900, [glow, glow, "#000000"], [0, .25, 1], ga * .8)))
        bl = min(16.0, vel / 260)
        with capa(c, blur=0) if bl < .5 else _blurv(c, bl):
            _pared(c, capa_, -80, WL, scroll, t, lado=-1)
            _pared(c, capa_, WR, W + 80, scroll * 1.03 + 333, t, lado=1)
        # líneas de velocidad y partículas que suben
        rng = np.random.default_rng(77)
        if vel > 0:
            for k in range(26):
                x = WL + 20 + (WR - WL - 40) * rng.random(); L = 60 + 220 * rng.random() * min(1, vel / 3000)
                y = (rng.random() * 1700 - (vel * 1.6) * (t - e["t0"]) * (.6 + .6 * rng.random())) % 1700 - 150
                c.drawLine(x, y, x, y + L, trazo("#FFFFFF" if capa_ not in ("manto", "nucleo") else "#FFE0A0", 2 + 2 * rng.random(), .12 + .14 * rng.random()))
        part = {"manto": "#FFB060", "nucleo": "#FFF0B0", "interno": "#FFFFFF", "centro": "#FFFFFF", "moho": "#FF9A5A"}.get(capa_, "#D9C2A0")
        for k in range(40):
            x = rng.random() * W; y = (rng.random() * 1800 - (vel * .9 + 60) * (t - e["t0"]) * (.5 + rng.random())) % 1800 - 100
            c.drawCircle(x, y, 1.5 + 3 * rng.random(), relleno(part, .25 + .35 * rng.random()))
        if capa_ in ("interno", "centro"):
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawCircle(CX, 640, 700, _p(_rad(CX, 640, 700, ["#FFFFFF", "#FFE9A0", "#000000"], [0, .35, 1], .35 if capa_ == "centro" else .18)))

    @contextmanager
    def _blurv(c, s):
        c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(.01, s)))
        yield c
        c.restore()

    # ---------------------------------------------------------------- extras del túnel
    def e_tunel(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; capa_ = s.get("capa", "roca"); vel = s.get("vel", 1500)
        pj = s.get("pj", [520, 720, 1.5]); px, py, ps = pj
        with _mundo(self, c, e, t):
            _fondo_tunel(self, c, e, t, capa_, vel)
            # borde de la corteza (Moho) que pasa
            for x in s.get("extras", []):
                if x["tipo"] == "moho":
                    tw = self.ta(x["word"], e); u = TI.clamp((t - tw + .2) / 1.4)
                    yb = 1400 - 1700 * _io(u)
                    if u > 0:
                        c.save(); c.clipRect(skia.Rect(-80, yb, W + 80, H + 80)); _fondo_tunel(self, c, e, t, "manto", vel); c.restore()
                        with capa(c, modo=skia.BlendMode.kPlus):
                            c.drawRect(skia.Rect(-80, yb - 30, W + 80, yb + 30), _p(_lin(yb - 30, yb + 30, ["#000000", "#FF7A2A", "#000000"], .8)))
                        c.drawLine(-80, yb, W + 80, yb, trazo("#FFD08A", 4, .9))
            # protagonista (flota y se sacude un poco)
            fl = 14 * math.sin(t * 2.1); sac = 4 * math.sin(t * 23) * min(1, vel / 3000)
            pose = s.get("pose", "cae")
            if s.get("atrapado"):
                amp = 60 * math.exp(-.35 * dt0); fl = amp * math.sin(dt0 * 2.4)
            sud = 1.0 if s.get("cara") == "calor" else 0
            persona(self, c, px + sac, py + fl, ps, t, pose=pose, cara=s.get("cara", "o"), viento=(1.0 if vel > 0 else .15) * (1.4 if capa_ == "aire" else 1), sudor=sud,
                    rot=(8 * math.sin(t * .7) if pose == "estrella" else 3 * math.sin(t * 1.3)))
            c.drawRect(skia.Rect(-80, 1120, W + 80, H + 80), _p(_lin(1120, 1420, ["#000000", "#000000"], 1.0)) if False else
                       skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1040), (0, 1290)], [color("#05060C", 0), color("#05060C", .78)])))
            for x in s.get("extras", []): _extra(self, c, e, t, S, x, (px, py + fl, ps))
        capa_hud(self, c, e, t, S)

    def _extra(self, c, e, t, S, x, pj):
        a, dt = _vis(self, e, t, x)
        if a <= 0: return
        tp = x["tipo"]; px, py, ps = pj; sp = resorte(dt + .05, 8, 11)
        if tp == "f1":
            X, Y = 830, 700 + 20 * math.sin(t * 3) + 500 * (1 - sp)
            c.save(); c.translate(X, Y); c.rotate(180); c.scale(1.1, 1.1)
            c.drawRect(skia.Rect(-62, -160, 62, -138), relleno("#D21E1E", a))
            for wy in (-92, 70):
                for sx in (-1, 1): c.drawRRect(rrc(sx * 50, wy, 28, 54, 8), relleno("#14141A", a))
            body = skia.Path(); body.moveTo(0, -150); body.cubicTo(18, -120, 26, -40, 30, 40); body.lineTo(30, 110); body.lineTo(-30, 110); body.lineTo(-30, 40); body.cubicTo(-26, -40, -18, -120, 0, -150); body.close()
            c.drawPath(body, _p(skia.GradientShader.MakeLinear([(-30, 0), (30, 0)], [color("#FF6A5A", a), color("#D21E1E", a), color("#8A0E0E", a)])))
            c.drawRect(skia.Rect(-4, -150, 4, 100), relleno("#FFFFFF", .7 * a))
            c.drawOval(skia.Rect(-14, -10, 14, 30), relleno("#14141A", a)); c.drawCircle(0, 6, 10, relleno("#F2C14E", a))
            c.drawRect(skia.Rect(-56, 112, 56, 134), relleno("#D21E1E", a)); c.restore()
            for k in range(4):
                c.drawLine(X - 30 + k * 20, Y - 330 - 30 * (k % 2), X - 30 + k * 20, Y - 190, trazo("#FFFFFF", 3, .35 * a))
            self.pildora(c, "≈ 350 KM/H", 760, 1010, S, a, fnt=self.F["pillb"], fondo="#8A0E0E")
        elif tp == "avion":
            X, Y = 190, 760 + 20 * math.sin(t * 2.4) + 500 * (1 - sp)
            c.save(); c.translate(X, Y); c.rotate(180); c.scale(1.15, 1.15)
            c.drawPath(skia.Path.Polygon([(0, -40), (-130, 40), (-130, 60), (0, 26), (130, 60), (130, 40)], True), _p(_lin(-40, 60, ["#E9EEF6", "#AEB8CC"], a)))
            c.drawRRect(rrc(0, 0, 44, 300, 22), _p(skia.GradientShader.MakeLinear([(-22, 0), (22, 0)], [color("#FFFFFF", a), color("#C9D2E2", a)])))
            c.drawPath(skia.Path.Polygon([(0, 110), (-52, 150), (-52, 162), (0, 142), (52, 162), (52, 150)], True), relleno("#C9D2E2", a))
            c.drawRRect(rrc(0, -128, 22, 22, 11), relleno("#2A3A5A", a))
            for sx in (-1, 1): c.drawRRect(rrc(sx * 62, 30, 20, 40, 8), relleno("#8A94A8", a))
            c.restore()
            self.pildora(c, "≈ 1.000 KM/H", 220, 1060, S, a, fnt=self.F["pillb"], fondo="#1E2A4A")
        elif tp == "mina":
            Y = 1000 - 330 * _io(dt / .8) - 40 * max(0, dt - .8); X0, X1 = -20, WL + 4
            c.drawRect(skia.Rect(X0, Y - 120, X1, Y + 120), _p(_lin(Y - 120, Y + 120, ["#0E0A08", "#1E1610"], a)))
            for xx in (X0 + 30, X0 + 130, X0 + 230):
                c.drawRect(skia.Rect(xx - 8, Y - 120, xx + 8, Y + 120), relleno("#8A5A32", a)); c.drawRect(skia.Rect(xx - 40, Y - 120, xx + 40, Y - 104), relleno("#6A4A2A", a))
            c.drawLine(X0, Y + 112, X1, Y + 112, trazo("#9A9AA8", 5, a)); c.drawLine(X0, Y + 100, X1, Y + 100, trazo("#9A9AA8", 3, a))
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawCircle(X0 + 180, Y - 40, 90, _p(_rad(X0 + 180, Y - 40, 90, ["#FFE6A0", "#000000"], None, .55 * a)))
            c.drawCircle(X0 + 180, Y - 40, 12, relleno("#FFF6D0", a))
            # casco de minero
            c.drawArc(skia.Rect(X0 + 70, Y + 10, X0 + 150, Y + 70), 180, 180, True, relleno("#F2C14E", a)); c.drawRect(skia.Rect(X0 + 60, Y + 38, X0 + 160, Y + 46), relleno("#D9A03A", a))
            c.drawCircle(X0 + 110, Y + 22, 9, relleno("#FFFFFF", a))
            self.pildora(c, x.get("txt", ""), CX, 1050, S, a, fnt=self.F["pillb"], fondo="#3A2A05")
            if x.get("sub"): self.pildora(c, x["sub"], CX, 1122, S, a * aparece(dt - .25, .15), fnt=self.F["pill"])
        elif tp == "taladro":
            Y = 760 - 60 * min(dt, 6) / 6; X = 120
            c.drawRect(skia.Rect(X - 14, -100, X + 14, Y - 60), _p(skia.GradientShader.MakeLinear([(X - 14, 0), (X + 14, 0)], [color("#C9CFDB", a), color("#6A7488", a)])))
            for yy in range(int(Y - 60) - 600, int(Y - 60), 120): c.drawRect(skia.Rect(X - 18, yy, X + 18, yy + 14), relleno("#8A94A8", a))
            rot = t * 14
            c.save(); c.translate(X, Y); c.drawPath(skia.Path.Polygon([(-34, -60), (34, -60), (24, 0), (0, 30), (-24, 0)], True), _p(_lin(-60, 30, ["#E9EEF6", "#6A7488"], a)))
            for k in range(3):
                an = rot + k * 2.09; c.drawCircle(18 * math.cos(an), -10 + 6 * math.sin(an), 10, relleno("#4A5468", a))
            c.restore()
            fl_ = aparece(dt - .3, .15)
            self.pildora(c, x.get("txt", ""), X + 20, Y + 90, S, a * fl_, fnt=self.F["pillb"], fondo="#3A2A05", alinear="i")
        elif tp == "calendario":
            X, Y = 740, 1010; sc = .7 + .3 * sp
            ta = self.ta(x.get("anio_word", x["word"]), e); u = TI.cubic_out(TI.clamp((t - ta) / 1.1)) if t > ta else 0
            an = int(round(x["desde_anio"] + (x["anio"] - x["desde_anio"]) * u))
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            c.drawRRect(rrc(0, 10, 300, 230, 22), relleno("#000000", .3 * a))
            c.drawRRect(rrc(0, 0, 300, 230, 22), _p(_lin(-115, 115, ["#FFFDF7", "#EDE4D2"], a)))
            c.drawRRect(rrc(0, -80, 300, 70, 22), relleno("#C9302C", a)); c.drawRect(skia.Rect(-150, -70, 150, -45), relleno("#C9302C", a))
            texto(c, x.get("txt", ""), 0, -82, F(800, 34), "#FFFFFF", alfa=a)
            with capa(c, alfa=a, blur=(3 if 0 < u < 1 else 0)): texto(c, str(an), 0, 40, F(800, 96), "#14182A", tnum=True)
            c.restore()
            if u >= 1: self.pildora(c, f"{x['desde_anio']} → {x['anio']}", X, Y + 160, S, a * aparece(t - ta - 1.1, .15), fnt=self.F["pillb"])
        elif tp == "termometro":
            X, Y, Hh = 800, 760, 430; sc = .75 + .25 * sp
            u = TI.cubic_out(TI.clamp((dt - .1) / 1.0)); fr = x["valor"] / x["max"] * u
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            c.drawRRect(rrc(0, 0, 70, Hh, 35), _p(_lin(-Hh / 2, Hh / 2, ["#FFFFFF", "#D9DEE8"], .95 * a))); c.drawCircle(0, Hh / 2 + 20, 58, relleno("#FFFFFF", .95 * a))
            c.drawCircle(0, Hh / 2 + 20, 44, _p(_rad(-10, Hh / 2 + 10, 50, ["#FF8A6A", "#E5322D"], None, a)))
            c.drawRRect(rrc(0, Hh / 2 - (Hh - 40) * fr / 2 + 10, 34, (Hh - 40) * fr + 30, 17), relleno("#E5322D", a))
            for k in range(8): c.drawLine(22, -Hh / 2 + 30 + k * 50, 34, -Hh / 2 + 30 + k * 50, trazo("#8A94A8", 3, a))
            c.restore()
            if u > .6:
                v = int(round(x["valor"] * u / (10 if x["valor"] >= 1000 else 1))) * (10 if x["valor"] >= 1000 else 1)
                self.pildora(c, x.get("txt", ""), X - 20, Y - Hh / 2 * sc - 60, S, a * aparece(dt - .7, .15), fnt=F(800, 40), fondo="#B3121C")
            if x["valor"] >= 1000 or u > 0:                                    # vapor de calor
                for k in range(3):
                    ph = (t * .6 + k / 3) % 1; c.drawCircle(X + 30 * math.sin(t * 2 + k), Y - Hh / 2 * sc - 120 - 80 * ph, 12 + 10 * ph, relleno("#FFFFFF", .18 * (1 - ph) * a))
        elif tp == "crono":
            X, Y = CX, 1050; sc = .6 + .4 * sp
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            c.drawRRect(rrc(0, 10, 420, 150, 40), relleno("#000000", .35 * a))
            c.drawRRect(rrc(0, 0, 420, 150, 40), _p(_lin(-75, 75, ["#1C2340", "#070B1A"], .95 * a))); c.drawRRect(rrc(0, 0, 420, 150, 40), trazo("#FFE15A", 3, a))
            texto(c, x.get("txt", ""), -130, 0, F(800, 44), "#FFE15A", alfa=a)
            texto(c, x.get("valor", ""), 60, 0, F(800, 96), "#FFFFFF", alfa=a, tnum=True)
            c.restore()
        elif tp == "moho":
            self.pildora(c, x.get("txt", ""), CX, 1080, S, a * aparece(dt - .5, .15), fnt=self.F["pillb"], fondo="#7A220E")
        elif tp == "caramelo":
            X, Y = WR + 6, 420; u = _io(dt / 2.2) + .05 * math.sin(t * 2)
            L = 120 + 330 * u
            c.save(); c.translate(X, Y); c.scale(1.9, 1.9); c.translate(-X, -Y)
            gp = skia.Path(); gp.moveTo(X, Y - 60); gp.cubicTo(X - 70, Y - 40, X - 50, Y + L * .4, X - 40, Y + L * .7)
            gp.cubicTo(X - 36, Y + L * .85, X - 70, Y + L, X - 40, Y + L + 30); gp.cubicTo(X - 10, Y + L + 50, X + 10, Y + L, X - 6, Y + L * .7)
            gp.cubicTo(X - 10, Y + L * .3, X + 20, Y, X, Y - 60); gp.close()
            c.drawPath(gp, _p(_lin(Y - 60, Y + L + 50, ["#FFB04A", "#E07A1A", "#A0420A"], a)))
            c.drawPath(gp, trazo("#5A2206", 2, .5 * a))
            c.drawLine(X - 46, Y, X - 36, Y + L * .6, trazo("#FFE6B0", 5, .55 * a)); c.restore()
            self.pildora(c, x.get("txt", ""), CX, 1080, S, a * aparece(dt - .3, .15), fnt=self.F["pillb"], fondo="#7A220E")
        elif tp == "campo":
            X, Y, R = CX, 960, 70; sc = (.7 + .3 * sp) * 1.45
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            for k, ww in enumerate((150, 210, 270)):
                for sx in (-1, 1):
                    rect = skia.Rect(sx * ww / 2 - ww / 2, -ww * .45, sx * ww / 2 + ww / 2, ww * .45)
                    pl = trazo("#7FE0FF", 3, .7 * a); pl.setPathEffect(skia.DashPathEffect.Make([14, 10], -t * 60 * sx))
                    c.drawOval(rect, pl)
            c.drawCircle(0, 0, R, _p(_rad(-20, -20, R * 1.4, ["#5C96FF", "#1A4AA8"], None, a)))
            c.drawCircle(0, 0, R * .55, _p(_rad(0, 0, R * .55, ["#FFE08A", "#FF8A3D"], None, a)))
            for sy, lt in ((-1, "N"), (1, "S")): texto(c, lt, 0, sy * (R + 22), F(800, 28), "#FFFFFF", alfa=a)
            c.restore()
            self.pildora(c, x.get("txt", ""), X, Y + 175, S, a * aparece(dt - .2, .15), fnt=self.F["pillb"], fondo="#0E3A5A")
        elif tp == "brujula":
            X, Y = 800, 820; sc = .7 + .3 * sp; ang = 60 * math.exp(-2.2 * dt) * math.cos(dt * 9)
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            c.drawCircle(0, 8, 104, relleno("#000000", .35 * a))
            c.drawCircle(0, 0, 104, _p(_lin(-104, 104, ["#E6C27A", "#9A6A2A"], a))); c.drawCircle(0, 0, 86, _p(_rad(-20, -20, 110, ["#FFFFFF", "#E9EEF6"], None, a)))
            for k in range(4):
                an = k * math.pi / 2; texto(c, "NESO"[k], 66 * math.sin(an), -66 * math.cos(an), F(800, 24), "#14182A", alfa=a)
            c.rotate(ang)
            c.drawPath(skia.Path.Polygon([(0, -64), (14, 0), (-14, 0)], True), relleno("#E5322D", a)); c.drawPath(skia.Path.Polygon([(0, 64), (14, 0), (-14, 0)], True), relleno("#3A4462", a))
            c.drawCircle(0, 0, 8, relleno("#14182A", a)); c.restore()
        elif tp == "gravedad":
            X, Y = CX, 960; sc = (.7 + .3 * sp) * 1.5
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            for k, (dx, L, txt, col) in enumerate(((-150, 90, "ARRIBA", "#9DB8FF"), (150, 98 + 14 * _io(dt / .6), "AQUÍ", "#FFB45C"))):
                c.drawLine(dx, -60, dx, -60 + L, trazo(col, 16, a)); c.drawPath(skia.Path.Polygon([(dx - 26, -60 + L), (dx + 26, -60 + L), (dx, -60 + L + 36)], True), relleno(col, a))
                texto(c, txt, dx, -90, F(800, 28), "#FFFFFF", alfa=a)
            c.restore()
            self.pildora(c, x.get("txt", ""), X, Y + 150, S, a * aparece(dt - .3, .15), fnt=self.F["pillb"], fondo="#7A3A05")
        elif tp == "pluton":
            Y = 950; R = 100 * (.6 + .4 * sp)
            x1, x2 = CX - 190, CX + 190
            with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(x1, Y, R * 1.5, _p(_rad(x1, Y, R * 1.5, ["#FFE08A", "#000000"], None, .5 * a)))
            c.drawCircle(x1, Y, R, _p(_rad(x1 - R * .3, Y - R * .3, R * 1.4, ["#FFFFFF", "#FFE08A", "#E0901A"], [0, .45, 1], a)))
            for k in range(7):
                an = k * .9 + t * .2; c.drawCircle(x1 + R * .6 * math.cos(an), Y + R * .6 * math.sin(an), 8, relleno("#FFFFFF", .4 * a))
            ap = a * aparece(dt - .5, .2)
            c.drawCircle(x2, Y, R, _p(_rad(x2 - R * .3, Y - R * .3, R * 1.4, ["#F2E2C8", "#C9A27E", "#7A5A3A"], [0, .55, 1], ap)))
            hp = skia.Path(); hx, hy = x2 + R * .15, Y + R * .2
            hp.moveTo(hx, hy + 40); hp.cubicTo(hx - 60, hy, hx - 40, hy - 50, hx, hy - 20); hp.cubicTo(hx + 40, hy - 50, hx + 60, hy, hx, hy + 40)
            c.drawPath(hp, relleno("#FFF6E8", .9 * ap))
            texto(c, "=", CX, Y, F(800, 80), "#FFFFFF", alfa=ap)
            self.pildora(c, x.get("txt", ""), x1, Y + R + 40, S, a, fnt=self.F["pill"], fondo="#7A4A05")
            self.pildora(c, x.get("txt2", ""), x2, Y + R + 40, S, ap, fnt=self.F["pill"], fondo="#4A3A2A")
        elif tp == "sol":
            X, Y = CX, 940; R = 100 * (.6 + .4 * sp)
            with capa(c, modo=skia.BlendMode.kPlus):
                c.drawCircle(X, Y, R * 2, _p(_rad(X, Y, R * 2, ["#FFD24A", "#FF8A3D", "#000000"], [0, .4, 1], .6 * a)))
            for k in range(16):
                an = k * math.pi / 8 + t * .3; L = R * (1.25 + .12 * math.sin(t * 4 + k))
                c.drawLine(X + R * 1.05 * math.cos(an), Y + R * 1.05 * math.sin(an), X + L * math.cos(an), Y + L * math.sin(an), trazo("#FFE08A", 8, .8 * a))
            c.drawCircle(X, Y, R, _p(_rad(X - R * .3, Y - R * .3, R * 1.4, ["#FFFFFF", "#FFE58A", "#FF9A2A"], [0, .4, 1], a)))
            self.pildora(c, x.get("txt", ""), X, Y + R + 70, S, a * aparece(dt - .3, .15), fnt=F(800, 40), fondo="#B3121C")
        elif tp == "velocimetro":
            X, Y, R = CX, 960, 140; sc = .7 + .3 * sp
            u = TI.cubic_out(TI.clamp((dt - .05) / 1.0)); v = x["valor"] * u; fr = v / x["max"]
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            c.drawCircle(0, 8, R + 40, relleno("#000000", .3 * a)); c.drawCircle(0, 0, R + 36, _p(_lin(-R, R, ["#1C2340", "#070B1A"], .94 * a)))
            c.drawArc(skia.Rect(-R, -R, R, R), 150, 240, False, trazo("#000000", 34, .35 * a))
            c.drawArc(skia.Rect(-R, -R, R, R), 150, 240, False, trazo("#2A3150", 26, .95 * a))
            c.drawArc(skia.Rect(-R, -R, R, R), 150, 240 * fr, False, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26, StrokeCap=skia.Paint.kRound_Cap,
                      Shader=skia.GradientShader.MakeSweep(0, 0, [color("#2ED47A", a), color("#FFD24A", a), color("#FF3B4A", a)], [0, .5, 1], skia.TileMode.kClamp, 150, 390)))
            an = math.radians(150 + 240 * fr)
            c.drawLine(0, 0, (R - 40) * math.cos(an), (R - 40) * math.sin(an), trazo("#FFFFFF", 8, a)); c.drawCircle(0, 0, 16, relleno("#FFFFFF", a))
            with capa(c, alfa=a, blur=(2 if 0 < u < 1 else 0)): texto(c, _fmt_n(v), 0, 70, F(800, 62), "#FFFFFF", tnum=True)
            texto(c, x.get("txt", ""), 0, 120, F(700, 28), "#C9D3EA", alfa=a)
            c.restore()
        elif tp == "cero":
            self.pildora(c, x.get("txt", ""), CX, 1100, S, a, fnt=F(800, 44), fondo="#1E2A4A")
        elif tp == "flechas":
            pul = .5 + .5 * math.sin(t * 5)
            for k in range(8):
                an = k * math.pi / 4 + .39; r0 = 270 + 16 * pul; r1 = r0 + 110
                cx_, cy_ = px, py - 60 * ps
                x0, y0, x1, y1 = cx_ + r0 * math.cos(an), cy_ + r0 * math.sin(an) * 1.05, cx_ + r1 * math.cos(an), cy_ + r1 * math.sin(an) * 1.05
                c.drawLine(x0, y0, x1, y1, trazo("#FFE15A", 12, .9 * a))
                hx, hy = x1, y1; nx, ny = math.cos(an), math.sin(an)
                c.drawPath(skia.Path.Polygon([(hx + nx * 26, hy + ny * 26), (hx - ny * 20, hy + nx * 20), (hx + ny * 20, hy - nx * 20)], True), relleno("#FFE15A", .9 * a))
        elif tp == "viento":
            for k in range(18):
                rng = np.random.default_rng(300 + k); xx = WL + 30 + (WR - WL - 60) * rng.random()
                y = (rng.random() * 1500 - t * 1400 * (.7 + .5 * rng.random())) % 1500 - 100
                wv = skia.Path(); wv.moveTo(xx, y)
                for j in range(8): wv.lineTo(xx + 16 * math.sin(j * .9 + t * 6 + k), y + j * 26)
                c.drawPath(wv, trazo("#FFFFFF", 4, .45 * a))
            if dt < 1.2: _comic(c, "¡FUUUUH!", CX + 120, 300, 80, -7, .7 + .3 * resorte(dt, 10, 14), a * (1 - TI.clamp((dt - .9) / .3)), "#FFFFFF")
        elif tp == "dias":
            X, Y, R = CX, 1000, 120; sc = .7 + .3 * sp; ang = dt * 4.2
            c.save(); c.translate(X, Y); c.scale(sc, sc)
            c.drawArc(skia.Rect(-R, -R, R, R), 180, 180, False, trazo("#FFFFFF", 3, .35 * a))
            for k, (col, off) in enumerate((("#FFE08A", 0), ("#DDE6FF", math.pi))):
                an = math.pi + (ang + off) % (2 * math.pi)
                if math.sin(an) <= .05:
                    xx, yy = R * math.cos(an), R * math.sin(an)
                    c.drawCircle(xx, yy, 34, relleno(col, a))
                    if k == 1: c.drawCircle(xx + 14, yy - 8, 30, relleno("#2A1E3A", a))
            c.drawLine(-R - 30, 0, R + 30, 0, trazo("#FFFFFF", 4, .6 * a))
            c.restore()
            self.pildora(c, x.get("txt", ""), X, Y + 70, S, a * aparece(dt - .2, .15), fnt=F(800, 40), fondo="#3A2A05")
        elif tp == "atrapado":
            self.pildora(c, x.get("txt", ""), CX, 1100, S, a, fnt=self.F["pillb"], fondo="#B3121C")

    # ---------------------------------------------------------------- capa: la corteza y la manzana
    def e_capa(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; T = lambda k: _tw(self, e, s.get(k))
        tm = T("manzana_word"); um = _io((t - tm + .1) / .6)
        c.drawRect(skia.Rect(-80, -80, W + 80, H + 80), _p(_lin(0, H, ["#EEF4FF", "#D6E2F6"])))
        # trozo de la Tierra: arco enorme
        cy = 760 - 300 * um; Rg = 2600; cx = CX; top = cy - 160
        c.save(); c.translate(0, 0)
        cen = (cx, top + Rg)
        def arco(r, col):
            c.drawCircle(cen[0], cen[1], r, relleno(col))
        c.save(); c.clipRect(skia.Rect(-80, top - 300, W + 80, top + 520 - 250 * um))
        arco(Rg + 40, "#BFD8F7")                                                  # cielo (atmósfera)
        arco(Rg, "#7A5636"); arco(Rg - 24, "#E0602A"); arco(Rg - 120, "#C2401C"); arco(Rg - 260, "#8A2A12")
        c.drawCircle(cen[0], cen[1], Rg - 24, trazo("#3A1E0E", 2, .5))
        # mar
        tma = T("mares_word")
        if t > tma:
            u = _io((t - tma) / .4)
            c.save(); cl = skia.Path(); cl.addCircle(cen[0], cen[1], Rg + 3); c.clipPath(cl, doAntiAlias=True)
            c.drawRect(skia.Rect(500, top - 40, 500 + 230 * u, top + 30), relleno("#3A8AE0")); c.restore()
            for k in range(4): c.drawLine(510 + k * 55, top - 2 + 3 * math.sin(t * 3 + k), 600 + k * 60, top - 2 + 3 * math.sin(t * 3 + k), trazo("#FFFFFF", 3, .7 * u))
        tmo = T("montes_word")
        if t > tmo:
            for k, (mx, mh) in enumerate(((130, 190), (270, 270), (400, 170))):
                u = resorte(t - tmo - k * .08, 8, 10); hh = mh * u
                ang_y = top + (cx - mx) ** 2 / (2 * Rg) * 1
                c.drawPath(skia.Path.Polygon([(mx - 105, ang_y + 4), (mx, ang_y - hh), (mx + 105, ang_y + 4)], True), _p(_lin(ang_y - hh, ang_y, ["#9A8A7A", "#6A5A4A"])))
                c.drawPath(skia.Path.Polygon([(mx - 33, ang_y - hh + 50 * u), (mx, ang_y - hh), (mx + 33, ang_y - hh + 50 * u)], True), relleno("#FFFFFF"))
        tci = T("ciudad_word")
        if t > tci:
            for k in range(6):
                u = resorte(t - tci - k * .05, 8, 10); bx = 760 + k * 36; by = top + (cx - bx) ** 2 / (2 * Rg)
                hh = (70 + 90 * ((k * 7) % 5) / 4) * u
                c.drawRect(skia.Rect(bx - 15, by - hh, bx + 15, by + 4), _p(_lin(by - hh, by, ["#5A6A8A", "#2A3450"])))
                for j in range(int(hh // 14)): c.drawRect(skia.Rect(bx - 6, by - hh + 6 + j * 14, bx - 1, by - hh + 11 + j * 14), relleno("#FFE08A", .8))
        c.restore()
        tc = T("capa_word")
        if t > tc:
            u = aparece(t - tc, .2); yy = top + 10
            c.drawLine(60, top - 4, 60, top + 22, trazo("#14182A", 5, u)); c.drawLine(52, top - 4, 80, top - 4, trazo("#14182A", 5, u)); c.drawLine(52, top + 22, 80, top + 22, trazo("#14182A", 5, u))
            self.pildora(c, "← " + s.get("capa_txt", "CORTEZA"), 330, top + 80, S, u, fnt=self.F["pillb"], fondo="#7A3A05")
            texto(c, "MANTO", CX, top + 250, F(800, 40), "#FFFFFF", alfa=.85 * u)
        c.restore()
        # manzana
        if um > 0:
            ax, ay, R = CX, 930 + 200 * (1 - um), 175 * (.7 + .3 * resorte(t - tm + .1, 8, 10))
            _sombra(c, ax, ay + R + 10, R * .8, 18, .25 * um)
            ap = skia.Path(); ap.moveTo(ax, ay - R * .78)
            ap.cubicTo(ax + R * .4, ay - R * 1.1, ax + R * 1.15, ay - R * .9, ax + R * 1.0, ay - R * .05)
            ap.cubicTo(ax + R * .95, ay + R * .7, ax + R * .5, ay + R * 1.05, ax, ay + R * .9)
            ap.cubicTo(ax - R * .5, ay + R * 1.05, ax - R * .95, ay + R * .7, ax - R * 1.0, ay - R * .05)
            ap.cubicTo(ax - R * 1.15, ay - R * .9, ax - R * .4, ay - R * 1.1, ax, ay - R * .78); ap.close()
            c.drawPath(ap, relleno("#C9161E", um))
            c.save(); c.translate(ax, ay); c.scale(.965, .965); c.translate(-ax, -ay)
            c.drawPath(ap, _p(_rad(ax - R * .2, ay - R * .1, R * 1.2, ["#FFF6DA", "#F7E6B0", "#EED38A"], [0, .7, 1], um))); c.restore()
            for sx in (-1, 1): c.drawOval(skia.Rect(ax + sx * 34 - 12, ay + 10, ax + sx * 34 + 12, ay + 44), relleno("#3A1E0E", um))
            c.drawLine(ax, ay - R * .78, ax + 12, ay - R * 1.08, trazo("#5A3A20", 10, um))
            lf = skia.Path(); lf.moveTo(ax + 14, ay - R * .98); lf.cubicTo(ax + 60, ay - R * 1.25, ax + 120, ay - R * 1.08, ax + 130, ay - R * 1.0); lf.cubicTo(ax + 90, ay - R * .9, ax + 40, ay - R * .9, ax + 14, ay - R * .98)
            c.drawPath(lf, relleno("#4EA34A", um))
            ua = aparece(t - tm - .5, .2)
            self.pildora(c, s.get("manzana_txt", ""), ax + R * .55, ay - R * 1.2, S, ua * um, fnt=self.F["pillb"], fondo="#8A0E14", alinear="i")

    # ---------------------------------------------------------------- mapa: Madrid → Barcelona
    def e_mapa_es(self, c, e, t, S):
        s = e["spec"]; dt0 = t - e["t0"]; G_ = self.geo([-3.0, 40.0])
        k = 430 / 560 * (.95 + .05 * resorte(dt0, 6, 8)); cen = np.array(G_["pr"](-3.0, 40.2))
        P = lambda lon, lat: (lambda q: (CX + (q[0] - cen[0]) * k, 700 - (q[1] - cen[1]) * k))(G_["pr"](lon, lat))
        c.save(); c.translate(CX, 700); c.scale(k, -k); c.translate(-cen[0], -cen[1])
        for pk in ("tierra", "francia"): c.drawPath(G_[pk], relleno("#1E47B8", .95)); c.drawPath(G_[pk], trazo("#9DB8FF", 1.6 / k, .7))
        if "724" in G_["ids"]:
            c.drawPath(G_["ids"]["724"], relleno("#FFFFFF", .16)); c.drawPath(G_["ids"]["724"], trazo("#FFFFFF", 3 / k, .9))
        c.restore()
        mx, my = P(-3.70, 40.42); bx, by = P(2.17, 41.39)
        tw = self.ta(s["word"], e) - .35; u = TI.clamp((t - tw) / .9)
        for (x, y), txt, d in (((mx, my), s.get("a_txt"), 0), ((bx, by), s.get("b_txt"), .9)):
            a = aparece(dt0 - .1 if d == 0 else t - tw - .7, .15)
            if a <= 0: continue
            c.drawCircle(x, y, 14, relleno("#FFFFFF", a)); c.drawCircle(x, y, 7, relleno("#FF5A3D", a))
            self.pildora(c, txt, x, y + 60, S, a, fnt=self.F["pillb"])
        if u > 0:
            ue = ease(u); hx, hy = mx + (bx - mx) * ue, my + (by - my) * ue
            for j in range(16):
                q = max(0, ue - j * .03); c.drawCircle(mx + (bx - mx) * q, my + (by - my) * q, 16 * (1 - j / 16), relleno("#FFE15A", .5 * (1 - j / 16)))
            with capa(c, modo=skia.BlendMode.kPlus): c.drawCircle(hx, hy, 60, _p(_rad(hx, hy, 60, ["#FFFFFF", "#FFE15A", "#000000"], [0, .3, 1], .9)))
            persona(self, c, hx, hy - 60, .22, t, pose="estrella", cara="feliz", viento=1)
        # cronómetro
        a = aparece(t - tw, .15)
        if a > 0:
            v = 51 * TI.cubic_out(u); c.save(); c.translate(CX, 1090)
            c.drawRRect(rrc(0, 0, 380, 130, 40), _p(_lin(-65, 65, ["#1C2340", "#070B1A"], .95 * a))); c.drawRRect(rrc(0, 0, 380, 130, 40), trazo("#FFE15A", 3, a))
            with capa(c, alfa=a, blur=(2 if 0 < u < 1 else 0)): texto(c, f"0:{int(v):02d}", 0, 0, F(800, 84), "#FFFFFF", tnum=True)
            c.restore()

    # ---------------------------------------------------------------- efectos de sonido
    def efectos_tierra(self, e, pon, libre):
        s = e["spec"]; tp = s["tipo"]; Tw = lambda w: self.ta(w, e)
        sf = lambda tt, n, v: self.sfx(TI.f_de_t(max(0, tt)), n, v)
        h = s.get("hud")
        if h and h.get("word") and h.get("hasta") != h.get("desde"): self.rodillo(Tw(h["word"]), h.get("dur", 1.0))
        if h and h.get("capitulo"):
            sf(e["t0"] + .1, "ding", .7); sf(e["t0"] + h.get("grande", 1.05), "whoosh", .45)
        if tp == "superficie":
            m = s.get("modo")
            if s.get("agujero_word"): sf(Tw(s["agujero_word"]), "rumor", 1.0); sf(Tw(s["agujero_word"]) + .1, "golpe", .5)
            if s.get("linea_word"): sf(Tw(s["linea_word"]), "subida", .6)
            if m == "salto":
                tj = Tw("saltas") - .25; sf(tj, "chuf", .8); sf(tj + .2, "whoosh", .9); sf(tj + .55, "caida", .8)
            if m == "salida":
                sf(Tw(s["asoma_word"]), "subida", .6); sf(Tw(s["agarra_word"]), "tac", 1.0); sf(Tw(s["agarra_word"]) + .1, "tac", .7)
                sf(Tw(s["oveja_word"]) - .6, "paso", .6); sf(Tw(s["oveja_word"]) - .3, "paso", .5); sf(Tw(s["oveja_word"]) + .3, "balido", 1.0)
            if m == "cierre":
                sf(Tw(s["pulgar_word"]), "pop", .6); sf(Tw(s["aire_word"]) - .1, "aliento", 1.0); sf(Tw(s["aire_word"]) + .25, "pop", .5)
        if tp == "globo":
            sf(Tw(s["madrid_word"]), "pop", .6); sf(Tw(s["gira_word"]), "whoosh", .8); sf(Tw(s["gira_word"]) + .8, "whoosh", .5); sf(Tw(s["weber_word"]), "pop", .6)
        if tp == "corte":
            for k in ("tunel_word", "regla_word", "crono_word", "aviso_word", "reloj_word"):
                if s.get(k): sf(Tw(s[k]), {"tunel_word": "subida", "regla_word": "rotulador", "crono_word": "tic", "aviso_word": "alarma", "reloj_word": "pop"}[k], .7)
            if s.get("crono_word"):
                for j in range(6): sf(Tw(s["crono_word"]) + .15 + j * .25, "tic", .45)
            if s.get("punto"): sf(Tw(s["punto"]["word"]), "subida", .7)
            if s.get("yoyo_word"):
                ty = Tw(s["yoyo_word"]); per = s.get("periodo", 3.0); k = 0
                while ty + k * per / 2 < e["t1"] - .3 and k < 12:
                    sf(ty + k * per / 2 + per / 4 - .3, "whoosh", .35); k += 1
        if tp == "tunel":
            sf(e["t0"] + .3, "viento", .8)
            capa_ = s.get("capa")
            if capa_ in ("manto", "nucleo"): sf(e["t0"] + 1.4, "rumor", .7); sf(e["t0"] + 2.6, "crepita" if capa_ == "manto" else "burbuja", .9)
            if capa_ in ("interno", "centro"): sf(e["t0"] + 1.4, "destello", .5)
            for x in s.get("extras", []):
                tt = Tw(x["word"]); n = {"f1": "motor", "avion": "zum", "mina": "pop", "taladro": "taladro", "calendario": "pop", "termometro": "subida", "crono": "sello",
                                         "moho": "rumor", "caramelo": "burbuja", "campo": "hum", "brujula": "tic", "gravedad": "golpe", "pluton": "pop", "sol": "crepita",
                                         "velocimetro": "subida", "cero": "destello", "flechas": "zum", "viento": "viento", "dias": "campana", "atrapado": "bajada"}[x["tipo"]]
                sf(tt, n, .8)
                if x["tipo"] == "calendario":
                    self.rodillo(Tw(x.get("anio_word", x["word"])), 1.1)
                if x["tipo"] == "velocimetro": self.rodillo(tt, 1.0)
                if x["tipo"] == "brujula":
                    for j in range(4): sf(tt + .2 + j * .18, "tic", .4)
                if x["tipo"] == "pluton": sf(tt + .5, "pop", .6)
                if x["tipo"] in ("termometro", "mina", "moho", "caramelo", "campo", "gravedad", "sol", "dias", "atrapado") and x.get("txt"): sf(tt + .55, "pop", .35)
        if tp == "capa":
            for k, n in (("montes_word", "pop"), ("mares_word", "ola"), ("ciudad_word", "pop"), ("capa_word", "rotulador"), ("manzana_word", "nam")):
                if s.get(k): sf(Tw(s[k]), n, .7)
        if tp == "mapa_es":
            tw = Tw(s["word"]) - .35; sf(tw, "zum", 1.0); sf(tw + .9, "golpe", .5); self.rodillo(tw, .9)

    V.persona_t = persona; V.comic_t = staticmethod(_comic); V.oveja_t = staticmethod(oveja)
    for k, fn in (("superficie", e_superficie), ("globo", e_globo), ("corte", e_corte), ("tunel", e_tunel), ("capa", e_capa), ("mapa_es", e_mapa_es)):
        setattr(V, "e_" + k, fn); setattr(V, "efectos_" + k, efectos_tierra)
