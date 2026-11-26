"""Música de fondo ORIGINAL generada por código (sin muestras ni música de terceros).

Estilo «aldea»: tema tranquilo de aldea de MMO de principios de los 2000 — bajo suave,
colchón de acordes, arpegio de pulso (chiptune suave), campanita en los cambios de
sección y batería ligera con algo de swing. Pensada para ir MUY por debajo de la voz:
nada de melodía cantable en la banda media (no compite con la voz), solo textura.

Se activa en el guion con  "music": {"style": "aldea", "db": -19, "duck_db": -5}
  db       nivel RMS de la música respecto a la voz hablada (negativo = por debajo)
  duck_db  atenuación extra mientras se habla (sidechain suave)
"""
import math
import numpy as np

SR = 44100
BPM = 100.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT

# acordes por compás (notas MIDI), en Fa mayor: F  C/E  Dm  Bb | Bb  C  Am  Dm | ...
PROG_A = [("F", [53, 57, 60, 65]), ("C/E", [52, 55, 60, 64]), ("Dm", [50, 57, 62, 65]), ("Bb", [46, 58, 62, 65])]
PROG_B = [("Bb", [46, 58, 62, 65]), ("C", [48, 55, 60, 64]), ("Am", [45, 57, 60, 64]), ("Dm", [50, 57, 62, 65])]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _env(n, a, d, s, r, sr=SR):
    """ADSR en muestras (a, d, r en segundos; s nivel)."""
    e = np.ones(n) * s
    na, nd, nr = int(a * sr), int(d * sr), int(r * sr)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na, endpoint=False) if na else e[:na]
    nd2 = min(nd, max(0, n - na))
    if nd2:
        e[na:na + nd2] = np.linspace(1, s, nd2, endpoint=False)
    nr = min(nr, n)
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def _lp(x, fc, sr=SR):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, "lowpass", fs=sr, output="sos"), x)


def _hp(x, fc, sr=SR):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, "highpass", fs=sr, output="sos"), x)


def _place(buf, t, sig):
    k = int(t * SR)
    if k >= len(buf):
        return
    m = min(len(sig), len(buf) - k)
    buf[k:k + m] += sig[:m]


def _tri(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * np.abs(2 * ((f * t + phase) % 1.0) - 1) - 1


def _pulse(f, n, duty=0.25):
    t = np.arange(n) / SR
    return np.where((f * t) % 1.0 < duty, 1.0, -1.0) - (2 * duty - 1)


# ------------------------------------------------------------------ instrumentos

def pad(chord, dur):
    n = int(dur * SR)
    x = np.zeros(n)
    for i, m in enumerate(chord[1:]):            # sin la fundamental grave (la hace el bajo)
        for det in (-0.12, 0.12):                # coro suave
            x += _tri(hz(m + 12) * (1 + det / 100), n, phase=0.17 * i)
    x = _lp(x, 2200) * _env(n, 0.35, 0.4, 0.8, 0.5)
    return x / 6


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m - 12)
    x = np.sin(2 * np.pi * f * t) + 0.35 * _tri(f, n)
    return _lp(x, 700) * _env(n, 0.008, 0.25, 0.55, 0.08)


def pluck(m, dur=0.28):
    n = int(dur * SR)
    x = _pulse(hz(m + 12), n, 0.25) * np.exp(-np.arange(n) / SR * 11)
    return _lp(x, 3600) * _env(n, 0.003, 0.0, 1.0, 0.03)


def bell(m, dur=1.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m + 24)
    x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
    return x * np.exp(-t * 3.2) * _env(n, 0.002, 0.0, 1.0, 0.2)


def kick():
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)


def snare(seed):
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(seed).uniform(-1, 1, n)
    x = _hp(_lp(noise, 5000), 900) * np.exp(-t * 28) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4
    return x


def hat(seed, open_=False):
    n = int((0.09 if open_ else 0.03) * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(seed).uniform(-1, 1, n)
    return _hp(noise, 7000) * np.exp(-t * (30 if open_ else 120))


# ------------------------------------------------------------------ composición

def compose(dur, style="aldea", seed=0):
    """Devuelve la pista de música (mono, SR) de `dur` segundos, con entrada y salida suaves."""
    n = int(dur * SR) + SR
    pads, bas, arp, drm, bel = (np.zeros(n) for _ in range(5))
    bars = int(math.ceil(dur / BAR)) + 1
    swing = 0.06 * BEAT
    for b in range(bars):
        t0 = b * BAR
        if t0 > dur + 0.5:
            break
        prog = PROG_A if (b // 4) % 2 == 0 else PROG_B
        name, ch = prog[b % 4]
        last = t0 + BAR > dur - 0.2
        pads[:] += 0  # (claridad)
        _place(pads, t0, pad(ch, BAR + 0.4))
        # bajo: 1, «y» del 2, 3 (octava) — el último compás solo la redonda
        root = ch[0]
        if last:
            _place(bas, t0, bass(root, BAR))
        else:
            _place(bas, t0, bass(root, BEAT * 1.4))
            _place(bas, t0 + BEAT * 1.5 + swing, bass(root, BEAT * 0.45) * 0.7)
            _place(bas, t0 + BEAT * 2, bass(root + 12, BEAT * 0.9) * 0.6)
            _place(bas, t0 + BEAT * 3, bass(ch[1] - 12 if ch[1] - root < 12 else root + 7, BEAT * 0.9) * 0.7)
        # arpegio de corcheas sobre las notas del acorde (sube y baja), sin el último compás
        if not last:
            pat = [ch[1], ch[2], ch[3], ch[2] + 12, ch[3], ch[2], ch[1], ch[2]]
            for k, m in enumerate(pat):
                tt = t0 + k * BEAT / 2 + (swing if k % 2 else 0.0)
                _place(arp, tt, pluck(m) * (0.9 if k % 2 == 0 else 0.6))
        # campanita al empezar cada sección de 4 compases y en el final
        if b % 4 == 0 or last:
            _place(bel, t0, bell(ch[-1]))
        # batería: entra en el compás 2, sale en el último
        if 1 <= b and not last:
            for beat in range(4):
                tb = t0 + beat * BEAT
                if beat in (0, 2):
                    _place(drm, tb, kick() * 0.9)
                else:
                    _place(drm, tb, snare(seed + b * 4 + beat) * 0.35)
                for h in range(2):
                    _place(drm, tb + h * BEAT / 2 + (swing if h else 0.0),
                           hat(seed + b * 8 + beat * 2 + h, open_=(beat == 3 and h == 1)) * (0.22 if h == 0 else 0.15))
    mix = pads * 0.9 + bas * 0.32 + arp * 0.5 + drm * 0.3 + bel * 0.25
    mix = _hp(_lp(mix, 7000), 70)                         # tono cálido, algo «lo-fi»; sin subgraves
    mix = mix[:int(dur * SR)]
    fi, fo = int(0.25 * SR), int(min(2.0, dur * 0.1) * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return mix
