#!/usr/bin/env python3
"""Hoja de revisión de personajes: 5 poses + 3 s de animación (cada 0,25 s)
para el narrador y el perro. Uso: python tools/preview_characters.py [salida_dir]"""
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT))
from retro3d.render import Renderer, Camera  # noqa
from retro3d.world import World  # noqa
from retro3d.characters.narrator import Narrator  # noqa
from retro3d.characters.dog import Dog  # noqa
from make_video import label, sheet  # noqa

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "characters")
os.makedirs(out, exist_ok=True)
r = Renderer(540, 960)
w = World(r)
n = Narrator(); n.upload(r); n.env_fn = lambda t: 0.7
d = Dog(); d.upload(r)
print("triángulos: narrador", n.tri_count(), "| perro", d.tri_count())


def shot(ch, act, t, cam, params=None):
    ch.timeline = [(0, act, params or {})]
    ch._last_t = None
    ch.update(t)
    r.shadow_center = np.zeros(3); r.shadow_radius = 6
    return label(r.render(cam, w.items + ch.items()), f"{act}  t={t:.2f}s")


NC = [Camera((0.0, -3.4, 1.55), (0, 0, 1.0), 38), Camera((1.6, -3.0, 1.6), (0, 0, 1.0), 38)]
DC = [Camera((1.3, -3.0, 1.3), (0, 0, 0.5), 30), Camera((3.0, -1.2, 1.3), (0, 0, 0.5), 30)]
for ch, name, poses, cams in (
        (n, "narrador", [("idle", {}), ("talk", {}), ("point", {"side": "L"}), ("shrug", {}), ("lean_in", {})], NC),
        (d, "perro", [("idle", {}), ("wag", {}), ("sit", {}), ("jump", {}), ("lick", {"up": 0.5})], DC)):
    ims = [shot(ch, a, 0.45 if a == "jump" else 0.9, cams[i % 2], p) for i, (a, p) in enumerate(poses)]
    sheet(ims, 5, os.path.join(out, f"{name}_poses.jpg"))
    anim = "walk" if ch is n else "lick"
    ch.timeline = [(0, "explain" if ch is n else "lick", {})]
    ch._last_t = None
    ims = []
    for k in range(12):
        t = k * 0.25
        ch.update(t)
        ims.append(label(r.render(cams[0], w.items + ch.items()), f"t={t:.2f}s").resize((270, 480)))
    sheet(ims, 6, os.path.join(out, f"{name}_anim3s.jpg"))
print("→", out)
