#!/usr/bin/env python3
"""Fija la huella de config/narrator.json en config/narrator.lock.
SOLO tras un cambio del narrador pedido explícitamente por el usuario."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from retro3d.characters.narrator import config_hash, LOCK  # noqa
h = config_hash()
with open(LOCK, "w") as f:
    f.write(h + "  config/narrator.json\n")
print("narrator.lock →", h[:16])
