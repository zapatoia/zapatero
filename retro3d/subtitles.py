"""Subtítulos palabra a palabra: bloques de hasta 3 palabras, palabra actual
resaltada y con pequeño rebote, texto claro con contorno oscuro grueso.
Respetan zonas seguras: nada en el 20 % inferior ni en el 12 % derecho."""
import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .style import SUBS, SAFE, RENDER
from .anim import ease_out_back, seg

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

    def render(self, t):
        """Devuelve (RGBA, x, y) o None."""
        j = self.active(t)
        if j is None:
            return None
        c = self.chunks[j]
        cur = None
        for k, i in enumerate(c):
            if self.words[i]["start"] - 0.04 <= t:
                cur = k
        pop = 1.0
        if cur is not None:
            pop = ease_out_back(seg(t, self.words[c[cur]]["start"] - 0.04, self.words[c[cur]]["start"] + 0.12), 2.5)
        # aparición del bloque: pequeño salto vertical
        a = self.spans[j][0]
        appear = ease_out_back(seg(t, a, a + 0.14), 1.8)
        key = (j, cur, round(pop, 2), round(appear, 2))
        if key in self._cache:
            return self._cache[key]
        toks, widths, sp, lines, lh = self._layout(j)
        pad = self.stroke * 2 + 30
        bw = int(max(sum(widths[i] for i in L) + sp * (len(L) - 1) for L in lines) + pad * 2)
        bh = int(lh * len(lines) + pad * 2)
        img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        shadow = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        ds = ImageDraw.Draw(shadow)
        for li, L in enumerate(lines):
            lw = sum(widths[i] for i in L) + sp * (len(L) - 1)
            x = (bw - lw) / 2
            y = pad + li * lh
            for i in L:
                is_cur = (i == cur)
                fill = SUBS["highlight"] if is_cur else SUBS["fill"]
                if is_cur and pop != 1.0:
                    # palabra actual algo más grande con rebote
                    s = 1 + 0.07 * min(pop, 1.3)
                    f2 = self.font.font_variant(size=int(self.font.size * s))
                    w2 = f2.getlength(toks[i])
                    dx = (w2 - widths[i]) / 2
                    dy = (f2.size - self.font.size) * 0.6
                    d.text((x - dx, y - dy), toks[i], font=f2, fill=fill, stroke_width=self.stroke,
                           stroke_fill=SUBS["stroke"])
                else:
                    d.text((x, y), toks[i], font=self.font, fill=fill, stroke_width=self.stroke,
                           stroke_fill=SUBS["stroke"])
                x += widths[i] + sp
        out = Image.alpha_composite(shadow, img)
        cy = SUBS["center_y"] * self.H + (1 - appear) * 24
        X = int(self.cx - bw / 2)
        Y = int(cy - bh / 2)
        # forzar zona segura
        X = max(int(self.safe[0]) - pad, min(X, int(self.safe[2]) - bw + pad))
        Y = min(Y, int(self.safe[3]) - bh + pad)
        res = (out, X, Y)
        self._cache[key] = res
        return res

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
        """Caja ocupada por el texto (para verificar zonas seguras)."""
        r = self.render(t)
        if r is None:
            return None
        img, X, Y = r
        a = np.asarray(img)[..., 3]
        ys, xs = np.where(a > 20)
        if not len(xs):
            return None
        return (X + xs.min(), Y + ys.min(), X + xs.max(), Y + ys.max())
