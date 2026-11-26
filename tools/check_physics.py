#!/usr/bin/env python3
"""Comprobación rápida de físicas sin renderizar: interpenetraciones por par y tramo."""
import sys, json, io, contextlib, collections, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from make_video import prepare_voice, build_dir  # noqa
from retro3d.production import Production  # noqa
S = json.load(open(sys.argv[1]))
with contextlib.redirect_stdout(io.StringIO()):
    voice, words, dur, env = prepare_voice(S, build_dir(S), {})
prod = Production(S, words, dur, 270, 480, env=env)
pairs = collections.defaultdict(list)
fps = 30
for k in range(int(dur * fps)):
    t = k / fps
    for ch in prod.cast.values():
        ch.update(t, 1 / fps)
    prod.contacts = prod.solve_physics(t)
    for a, b, d in prod.check_penetrations():
        pairs[(f"{a.owner}.{a.node}", f"{b.owner}.{b.node}")].append((t, d))
for k, v in sorted(pairs.items(), key=lambda x: -len(x[1])):
    ts = [x[0] for x in v]
    print(f"{len(v):4d}  {k[0]:>14} ↔ {k[1]:<14} max {max(x[1] for x in v):.3f}  t {min(ts):.2f}-{max(ts):.2f}")
print("TOTAL fotogramas con algún par:", len({round(t, 3) for v in pairs.values() for t, _ in v}))
