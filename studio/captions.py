"""Subtítulos palabra a palabra con la palabra actual resaltada.

Grandes, centrados en el área segura, texto crema con contorno oscuro grueso.
Nunca entran en el 20 % inferior ni en el 12 % derecho.
"""
from __future__ import annotations

import re

from .style import (C, CAPTION_Y, SAFE_CX, SAFE_LEFT, SAFE_RIGHT, cap_height, clamp,
                    draw_text, ease_out_back, prog, text_width, with_alpha)

SIZE = 96
MIN_SIZE = 68
OUTLINE = 22
MAX_W = (SAFE_RIGHT - SAFE_LEFT) - 60       # 820 px
LINE_GAP = 1.08
MAX_CHARS = 16
MAX_WORDS = 3


def clean(display: str) -> str:
    s = display.strip()
    s = re.sub(r"[.,;:…]+$", "", s)       # fuera puntuación final suave
    s = s.strip("«»\"“”")
    return s.upper()


def build_chunks(words):
    """Agrupa palabras en bloques cortos (≤3 palabras / ≤16 caracteres)."""
    chunks, cur = [], []
    for i, w in enumerate(words):
        txt = clean(w.display)
        cur_len = sum(len(clean(x.display)) + 1 for x in cur)
        if cur and (len(cur) >= MAX_WORDS or cur_len + len(txt) > MAX_CHARS
                    or w.beat != cur[-1].beat):
            chunks.append(cur)
            cur = []
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt.start - w.end) if nxt else 9
        if w.clause_end or gap > 0.35:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    # no dejar palabras huérfanas de 1-2 letras solas al final de un bloque
    return chunks


class Captions:
    def __init__(self, words, end_time):
        self.words = words
        self.chunks = build_chunks(words)
        self.spans = []
        for i, ch in enumerate(self.chunks):
            s = ch[0].start - 0.06
            nxt = self.chunks[i + 1][0].start - 0.06 if i + 1 < len(self.chunks) else end_time
            e = min(nxt, ch[-1].end + 0.6)
            self.spans.append((s, e))
        self.layouts = [self._layout(ch) for ch in self.chunks]

    def _layout(self, chunk):
        texts = [clean(w.display) for w in chunk]
        size = SIZE
        space = size * 0.28

        def width(ts, sz):
            return sum(text_width(t, sz) for t in ts) + sz * 0.28 * (len(ts) - 1)

        lines = [list(range(len(texts)))]
        while width(texts, size) > MAX_W and size > MIN_SIZE:
            size -= 2
        if width(texts, size) > MAX_W and len(texts) > 1:
            size = SIZE
            cut = max(1, len(texts) // 2)
            lines = [list(range(cut)), list(range(cut, len(texts)))]
            while max(width([texts[i] for i in ln], size) for ln in lines) > MAX_W:
                size -= 2
        space = size * 0.28
        pos = []
        n_lines = len(lines)
        for li, ln in enumerate(lines):
            lw = width([texts[i] for i in ln], size)
            x = SAFE_CX - lw / 2
            y = CAPTION_Y + cap_height(size) / 2 + (li - (n_lines - 1) / 2) * size * LINE_GAP
            for i in ln:
                w = text_width(texts[i], size)
                pos.append((i, x + w / 2, y, w))
                x += w + space
        pos.sort()
        return texts, size, pos

    def draw(self, c, t):
        for ci, (s, e) in enumerate(self.spans):
            if not (s <= t < e):
                continue
            chunk = self.chunks[ci]
            texts, size, pos = self.layouts[ci]
            # salida rápida
            fade = clamp((e - t) / 0.08)
            for (i, x, y, w), word, txt in zip(pos, chunk, texts):
                if t < word.start - 0.06:
                    continue
                k = ease_out_back(prog(t, word.start - 0.06, 0.16), 2.6)
                k = 0.6 + 0.4 * k
                nxt_start = chunk[i + 1].start if i + 1 < len(chunk) else e
                current = word.start - 0.06 <= t < max(word.end, nxt_start - 0.06)
                if current:
                    color = C["yellow"] if word.emph else C["orange"]
                    k *= 1.06
                else:
                    color = C["yellow"] if word.emph else C["cream"]
                color = with_alpha(color, fade)
                c.save()
                c.translate(x, y - cap_height(size) / 2)
                c.scale(k, k)
                draw_text(c, txt, 0, cap_height(size) / 2, size, color,
                          outline=OUTLINE, outline_color=with_alpha(C["navy"], fade))
                c.restore()


DISCLAIMER = "Información, no consejo financiero."


def draw_disclaimer(c, t, t_end):
    p = prog(t, t_end - 1.0, 0.18)
    if p <= 0:
        return
    size = 36
    y = 1488
    draw_text(c, DISCLAIMER, SAFE_CX, y, size, with_alpha(C["cream"], 0.9 * p), "semi",
              outline=10, outline_color=with_alpha(C["navy"], p))
