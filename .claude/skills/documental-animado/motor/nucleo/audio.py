"""Audio del núcleo: mezcla (voz + música nivelada + SFX alineados al cuadro), master, y reloj musical para los estilos sin voz.

SFX suaves sintetizados: pop, ding, tecla, teclado, whoosh, sello, tic, palomita, destello, golpe, nota (más en SFX).
Un evento es {"f": cuadro, "sfx": nombre, "vol": 1.0}. La muestra 0 del efecto cae EXACTA en el cuadro f (f/30 s).
Regla: el pico del pop va en f1–f2 del POP → dispara el SFX con f = entrada + 1.
"""
import json, math, os, subprocess, sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

from .tiempo import FPS

from .rutas import MOTOR as MV, HERRAMIENTAS, FF, perfil
sys.path.insert(0, str(HERRAMIENTAS))
import audio_youtube as AY  # noqa: E402

SR = 48000
MUSICA = Path(perfil().get("musica_carpeta") or ".").expanduser()   # carpeta de música del usuario (perfil.json); "pista" también puede ser una ruta completa
LUFS, TP = -14.0, -1.0


def _env(n, ataque=.004, caida=.08):
    t = np.arange(n) / SR; return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / caida)
def _ruido(n, s=0): return np.random.default_rng(s).standard_normal(n)
def _banda(x, a, b, o=2): return sosfilt(butter(o, [a, b], btype="band", fs=SR, output="sos"), x)
def _bajos(x, f, o=2): return sosfilt(butter(o, f, btype="low", fs=SR, output="sos"), x)
def _altos(x, f, o=2): return sosfilt(butter(o, f, btype="high", fs=SR, output="sos"), x)
def _barrido(f0, f1, d, cur=1.0):
    n = int(d * SR); u = np.linspace(0, 1, n) ** cur; return np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * u) / SR)


def s_pop():
    d = .09; n = int(d * SR); return _barrido(320, 780, d, .55) * _env(n, .002, .028) + .12 * _banda(_ruido(n), 1200, 4500) * _env(n, .001, .005)
def s_ding():
    d = .55; n = int(d * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for m, a, dc in ((1, 1, .20), (2.01, .35, .10), (3.0, .12, .05)): x += a * np.sin(2 * np.pi * 1240 * m * t) * np.exp(-t / dc) * np.minimum(1, t / .002)
    return x
def s_palomita():
    d = .35; n = int(d * SR); x = np.zeros(n); t = np.arange(n) / SR
    for f0, t0 in ((880, 0), (1320, .07)):
        k = int(t0 * SR); tt = t[:n - k]; x[k:] += np.sin(2 * np.pi * f0 * tt) * np.exp(-tt / .07) * np.minimum(1, tt / .002)
    return x
def s_tecla(s=4):
    m = int(.025 * SR); r = np.random.default_rng(s)
    return _banda(r.standard_normal(m), 1500, 5500) * _env(m, .0005, .004) + .4 * np.sin(2 * np.pi * r.uniform(800, 1100) * np.arange(m) / SR) * _env(m, .0005, .005)
def s_whoosh():
    d = .34; n = int(d * SR); u = np.linspace(0, 1, n); r = _ruido(n, 7); o = np.zeros(n); B = 20
    for k in range(B):
        a, b = k * n // B, (k + 1) * n // B; fc = 300 + 1900 * (k / B) ** 1.4; o[a:b] = _banda(r, fc * .7, fc * 1.4)[a:b]
    return o * np.sin(np.pi * u) ** 2
def s_sello():
    d = .22; n = int(d * SR); x = _barrido(150, 62, d, .35) * _env(n, .001, .05) + .35 * _bajos(_ruido(n, 3), 1400) * _env(n, .0005, .012)
    return np.tanh(x * 1.3)
def s_golpe():
    d = .32; n = int(d * SR); return np.tanh((_barrido(120, 45, d, .35) * _env(n, .001, .09) * 1.2 + .4 * _bajos(_ruido(n, 3), 800) * _env(n, .0005, .02)) * 1.4)
def s_tic():
    d = .03; n = int(d * SR); return np.sin(2 * np.pi * 1900 * np.arange(n) / SR) * _env(n, .0005, .006)
def s_destello():
    d = .7; n = int(d * SR); x = np.zeros(n)
    for k, f in enumerate((1760, 2349, 2637, 3520)):
        a = int(k * .05 * SR); m = n - a; tt = np.arange(m) / SR; x[a:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / .12) * np.minimum(1, tt / .002) * (.9 - .15 * k)
    return x


SFX = dict(pop=(s_pop, -23), ding=(s_ding, -27), palomita=(s_palomita, -25), tecla=(s_tecla, -28), whoosh=(s_whoosh, -29), sello=(s_sello, -20),
           golpe=(s_golpe, -20), tic=(s_tic, -30), destello=(s_destello, -31))


def efecto(nombre):
    f, db = SFX[nombre]; x = f(); x = x / (np.abs(x).max() + 1e-9); return x * 10 ** (db / 20)


def leer(path, canales=2, t=None, desde=0.0):
    cmd = [FF, "-v", "error", "-ss", f"{desde:.3f}", "-i", str(path)]
    if t: cmd += ["-t", f"{t:.3f}"]
    cmd += ["-f", "f32le", "-ac", str(canales), "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, canales).astype(np.float64)


def tramo_con_energia(path, dur):
    x = leer(path, 2); t, L = AY.loudness_corto(x, SR, 3.0, .5); mejor, best = 0.0, -1e9
    for t0 in t:
        if t0 + dur > len(x) / SR * .95 or t0 > len(x) / SR * .7: break
        v = np.median(L[(t >= t0) & (t <= t0 + dur)])
        if v > best + .5: best, mejor = v, t0
    return float(mejor)


def musica_bajo_voz(V, hab, n, cfg):
    """Pista de tu carpeta de música (perfil.json) → nivelada, X dB bajo la voz, solo graves/medios si `pasa_bajos`. cfg: pista, bajo_voz_db, desde, pasa_bajos."""
    pista = MUSICA / cfg["pista"]; fin = n / SR; desde = cfg.get("desde") if cfg.get("desde") is not None else tramo_con_energia(pista, fin)
    m = leer(pista, 2, fin + 1, desde)[:n]; m = np.pad(m, ((0, n - len(m)), (0, 0)))
    if cfg.get("pasa_bajos"): m = np.stack([_bajos(m[:, i], cfg["pasa_bajos"], 4) for i in (0, 1)], 1)
    m = AY.normalizar_lufs(m, -16.0, SR); m, _, niv = AY.nivelar_corto_plazo(m, SR)
    lv = AY.lufs_integrado(V, SR); bajo = cfg.get("bajo_voz_db", 17)
    m = m * 10 ** ((lv - bajo - AY.lufs_integrado(m, SR)) / 20)
    m, _ = AY.techo_musica(V, m, hab, SR, techo=-(bajo - 3))
    k = int(.015 * SR); m[:k] *= np.linspace(0, 1, k)[:, None]
    k = int(cfg.get("fade_final", .2) * SR); m[-k:] *= np.linspace(1, 0, k)[:, None]
    mv, _ = AY.musica_menos_voz(V, m, hab, SR)
    return m, dict(musica=pista.name, desde_s=round(desde, 1), musica_menos_voz=mv)


def mezclar(salida, fin_s, voz=None, palabras=None, eventos=(), musica=None, base=None, sep_min=.09, baja_sobre_voz=5.0):
    """Escribe mezcla float. voz=wav mono; palabras=[{s,e}]; musica=cfg de pista; base=(n,2) ya sintetizada (RelojMusical). SFX bajan al caer sobre una palabra."""
    n = int(round(fin_s * SR)); info = {}; M = np.zeros((n, 2)); hab = np.zeros(n, bool); pal_on = np.zeros(n, bool)
    if voz is not None:
        v = leer(voz, 1)[:, 0]; v = np.pad(v, (0, max(0, n - len(v))))[:n]; V = np.stack([v, v], 1); M += V
        for k, p in enumerate(palabras):
            fp = palabras[k + 1]["s"] if k + 1 < len(palabras) and palabras[k + 1]["s"] - p["e"] < .7 else p["e"]
            hab[int(p["s"] * SR):int(fp * SR)] = True; pal_on[int(p["s"] * SR):int(p["e"] * SR)] = True
        info["voz_lufs"] = round(AY.lufs_integrado(V, SR), 1)
        if musica:
            m, im = musica_bajo_voz(V, hab, n, musica); M += m; info.update(im); info["musica_lufs"] = round(AY.lufs_integrado(m, SR), 1)
    if base is not None:
        b = base[:n]; M[:len(b)] += b
    fx = np.zeros(n); usados = []; ult = -9
    for e in sorted(eventos, key=lambda e: e["f"]):
        t = e["f"] / FPS
        if e["sfx"] not in SFX or t < 0 or t >= fin_s or t - ult < sep_min: continue
        x = efecto(e["sfx"]) * e.get("vol", 1.0); a = int(round(e["f"] * SR / FPS)); b = min(n, a + len(x))
        if pal_on[a:b].mean() > .2: x = x * 10 ** (-baja_sobre_voz / 20)
        fx[a:b] += x[:b - a]; usados.append(f"{t:.2f} {e['sfx']}"); ult = t
    M += np.stack([fx, fx], 1)
    sf.write(str(salida), M.astype(np.float32), SR, subtype="FLOAT")
    info.update(efectos=len(usados), efectos_lista=usados)
    return info


def medir(f):
    r = subprocess.run([FF, "-hide_banner", "-i", str(f), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return float(r.split("I:")[-1].split("LUFS")[0]), float(r.split("Peak:")[-1].split("dBFS")[0])


def montar(mudo, mezcla, salida, lufs=LUFS, tp=TP):
    """Pega mezcla a video mudo y hace el master con herramientas/master_video.py (pico medido DESPUÉS del AAC)."""
    tmp = Path(salida).with_suffix(".tmp.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(mudo), "-i", str(mezcla), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "pcm_f32le", "-f", "mov", str(tmp)], check=True)
    r = subprocess.run([sys.executable, str(MV / "herramientas" / "master_video.py"), str(tmp), str(salida), f"--lufs={lufs}", f"--tp={tp}"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode: raise RuntimeError(r.stderr[-800:])
    tmp.unlink(missing_ok=True)
    return medir(salida)


# ------------------------------------------------------------------ reloj musical (estilos sin voz)
_NOTA = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def midi(nombre):
    """'A4' → 69"""
    nm = nombre[:-1]; return 12 * (int(nombre[-1]) + 1) + _NOTA[nm]


def acorde(nombre, oct=3):
    """'Am' / 'C' / 'G7' → notas MIDI."""
    raiz = nombre[:2] if nombre[1:2] in ("#", "b") else nombre[0]; suf = nombre[len(raiz):]; r = 12 * (oct + 1) + _NOTA[raiz]
    iv = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11)}[suf]
    return [r + i for i in iv]


def _pluck(f0, d, vel, brillo=.5):
    n = int(d * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for k, (a, dc) in enumerate(((1, .9), (.45 * brillo + .1, .5), (.22 * brillo, .28), (.1 * brillo, .16))):
        x += a * np.sin(2 * np.pi * f0 * (k + 1) * t) * np.exp(-t / dc)
    return x * np.minimum(1, t / .003) * vel


def _pad(f0, d, vel):
    n = int(d * SR); t = np.arange(n) / SR; x = sum(np.sin(2 * np.pi * f0 * m * t + m) * a for m, a in ((1, 1), (2.003, .2), (.5, .3)))
    return x * np.minimum(1, t / .25) * np.minimum(1, (d - t) / .4) * vel


class RelojMusical:
    """Primero la música, después la imagen (sonificación): la partitura manda y cada evento visual se dispara de aquí.

      r = RelojMusical(cuadros_por_pulso=25)                         # 25 f = 72 BPM exactos en cuadros
      r.nota(pulso=3, midi=69, vel=.8, timbre="pluck", nombre="n3")  # o r.acorde(pulso, "Am", dur=4, timbre="pad")
      r.f(3) → cuadro del pulso 3 · r.notas_f("n") → cuadros de las notas · r.f_visual(3) → pulso +1 cuadro (la imagen reacciona +1…+3 f)
      r.sintetizar(fin_s, reverb_s=1.5, estereo=.3, cresc=(-17.3, -14.2)) → (n, 2) float para audio.mezclar(base=…)
    Todas las notas caen en una muestra múltiplo exacto del cuadro."""
    def __init__(self, cuadros_por_pulso=25): self.cpp = cuadros_por_pulso; self.notas = []
    @property
    def bpm(self): return 60 * FPS / self.cpp
    def f(self, pulso): return int(round(pulso * self.cpp))
    def f_visual(self, pulso, retraso=1): return self.f(pulso) + retraso

    def nota(self, pulso, midi, vel=.8, dur=1.4, timbre="pluck", nombre=None, pan=0.0):
        self.notas.append(dict(f=self.f(pulso), midi=midi, vel=vel, dur=dur, timbre=timbre, nombre=nombre, pan=pan)); return self

    def acorde(self, pulso, nombre, dur=4.0, vel=.25, timbre="pad", oct=3):
        for m in acorde(nombre, oct): self.nota(pulso, m, vel, dur * self.cpp / FPS, timbre)
        return self

    def notas_f(self, prefijo=""): return [n["f"] for n in self.notas if n["nombre"] and n["nombre"].startswith(prefijo)]

    def sintetizar(self, fin_s, reverb_s=1.2, estereo=.35, cresc=None, semilla=9):
        n = int(round(fin_s * SR)); L = np.zeros(n + SR * 4); R = np.zeros(n + SR * 4); rng = np.random.default_rng(semilla)
        for k, e in enumerate(self.notas):
            f0 = 440 * 2 ** ((e["midi"] - 69) / 12); x = _pad(f0, e["dur"], e["vel"]) if e["timbre"] == "pad" else _pluck(f0, e["dur"], e["vel"])
            a = int(round(e["f"] * SR / FPS))
            if a >= n: continue
            pan = e["pan"] if e["pan"] else rng.uniform(-estereo, estereo)
            L[a:a + len(x)] += x * math.cos((pan + 1) * math.pi / 4); R[a:a + len(x)] += x * math.sin((pan + 1) * math.pi / 4)
        if reverb_s:
            m = int(reverb_s * SR); t = np.arange(m) / SR; g = np.exp(-t / (reverb_s / 4))
            for ch, sd in ((0, 1), (1, 2)):
                ir = _bajos(np.random.default_rng(sd).standard_normal(m) * g, 4000) * .02
                (L, R)[ch][:] = (L, R)[ch] + fftconvolve((L, R)[ch], ir)[:len(L)]
        o = np.stack([L[:n], R[:n]], 1)
        if cresc: o *= (10 ** (np.linspace(cresc[0], cresc[1], n) / 20))[:, None] / 10 ** (cresc[1] / 20)
        k = int(.003 * SR); o[:k] *= np.linspace(0, 1, k)[:, None]
        return o
