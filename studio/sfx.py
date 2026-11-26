"""Efectos de sonido generados por código (sin samples de terceros) y mezcla."""
from __future__ import annotations

import json
import subprocess

import numpy as np

SR = 48000


def _env(n, attack=0.005, release=None, sr=SR):
    a = max(1, int(attack * sr))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    if release:
        e *= np.exp(-np.arange(n) / (release * sr))
    return e


def _bandnoise(n, f_start, f_end, q=1.5, seed=0):
    """Ruido filtrado con banda que se desplaza (STFT overlap-add)."""
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n + 1024)
    hop, win = 256, 1024
    w = np.hanning(win)
    out = np.zeros(n + 1024)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    frames = (n) // hop + 1
    for k in range(frames):
        i = k * hop
        seg = noise[i:i + win]
        if len(seg) < win:
            break
        u = k / max(1, frames - 1)
        fc = f_start * (f_end / f_start) ** u
        bw = fc / q
        mask = np.exp(-0.5 * ((freqs - fc) / bw) ** 2)
        spec = np.fft.rfft(seg * w) * mask
        out[i:i + win] += np.fft.irfft(spec) * w
    out = out[:n]
    return out / (np.abs(out).max() + 1e-9)


def whoosh(dur=0.38, seed=0):
    n = int(dur * SR)
    x = _bandnoise(n, 500, 2600, q=1.2, seed=seed)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t ** 0.7) ** 2
    return x * env


def pop(freq=520, dur=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * np.exp(-t * 18) + freq * 0.45
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env(n, 0.002, 0.025)


def ding(freq=1320, dur=0.7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 1.5 * t)
         + 0.18 * np.sin(2 * np.pi * freq * 2.01 * t))
    return x * _env(n, 0.003, 0.18) / 1.5


def tick(dur=0.02):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2300 * t) * _env(n, 0.0005, 0.004)


def thud(dur=0.18):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 140 * np.exp(-t * 10) + 55
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env(n, 0.002, 0.05)


def stamp_hit():
    a = thud(0.25) * 1.0
    b = _bandnoise(int(0.12 * SR), 1800, 600, q=1.0, seed=3) * _env(int(0.12 * SR), 0.001, 0.03) * 0.5
    a[: len(b)] += b
    return a


SOUNDS = {"whoosh": whoosh, "pop": pop, "ding": ding, "tick": tick, "thud": thud,
          "stamp": stamp_hit}
# volúmenes bajos: la voz manda
GAINS = {"whoosh": 0.16, "pop": 0.14, "ding": 0.10, "tick": 0.05, "thud": 0.22, "stamp": 0.22}


def render_sfx(cues, total_dur):
    out = np.zeros(int(total_dur * SR) + SR)
    cache = {}
    for cue in cues:
        kind = cue["kind"]
        key = (kind, cue.get("var", 0))
        if key not in cache:
            if kind == "whoosh":
                cache[key] = whoosh(seed=cue.get("var", 0))
            elif kind == "pop":
                cache[key] = pop(freq=440 + 90 * (cue.get("var", 0) % 4))
            else:
                cache[key] = SOUNDS[kind]()
        x = cache[key] * GAINS[kind] * cue.get("gain", 1.0)
        i = int(max(0, cue["t"]) * SR)
        j = min(len(out), i + len(x))
        out[i:j] += x[: j - i]
    return out[: int(total_dur * SR)]


def mix(voice: np.ndarray, voice_offset: float, sfx: np.ndarray, total_dur: float):
    n = int(total_dur * SR)
    out = np.zeros(n)
    i = int(voice_offset * SR)
    j = min(n, i + len(voice))
    out[i:j] += voice[: j - i]
    out[: len(sfx)] += sfx[:n]
    # anti-clip suave
    peak = np.abs(out).max()
    if peak > 0.98:
        out *= 0.98 / peak
    return out.astype(np.float32)


def write_wav(path, x):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                    "-i", "-", "-c:a", "pcm_s16le", str(path)], input=x.tobytes(), check=True)


def loudnorm_filter(path, I=-14.0, TP=-1.5, LRA=11.0):
    """Primera pasada de loudnorm; devuelve el filtro para la segunda pasada."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                        f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    js = json.loads(txt[txt.rindex("{"): txt.rindex("}") + 1])
    return (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={js['input_i']}:"
            f"measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
            f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
