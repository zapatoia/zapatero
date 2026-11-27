#!/usr/bin/env python3
"""Outro corta de «compartir» pegada al final de un vídeo vertical YA renderizado (sin volver a renderizarlo).

  PY outro.py <proyecto>            voz (una toma, se guarda) + animación + unión → final/<proyecto>-v2.mp4

Lee guion.json → "outro": {"texto", "tts", "key", "salida" (opcional), "contacto" (opcional)}.
Fondo: el último cuadro del vídeo, que se oscurece y desenfoca. Encima: botón de compartir que se pulsa, avión de papel
que vuela con estela hasta el avatar del amigo (con gafas de sol), y la tipografía cinética de la voz.
El vídeo original se copia tal cual (sin recodificar); solo se rehace el audio entero para unirlo sin clics.
"""
import base64, json, math, os, subprocess, sys, urllib.request
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MOTOR))
os.environ.setdefault("DOC_FPS", "60")
from nucleo import tiempo as TI                                   # noqa: E402
TI.FPS = 60
import numpy as np                                                # noqa: E402
import skia                                                       # noqa: E402
from nucleo.texto import fuente, texto, ancho, color              # noqa: E402
from nucleo.lienzo import Lienzo, capa, relleno, trazo, rrc       # noqa: E402
from nucleo.rutas import FF, perfil, clave_eleven                 # noqa: E402
from nucleo.render import ENC                                     # noqa: E402
from nucleo.audio import efecto                                   # noqa: E402
TX = sys.modules["nucleo.texto"]

W, H, FPS, SR = 1080, 1920, 60, 48000
CX = 520; CAP_CTX_Y, CAP_KEY_Y = 1268, 1400
ACC = "#6EA0FF"


def run(*a, **k): return subprocess.run(list(a), check=True, **k)


def ease(u):
    u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


def resorte(dt, k=9.0, w=13.0):
    return 0.0 if dt <= 0 else 1 - math.exp(-k * dt) * math.cos(w * dt)


def voz(proy, o):
    au = proy / "audio"; js = au / "outro_toma.json"
    if not js.exists():
        g = json.loads((proy / "guion.json").read_text())
        body = dict(text=o["tts"], model_id=g.get("voz_modelo", "eleven_v3"), language_code="es",
                    voice_settings=dict(stability=.5, similarity_boost=.85))
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{perfil()['voz_id']}/with-timestamps?output_format=mp3_44100_192",
                                     data=json.dumps(body).encode(), headers={"xi-api-key": clave_eleven(), "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r: d = json.loads(r.read())
        (au / "outro_toma.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
        js.write_text(json.dumps(dict(texto=o["tts"], caracteres=len(o["tts"]), al=d.get("alignment") or d.get("normalized_alignment")), ensure_ascii=False))
        print(f"voz outro: {len(o['tts'])} caracteres")
    t = json.loads(js.read_text()); al = t["al"]
    x = np.frombuffer(run(FF, "-v", "error", "-i", str(au / "outro_toma.mp3"), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-",
                          capture_output=True).stdout, np.float32).copy()
    # palabras habladas (sin etiquetas [..]) con su tramo
    ch, cs, ce = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    full = "".join(ch); pal = []; i = 0; dentro = False
    while i < len(full):
        if full[i] == "[": dentro = True
        if dentro:
            if full[i] == "]": dentro = False
            i += 1; continue
        if full[i].isspace(): i += 1; continue
        j = i
        while j < len(full) and not full[j].isspace(): j += 1
        pal.append(dict(w=full[i:j], s=cs[i], e=ce[j - 1])); i = j
    vis = o["texto"].split()
    for p, w in zip(pal, vis): p["w"] = w
    # recorte del silencio inicial y de la cola
    e = np.sqrt(np.convolve(x ** 2, np.ones(240) / 240, "same")) + 1e-9; db = 20 * np.log10(e / e.max())
    a = max(0, int(np.argmax(db > -45)) - 120); b = len(x) - int(np.argmax(db[::-1] > -50)) + int(.12 * SR)
    x = x[a:b]; x[:96] *= np.linspace(0, 1, 96); x[-int(.06 * SR):] *= np.linspace(1, 0, int(.06 * SR))
    for p in pal: p["s"] -= a / SR; p["e"] -= a / SR
    return x, pal


def avion(c, x, y, s, ang, a=1.0, col="#FFFFFF"):
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang)); c.scale(s, s)
    p = skia.Path(); p.moveTo(-.9, -.05); p.lineTo(.9, -.75); p.lineTo(.3, .85); p.lineTo(.05, .2); p.close()
    c.drawPath(p, relleno(col, a))
    f = skia.Path(); f.moveTo(.05, .2); f.lineTo(.9, -.75)
    c.drawPath(f, trazo("#5B4BD6", .07, .8 * a))
    c.restore()


def avatar(c, x, y, r, a, gafas):
    c.drawCircle(x, y + r * .18, r * 1.02, skia.Paint(AntiAlias=True, Color=color("#000000", .35 * a),
                                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Alphaf=a, Shader=skia.GradientShader.MakeLinear(
        [(x, y - r), (x, y + r)], [color("#7F6BFF"), color("#3A2BA8")])))
    c.save(); pc = skia.Path(); pc.addCircle(x, y, r - 4); c.clipPath(pc, doAntiAlias=True)
    piel = "#F2C7A5"
    c.drawOval(skia.Rect.MakeXYWH(x - r * .78, y + r * .42, r * 1.56, r * 1.2), relleno("#1B1F3B", a))       # hombros
    c.drawCircle(x, y - r * .08, r * .42, relleno(piel, a))                                                    # cabeza
    c.drawArc(skia.Rect.MakeXYWH(x - r * .44, y - r * .54, r * .88, r * .7), 180, 180, True, relleno("#3B2416", a))  # pelo
    c.restore()
    c.drawCircle(x, y, r, trazo("#FFFFFF", 3, .55 * a))
    if gafas > 0:                                                                                              # gafas de sol que caen
        yy = y - r * .1 - 40 * (1 - gafas); ag = a * min(1, gafas * 3)
        for sx in (-1, 1):
            c.drawRRect(rrc(x + sx * r * .2, yy, r * .34, r * .2, r * .07), relleno("#0A0A12", ag))
            c.drawLine(x + sx * r * .27, yy - r * .06, x + sx * r * .17, yy - r * .02, trazo("#FFFFFF", 2.2, .6 * ag))
        c.drawLine(x - r * .04, yy - r * .03, x + r * .04, yy - r * .03, trazo("#0A0A12", 4, ag))


def main(proy):
    proy = Path(proy).resolve(); g = json.loads((proy / "guion.json").read_text()); o = g["outro"]
    nombre = proy.name; vid = proy / "final" / f"{nombre}.mp4"; sal = proy / "final" / o.get("salida", f"{nombre}-v2.mp4")
    tmp = proy / ".render" / "outro"; tmp.mkdir(parents=True, exist_ok=True)
    x, pal = voz(proy, o)
    T0 = .45                                                       # la voz entra cuando el fondo ya se apagó
    for p in pal: p["s"] += T0; p["e"] += T0
    fin = pal[-1]["e"] + .9; nf = int(round(fin * FPS))
    # último cuadro del vídeo original como fondo
    ult = tmp / "ultimo.png"
    run(FF, "-v", "error", "-y", "-sseof", "-0.05", "-i", str(vid), "-frames:v", "1", "-update", "1", str(ult))
    fondo = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(ult.read_bytes()))
    key = o.get("key", ""); kw = key.split(); idx = {i for i in range(len(pal) - len(kw), len(pal))} if kw else set()
    t_amigo = next((p["s"] for p in pal if TI.norm(p["w"]) == TI.norm(o.get("amigo_word", "amigo"))), pal[len(pal) // 2]["s"])
    t_key = pal[min(idx)]["s"] if idx else pal[-1]["s"]
    BX, BY, BR = CX, 900, 112          # botón compartir
    AX, AY, AR = CX, 430, 104          # avatar
    t_tap, t_vuelo, d_vuelo = .62, t_amigo - .05, .8
    Fctx, Fkey, Flab = fuente("Inter", 600, 46), fuente("Inter", 800, 124), fuente("Inter", 700, 34)
    L = Lienzo(); c = L.canvas
    ff = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           *ENC, str(tmp / "outro.mp4")], stdin=subprocess.PIPE)
    def curva(u):
        p0, p1, p2 = np.array([BX, BY - 20]), np.array([CX + 330, 700]), np.array([AX, AY])
        q = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u * u * p2
        d = 2 * (1 - u) * (p1 - p0) + 2 * u * (p2 - p1); return q, math.atan2(d[1], d[0])
    for f in range(nf):
        t = f / FPS; c.clear(skia.ColorBLACK)
        u = ease(t / .4); s = 1 + .04 * u
        c.save(); c.translate(CX, 760); c.scale(s, s); c.translate(-CX, -760)
        c.drawImage(fondo, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(ImageFilter=skia.ImageFilters.Blur(22 * u + .01, 22 * u + .01)))
        c.restore()
        c.drawRect(skia.Rect.MakeWH(W, H), relleno("#050818", .72 * u))
        c.drawRect(skia.Rect.MakeXYWH(0, 1080, W, H - 1080), skia.Paint(Shader=skia.GradientShader.MakeLinear(       # tapa los textos del final
            [(0, 1080), (0, 1200)], [color("#050818", 0), color("#050818", .97 * u)])))
        c.drawCircle(CX, 680, 600, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX, 680), 600, [color("#8F7CFF", .22 * u), color("#8F7CFF", 0)], [0, 1])))
        # botón de compartir
        dtb = t - .15
        if dtb > 0:
            sc = resorte(dtb, 9, 13); prs = 1 - .1 * math.sin(math.pi * min(1, max(0, (t - t_tap) / .22))) if t > t_tap else 1
            r = BR * sc * prs; ab = min(1, dtb / .1)
            with capa(c, alfa=.6 * ab, blur=26): c.drawCircle(BX, BY, r, relleno("#8F7CFF"))
            c.drawCircle(BX, BY, r, skia.Paint(AntiAlias=True, Alphaf=ab, Shader=skia.GradientShader.MakeLinear(
                [(BX, BY - r), (BX, BY + r)], [color("#9C8BFF"), color("#5B46E0")])))
            c.drawCircle(BX, BY, r, trazo("#FFFFFF", 3, .5 * ab))
            if t < t_vuelo: avion(c, BX - 4, BY + 2, r * .5, 0, ab)
            elif t > t_vuelo + .25: avion(c, BX - 4, BY + 2, r * .5 * resorte(t - t_vuelo - .25, 9, 13), 0, ab)
            texto(c, o.get("boton", "Compartir"), BX, BY + BR + 62, Flab, "#FFFFFF", alfa=.9 * ab, sombra=(3, 8, .4))
            if t > t_tap:                                          # onda del toque
                for q in range(2):
                    v = (t - t_tap - q * .12) / .6
                    if 0 < v < 1: c.drawCircle(BX, BY, BR * (1 + .9 * v), trazo("#FFFFFF", 4, .6 * (1 - v)))
                dd = t - t_tap                                     # dedo
                if dd < .5:
                    a_ = min(1, (.5 - dd) / .15) * min(1, (dd + .2) / .1); yy = BY + 40 + 30 * max(0, .15 - dd) / .15
                    c.drawCircle(BX + 30, yy + 30, 26, relleno("#FFFFFF", .85 * a_)); c.drawCircle(BX + 30, yy + 30, 26, trazo("#0A0F2C", 3, .4 * a_))
            elif t > t_tap - .35:
                a_ = (t - (t_tap - .35)) / .35; c.drawCircle(BX + 30 + 60 * (1 - a_), BY + 70 + 90 * (1 - a_), 26, relleno("#FFFFFF", .85 * a_))
        # avatar del amigo
        dta = t - (t_amigo - .25)
        if dta > 0:
            sc = resorte(dta, 9, 13); g_ = max(0.0, min(1.0, resorte(t - t_key, 10, 14))) if t > t_key else 0
            c.save(); c.translate(AX, AY); c.scale(sc, sc); c.translate(-AX, -AY)
            avatar(c, AX, AY, AR, min(1, dta / .12), g_)
            c.restore()
            texto(c, o.get("contacto", "Tu amigo"), AX, AY + AR + 46, Flab, "#C9C3EE", alfa=min(1, dta / .15) * .9, sombra=(3, 8, .4))
        # avión de papel en vuelo con estela
        if t >= t_vuelo:
            v = min(1, (t - t_vuelo) / d_vuelo); ue = ease(v)
            for k in range(1, 26):
                uu = ue * k / 25; q, _ = curva(uu)
                c.drawCircle(float(q[0]), float(q[1]), 3.2, relleno("#FFFFFF", .45 * (k / 25) * (1 if v < 1 else max(0, 1 - (t - t_vuelo - d_vuelo) / .4))))
            if v < 1:
                q, ang = curva(ue); avion(c, float(q[0]), float(q[1]), 46 * (1 - .4 * ue), ang + math.radians(38))
            else:                                                 # llegada: destello + check
                dl = t - t_vuelo - d_vuelo
                if dl < .5: c.drawCircle(AX, AY, AR * (1 + .7 * dl / .5), trazo("#FFFFFF", 5, .8 * (1 - dl / .5)))
                sc = resorte(dl, 10, 14); cx_, cy_ = AX + AR * .72, AY + AR * .72
                c.drawCircle(cx_, cy_, 30 * sc, relleno("#2ED47A")); c.drawCircle(cx_, cy_, 30 * sc, trazo("#FFFFFF", 3, .9))
                pk = skia.Path(); pk.moveTo(cx_ - 12 * sc, cy_); pk.lineTo(cx_ - 3 * sc, cy_ + 10 * sc); pk.lineTo(cx_ + 13 * sc, cy_ - 9 * sc)
                c.drawPath(pk, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap,
                                          StrokeJoin=skia.Paint.kRound_Join, Color=color("#FFFFFF")))
        # tipografía cinética (contexto + clave final)
        ctx = [i for i in range(len(pal)) if i not in idx]; esp = ancho(" ", Fctx)
        filas = TX.partir_lineas([pal[i]["w"] for i in ctx], Fctx, 820, esp)
        for fi, fila in enumerate(filas):
            tot = sum(ancho(pal[ctx[j]]["w"], Fctx) for j in fila) + esp * (len(fila) - 1); xx = CX - tot / 2
            yb = CAP_CTX_Y - 62 * (len(filas) - 1 - fi)
            for j in fila:
                p = pal[ctx[j]]; dt = t - p["s"] + .02; a = min(1, max(0, dt / (4 / 60)))
                if a > 0: texto(c, p["w"], xx, yb + 18 * (1 - resorte(dt, 12, 14)), Fctx, "#FFFFFF", alinear="i", alfa=.88 * a, sombra=(3, 8, .35))
                xx += ancho(p["w"], Fctx) + esp
        if idx:
            dt = t - t_key + .02; a = min(1, max(0, dt / (4 / 60)))
            if a > 0:
                kt = key.rstrip(".,:!?"); s_ = .94 + .06 * resorte(dt, 8, 10)
                c.save(); c.translate(CX, CAP_KEY_Y + 26 * (1 - resorte(dt, 8, 10))); c.scale(s_, s_)
                with capa(c, alfa=.55 * a, blur=22): texto(c, kt, 0, 0, Fkey, ACC)
                texto(c, kt, 0, 0, Fkey, ACC, alfa=a, sombra=(4, 12, .35)); c.restore()
        L.arr[..., 3] = 255; ff.stdin.write(L.arr.tobytes())
    ff.stdin.close(); ff.wait()
    # audio: voz al mismo nivel que la voz del vídeo + efectos suaves
    orig = np.frombuffer(run(FF, "-v", "error", "-i", str(vid), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-", capture_output=True).stdout, np.float32).reshape(-1, 2)
    def rms_activa(m):
        e = np.sqrt(np.convolve(m ** 2, np.ones(2400) / 2400, "same")); umb = np.percentile(e, 95) * .25
        return float(np.sqrt(np.mean(m[e > umb] ** 2)))
    ganancia = rms_activa(orig.mean(1)) / rms_activa(x)
    n = int(fin * SR); mono = np.zeros(n, np.float32); a0 = int(T0 * SR)
    mono[a0:a0 + len(x)] += (x * ganancia)[: n - a0]
    def sfx(t, nom, vol):
        e_ = efecto(nom) * vol * ganancia * .55; i = int(t * SR); m = min(n, i + len(e_)); mono[i:m] += e_[: m - i]
    sfx(.12, "pop", .5); sfx(t_tap - .02, "tecla", .6); sfx(t_vuelo, "whoosh", .7); sfx(t_vuelo + d_vuelo, "ding", .6)
    pico = np.abs(mono).max(); lim = 10 ** (-1.5 / 20)
    if pico > lim: mono *= lim / pico
    wav = np.vstack([orig, np.c_[mono, mono]])
    import soundfile as sf
    sf.write(tmp / "audio.wav", wav, SR, subtype="FLOAT")
    # vídeo: original copiado sin recodificar + outro; audio unido y codificado una vez
    lista = tmp / "lista.txt"; lista.write_text(f"file '{vid}'\nfile '{tmp / 'outro.mp4'}'\n")
    run(FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(tmp / "audio.wav"),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-movflags", "+faststart", str(sal))
    print(f"{sal} · outro {fin:.2f} s · ganancia voz {20 * math.log10(ganancia):+.1f} dB")


if __name__ == "__main__":
    main(sys.argv[1])
