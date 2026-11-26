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


def _noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _lp(x, a):
    from scipy.signal import lfilter
    return lfilter([a], [1, -(1 - a)], x)


def _fade(x, fin=0.005, fout=0.03, sr=SR):
    """Fundido de entrada y salida (coseno) en cada efecto."""
    x = x.copy()
    ni, no = max(1, int(fin * sr)), max(1, int(fout * sr))
    ni, no = min(ni, len(x) // 2), min(no, len(x) // 2)
    x[:ni] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, ni))
    x[-no:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, no))
    return x


# Efectos SUAVES (nada estridente). Cada uno es un evento puntual y corto.
def sfx_pop(seed=0):
    t = _t(0.07)
    f = 420 + 380 * np.exp(-t * 60)
    return _fade(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45), 0.002, 0.03)


def sfx_whoosh(seed=0):
    d = 0.28
    t = _t(d)
    y = _lp(_lp(_noise(len(t), seed + 7), 0.05), 0.08)
    return _fade(y / (np.abs(y).max() + 1e-9) * np.sin(np.pi * t / d) ** 2, 0.03, 0.08)


def sfx_step(seed=0):
    t = _t(0.06)
    y = _lp(_noise(len(t), seed), 0.06) * 3 + np.sin(2 * np.pi * 110 * t) * 0.6
    return _fade(y * np.exp(-t * 55), 0.002, 0.025)


def sfx_lick(seed=0):
    """Lametón corto y blando (0,14 s): ruido muy filtrado con un leve barrido."""
    d = 0.14
    t = _t(d)
    n = _noise(len(t), seed + 3)
    y = _lp(_lp(n, 0.12), 0.18)
    y = y / (np.abs(y).max() + 1e-9) * np.sin(np.pi * t / d) ** 1.5
    return _fade(y, 0.01, 0.04)


def sfx_ding(seed=0, base=880.0):
    t = _t(0.35)
    y = np.sin(2 * np.pi * base * t) + 0.3 * np.sin(2 * np.pi * base * 2.0 * t) * np.exp(-t * 12)
    return _fade(y * np.exp(-t * 9), 0.003, 0.1)


def sfx_blip(seed=0):
    t = _t(0.06)
    return _fade(np.sin(2 * np.pi * (660 + 220 * (t > 0.03)) * t) * np.exp(-t * 30), 0.003, 0.02)


def sfx_thud(seed=0):
    t = _t(0.12)
    return _fade(np.sin(2 * np.pi * 75 * t) * np.exp(-t * 30), 0.003, 0.04)


def sfx_boing(seed=0):
    t = _t(0.22)
    f = 220 + 160 * np.exp(-t * 10)
    return _fade(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12), 0.005, 0.06)


SFX = {"pop": sfx_pop, "ding": sfx_ding, "blip": sfx_blip, "step": sfx_step, "lick": sfx_lick,
       "boing": sfx_boing, "whoosh": sfx_whoosh, "thud": sfx_thud}

# dB por debajo de la voz (RMS de los tramos hablados). Regla: 18-24 dB.
SFX_REL_DB = {"pop": -20, "ding": -22, "blip": -22, "step": -24, "lick": -20, "boing": -22, "whoosh": -22, "thud": -22}


def _rms(x):
    return float(np.sqrt(np.mean(x ** 2) + 1e-20))


def voice_rms(voice, sr=SR):
    env = envelope(voice, sr)
    thr = env.max() * 10 ** (-30 / 20)
    act = env[env > thr]
    return float(np.sqrt(np.mean(act ** 2))) if len(act) else _rms(voice)


def mix(voice, events, dur, duck_db=-6.0, ambience_db=None):
    """Mezcla voz + efectos puntuales.

    events: lista de dicts {t, type, gain (dB extra, opcional), why}
    - cada efecto se normaliza a SFX_REL_DB respecto al RMS de la voz hablada
    - fundidos en cada evento; atenuación extra (duck_db) mientras se habla
    Devuelve (mezcla, bus_efectos, lista_eventos_detallada)."""
    n = int(dur * SR)
    out = np.zeros(n)
    out[:min(n, len(voice))] += voice[:n]
    bus = np.zeros(n)
    vr = voice_rms(voice)
    detail = []
    for ev in sorted(events, key=lambda e: e["t"]):
        s = SFX[ev["type"]](seed=int(ev["t"] * 100))
        rel = SFX_REL_DB[ev["type"]] + ev.get("gain", 0.0)
        rel = max(-24.0, min(-18.0, rel))          # siempre dentro de 18-24 dB bajo la voz
        g = vr * 10 ** (rel / 20) / _rms(s)
        k = int(ev["t"] * SR)
        if 0 <= k < n:
            m = min(len(s), n - k)
            bus[k:k + m] += s[:m] * g
        detail.append({**ev, "rel_db": round(rel, 1), "dur": round(len(s) / SR, 3)})
    # atenuación mientras se habla (ataque 20 ms, liberación 150 ms)
    env = envelope(voice) if len(voice) else np.zeros(1)
    thr = env.max() * 10 ** (-32 / 20)
    talking = np.repeat((env > thr).astype(float), int(0.01 * SR))
    talking = np.pad(talking, (0, max(0, n - len(talking))))[:n]
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import lfilter
    talking = maximum_filter1d(talking, int(0.15 * SR))
    a = math.exp(-1 / (0.02 * SR))
    talking = lfilter([1 - a], [1, -a], talking)
    duck = 10 ** (duck_db * np.clip(talking, 0, 1) / 20)
    bus *= duck
    out += bus
    if ambience_db is not None:   # solo si el guion lo pide explícitamente
        amb = _lp(_lp(_noise(n, 1), 0.01), 0.02)
        out += amb / (np.abs(amb).max() + 1e-9) * vr * 10 ** (ambience_db / 20)
    return out, bus, detail


def sfx_report(bus, detail, voice, segments, sr=SR, sustain_s=1.0):
    """Verificación: energía del bus de efectos por escena y sonidos sostenidos > sustain_s."""
    vr = voice_rms(voice)
    env = envelope(bus, sr, 0.05)
    thr = vr * 10 ** (-40 / 20)          # «suena» = por encima de -40 dB respecto a la voz
    on = env > thr
    sustained = []
    run = 0
    for i, v in enumerate(on):
        run = run + 1 if v else 0
        if run * 0.05 > sustain_s and (not sustained or sustained[-1][1] < i - run):
            sustained.append((round((i - run + 1) * 0.05, 2), i))
    sust = []
    for st, end in sustained:
        j = end
        while j < len(on) and on[j]:
            j += 1
        sust.append({"start": st, "end": round(j * 0.05, 2)})
    scenes = []
    for name, a, b in segments:
        seg = bus[int(a * sr):int(b * sr)]
        e = _rms(seg) if len(seg) else 0.0
        scenes.append({"scene": name, "start": round(a, 2), "end": round(b, 2),
                       "sfx_rms_db_rel_voice": round(20 * math.log10(e / vr + 1e-12), 1),
                       "events": sum(1 for d in detail if a <= d["t"] < b)})
    return {"voice_rms_dbfs": round(20 * math.log10(vr + 1e-12), 1), "events": detail, "scenes": scenes,
            "sustained_over_1s": sust}


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


# ------------------------------------------------------------------ máster limpio (v3)
# El máster original (compress + limit_true_peak iterativo) aplastaba los picos de la
# voz con un limitador de 2 ms que trabajaba ~3-6 dB en casi un 20 % del tiempo: eso se
# oye como saturación. Este máster reparte el trabajo en etapas suaves:
#   paso alto 70 Hz → de-esser suave → compresor RMS en dB (rodilla blanda, 2:1,
#   ataque 15 ms / liberación 180 ms) → ganancia → limitador con anticipación de 5 ms
#   y curva coseno (sin recortes ni cambios de ganancia bruscos) → techo -2 dBTP.

def _highpass(x, fc, sr=SR, order=2):
    from scipy.signal import butter, sosfiltfilt
    return sosfiltfilt(butter(order, fc, "highpass", fs=sr, output="sos"), x)


def _env_db(x, sr, attack, release, rms_win=0.01):
    """Envolvente RMS en dB con ataque/liberación separados (seguidor de nivel)."""
    from scipy.ndimage import uniform_filter1d
    p = uniform_filter1d(x ** 2, max(1, int(rms_win * sr)))
    lvl = 10 * np.log10(p + 1e-12)
    # seguidor ataque/liberación por bloques de 1 ms (rápido en numpy)
    blk = max(1, int(sr * 0.001))
    m = len(lvl) // blk + 1
    lv = np.pad(lvl, (0, m * blk - len(lvl)), constant_values=-120).reshape(m, blk).max(1)
    aa = math.exp(-0.001 / attack)
    ar = math.exp(-0.001 / release)
    out = np.empty(m)
    s = lv[0]
    for i in range(m):
        v = lv[i]
        c = aa if v > s else ar
        s = c * s + (1 - c) * v
        out[i] = s
    t_blk = (np.arange(m) + 0.5) * blk
    return np.interp(np.arange(len(x)), t_blk, out)


def _gain_computer(lvl_db, thr, ratio, knee):
    over = lvl_db - thr
    g = np.zeros_like(lvl_db)
    hi = over > knee / 2
    mid = np.abs(over) <= knee / 2
    g[hi] = -over[hi] * (1 - 1 / ratio)
    g[mid] = -(1 - 1 / ratio) * (over[mid] + knee / 2) ** 2 / (2 * knee)
    return g


def deess(x, sr=SR, f0=5500.0, max_cut_db=4.0):
    """De-esser suave: reduce la banda alta solo cuando las eses sobresalen."""
    from scipy.signal import butter, sosfiltfilt
    hi = sosfiltfilt(butter(2, f0, "highpass", fs=sr, output="sos"), x)
    lo = x - hi
    eh = _env_db(hi, sr, 0.002, 0.06)
    ef = _env_db(x, sr, 0.002, 0.06)
    excess = np.clip((eh - ef) + 6.0, 0, None)       # eses más fuertes que el resto − 6 dB
    cut = -np.minimum(max_cut_db, excess * 0.8)
    return lo + hi * 10 ** (cut / 20)


def lookahead_limiter(x, ceiling_db=-2.0, sr=SR, look=0.005, release=0.12):
    """Limitador de pico verdadero (sobremuestreo ×4) con anticipación y curva suave.
    La ganancia baja en `look` segundos ANTES del pico (rampa coseno) y se recupera
    exponencialmente: no hay recortes, solo cambios lentos de volumen."""
    from scipy.signal import resample_poly
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import lfilter
    c = 10 ** (ceiling_db / 20)
    up = np.abs(resample_poly(x, 4, 1))[:len(x) * 4]
    pk = up.reshape(-1, 4).max(1)
    need = np.maximum(0.0, 20 * np.log10(pk + 1e-12) - ceiling_db)      # dB a reducir
    L = max(1, int(look * sr))
    need = maximum_filter1d(need, 2 * L + 1)                             # mantener durante la ventana
    w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, 2 * L + 1))
    w /= w.sum()
    need = np.convolve(need, w, mode="same") * 1.0
    need = np.maximum(need, maximum_filter1d(need, 3))
    a = math.exp(-1 / (release * sr))
    rel = lfilter([1 - a], [1, -a], need)
    need = np.maximum(need, rel)
    y = x * 10 ** (-need / 20)
    # red de seguridad: recorte suave por si queda algún pico (no debería actuar)
    tp = np.abs(resample_poly(y, 4, 1)).max()
    if tp > c:
        y *= c / tp
    return y, need


def peak_compressor(x, thr_db, ratio, sr=SR, look=0.01, release=0.15, knee=6.0):
    """Compresor de picos (detección de pico verdadero) con anticipación y ventana Hann:
    la ganancia nunca cambia a saltos."""
    from scipy.signal import resample_poly, lfilter
    from scipy.ndimage import maximum_filter1d
    pk = np.abs(resample_poly(x, 4, 1))[:len(x) * 4].reshape(-1, 4).max(1)
    need = -_gain_computer(20 * np.log10(pk + 1e-12), thr_db, ratio, knee)
    L = max(1, int(look * sr))
    need = maximum_filter1d(need, 2 * L + 1)
    w = 0.5 - 0.5 * np.cos(np.linspace(0, 2 * np.pi, 2 * L + 1))
    need = np.convolve(need, w / w.sum(), "same")
    a = math.exp(-1 / (release * sr))
    need = np.maximum(need, lfilter([1 - a], [1, -a], need))
    return x * 10 ** (-need / 20), need


def master_clean(x, target_lufs=-14.0, ceiling_db=-2.0, sr=SR, report=None):
    """Máster limpio (desde v3 del vídeo 01). Toda la reducción con curvas suaves:
    paso alto 70 Hz → de-esser → nivelador RMS lento (2,5:1, rodilla 8 dB, 15/180 ms)
    → compresor de picos (4:1 desde -9 dBFS, anticipación 10 ms, liberación 150 ms)
    → limitador de pico verdadero (anticipación 5 ms, liberación 50 ms, techo -2 dBTP).
    La ganancia se busca aplicando las etapas UNA vez (sin pasadas acumuladas).
    Frente a `master()`: ~13 dB menos modulación de ganancia audible (>40 Hz)."""
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    y0 = deess(_highpass(x, 70.0, sr), sr)
    L0 = meter.integrated_loudness(y0)
    lvl = _env_db(y0, sr, 0.015, 0.18, rms_win=0.02)
    act = lvl > lvl.max() - 30
    thr = float(np.percentile(lvl[act], 50))
    gdb = np.maximum(_gain_computer(lvl, thr, 2.5, 8.0), -8.0)
    yc = y0 * 10 ** (gdb / 20)
    G = target_lufs - meter.integrated_loudness(yc)
    y, gl, L = yc, np.zeros(len(yc)), -99.0
    for _ in range(16):
        z, gp = peak_compressor(yc * 10 ** (G / 20), ceiling_db - 7.0, 4.0, sr)
        y, gl = lookahead_limiter(z, ceiling_db, sr, look=0.005, release=0.05)
        L = meter.integrated_loudness(y)
        if abs(L - target_lufs) < 0.04:
            break
        G += (target_lufs - L) * 1.6
    if report is not None:
        report.update({
            "input_lufs": round(float(L0), 2),
            "leveler_gr_db_p50": round(float(np.percentile(-gdb[act], 50)), 2),
            "limiter_gr_db_p95": round(float(np.percentile(gl[act], 95)), 2),
            "limiter_gr_db_max": round(float(gl.max()), 2),
        })
    return y, L, true_peak(y, sr)


# ------------------------------------------------------------------ máster «clean2» (desde la v5 del vídeo 01)
# Problema del máster «clean»: el compresor de picos tenía umbral fijo y el bucle de ganancia
# lo perseguía (+38 dB de ganancia, 25 dB de compresión) → voz aplastada y ruido de fondo
# de los silencios subido ~30 dB. «clean2» procesa SOLO la voz (expansor que baja los
# silencios, nivelador, compresor de picos con trabajo limitado), después se suman efectos y
# música, y al final un limitador suave sobre la mezcla. Sin recortador (añade armónicos).

def expander(x, sr=SR, range_db=12.0):
    """Expansor hacia abajo: baja hasta `range_db` lo que queda por debajo de la voz más suave
    (silencios entre frases); ganancia con retención de 80 ms para no cerrar dentro de palabras."""
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    lvl = _env_db(x, sr, 0.003, 0.12, rms_win=0.01)
    act = lvl > lvl.max() - 30
    thr = np.percentile(lvl[act], 8) - 4
    g = -np.minimum(range_db, np.clip(thr - lvl, 0, None) * 1.5)
    g = -maximum_filter1d(-g, int(0.08 * sr))
    g = uniform_filter1d(g, int(0.03 * sr))
    return x * 10 ** (g / 20)


def _peak_comp_capped(x, thr_db, ratio, sr=SR, look=0.002, rel=0.1, knee=6.0, max_gr=6.0):
    from scipy.signal import resample_poly, lfilter
    from scipy.ndimage import maximum_filter1d
    pk = np.abs(resample_poly(x, 4, 1))[:len(x) * 4].reshape(-1, 4).max(1)
    need = np.minimum(max_gr, -_gain_computer(20 * np.log10(pk + 1e-12), thr_db, ratio, knee))
    L = max(1, int(look * sr))
    need = maximum_filter1d(need, 2 * L + 1)
    w = 0.5 - 0.5 * np.cos(np.linspace(0, 2 * np.pi, 2 * L + 1))
    need = np.convolve(need, w / w.sum(), "same")
    a = math.exp(-1 / (rel * sr))
    need = np.maximum(need, lfilter([1 - a], [1, -a], need))
    return x * 10 ** (-need / 20), need


def voice_chain(x, target_lufs=-16.0, ceiling_db=-2.0, sr=SR, report=None):
    """Voz sola → `target_lufs` con procesado moderado. Devuelve la voz procesada."""
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    y0 = expander(deess(_highpass(x, 70.0, sr), sr), sr)
    lvl = _env_db(y0, sr, 0.015, 0.18, rms_win=0.02)
    act = lvl > lvl.max() - 30
    thr = float(np.percentile(lvl[act], 50))
    gl1 = np.maximum(_gain_computer(lvl, thr, 2.5, 8.0), -8.0)
    y1 = y0 * 10 ** (gl1 / 20)
    G = target_lufs - meter.integrated_loudness(y1)
    for _ in range(14):
        z, gp = _peak_comp_capped(y1 * 10 ** (G / 20), -14.0, 4.0, sr)
        y, gl = lookahead_limiter(z, ceiling_db, sr, look=0.003, release=0.04)
        L = meter.integrated_loudness(y)
        if abs(L - target_lufs) < 0.04:
            break
        G += (target_lufs - L)
    if report is not None:
        report.update({"input_lufs": round(float(meter.integrated_loudness(x)), 2), "voice_gain_db": round(float(G), 1),
                       "leveler_gr_db_p50": round(float(np.percentile(-gl1[act], 50)), 1),
                       "peakcomp_gr_db_p50": round(float(np.percentile(gp[act], 50)), 1),
                       "limiter_gr_db_p95": round(float(np.percentile(gl[act], 95)), 1)})
    return y


def talking_curve(voice, n, sr=SR):
    """0-1: cuánto se está hablando (para atenuar efectos y música bajo la voz)."""
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import lfilter
    env = envelope(voice) if len(voice) else np.zeros(1)
    thr = env.max() * 10 ** (-32 / 20)
    talking = np.repeat((env > thr).astype(float), int(0.01 * sr))
    talking = np.pad(talking, (0, max(0, n - len(talking))))[:n]
    talking = maximum_filter1d(talking, int(0.25 * sr))
    a = math.exp(-1 / (0.08 * sr))
    return np.clip(lfilter([1 - a], [1, -a], talking), 0, 1)


def music_bed(voice, music, db=-19.0, duck_db=-5.0):
    """Música a `db` (RMS) respecto a la voz hablada, con atenuación suave al hablar."""
    n = len(music)
    vr = voice_rms(voice)
    mr = float(np.sqrt(np.mean(music[np.abs(music) > 1e-4] ** 2))) if np.any(np.abs(music) > 1e-4) else 1.0
    m = music * vr * 10 ** (db / 20) / mr
    return m * 10 ** (duck_db * talking_curve(voice, n) / 20)


def final_bus(x, target_lufs=-16.0, ceiling_db=-2.0, sr=SR):
    """Ajuste final de la mezcla: ganancia fina + limitador suave (normalmente ~0-1 dB)."""
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    G = target_lufs - meter.integrated_loudness(x)
    for _ in range(8):
        y, gl = lookahead_limiter(x * 10 ** (G / 20), ceiling_db, sr, look=0.003, release=0.04)
        L = meter.integrated_loudness(y)
        if abs(L - target_lufs) < 0.04:
            break
        G += target_lufs - L
    return y, L, true_peak(y, sr), float(gl.max())
