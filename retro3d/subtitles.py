"""Subtítulos palabra a palabra: bloques de hasta 3 palabras, palabra actual
resaltada y con pequeño rebote, texto claro con contorno oscuro grueso.
Respetan zonas seguras: nada en el 20 % inferior ni en el 12 % derecho."""
import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .style import SUBS, SAFE, RENDER
from .anim import ease_out_back, seg, EASE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chunk_words(words, max_words=3, gap_break=0.28):
    """Agrupa palabras en bloques; corta en puntuación fuerte y en pausas."""
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        end_punct = re.search(r"[.,:;!?»]$", w["text"]) is not None
        nxt_gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 9
        if len(cur) >= max_words or end_punct or nxt_gap > gap_break:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    # evitar bloques de 1 palabra corta colgando si se puede unir al anterior
    out = []
    for c in chunks:
        if out and len(c) == 1 and len(out[-1]) < max_words and len(words[c[0]]["text"]) <= 3 \
                and not re.search(r"[.:!?]$", words[out[-1][-1]]["text"]):
            out[-1] = out[-1] + c
        else:
            out.append(c)
    return out


class Subtitles:
    def __init__(self, words, W=None, H=None):
        self.W = W or RENDER["width"]
        self.H = H or RENDER["height"]
        k = self.W / 1080
        self.font = ImageFont.truetype(os.path.join(ROOT, SUBS["font"]), int(SUBS["size"] * k))
        self.stroke = int(SUBS["stroke_w"] * k)
        self.words = words
        self.chunks = chunk_words(words, SUBS["max_words"])
        # ventana de cada bloque: desde su primera palabra hasta la siguiente (máx. +0,5 s)
        self.spans = []
        for j, c in enumerate(self.chunks):
            a = words[c[0]]["start"] - 0.04
            b = words[c[-1]]["end"] + 0.35
            if j + 1 < len(self.chunks):
                b = min(b, words[self.chunks[j + 1][0]]["start"] - 0.04)
            self.spans.append((a, b))
        x0 = SAFE["left"] * self.W
        x1 = (1 - SAFE["right"]) * self.W
        self.safe = (x0, SAFE["top"] * self.H, x1, (1 - SAFE["bottom"]) * self.H)
        self.cx = (x0 + x1) / 2
        self.max_w = (x1 - x0) * SUBS["max_width"]
        self._cache = {}
        self._glyphs = {}

    @staticmethod
    def display(text):
        return text.upper()

    def _layout(self, j):
        c = self.chunks[j]
        toks = [self.display(self.words[i]["text"]) for i in c]
        sp = self.font.getlength(" ")
        widths = [self.font.getlength(t) for t in toks]
        lines, cur, cw = [], [], 0
        for i, (t, w) in enumerate(zip(toks, widths)):
            if cur and cw + sp + w > self.max_w:
                lines.append(cur)
                cur, cw = [], 0
            cur.append(i)
            cw += (sp if cw else 0) + w
        if cur:
            lines.append(cur)
        asc, desc = self.font.getmetrics()
        lh = int((asc + desc) * 1.02)
        return toks, widths, sp, lines, lh

    def active(self, t):
        for j, (a, b) in enumerate(self.spans):
            if a <= t < b:
                return j
        return None

    LETTER_FADE = 0.1      # cada letra sube y se funde en 0,1 s
    MAX_RATE = 30.0        # letras por segundo como máximo
    EXIT_FADE = 0.12       # salida: fundido rápido

    def letter_times(self, i):
        """Instantes de aparición de cada letra de la palabra i (dentro de su pronunciación)."""
        w = self.words[i]
        tok = self.display(w["text"])
        n = max(1, len(tok))
        dur = max(0.05, w["end"] - w["start"])
        step = min(1.0 / self.MAX_RATE, 0.85 * dur / n)
        t0 = w["start"] - 0.03
        return [t0 + k * step for k in range(len(tok))]

    def _letter_img(self, ch, fill):
        key = (ch, fill)
        if key not in self._glyphs:
            m = self.stroke + 4
            w = int(self.font.getlength(ch)) + 2 * m
            asc, desc = self.font.getmetrics()
            im = Image.new("RGBA", (w, asc + desc + 2 * m), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((m, m), ch, font=self.font, fill=fill, stroke_width=self.stroke,
                                    stroke_fill=SUBS["stroke"])
            self._glyphs[key] = (np.asarray(im, np.float32), m)
        return self._glyphs[key]

    def render(self, t, full=False):
        """Devuelve (RGBA, x, y) o None. Letra a letra; palabra actual resaltada; salida en fundido."""
        j = self.active(t)
        if j is None:
            return None
        c = self.chunks[j]
        cur = None
        for k, i in enumerate(c):
            if self.words[i]["start"] - 0.04 <= t:
                cur = k
        a_, b_ = self.spans[j]
        fade = 1.0 if full else 1.0 - seg(t, b_ - self.EXIT_FADE, b_)
        toks, widths, sp, lines, lh = self._layout(j)
        pad = self.stroke * 2 + 30
        bw = int(max(sum(widths[i] for i in L) + sp * (len(L) - 1) for L in lines) + pad * 2)
        bh = int(lh * len(lines) + pad * 2)
        canvas = np.zeros((bh, bw, 4), np.float32)
        k_rise = 8 * self.W / 1080
        for li, L in enumerate(lines):
            lw = sum(widths[i] for i in L) + sp * (len(L) - 1)
            x = (bw - lw) / 2
            y = pad + li * lh
            for i in L:
                wi = c[i]
                fill = SUBS["highlight"] if i == cur else SUBS["fill"]
                times = self.letter_times(wi)
                for q, ch in enumerate(toks[i]):
                    al = 1.0 if full else seg(t, times[q], times[q] + self.LETTER_FADE)
                    if al <= 0:
                        continue
                    g, m = self._letter_img(ch, fill)
                    off = self.font.getlength(toks[i][:q])
                    rise = 0 if full else (1 - EASE["out"](al)) * k_rise
                    X0 = int(round(x + off - m))
                    Y0 = int(round(y - m + rise))
                    h, w = g.shape[:2]
                    xs0, ys0 = max(0, X0), max(0, Y0)
                    xs1, ys1 = min(bw, X0 + w), min(bh, Y0 + h)
                    if xs1 <= xs0 or ys1 <= ys0:
                        continue
                    src = g[ys0 - Y0:ys1 - Y0, xs0 - X0:xs1 - X0]
                    sa = src[..., 3:4] / 255 * al
                    dst = canvas[ys0:ys1, xs0:xs1]
                    out_a = sa + dst[..., 3:4] * (1 - sa)
                    rgb = (src[..., :3] * sa + dst[..., :3] * dst[..., 3:4] * (1 - sa)) / np.maximum(out_a, 1e-6)
                    canvas[ys0:ys1, xs0:xs1, :3] = rgb
                    canvas[ys0:ys1, xs0:xs1, 3:4] = out_a * 255 if False else out_a
                x += widths[i] + sp
        canvas[..., 3] *= fade
        out = Image.fromarray(np.dstack([canvas[..., :3], canvas[..., 3:4] * 255]).clip(0, 255).astype(np.uint8), "RGBA")
        cy = SUBS["center_y"] * self.H
        X = int(self.cx - bw / 2)
        Y = int(cy - bh / 2)
        X = max(int(self.safe[0]) - pad, min(X, int(self.safe[2]) - bw + pad))
        Y = min(Y, int(self.safe[3]) - bh + pad)
        return (out, X, Y)

    def composite(self, frame, t):
        r = self.render(t)
        if r is None:
            return frame
        img, X, Y = r
        a = np.asarray(img, np.float32) / 255
        h, w = a.shape[:2]
        x0, y0 = max(X, 0), max(Y, 0)
        x1, y1 = min(X + w, frame.shape[1]), min(Y + h, frame.shape[0])
        sub = a[y0 - Y:y1 - Y, x0 - X:x1 - X]
        al = sub[..., 3:4]
        out = frame.copy()
        reg = out[y0:y1, x0:x1].astype(np.float32)
        out[y0:y1, x0:x1] = (reg * (1 - al) + sub[..., :3] * 255 * al).astype(np.uint8)
        return out

    def bbox(self, t):
        """Caja ocupada por el bloque completo (para verificar zonas seguras)."""
        r = self.render(t, full=True)
        if r is None:
            return None
        img, X, Y = r
        a = np.asarray(img)[..., 3]
        ys, xs = np.where(a > 20)
        if not len(xs):
            return None
        return (X + xs.min(), Y + ys.min(), X + xs.max(), Y + ys.max())
