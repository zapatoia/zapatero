"""Guion → texto hablado, palabras con tiempos, visemas y envolvente.

Sintaxis del texto de cada beat:
  palabra          se dice y se subtitula igual
  *palabra*        énfasis (subtítulo en amarillo + golpe de cámara)
  {82 %|ochenta y dos por ciento}
                   se subtitula "82 %" pero se dice lo de la derecha
  *{82 %|ochenta y dos por ciento}*   ambas cosas
"""
from __future__ import annotations

import bisect
import math
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np

from .shoe import MOUTHS

_TOKEN = re.compile(r"(\*?)\{([^|}]*)\|([^}]*)\}(\*?)([^\s]*)|(\S+)")


@dataclass
class Word:
    display: str
    spoken_start: int      # índice de carácter en el texto hablado
    spoken_end: int
    emph: bool = False
    beat: int = 0
    start: float = 0.0
    end: float = 0.0
    sentence_end: bool = False
    clause_end: bool = False


@dataclass
class Beat:
    index: int
    text: str
    scene: dict
    words: list = field(default_factory=list)
    start: float = 0.0
    end: float = 0.0


def parse_beats(beats_json: list) -> tuple[str, list[Beat], list[Word]]:
    spoken = []
    pos = 0
    beats, words = [], []
    for bi, b in enumerate(beats_json):
        beat = Beat(bi, b["text"], b.get("scene", {}))
        for m in _TOKEN.finditer(b["text"]):
            if m.group(6) is not None:
                raw = m.group(6)
                emph = raw.startswith("*") or raw.rstrip(".,;:!?»”").endswith("*")
                say = raw.replace("*", "")
                disp = say
            else:
                emph = bool(m.group(1)) or bool(m.group(4))
                disp = m.group(2) + m.group(5)
                say = m.group(3) + m.group(5)
            if spoken:
                spoken.append(" ")
                pos += 1
            spoken.append(say)
            w = Word(display=disp, spoken_start=pos, spoken_end=pos + len(say), emph=emph,
                     beat=bi)
            w.sentence_end = bool(re.search(r"[.!?…]+[»”\"]?$", say))
            w.clause_end = w.sentence_end or bool(re.search(r"[,;:]$", say))
            pos += len(say)
            beat.words.append(w)
            words.append(w)
        beats.append(beat)
    return "".join(spoken), beats, words


def apply_alignment(words: list[Word], beats: list[Beat], alignment: dict, duration: float):
    chars = alignment["characters"]
    st = alignment["character_start_times_seconds"]
    en = alignment["character_end_times_seconds"]
    n = len(chars)
    for w in words:
        a = min(w.spoken_start, n - 1)
        b = min(max(w.spoken_end - 1, a), n - 1)
        # ignorar signos al principio/final
        while a < b and not chars[a].isalnum():
            a += 1
        while b > a and not chars[b].isalnum():
            b -= 1
        w.start, w.end = st[a], en[b]
    # beats: empiezan en su primera palabra; el primero en 0
    for i, bt in enumerate(beats):
        bt.start = 0.0 if i == 0 else bt.words[0].start - 0.05
    for i, bt in enumerate(beats):
        bt.end = beats[i + 1].start if i + 1 < len(beats) else duration


# ------------------------------------------------------------------ visemas
def _strip(c):
    return unicodedata.normalize("NFD", c.lower())[0] if c else c


def viseme_of(c: str) -> str | None:
    c = _strip(c)
    if c in "a":
        return "A"
    if c in "ei":
        return "E"
    if c in "ou":
        return "O"
    if c in "mbp":
        return "M"
    if c.isalpha():
        return "C"   # consonante: forma intermedia
    return None


class LipSync:
    """Muestrea los parámetros de boca a 100 Hz y los suaviza."""

    RATE = 100

    def __init__(self, alignment: dict | None, envelope: "Envelope", duration: float,
                 lead=0.035):
        n = int(math.ceil(duration * self.RATE)) + 2
        keys = ("w", "h", "r", "teeth")
        arr = {k: np.zeros(n, dtype=np.float32) for k in keys}
        rest = MOUTHS["X"]
        for k in keys:
            arr[k][:] = rest[k]
        if alignment:
            chars = alignment["characters"]
            st = alignment["character_start_times_seconds"]
            en = alignment["character_end_times_seconds"]
            last_vowel = "E"
            for i, ch in enumerate(chars):
                v = viseme_of(ch)
                if v is None:
                    continue
                if v == "C":
                    # mezcla con la vocal siguiente para co-articulación
                    nxt = next((viseme_of(c) for c in chars[i + 1:i + 3]
                                if viseme_of(c) in ("A", "E", "O")), last_vowel)
                    base = MOUTHS[nxt]
                    shape = {k: base[k] for k in keys}
                    shape["h"] *= 0.45
                    shape["teeth"] = max(shape["teeth"], 0.6)
                else:
                    shape = MOUTHS[v]
                    if v in ("A", "E", "O"):
                        last_vowel = v
                a = int((st[i] - lead) * self.RATE)
                b = max(a + 1, int((en[i] - lead) * self.RATE))
                a, b = max(0, a), min(n, b)
                for k in keys:
                    arr[k][a:b] = shape[k]
        else:
            # sin timestamps: forma a partir de la envolvente, alternando vocales
            env = envelope.sample_grid(n, self.RATE)
            cyc = ["A", "E", "O", "E"]
            for i in range(n):
                if env[i] > 0.12:
                    s = MOUTHS[cyc[(i // 9) % 4]]
                    for k in keys:
                        arr[k][i] = s[k]
        # suavizado gaussiano (sigma 30 ms)
        ker = np.exp(-0.5 * (np.arange(-8, 9) / 3.0) ** 2)
        ker /= ker.sum()
        for k in keys:
            arr[k] = np.convolve(np.pad(arr[k], 8, mode="edge"), ker, mode="valid")
        # la apertura sigue el volumen real de la voz
        env = envelope.sample_grid(n, self.RATE, shift=-lead)
        amp = np.clip(0.45 + env * 0.75, 0.0, 1.15)
        h = arr["h"] * amp
        # si hay sonido pero el texto dice silencio, abrir igualmente un poco
        h = np.maximum(h, np.where(env > 0.2, env * 0.38, 0.0))
        # si no hay sonido, cerrar
        h = h * np.clip(env / 0.08, 0.0, 1.0) ** 0.5
        arr["h"] = h
        self.arr = arr
        self.n = n

    def __call__(self, t: float):
        i = t * self.RATE
        i0 = int(max(0, min(self.n - 2, math.floor(i))))
        f = min(1.0, max(0.0, i - i0))
        shape = {k: float(v[i0] * (1 - f) + v[i0 + 1] * f) for k, v in self.arr.items()}
        return shape, 1.0


class Envelope:
    """Envolvente RMS normalizada (0..~1) de la voz."""

    def __init__(self, samples: np.ndarray, sr: int, offset: float = 0.0):
        hop = sr // 100
        n = len(samples) // hop
        frames = samples[: n * hop].reshape(n, hop)
        rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
        ref = np.percentile(rms[rms > rms.max() * 0.05], 90) if n else 1.0
        e = np.clip(rms / (ref + 1e-9), 0, 1.4)
        ker = np.ones(5) / 5
        self.e = np.convolve(e, ker, mode="same").astype(np.float32)
        self.rate = 100
        self.offset = offset

    def __call__(self, t: float) -> float:
        i = int((t - self.offset) * self.rate)
        if i < 0 or i >= len(self.e):
            return 0.0
        return float(self.e[i])

    def sample_grid(self, n, rate, shift=0.0):
        ts = np.arange(n) / rate - shift - self.offset
        idx = np.clip((ts * self.rate).astype(int), 0, len(self.e) - 1)
        out = self.e[idx].copy()
        out[(ts < 0) | (ts * self.rate >= len(self.e))] = 0
        return out


# ------------------------------------------------------------------ refinado
_VOICED = set("lmnrydbgvwñ")


def _char_level(c: str) -> float:
    c = _strip(c)
    if c in "aeiou":
        return 1.0
    if c in _VOICED:
        return 0.75
    if c.isalpha():
        return 0.4
    return 0.0


def refine_alignment(alignment: dict, samples: np.ndarray, sr: int, band_s: float = 0.7) -> dict:
    """Corrige los timestamps con DTW contra la sonoridad real del audio.

    Los timestamps de eleven_v3 son aproximados (pueden ir 0,1-0,3 s
    adelantados y alargar la última palabra). Se construye la sonoridad que
    predicen los caracteres y se alinea con la sonoridad medida (100 Hz).
    """
    R = 100
    chars = alignment["characters"]
    st = np.array(alignment["character_start_times_seconds"], dtype=np.float64)
    en = np.array(alignment["character_end_times_seconds"], dtype=np.float64)
    dur = len(samples) / sr
    n = int(dur * R) + 1
    # sonoridad medida
    hop = sr // R
    m = len(samples) // hop
    rms = np.sqrt((samples[: m * hop].reshape(m, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms)
    B = np.clip((db - (db.max() - 38)) / 30, 0, 1)
    B = np.convolve(B, np.ones(3) / 3, mode="same")
    # sonoridad prevista
    A = np.zeros(max(n, m))
    for i, c in enumerate(chars):
        a, b = int(st[i] * R), max(int(st[i] * R) + 1, int(en[i] * R))
        A[a:b] = np.maximum(A[a:b], _char_level(c))
    A = np.convolve(A, np.ones(5) / 5, mode="same")[:m]
    N = len(A)
    band = int(band_s * R)
    INF = 1e18
    D = np.full((N + 1, m + 1), INF)
    D[0, 0] = 0
    diag_pen, off_pen = 0.0, 0.12
    for i in range(1, N + 1):
        j0, j1 = max(1, i - band), min(m, i + band)
        ai = A[i - 1]
        prev = D[i - 1]
        row = D[i]
        for j in range(j0, j1 + 1):
            cost = abs(ai - B[j - 1])
            best = prev[j - 1] + diag_pen
            v = prev[j] + off_pen
            if v < best:
                best = v
            v = row[j - 1] + off_pen
            if v < best:
                best = v
            row[j] = cost + best
    # backtrack
    i, j = N, m
    mapping = np.zeros(N + 1)
    counts = np.zeros(N + 1)
    while i > 0 and j > 0:
        mapping[i] += j
        counts[i] += 1
        opts = (D[i - 1, j - 1], D[i - 1, j], D[i, j - 1])
        k = int(np.argmin(opts))
        if k == 0:
            i, j = i - 1, j - 1
        elif k == 1:
            i -= 1
        else:
            j -= 1
    counts[counts == 0] = 1
    mp = mapping / counts
    mp[0] = 0
    # monotonía + suavizado (evita palabras comprimidas a 0 s)
    mp = np.maximum.accumulate(mp)
    k = 13
    pad = np.pad(mp, k, mode="edge")
    mp = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
    mp = np.maximum.accumulate(mp)

    def warp(t):
        x = t * R
        i0 = int(min(max(0, np.floor(x)), N - 1))
        f = x - i0
        return float((mp[i0] * (1 - f) + mp[min(i0 + 1, N)] * f) / R)

    new_st = [warp(t) for t in st]
    new_en = [max(s + 0.01, warp(t)) for s, t in zip(new_st, en)]
    # el final de la voz no puede pasar del último tramo con sonido
    voiced = np.where(B > 0.15)[0]
    if len(voiced):
        last = (voiced[-1] + 2) / R
        new_en = [min(e, max(last, s + 0.02)) for s, e in zip(new_st, new_en)]
    out = dict(alignment)
    out["character_start_times_seconds"] = new_st
    out["character_end_times_seconds"] = new_en
    return out
