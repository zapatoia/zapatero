"""Curvas de aceleración, claves y utilidades de animación."""
import math
import numpy as np


def linear(t):
    return t


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def ease_in_out_cubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    return t ** 3


def ease_out_back(t, s=1.70158):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_back(t, s=1.70158):
    return t * t * ((s + 1) * t - s)


def ease_out_elastic(t):
    if t <= 0 or t >= 1:
        return float(t >= 1)
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def ease_out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


EASE = {
    "linear": linear, "inout": ease_in_out, "inout3": ease_in_out_cubic,
    "out": ease_out_cubic, "in": ease_in_cubic, "back": ease_out_back,
    "inback": ease_in_back, "elastic": ease_out_elastic, "bounce": ease_out_bounce,
}


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def seg(t, a, b):
    """Progreso 0..1 de t entre a y b."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp01((t - a) / (b - a))


def pop(t, t0, dur_in=0.35, hold=None, dur_out=0.25):
    """Escala de aparición con rebote (easeOutBack) y salida (easeInBack)."""
    if t < t0:
        return 0.0
    s = ease_out_back(seg(t, t0, t0 + dur_in), 2.4)
    if hold is not None:
        t1 = t0 + dur_in + hold
        if t > t1:
            s *= 1 - ease_in_back(seg(t, t1, t1 + dur_out), 1.6) if t < t1 + dur_out else 0.0
    return max(0.0, s)


class Track:
    """Claves (t, valor) con curva por tramo. Valor escalar o vector."""

    def __init__(self, keys, loop=None):
        self.keys = [(k[0], np.asarray(k[1], "f8"), k[2] if len(k) > 2 else "inout") for k in keys]
        self.loop = loop

    def __call__(self, t):
        ks = self.keys
        if self.loop:
            t = t % self.loop
        if t <= ks[0][0]:
            return ks[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(ks, ks[1:]):
            if t <= t1:
                u = EASE[e]((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
                return v0 + (v1 - v0) * u
        return ks[-1][1]


class Spring:
    """Muelle amortiguado para movimiento secundario (orejas, cola, antenas)."""

    def __init__(self, k=60.0, d=7.0, x=0.0):
        self.k, self.d = k, d
        self.x = np.asarray(x, "f8") * 1.0
        self.v = np.zeros_like(self.x)

    def step(self, target, dt):
        n = max(1, int(dt / 0.004))
        h = dt / n
        for _ in range(n):
            a = self.k * (target - self.x) - self.d * self.v
            self.v = self.v + a * h
            self.x = self.x + self.v * h
        return self.x


def noise1(t, seed=0.0):
    """Ruido suave determinista (suma de senos) en [-1, 1]."""
    return (math.sin(t * 1.3 + seed) * 0.5 + math.sin(t * 2.7 + seed * 1.7) * 0.3 +
            math.sin(t * 4.1 + seed * 2.3) * 0.2)


def blink_times(duration, seed=3, lo=2.0, hi=4.0):
    rng = np.random.default_rng(seed)
    out = []
    t = rng.uniform(0.8, 1.6)
    while t < duration:
        out.append(t)
        if rng.random() < 0.18:   # parpadeo doble ocasional
            out.append(t + 0.28)
        t += rng.uniform(lo, hi)
    return out


def blink_state(t, times, dur=0.14):
    for b in times:
        if b <= t < b + dur:
            u = (t - b) / dur
            return "half" if u < 0.25 or u > 0.75 else "closed"
    return None
