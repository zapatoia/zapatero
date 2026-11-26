"""Sincronía labial: forma de la boca por letra (timestamps) × apertura por
envolvente de volumen. 5 bocas: X cerrada, M entreabierta, E ancha, A abierta, O redonda."""
import numpy as np

VOWEL = {"a": "A", "á": "A", "e": "E", "é": "E", "i": "E", "í": "E", "o": "O", "ó": "O", "u": "O", "ú": "O", "ü": "O"}
CLOSED = set("mbpv")


class LipSync:
    def __init__(self, words, env=None, hop=0.01, lead=0.035):
        self.chars = [(c.lower(), s, e) for w in words for (c, s, e) in w["chars"] if c.isalpha()]
        self.starts = np.array([s for _, s, _ in self.chars]) if self.chars else np.zeros(0)
        self.env = None
        if env is not None:
            e = np.asarray(env, float)
            p95 = np.percentile(e[e > 0], 95) if (e > 0).any() else 1.0
            self.env = np.clip(e / (p95 + 1e-9), 0, 1.2)
        self.hop = hop
        self.lead = lead
        self.word_spans = [(w["start"], w["end"]) for w in words]
        self._cache = {}

    def level(self, t):
        """Volumen normalizado 0..1 (o 0.8 dentro de palabra si no hay audio)."""
        if self.env is None:
            return 0.8 if any(a <= t <= b for a, b in self.word_spans) else 0.0
        i = int(t / self.hop)
        if i < 0 or i >= len(self.env):
            return 0.0
        return float(self.env[max(0, i - 1):i + 2].mean())

    def raw(self, t):
        t = t + self.lead
        lv = self.level(t)
        if lv < 0.10 or not len(self.chars):
            return "X"
        i = int(np.searchsorted(self.starts, t, side="right")) - 1
        if i < 0:
            return "X"
        c, s, e = self.chars[i]
        if t > e + 0.12:
            return "X"
        if c in CLOSED and t < s + 0.6 * (e - s):
            return "X" if lv < 0.5 else "M"
        shape = VOWEL.get(c)
        if shape is None:
            # consonante: mirar la vocal siguiente para anticipar la forma
            nxt = self.chars[i + 1][0] if i + 1 < len(self.chars) else ""
            shape = VOWEL.get(nxt, "M")
            if lv < 0.45:
                return "M"
        if shape == "A" and lv < 0.32:
            return "M"
        if shape in ("E", "O") and lv < 0.22:
            return "M"
        return shape

    def state_frames(self, n_frames, fps):
        """Estados por fotograma con retención mínima de 2 fotogramas (sin parpadeos)."""
        st = [self.raw(k / fps) for k in range(n_frames)]
        out = list(st)
        k = 1
        while k < n_frames - 1:
            if out[k] != out[k - 1] and out[k] != out[k + 1]:
                out[k + 1] = out[k]
                k += 2
            else:
                k += 1
        return out
