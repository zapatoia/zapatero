"""Audio: decodificar, verificar/corregir timestamps, acortar pausas, efectos
generados por código, mezcla y sonoridad (-14 LUFS, pico ≤ -1,5 dBTP)."""
import json
import math
import re
import subprocess
import numpy as np

SR = 44100


# ------------------------------------------------------------------ E/S

def decode(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def write_wav(path, x, sr=SR):
    import soundfile as sf
    sf.write(path, np.asarray(x, np.float32), sr, subtype="FLOAT")


def envelope(x, sr=SR, hop=0.01):
    n = int(sr * hop)
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return np.sqrt((fr ** 2).mean(1) + 1e-12)


# ------------------------------------------------------------------ palabras

def words_from_alignment(al):
    """Agrupa caracteres en palabras {text, start, end} (puntuación incluida)."""
    chars = al["characters"]
    st = al["character_start_times_seconds"]
    en = al["character_end_times_seconds"]
    words, cur = [], None
    for c, s, e in zip(chars, st, en):
        if c.isspace():
            if cur:
                words.append(cur)
                cur = None
            continue
        if cur is None:
            cur = {"text": c, "start": s, "end": e, "chars": [(c, s, e)]}
        else:
            cur["text"] += c
            cur["end"] = e
            cur["chars"].append((c, s, e))
    if cur:
        words.append(cur)
    # la puntuación no suena: ajustar fin al último carácter alfanumérico
    for w in words:
        alnum = [x for x in w["chars"] if x[0].isalnum()]
        if alnum:
            w["start"], w["end"] = alnum[0][1], alnum[-1][2]
    return words


def estimate_words(text, wps=2.95, pause_comma=0.18, pause_stop=0.34, lead=0.15):
    """Tiempos estimados (modo --dry, sin voz)."""
    out = []
    t = lead
    for tok in text.split():
        core = re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ]", "", tok)
        dur = max(0.14, len(core) * 0.062) * (2.95 / wps)
        chars = []
        cd = dur / max(1, len(tok))
        for i, c in enumerate(tok):
            chars.append((c, t + i * cd, t + (i + 1) * cd))
        out.append({"text": tok, "start": t, "end": t + dur, "chars": chars})
        t += dur + 0.06
        if tok[-1] in ",;":
            t += pause_comma
        elif tok[-1] in ".:!?»":
            t += pause_stop
    return out, t + 0.3


# ------------------------------------------------------------------ alineación

def check_alignment(x, words, sr=SR, max_lag=0.35):
    """Compara la actividad vocal real (envolvente) con la que predicen los
    timestamps. Devuelve el desfase óptimo en segundos (+ = el audio va después)."""
    env = envelope(x, sr)
    hop = 0.01
    db = 20 * np.log10(env / (env.max() + 1e-9) + 1e-9)
    voiced = (db > -32).astype(float)
    pred = np.zeros_like(voiced)
    for w in words:
        a, b = int(w["start"] / hop), int(w["end"] / hop)
        pred[max(a, 0):max(b, a + 1)] = 1.0
    best, best_lag = -1e9, 0
    L = int(max_lag / hop)
    for lag in range(-L, L + 1):
        p = np.roll(pred, lag)
        if lag > 0:
            p[:lag] = 0
        elif lag < 0:
            p[lag:] = 0
        score = (p * voiced).sum() - 0.5 * (p * (1 - voiced)).sum()
        if score > best:
            best, best_lag = score, lag
    agree = ((np.roll(pred, best_lag) > 0) == (voiced > 0)).mean()
    agree0 = ((pred > 0) == (voiced > 0)).mean()
    return best_lag * hop, float(agree), float(agree0)


def shift_words(words, dt):
    for w in words:
        w["start"] += dt
        w["end"] += dt
        w["chars"] = [(c, s + dt, e + dt) for c, s, e in w["chars"]]
    return words


# ------------------------------------------------------------------ pausas

def shorten_pauses(x, words, sr=SR, max_pause=0.42, target=0.30, lead=0.12, tail=0.35):
    """Recorta silencios largos (sin regenerar) y remapea los timestamps.

    Solo corta en huecos entre palabras donde la envolvente es realmente silencio."""
    env = envelope(x, sr)
    hop = 0.01
    thr = env.max() * 10 ** (-38 / 20)
    cuts = []  # (inicio, fin) en segundos de audio original a eliminar
    # silencio inicial
    first = words[0]["start"]
    if first > lead:
        cuts.append((0.0, first - lead))
    for w0, w1 in zip(words, words[1:]):
        gap0, gap1 = w0["end"], w1["start"]
        if gap1 - gap0 <= max_pause:
            continue
        a, b = int(gap0 / hop), int(gap1 / hop)
        seg = env[a:b]
        quiet = np.where(seg < thr)[0]
        if len(quiet) < (gap1 - gap0 - 0.1) / hop * 0.6:
            continue
        excess = (gap1 - gap0) - target
        mid = (gap0 + gap1) / 2
        cuts.append((mid - excess / 2, mid + excess / 2))
    end = words[-1]["end"]
    total = len(x) / sr
    if total - end > tail:
        cuts.append((end + tail, total))
    # construir audio nuevo con fundidos de 10 ms en cada corte
    fade = int(0.01 * sr)
    pieces, keep = [], []
    t = 0.0
    for a, b in cuts:
        if a > t:
            keep.append((t, a))
        t = b
    if t < total:
        keep.append((t, total))
    for (a, b) in keep:
        seg = x[int(a * sr):int(b * sr)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
        pieces.append(seg)
    y = np.concatenate(pieces) if pieces else x

    def remap(tt):
        removed = 0.0
        for a, b in cuts:
            if tt >= b:
                removed += b - a
            elif tt > a:
                removed += tt - a
        return tt - removed

    for w in words:
        w["start"], w["end"] = remap(w["start"]), remap(w["end"])
        w["chars"] = [(c, remap(s), remap(e)) for c, s, e in w["chars"]]
    removed = sum(b - a for a, b in cuts)
    return y, words, cuts, removed


# ------------------------------------------------------------------ efectos (síntesis)

def _t(d, sr=SR):
    return np.arange(int(d * sr)) / sr


def _adsr(n, a=0.005, r=0.1, sr=SR):
    env = np.ones(n)
    na, nr = int(a * sr), int(r * sr)
    if na:
        env[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        env[-nr:] *= np.linspace(1, 0, nr) ** 2
    return env


def _noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _lp(x, a):
    from scipy.signal import lfilter
    return lfilter([a], [1, -(1 - a)], x)


def sfx_pop(seed=0):
    t = _t(0.12)
    f = 300 + 900 * np.exp(-t * 40)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 30) * 0.8


def sfx_ding(seed=0, base=1320.0):
    t = _t(0.9)
    y = sum(a * np.sin(2 * np.pi * base * k * t) * np.exp(-t * d) for a, k, d in
            ((1.0, 1, 5), (0.5, 2.01, 8), (0.25, 3.02, 12), (0.15, 4.2, 16)))
    return y * _adsr(len(t), 0.002, 0.3) * 0.45


def sfx_blip(seed=0):
    t = _t(0.09)
    return np.sign(np.sin(2 * np.pi * (880 + 400 * (t > 0.045)) * t)) * np.exp(-t * 25) * 0.25


def sfx_step(seed=0):
    n = _noise(int(0.09 * SR), seed)
    n = _lp(n, 0.08)
    t = _t(0.09)
    thump = np.sin(2 * np.pi * 90 * t) * np.exp(-t * 45)
    return (n * 2.5 + thump) * np.exp(-t * 35) * 0.5


def sfx_lick(seed=0):
    """Lametón húmedo: ruido filtrado con barrido + chasquido final."""
    d = 0.22
    t = _t(d)
    n = _noise(len(t), seed + 3)
    a = 0.05 + 0.25 * (t / d)
    y = np.empty_like(n)
    acc = 0.0
    for i, v in enumerate(n):
        acc += a[i] * (v - acc)
        y[i] = acc
    env = np.sin(np.pi * t / d) ** 1.5
    click = np.zeros_like(t)
    k = int(0.17 * SR)
    click[k:k + 300] = np.sin(2 * np.pi * 1800 * _t(300 / SR)) * np.exp(-np.arange(300) / 60)
    wob = 1 + 0.4 * np.sin(2 * np.pi * 38 * t)
    return (y * env * wob * 2.2 + click * 0.4) * 0.6


def sfx_boing(seed=0):
    t = _t(0.45)
    f = 180 + 220 * np.exp(-t * 6) * (1 + 0.15 * np.sin(2 * np.pi * 14 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 6) * 0.5


def sfx_whoosh(seed=0):
    d = 0.35
    t = _t(d)
    n = _noise(len(t), seed + 7)
    a = 0.02 + 0.2 * np.sin(np.pi * t / d)
    y = np.empty_like(n)
    acc = 0.0
    for i, v in enumerate(n):
        acc += a[i] * (v - acc)
        y[i] = acc
    return y * np.sin(np.pi * t / d) ** 2 * 1.6


def sfx_thud(seed=0):
    t = _t(0.25)
    return (np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18) + _lp(_noise(len(t), seed), 0.1) * np.exp(-t * 30)) * 0.6


SFX = {"pop": sfx_pop, "ding": sfx_ding, "blip": sfx_blip, "step": sfx_step, "lick": sfx_lick,
       "boing": sfx_boing, "whoosh": sfx_whoosh, "thud": sfx_thud}

SFX_GAIN_DB = {"pop": -21, "ding": -24, "blip": -24, "step": -27, "lick": -19, "boing": -23, "whoosh": -30, "thud": -24}


def ambience(dur, seed=1):
    """Viento suave + pájaros sintéticos ocasionales (sin música)."""
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    w = _noise(n, seed)
    w = _lp(w, 0.01)
    w = _lp(w, 0.02)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * np.arange(n) / SR + 1)
    y = w / (np.abs(w).max() + 1e-9) * mod * 0.5
    t = 0.7
    while t < dur - 1:
        k = int(t * SR)
        for c in range(rng.integers(2, 4)):
            tt = _t(0.07)
            f0 = rng.uniform(2800, 4200)
            f = f0 + 900 * np.sin(np.pi * tt / 0.07)
            ph = 2 * np.pi * np.cumsum(f) / SR
            s = np.sin(ph) * np.sin(np.pi * tt / 0.07) * 0.18
            kk = k + int(c * 0.11 * SR)
            if kk + len(s) < n:
                y[kk:kk + len(s)] += s
        t += rng.uniform(2.5, 5.5)
    return y


def mix(voice, events, dur, amb_db=-36.0):
    n = int(dur * SR) + SR
    out = np.zeros(n)
    out[:len(voice)] += voice
    for (t, name, gain_db) in events:
        s = SFX[name](seed=int(t * 100))
        g = 10 ** ((SFX_GAIN_DB.get(name, -24) + gain_db) / 20)
        k = int(t * SR)
        if 0 <= k < n:
            m = min(len(s), n - k)
            out[k:k + m] += s[:m] * g
    amb = ambience(dur)
    out[:len(amb)] += amb * 10 ** (amb_db / 20)
    return out[:int(dur * SR)]


# ------------------------------------------------------------------ sonoridad

def ebur128(path):
    """Mide I (LUFS) y pico verdadero (dBTP) con el filtro ebur128 de ffmpeg."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-filter_complex",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    txt = r.stderr
    summ = txt[txt.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summ).group(1))
    return I, tp


def loudnorm_two_pass(src, dst, I=-14.0, TP=-1.5, LRA=11.0):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af",
                        f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:"
          f"linear=true,aresample={SR}")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af, "-ar", str(SR), dst], check=True)
    return js


# ------------------------------------------------------------------ máster propio

def _smooth_gain(g, sr, attack=0.002, release=0.08):
    """Envolvente de ganancia: mínimo con anticipación (attack) y recuperación exponencial."""
    from scipy.ndimage import minimum_filter1d
    from scipy.signal import lfilter
    la = max(1, int(attack * sr))
    g = minimum_filter1d(g, size=2 * la + 1)
    a = math.exp(-1 / (release * sr))
    # recuperación: filtro de un polo solo hacia arriba (aprox. con lfilter sobre 1-g)
    inv = 1 - g
    out = np.empty_like(inv)
    acc = 0.0
    # vectorizado por bloques: picos (inv grande) instantáneos, caída exponencial
    from scipy.ndimage import maximum_filter1d
    env = lfilter([1 - a], [1, -a], inv)
    env = np.maximum(env, inv)
    env = maximum_filter1d(env, size=la * 2 + 1)
    return 1 - env


def true_peak(x, sr=SR):
    from scipy.signal import resample_poly
    return 20 * np.log10(np.abs(resample_poly(x, 4, 1)).max() + 1e-12)


def limit_true_peak(x, ceiling_db=-2.0, sr=SR):
    from scipy.signal import resample_poly
    c = 10 ** (ceiling_db / 20)
    y = x.copy()
    for _ in range(6):
        up = np.abs(resample_poly(y, 4, 1))
        pk = up.reshape(-1, 4).max(1) if len(up) >= len(y) * 4 else np.abs(y)
        pk = pk[:len(y)]
        g = np.minimum(1.0, c / (pk + 1e-12))
        if g.min() >= 0.999:
            break
        y = y * _smooth_gain(g, sr)
    return y


def compress(x, sr=SR, thr_db=-24.0, ratio=2.5, attack=0.005, release=0.12):
    from scipy.signal import lfilter
    env = np.abs(x)
    a_r = math.exp(-1 / (release * sr))
    env = lfilter([1 - a_r], [1, -a_r], env)
    db = 20 * np.log10(env + 1e-9)
    over = np.maximum(0, db - thr_db)
    gdb = -over * (1 - 1 / ratio)
    return x * 10 ** (gdb / 20)


def master(x, target_lufs=-14.0, ceiling_db=-2.3, sr=SR):
    """Compresión suave + ganancia a target LUFS + limitador de pico verdadero (iterativo)."""
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    y = compress(x, sr, thr_db=-26.0, ratio=3.0)
    for _ in range(12):
        L = meter.integrated_loudness(y)
        y = y * 10 ** ((target_lufs - L) / 20)
        y = limit_true_peak(y, ceiling_db, sr)
        L2 = meter.integrated_loudness(y)
        if abs(L2 - target_lufs) < 0.05:
            break
    return y, meter.integrated_loudness(y), true_peak(y, sr)
