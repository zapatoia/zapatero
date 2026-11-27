#!/usr/bin/env python3
"""Voz de un proyecto vertical en UNA toma corrida con ElevenLabs /with-timestamps (sin Whisper).

  PY voz_eleven.py <proyecto>            genera (solo si no hay toma guardada) y arma voz.wav + palabras.json
  PY voz_eleven.py <proyecto> armar      vuelve a armar desde la toma guardada (no gasta)

Voz: perfil.json → voz_id. Clave: ELEVENLABS_API_KEY (entorno o .env), nunca se imprime. Modelo: guion.json → voz_modelo.
Marcas por palabra: alineación por carácter que devuelve ElevenLabs, mapeada a las palabras de `texto` (las cifras de `texto`
se reparten el tramo de sus palabras habladas en `tts`). Pausas > 0.8 s se acortan a 0.6 s dentro del silencio.
"""
import base64, difflib, json, os, subprocess, sys, urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

MOTOR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MOTOR))
from nucleo.rutas import FF, perfil, leer_texto, clave_eleven   # noqa: E402
from nucleo.tiempo import norm                                   # noqa: E402

SR = 48000


def generar(proy, g):
    au = proy / "audio"; au.mkdir(exist_ok=True); toma = au / "toma.json"
    if toma.exists(): return json.loads(toma.read_text())
    texto = " ".join(l["tts"] for l in g["lineas"])
    tope = g.get("tope_caracteres", 2500)
    if len(texto) > tope: sys.exit(f"{len(texto)} caracteres > tope {tope}")
    voz = perfil().get("voz_id"); modelo = g.get("voz_modelo", "eleven_v3")
    body = dict(text=texto, model_id=modelo, language_code="es", voice_settings=dict(stability=.5, similarity_boost=.85))
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps?output_format=mp3_44100_192",
                                 data=json.dumps(body).encode(), headers={"xi-api-key": clave_eleven(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r: d = json.loads(r.read())
    (au / "toma.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    t = dict(texto=texto, modelo=modelo, voz=voz, caracteres=len(texto), al=d.get("alignment") or d.get("normalized_alignment"))
    toma.write_text(json.dumps(t, ensure_ascii=False))
    (au / "eleven_gasto.json").write_text(json.dumps(dict(caracteres=len(texto), modelo=modelo), ensure_ascii=False))
    return t


def armar(proy, g, t):
    au = proy / "audio"
    x = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", str(au / "toma.mp3"), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                                     capture_output=True, check=True).stdout, np.float32).copy()
    al = t["al"]; ch = al["characters"]; cs = al["character_start_times_seconds"]; ce = al["character_end_times_seconds"]
    full = "".join(ch)
    # palabras habladas (tts) con su tramo
    hab = []; i = 0
    while i < len(full):
        if full[i].isspace(): i += 1; continue
        j = i
        while j < len(full) and not full[i:j + 1][-1].isspace(): j += 1
        w = full[i:j]
        if norm(w): hab.append(dict(w=w, s=cs[i], e=ce[j - 1]))
        i = j
    # palabras visibles (texto) por línea
    vis = []
    for n, l in enumerate(g["lineas"], 1):
        for w in l["texto"].split(): vis.append(dict(w=w, linea=n))
    A = [norm(w["w"]) for w in vis]; B = [norm(w["w"]) for w in hab]
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            for k in range(a1 - a0): vis[a0 + k].update(s=hab[b0 + k]["s"], e=hab[b0 + k]["e"])
        elif a1 > a0:
            if b1 > b0: s0, e0 = hab[b0]["s"], hab[b1 - 1]["e"]
            else: s0 = hab[b0 - 1]["e"] if b0 else 0; e0 = s0 + .05
            n = a1 - a0
            for k in range(n): vis[a0 + k].update(s=s0 + (e0 - s0) * k / n, e=s0 + (e0 - s0) * (k + 1) / n)
    # recorte de silencio inicial y pausas largas
    hop0 = int(.005 * SR); e0 = np.array([np.sqrt(np.mean(x[i:i + hop0] ** 2) + 1e-12) for i in range(0, int(3 * SR), hop0)])
    ini = max(0.0, next(i for i, v in enumerate(20 * np.log10(e0)) if v > -45) * .005 - .003)
    cortes = [(0.0, ini)]                      # (t original, quitar)
    # silencios reales (envolvente < -42 dB durante ≥ 0.25 s): se dejan en g.pausa (0.28 s) quitando el centro
    hop = int(.01 * SR); env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x) - hop, hop)])
    sil = 20 * np.log10(env) < -42; s0 = None; deja = g.get("pausa", .28)
    for i, v in enumerate(list(sil) + [False]):
        if v and s0 is None: s0 = i
        if not v and s0 is not None:
            a, d = s0 / 100, (i - s0) / 100; s0 = None
            if a > ini + .05 and d > deja + .02 and a + d < vis[-1]["e"]: cortes.append((a + deja / 2, d - deja))
    def mapa(tt):
        q = 0.0
        for c0, d in cortes:
            if tt > c0: q += min(d, tt - c0)
        return tt - q
    keep = np.ones(len(x), bool)
    for c0, d in cortes:
        keep[int(c0 * SR):int((c0 + d) * SR)] = False
    y = x[keep].copy()
    # fundido de 6 ms a cada lado de cada empalme (sin clics)
    k6 = int(.006 * SR); rampa = np.linspace(0, 1, k6)
    for c0, d in cortes[1:]:
        j = int(c0 * SR) - int(np.sum(~keep[:int(c0 * SR)]))
        if k6 < j < len(y) - k6: y[j - k6:j] *= rampa[::-1]; y[j:j + k6] *= rampa
    # final: la cola real de la voz (último tramo > −50 dB) + 0.12 s, nunca antes de la marca de la última palabra
    hop2 = int(.005 * SR); e2 = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + hop2] ** 2) + 1e-12) for i in range(0, len(y) - hop2, hop2)]))
    vivo = np.where(e2 > -50)[0]; fin = max(mapa(vis[-1]["e"]) + .05, (vivo[-1] * .005 + .12) if len(vivo) else 0)
    y = y[:int(fin * SR)]
    tempo = g.get("tempo", 1.0)
    if tempo != 1.0:
        y = np.frombuffer(subprocess.run([FF, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={tempo}", "-f", "f32le", "-"],
                                         input=y.astype(np.float32).tobytes(), capture_output=True, check=True).stdout, np.float32).copy()
    m0 = mapa; mapa = lambda tt: m0(tt) / tempo
    cola = 20 * np.log10(np.sqrt(np.mean(y[-int(.05 * SR):] ** 2)) + 1e-12)
    k = int((.22 if cola > -45 else .03) * SR); y[-k:] *= np.linspace(1, 0, k) ** 1.5   # si la toma acaba con aire (sigue sonando), fundido natural
    pal = [dict(w=v["w"], s=round(mapa(v["s"]), 3), e=round(mapa(v["e"]), 3), linea=v["linea"]) for v in vis]
    # arranques: si la marca cae en silencio, se mueve al primer borde de voz real (la palabra entra cuando se dice)
    hop = int(.005 * SR); ev = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + hop] ** 2) + 1e-12) for i in range(0, len(y) - hop, hop)]))
    for k, w in enumerate(pal):
        i0 = int(w["s"] / .005); lim = int((pal[k + 1]["e"] if k + 1 < len(pal) else w["e"]) / .005)
        if k and ev[i0:i0 + 6].max() < -40:
            j = next((i for i in range(i0, max(lim, i0 + 1)) if ev[i] > -40), None)
            if j is not None:
                w["s"] = round(max(j * .005 - .01, w["s"]), 3); w["e"] = max(w["e"], round(w["s"] + .08, 3))
                if k + 1 < len(pal) and pal[k + 1]["s"] < w["e"]: pal[k + 1]["s"] = w["e"]
    # líneas omitidas (guion.json → lineas[].omitir): se quita su audio de la toma ya pagada (con la pausa que la sigue)
    for n, l in reversed(list(enumerate(g["lineas"], 1))):
        if not l.get("omitir"): continue
        ks = [k for k, w in enumerate(pal) if w["linea"] == n]
        if not ks: continue
        k0, k1 = ks[0], ks[-1]; a = max(pal[k0]["s"] - .03, pal[k0 - 1]["e"] + .02 if k0 else 0)
        b = pal[k1 + 1]["s"] - .03 if k1 + 1 < len(pal) else len(y) / SR
        ia, ib = int(a * SR), int(b * SR); f6 = int(.006 * SR); y = y.copy()
        y[max(0, ia - f6):ia] *= np.linspace(1, 0, min(f6, ia)); y[ib:ib + f6] *= np.linspace(0, 1, len(y[ib:ib + f6]))
        y = np.concatenate([y[:ia], y[ib:]]); d = b - a
        for w in pal[k1 + 1:]: w["s"] = round(w["s"] - d, 3); w["e"] = round(w["e"] - d, 3)
        del pal[k0:k1 + 1]
    # silencios pedidos (guion.json → lineas[].silencio, en s): se insertan tras la última palabra de la línea (juegos con espera)
    for n, l in reversed(list(enumerate(g["lineas"], 1))):
        sil_s = float(l.get("silencio", 0) or 0)
        if sil_s <= 0: continue
        ult = max(k for k, w in enumerate(pal) if w["linea"] == n)
        sig = pal[ult + 1]["s"] if ult + 1 < len(pal) else len(y) / SR
        # punto de inserción: el primer tramo de 30 ms en silencio (< −48 dB) tras la palabra, para no cortar su cola
        i0 = int(pal[ult]["e"] * SR); fin_b = int(sig * SR) if ult + 1 < len(pal) else len(y); v30 = int(.03 * SR); ref = np.abs(y).max() + 1e-9
        while i0 + v30 < fin_b and 20 * np.log10(np.sqrt(np.mean(y[i0:i0 + v30] ** 2)) / ref + 1e-12) > -60: i0 += int(.005 * SR)
        i0 = min(i0 + v30 // 2, fin_b); f6 = int(.06 * SR)
        y = y.copy(); y[max(0, i0 - f6):i0] *= np.linspace(1, 0, min(f6, i0))
        y = np.concatenate([y[:i0], np.zeros(int(sil_s * SR), y.dtype), y[i0:]])
        for w in pal[ult + 1:]: w["s"] = round(w["s"] + sil_s, 3); w["e"] = round(w["e"] + sil_s, 3)
    sf.write(str(proy / "voz.wav"), y, SR, subtype="FLOAT")
    (proy / "palabras.json").write_text(json.dumps(pal, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"voz.wav {len(y) / SR:.2f} s · {len(pal)} palabras · pausas recortadas {len(cortes) - 1} · {t['caracteres']} caracteres ({t['modelo']})")


if __name__ == "__main__":
    proy = Path(sys.argv[1]).resolve(); g = json.loads(leer_texto(proy / "guion.json"))
    t = generar(proy, g) if (len(sys.argv) < 3 or sys.argv[2] != "armar") else json.loads((proy / "audio/toma.json").read_text())
    armar(proy, g, t)
