#!/usr/bin/env python3
"""Revisión de encuadres: 3 fotogramas por plano (inicio, mitad, final) + comprobación
automática de encuadre (cabeza del sujeto dentro del cuadro, iconos que tapan caras).

  python tools/shot_frames.py scripts/NN.json [--shots 1,4,13] [--scale 0.5]

Salida: build/NN/shots.jpg y build/NN/framing.md (no modifica nada más).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import make_video as MV  # noqa: E402
from retro3d import camera as CAM  # noqa: E402

HEAD = {"narrator": ("head", 0.30), "dog": ("head", 0.14)}


def subjects(prod, sh):
    sub = sh.get("sub", "narr")
    if isinstance(sub, list):
        return []
    if sub == "two":
        return ["narr", "dog"]
    if "." in sub:
        return []
    return sub.split("+")


def head_box(prod, cam, name):
    ch = prod.cast[name]
    node, r = HEAD[ch.kind]
    c = ch.point(node)
    pts = [c + np.array(o) for o in ((0, 0, r * 1.1), (0, 0, -r * 0.6), (r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0))]
    P = prod.r.project(cam, np.array(pts))
    return P


def check_frame(prod, cam, t, sh, W, H):
    """Devuelve avisos de encuadre para este fotograma."""
    out = []
    boxes = {}
    for name in subjects(prod, sh):
        P = head_box(prod, cam, name)
        if (P[:, 2] <= 0).any():
            out.append(f"{name}: cabeza detrás de la cámara")
            continue
        inside = ((P[:, 0] >= 0) & (P[:, 0] <= W) & (P[:, 1] >= 0) & (P[:, 1] <= H)).mean()
        if inside < 0.99:
            out.append(f"{name}: cabeza cortada ({inside * 100:.0f} % dentro)")
        boxes[name] = (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())
    # iconos sobre caras de cualquier personaje visible
    faces = {}
    for name, ch in prod.cast.items():
        P = head_box(prod, cam, name)
        if (P[:, 2] > 0).all() and P[:, 0].max() - P[:, 0].min() > W * 0.06:   # solo caras visibles de verdad
            faces[name] = (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())
    for pr in prod.props:
        if getattr(pr, "glow_col", None) is None and getattr(pr, "text_spec", None) is not None:
            continue
        if not hasattr(pr, "alive") or not pr.alive(t) or pr.scale_at(t) < 0.9:
            continue
        if pr.t_out is not None and t > pr.t_out:      # ya está saliendo
            continue
        bx = MV._project_box(prod, cam, pr)
        if bx is None:
            continue
        if bx[0] < 0 or bx[1] < 0 or bx[2] > W or bx[3] > H:
            out.append(f"recurso cortado por el borde {[round(v) for v in bx]}")
        elif bx[1] < H * 0.06:
            out.append(f"recurso pegado al borde superior (zona de la interfaz) {[round(v) for v in bx]}")
        for name, fb in faces.items():
            ix = max(0, min(bx[2], fb[2]) - max(bx[0], fb[0]))
            iy = max(0, min(bx[3], fb[3]) - max(bx[1], fb[1]))
            fa = (fb[2] - fb[0]) * (fb[3] - fb[1])
            if fa > 0 and ix * iy / fa > 0.12:
                out.append(f"recurso tapa la cara de {name} ({ix * iy / fa * 100:.0f} %)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--shots", default=None)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--W", type=int, default=540)
    ap.add_argument("--dry", action="store_true", help="tiempos estimados (sin voz en caché)")
    a = ap.parse_args()
    script = json.load(open(a.script))
    bdir = MV.build_dir(script)
    if a.dry:
        words, dur = MV.A.estimate_words(MV.tts_text(script))
        env = None
    else:
        voice, words, dur, env = MV.prepare_voice(script, bdir, {})
    W, H = a.W, a.W * 16 // 9
    prod = MV.Production(script, words, dur, W, H, env=env)
    subs = MV.Subtitles(words, W, H)
    want = None if not a.shots else {int(x) - 1 for x in a.shots.split(",")}
    ims, rep = [], ["# Encuadres por plano", ""]
    total = 0
    for i, t0, t1, sh in prod.shot_report():
        if want is not None and i not in want:
            continue
        lab = f"{i + 1} {sh.get('type')}/{sh.get('size', 'medium')} sub={sh.get('sub')}"
        warns = []
        for k, u in enumerate((0.04, 0.5, 0.96)):
            t = t0 + (t1 - t0) * u
            if sh.get("transition") == "whip" and u < 0.1:
                t = t0 + CAM.WHIP_DUR + 0.02
            img, cam = prod.frame(t)
            for w_ in check_frame(prod, cam, t, sh, W, H):
                warns.append(f"{('inicio', 'mitad', 'final')[k]} {t:.2f}s: {w_}")
            img = subs.composite(img, t)
            im = MV.label(Image.fromarray(img).resize((int(W * a.scale * 2), int(H * a.scale * 2))) if a.scale != 0.5 else Image.fromarray(img),
                          f"{lab} {('ini', 'mid', 'fin')[k]}", f"{t:.2f}s {MV.words_text(words, t - 0.4, t + 0.4)[:40]}")
            ims.append(im)
        rep.append(f"- Plano {i + 1} ({t0:.2f}-{t1:.2f} s, {lab}): " + ("OK" if not warns else ""))
        rep += [f"  - ⚠ {w_}" for w_ in warns]
        total += len(warns)
    rep.insert(2, f"Avisos: {total}\n")
    MV.sheet(ims, 6, os.path.join(bdir, "shots.jpg"))
    with open(os.path.join(bdir, "framing.md"), "w") as f:
        f.write("\n".join(rep) + "\n")
    print("\n".join(rep))
    print(os.path.join(bdir, "shots.jpg"))


if __name__ == "__main__":
    main()
