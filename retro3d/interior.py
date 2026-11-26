"""Segundo escenario: interior de la cabaña (minimalista).

Se construye lejos del claro (ORIGIN), con el frente abierto hacia -Y para que
la cámara mire dentro como a un escenario. Coordenadas locales: suelo en z=0,
paredes en x=±4 y y=+3,2, techo a 3 m.
"""
import numpy as np

from . import mesh as M
from .mesh import Mesh, hexcol
from .mathutil import translate, rot_z
from .render import Item
from .style import PAL

ORIGIN = np.array([0.0, -400.0, 0.0])
HALF_W, BACK, FRONT, HEIGHT = 4.0, 3.2, -4.0, 3.0
CUSHION = (0.95, 1.45, 0.52, 0.14)   # x, y, radio, altura de la superficie


def C(n, k=1.0):
    r, g, b, a = hexcol(PAL[n])
    return (min(r * k, 1), min(g * k, 1), min(b * k, 1), a)


def contains(x, y, margin=0.5):
    lx, ly = x - ORIGIN[0], y - ORIGIN[1]
    return -HALF_W - margin <= lx <= HALF_W + margin and FRONT - 6 <= ly <= BACK + margin


def build(r):
    """Devuelve (items, obstáculos [(x, y, radio)], items_de_fuego)."""
    T = translate(*ORIGIN)
    parts = {k: Mesh() for k in ("planks", "planks_v", "stone", "white")}
    W, B, H = HALF_W, BACK, HEIGHT
    D = B - FRONT
    cy = (B + FRONT) / 2
    # suelo y techo
    parts["planks"].extend(M.box(2 * W, D, 0.1, C("wood_a"), center=(0, cy, -0.05), uv_scale=0.6))
    ceiling = M.box(2 * W, D, 0.1, C("wood_b", 0.8), center=(0, cy, H + 0.05), uv_scale=0.6)
    # paredes: zócalo de piedra + tablas
    for (sx, sy, cx, cyy) in ((2 * W, 0.2, 0, B + 0.1), (0.2, D, -W - 0.1, cy), (0.2, D, W + 0.1, cy)):
        parts["stone"].extend(M.box(sx, sy, 0.7, C("stone_a"), center=(cx, cyy, 0.35), uv_scale=0.7))
        parts["planks_v"].extend(M.box(sx, sy, H - 0.7, C("wood_a", 0.92), center=(cx, cyy, 0.7 + (H - 0.7) / 2),
                                       uv_scale=0.55))
    # vigas
    for y in (-2.0, 0.4, 2.6):
        parts["white"].extend(M.box(2 * W, 0.22, 0.22, C("wood_b", 0.6), center=(0, y, H - 0.11)))
    # ventana en la pared izquierda (luz de día, emisiva)
    win = M.box(0.06, 1.1, 0.9, (0.86, 0.93, 1.0, 1), center=(-W + 0.01, 0.4, 1.7))
    frame = Mesh()
    frame.extend(M.box(0.1, 1.3, 0.1, C("wood_b", 0.6), center=(-W + 0.03, 0.4, 2.2)))
    frame.extend(M.box(0.1, 1.3, 0.1, C("wood_b", 0.6), center=(-W + 0.03, 0.4, 1.2)))
    frame.extend(M.box(0.1, 0.08, 1.0, C("wood_b", 0.6), center=(-W + 0.03, 0.4, 1.7)))
    frame.extend(M.box(0.1, 1.2, 0.06, C("wood_b", 0.6), center=(-W + 0.03, 0.4, 1.7)))
    parts["white"].extend(frame)
    # chimenea en la pared del fondo
    fx = 1.7
    parts["stone"].extend(M.box(1.6, 0.7, 1.3, C("stone_a"), center=(fx, B - 0.3, 0.65), uv_scale=0.7))
    parts["stone"].extend(M.box(0.9, 0.5, H - 1.3, C("stone_a"), center=(fx, B - 0.25, 1.3 + (H - 1.3) / 2), uv_scale=0.7))
    parts["white"].extend(M.box(1.0, 0.1, 0.75, C("ui_ink"), center=(fx, B - 0.66, 0.45)))
    parts["white"].extend(M.box(1.8, 0.35, 0.12, C("wood_b", 0.7), center=(fx, B - 0.55, 1.33)))
    for dx in (-0.15, 0.15):
        parts["white"].extend(M.box(0.7, 0.12, 0.12, C("bark"), center=(fx, B - 0.75, 0.13)).transformed(
            translate(fx, B - 0.75, 0.13) @ rot_z(dx) @ translate(-fx, -(B - 0.75), -0.13)))
    fire = Mesh()
    for (dx, h, w, col) in ((-0.12, 0.5, 0.26, "scarf"), (0.13, 0.42, 0.22, "scarf"), (0.0, 0.33, 0.2, "flower_y")):
        fire.extend(M.cylinder(w / 2, 0.0, h, 4, C(col), center=(fx + dx, B - 0.8, 0.2 + h / 2), rot=0.785))
    # alfombra
    parts["white"].extend(M.box(2.8, 1.9, 0.02, C("roof_a"), center=(0.2, 0.3, 0.01)))
    parts["white"].extend(M.box(2.5, 1.6, 0.025, C("roof_b"), center=(0.2, 0.3, 0.012)))
    # cojín del perro junto al fuego
    parts["white"].extend(M.cylinder(0.55, 0.52, 0.14, 8, C("tunic_dark"), center=(CUSHION[0], CUSHION[1], 0.07)))
    # mesa, taburete, taza
    tx, ty = -2.4, 1.7
    parts["planks"].extend(M.box(1.3, 0.8, 0.08, C("wood_c"), center=(tx, ty, 0.78)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts["white"].extend(M.box(0.08, 0.08, 0.74, C("wood_b"), center=(tx + sx * 0.55, ty + sy * 0.32, 0.37)))
    parts["white"].extend(M.cylinder(0.07, 0.07, 0.12, 6, C("warn_white"), center=(tx + 0.3, ty - 0.1, 0.88)))
    parts["white"].extend(M.box(0.4, 0.4, 0.06, C("wood_c"), center=(tx + 0.9, ty - 0.7, 0.45)))
    parts["white"].extend(M.box(0.08, 0.08, 0.42, C("wood_b"), center=(tx + 0.9, ty - 0.7, 0.21)))
    # estantería con tarros en la pared derecha
    parts["white"].extend(M.box(0.3, 1.4, 0.06, C("wood_b", 0.8), center=(W - 0.15, 0.6, 1.6)))
    for k, col in enumerate(("flower_y", "tunic", "scarf")):
        parts["white"].extend(M.cylinder(0.09, 0.09, 0.22, 6, C(col), center=(W - 0.15, 0.2 + k * 0.4, 1.74)))
    items = []
    for tex, m in parts.items():
        if m.tris:
            items.append(Item(r.upload(m.transformed(T)), np.eye(4), tex=tex, shadow=tex != "planks_v" and tex != "stone"))
    items.append(Item(r.upload(ceiling.transformed(T)), np.eye(4), tex="planks", shadow=False))
    items.append(Item(r.upload(win.transformed(T)), np.eye(4), tex="white", emissive=1.0, unlit=True, shadow=False))
    fire_items = [Item(r.upload(fire.transformed(T)), np.eye(4), tex="white", emissive=1.2, unlit=True, shadow=False)]
    items += fire_items
    o = ORIGIN
    obstacles = [(o[0] + fx, o[1] + B - 0.3, 0.9), (o[0] + tx, o[1] + ty, 0.8)]
    return items, obstacles, fire_items


def surface_height(x, y):
    """Altura de la superficie pisable dentro de la casa (suelo o cojín)."""
    lx, ly = x - ORIGIN[0], y - ORIGIN[1]
    cx, cy, r, h = CUSHION
    if (lx - cx) ** 2 + (ly - cy) ** 2 < r * r:
        return h
    return 0.0
