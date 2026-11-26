"""Escenario reutilizable: claro del bosque con camino de tierra, cabaña,
muro de piedra, vallas, árboles, rocas, matojos, montañas y nubes."""
import math
import numpy as np

from . import mesh as M
from . import textures as T
from .mesh import Mesh, hexcol
from .mathutil import translate, rot_z, scale, euler
from .render import Item
from .style import PAL


def C(name, k=1.0):
    r, g, b, a = hexcol(PAL[name])
    return (min(r * k, 1), min(g * k, 1), min(b * k, 1), a)


# camino: polilínea en planta (x, y)
PATH = np.array([(-9, -22), (-5, -12), (-1.6, -5), (0.2, 0), (1.2, 5), (3.5, 11), (8, 18), (11, 28), (13, 40)], "f8")


def _dist_to_path(x, y):
    best = 1e9
    for (ax, ay), (bx, by) in zip(PATH, PATH[1:]):
        dx, dy = bx - ax, by - ay
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.hypot(x - (ax + t * dx), y - (ay + t * dy))
        best = np.minimum(best, d)
    return best


def ground_h(x, y):
    r = np.hypot(x, y - 4)
    hills = (np.sin(x * 0.11 + 1.3) * np.cos(y * 0.09 + 0.4) * 1.4 +
             np.sin(x * 0.23 + y * 0.17) * 0.5)
    rise = np.clip((r - 14) / 30, 0, 1) ** 1.6 * 9
    flat = np.clip((r - 6) / 8, 0, 1)
    bumps = np.sin(x * 1.7 + 2) * np.sin(y * 1.3) * 0.06
    return flat * (hills + rise) * 0.8 + bumps


def _terrain_grid(x0, x1, y0, y1, step, drop=0.0, path=True, seed=0):
    rng = np.random.default_rng(seed)
    xs = np.arange(x0, x1 + 1e-6, step)
    ys = np.arange(y0, y1 + 1e-6, step)
    X, Y = np.meshgrid(xs, ys)
    # desplazamiento leve de vértices: rompe la rejilla
    X = X + rng.uniform(-0.18, 0.18, X.shape) * step
    Y = Y + rng.uniform(-0.18, 0.18, Y.shape) * step
    Z = ground_h(X, Y) - drop
    if path:
        d = _dist_to_path(X, Y) + rng.uniform(-0.25, 0.25, X.shape)
        Bw = np.clip((1.7 - d) / 0.7, 0, 1)
        Z = Z - Bw * 0.04
    else:
        Bw = np.zeros_like(X)
    tone = 0.97 + rng.uniform(0, 0.06, X.shape)
    m = Mesh()
    s = 0.33  # repetición de textura cada 3 m
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            idx = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            P = [np.array([X[a], Y[a], Z[a]]) for a in idx]
            uv = [(X[a] * s, Y[a] * s) for a in idx]
            cols = [(tone[a], tone[a], tone[a] * 0.97, Bw[a]) for a in idx]
            for tri in ((0, 1, 2), (0, 2, 3)) if (i + j) % 2 else ((0, 1, 3), (1, 2, 3)):
                a, b, c = (P[k] for k in tri)
                n = np.cross(b - a, c - a)
                n /= np.linalg.norm(n)
                for k in tri:
                    m.p.append(P[k]); m.n.append(n); m.uv.append(uv[k]); m.c.append(cols[k])
    return m


# ------------------------------------------------------------ objetos

def tree_round(seed, h=1.0):
    rng = np.random.default_rng(seed)
    trunk = M.cylinder(0.24 * h, 0.15 * h, 2.0 * h, 6, C("bark"), center=(0, 0, 1.0 * h), uv_scale=1.0,
                       rot=rng.uniform(0, 1))
    # raíces
    for k in range(3):
        a = k * 2.1 + rng.uniform(0, 0.5)
        trunk.extend(M.box(0.18, 0.5, 0.16, C("bark", 0.9), center=(0, 0, 0.06)).transformed(
            rot_z(a) @ translate(0, 0.22 * h, 0) @ euler(0.35, 0, 0)))
    leaves = Mesh()
    lf = lambda n, rel: C("leaf_b") if n[2] > 0.55 else (C("leaf_a") if n[2] > -0.2 else C("leaf_c"))
    blobs = [((0, 0, 2.75), (1.4, 1.3, 1.15)), ((0.45, 0.25, 3.45), (0.85, 0.8, 0.7))]
    for k, (c, r) in enumerate(blobs):
        c = np.array(c) * h + rng.uniform(-0.15, 0.15, 3)
        leaves.extend(M.blob(r[0] * h, r[1] * h, r[2] * h, C("leaf_a"), n=14, noise=0.08, seed=seed * 7 + k,
                             center=c, jitter=0.0, color_fn=lf, uv_scale=0.8))
    return trunk, leaves


def tree_pine(seed, h=1.0):
    rng = np.random.default_rng(seed)
    trunk = M.cylinder(0.2 * h, 0.12 * h, 1.4 * h, 5, C("bark_dark"), center=(0, 0, 0.7 * h))
    lv = Mesh()
    for k, (z, r, hh) in enumerate([(1.0, 1.3, 1.9), (2.2, 0.9, 1.7)]):
        cone = M.cylinder(r * h, 0.0, hh * h, 7, C("pine_a"), center=(0, 0, (z + hh / 2) * h),
                          rot=rng.uniform(0, 1), jitter=0.0, cap_col=C("pine_a", 0.7))
        cone.recolor(lambda c, n, p: C("pine_b") if n[2] > 0.45 else C("pine_a", 0.95))
        lv.extend(cone)
    return trunk, lv


def rock(seed, s=1.0):
    return M.blob(0.7 * s, 0.55 * s, 0.42 * s, C("stone_a"), n=10, noise=0.2, seed=seed,
                  center=(0, 0, 0.12 * s), jitter=0.0, flat_bottom=-0.1 * s,
                  color_fn=lambda n, rel: C("moss") if n[2] > 0.72 else (C("stone_c") if n[2] > 0.2 else C("stone_b")))


def tuft(seed, s=1.0, n_quads=2):
    m = Mesh()
    rng = np.random.default_rng(seed)
    a0 = rng.uniform(0, math.pi)
    for k in range(n_quads):
        a = a0 + k * math.pi / n_quads
        dx, dy = math.cos(a) * 0.32 * s, math.sin(a) * 0.32 * s
        h = 0.42 * s
        m.quad((-dx, -dy, 0), (dx, dy, 0), (dx, dy, h), (-dx, -dy, h), (1, 1, 1, 1),
               uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # normales hacia arriba: los matojos se iluminan como el suelo
    m.n = [np.array([0, 0, 1.0]) for _ in m.n]
    return m


def hut():
    """Cabaña de piedra y madera. Origen en el centro de la planta, puerta mirando a -Y."""
    parts = {"stone": Mesh(), "planks": Mesh(), "planks_v": Mesh(), "roof": Mesh(), "white": Mesh()}
    W, D = 4.2, 3.4
    parts["stone"].extend(M.box(W + 0.2, D + 0.2, 0.8, C("stone_a", 1.05), center=(0, 0, 0.35), bevel=0.06, uv_scale=0.6))
    parts["planks_v"].extend(M.box(W, D, 1.9, C("wood_a"), center=(0, 0, 1.7), uv_scale=0.55, jitter=0))
    # vigas de esquina y travesaño
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts["planks"].extend(M.box(0.26, 0.26, 2.1, C("wood_b", 0.75), center=(sx * W / 2, sy * D / 2, 1.65), bevel=0.03))
    parts["planks"].extend(M.box(W + 0.3, 0.2, 0.2, C("wood_b", 0.75), center=(0, -D / 2 - 0.03, 2.62)))
    # tejado a dos aguas (cumbrera en X)
    ov = 0.45
    rh = 1.55
    for sy in (-1, 1):
        a = (-W / 2 - ov, sy * (D / 2 + ov), 2.55)
        b = (W / 2 + ov, sy * (D / 2 + ov), 2.55)
        c = (W / 2 + ov, 0, 2.55 + rh)
        d = (-W / 2 - ov, 0, 2.55 + rh)
        thick = Mesh()
        if sy < 0:
            thick.quad(a, b, c, d, C("roof_a"), uvs=[(0, 0), (2.6, 0), (2.6, 1.6), (0, 1.6)], jitter=0)
        else:
            thick.quad(b, a, d, c, C("roof_a"), uvs=[(0, 0), (2.6, 0), (2.6, 1.6), (0, 1.6)], jitter=0)
        parts["roof"].extend(thick)
        # canto del alero
        parts["planks"].extend(M.box(W + 2 * ov + 0.1, 0.16, 0.16, C("wood_b", 0.6), center=(0, sy * (D / 2 + ov), 2.52)))
    parts["planks"].extend(M.box(W + 2 * ov + 0.2, 0.22, 0.22, C("wood_b", 0.6), center=(0, 0, 2.55 + rh + 0.02)))
    # hastiales
    for sx in (-1, 1):
        g = Mesh()
        pa, pb, pc = (sx * W / 2, -D / 2, 2.6), (sx * W / 2, D / 2, 2.6), (sx * W / 2, 0, 2.55 + rh - 0.05)
        if sx > 0:
            g.tri(pa, pb, pc, C("wood_c", 0.95), uv_scale=0.55)
        else:
            g.tri(pb, pa, pc, C("wood_c", 0.95), uv_scale=0.55)
        parts["planks_v"].extend(g)
    # puerta
    parts["planks"].extend(M.box(0.95, 0.12, 1.75, C("wood_b", 0.85), center=(0.6, -D / 2 - 0.04, 1.2), jitter=0))
    parts["planks"].extend(M.box(1.15, 0.16, 0.14, C("wood_b", 0.55), center=(0.6, -D / 2 - 0.06, 2.12)))
    for sx in (-1, 1):
        parts["planks"].extend(M.box(0.14, 0.16, 1.85, C("wood_b", 0.55), center=(0.6 + sx * 0.55, -D / 2 - 0.06, 1.2)))
    parts["white"].extend(M.box(0.09, 0.06, 0.09, C("gold"), center=(0.92, -D / 2 - 0.13, 1.2)))
    # ventana con luz cálida
    win = M.box(0.7, 0.06, 0.6, C("window"), center=(-1.1, -D / 2 - 0.02, 1.75), jitter=0)
    frame = Mesh()
    for dz in (-0.34, 0.34):
        frame.extend(M.box(0.86, 0.14, 0.1, C("wood_b", 0.55), center=(-1.1, -D / 2 - 0.06, 1.75 + dz)))
    for dx in (-0.4, 0, 0.4):
        frame.extend(M.box(0.1 if dx else 0.06, 0.14, 0.7, C("wood_b", 0.55), center=(-1.1 + dx, -D / 2 - 0.06, 1.75)))
    frame.extend(M.box(0.06, 0.12, 0.7, C("wood_b", 0.55), center=(-1.1, -D / 2 - 0.07, 1.75)).transformed(np.eye(4)))
    parts["planks"].extend(frame)
    # contraventanas
    for sx in (-1, 1):
        parts["planks"].extend(M.box(0.34, 0.08, 0.72, C("roof_b", 0.9), center=(-1.1 + sx * 0.62, -D / 2 - 0.06, 1.75), jitter=0))
    # chimenea
    parts["stone"].extend(M.box(0.6, 0.6, 1.6, C("stone_a"), center=(-1.3, 0.6, 3.9), bevel=0.04, uv_scale=0.7))
    parts["stone"].extend(M.box(0.75, 0.75, 0.16, C("stone_b"), center=(-1.3, 0.6, 4.72), uv_scale=0.7))
    return parts, win


def stone_wall(length, seed=0):
    rng = np.random.default_rng(seed)
    m = Mesh()
    x = -length / 2
    while x < length / 2:
        w = rng.uniform(0.45, 0.75)
        for row, (z, hh) in enumerate([(0.18, 0.36), (0.52, 0.32), (0.8, 0.26)]):
            ox = rng.uniform(-0.12, 0.12) + (0.2 if row == 1 else 0)
            if x + ox + w / 2 > length / 2 + 0.2:
                continue
            m.extend(M.box(w * rng.uniform(0.85, 1.05), 0.55 * rng.uniform(0.9, 1.05), hh, C("stone_a"),
                           center=(x + w / 2 + ox, rng.uniform(-0.04, 0.04), z), bevel=0.04, jitter=0.0,
                           taper=(0.9, 0.9),
                           color_fn=lambda n, rel: C("stone_c") if n[2] > 0.3 else C("stone_a")).transformed(rot_z(rng.uniform(-0.06, 0.06))))
        x += w
    return m


def fence(length, seed=0):
    rng = np.random.default_rng(seed)
    m = Mesh()
    n = max(2, int(length / 1.4) + 1)
    for i in range(n):
        x = -length / 2 + i * length / (n - 1)
        m.extend(M.box(0.16, 0.16, 1.05, C("wood_b"), center=(x, 0, 0.5), bevel=0.03, taper=(0.75, 0.75)).transformed(
            euler(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0)))
    for z in (0.42, 0.78):
        m.extend(M.box(length + 0.2, 0.08, 0.12, C("wood_a"), center=(0, -0.08, z), jitter=0.0).transformed(
            euler(0, rng.uniform(-0.03, 0.03), 0)))
    return m


def barrel():
    m = Mesh()
    m.extend(M.cylinder(0.34, 0.4, 0.45, 8, C("wood_a"), center=(0, 0, 0.225), uv_scale=1.2))
    m.extend(M.cylinder(0.4, 0.34, 0.45, 8, C("wood_a"), center=(0, 0, 0.675), uv_scale=1.2))
    for z in (0.12, 0.45, 0.78):
        m.extend(M.cylinder(0.41 if z == 0.45 else 0.375, 0.41 if z == 0.45 else 0.375, 0.06, 8, C("metal_dark"),
                            center=(0, 0, z), caps=False))
    return m


def crate():
    m = M.box(0.7, 0.7, 0.7, C("wood_c"), center=(0, 0, 0.35), bevel=0.03, jitter=0)
    for sy in (-1, 1):
        m.extend(M.box(0.72, 0.04, 0.1, C("wood_b", 0.7), center=(0, sy * 0.36, 0.62)))
        m.extend(M.box(0.72, 0.04, 0.1, C("wood_b", 0.7), center=(0, sy * 0.36, 0.08)))
        m.extend(M.box(0.1, 0.04, 0.9, C("wood_b", 0.7), center=(0, sy * 0.36, 0.35)).transformed(
            translate(0, 0, 0.35) @ euler(0, 0.78, 0) @ translate(0, 0, -0.35)))
    return m


def lantern_post():
    m = Mesh()
    m.extend(M.box(0.16, 0.16, 2.2, C("wood_b", 0.7), center=(0, 0, 1.1), bevel=0.03))
    m.extend(M.box(0.7, 0.12, 0.12, C("wood_b", 0.7), center=(0.3, 0, 2.1)))
    cage = M.box(0.28, 0.28, 0.06, C("metal_dark"), center=(0.55, 0, 1.92))
    cage.extend(M.cylinder(0.2, 0.0, 0.16, 4, C("metal_dark"), center=(0.55, 0, 2.0), rot=0.785))
    m.extend(cage)
    glow = M.box(0.2, 0.2, 0.28, C("window"), center=(0.55, 0, 1.75), jitter=0)
    return m, glow


def mountains(seed=4):
    """Cordillera lejana: crestas facetadas irregulares, que la niebla vuelve azuladas."""
    rng = np.random.default_rng(seed)
    m = Mesh()
    N = 34
    for i in range(N):
        a = 2 * math.pi * i / N + rng.uniform(-0.04, 0.04)
        R = rng.uniform(125, 160)
        cx, cy = math.cos(a) * R, math.sin(a) * R + 10
        h = rng.uniform(12, 26)
        w = rng.uniform(22, 34)
        pk = M.blob(w, w * 0.7, h, C("mountain"), n=10, noise=0.2, seed=i + 40, center=(cx, cy, -2),
                    flat_bottom=0, jitter=0.0)
        pk.recolor(lambda c, n, p: C("mountain", 1.15) if n[0] * -0.62 + n[1] * -0.42 + n[2] * 0.5 > 0.25
                   else C("mountain", 0.88))
        m.extend(pk.transformed(translate(cx, cy, 0) @ rot_z(a) @ translate(-cx, -cy, 0)))
    return m


class World:
    """Construye y guarda el escenario. Las coordenadas del «escenario» de
    actuación están cerca del origen, mirando a -Y (hacia la cámara)."""

    def __init__(self, r, seed=1, extra_clear=()):
        self.r = r
        self.items = []
        self.obstacles = []   # (x, y, radio) para evitar meter la cámara dentro
        rng = np.random.default_rng(seed)
        for name, img in [("grass", T.grass()), ("dirt", T.dirt()), ("stone", T.stone_wall()),
                          ("planks", T.planks()), ("planks_v", T.planks(vertical=True)), ("bark", T.bark()),
                          ("leaves", T.leaves()), ("pine", T.leaves(kind="pine")), ("roof", T.roof_tiles()),
                          ("tuft", T.grass_tuft()), ("flower_r", T.flowers(col="flower_r")),
                          ("flower_w", T.flowers(seed=12, col="flower_w")), ("flower_p", T.flowers(seed=13, col="flower_p")),
                          ("rock", T.speckle()), ("cloud", T.cloud())]:
            r.add_texture(name, img)
        I = np.eye(4)
        add = lambda m, tex, **kw: self.items.append(Item(r.upload(m), I, tex=tex, **kw))
        # terreno: interior fino + exterior grueso
        add(_terrain_grid(-26, 26, -22, 34, 0.75, seed=seed), "grass", tex2="dirt")
        outer = _terrain_grid(-150, 150, -120, 170, 6.0, drop=0.12, path=False, seed=seed + 1)
        add(outer, "grass", tex2="dirt", shadow=False)
        self.layout(rng, add, extra_clear)
        add(mountains(), "white", shadow=False, fog_k=0.62)
        # nubes: planos altos que miran a la cámara (eje -Y)
        cl = Mesh()
        for k in range(5):
            x = rng.uniform(-110, 110)
            y = rng.uniform(90, 140)
            z = rng.uniform(30, 55)
            w = rng.uniform(26, 44)
            h = w * 0.42
            cl.extend(M.decal(w, h, center=(x, y, z)))
        add(cl, "cloud", unlit=True, shadow=False, fog_k=0.35, tint=(1.02, 0.94, 0.88, 1))

    def add_interior(self):
        from . import interior
        items, obs, fire = interior.build(self.r)
        self.items += items
        self.obstacles += obs
        self.fire_items = fire
        self.has_interior = True

    def height(self, x, y):
        if getattr(self, "has_interior", False):
            from . import interior
            if interior.contains(x, y):
                return 0.0
        return float(ground_h(x, y))

    def zone(self, x, y):
        if getattr(self, "has_interior", False):
            from . import interior
            if interior.contains(x, y, margin=8.0):
                return "casa"
        return "claro"

    def free(self, x, y, clear):
        for (cx, cy, rr) in clear:
            if math.hypot(x - cx, y - cy) < rr:
                return False
        return _dist_to_path(x, y) > 2.4

    def layout(self, rng, add, extra_clear):
        H = ground_h
        bark, leaves, pine, rocks = Mesh(), Mesh(), Mesh(), Mesh()
        # zona de actuación despejada + cabaña
        clear = [(0, 0, 7.5), (-6.5, 6.5, 4.5), *extra_clear]
        # cabaña
        hx, hy = -6.6, 6.8
        parts, win = hut()
        Mh = translate(hx, hy, H(hx, hy) - 0.1) @ rot_z(0.5)
        for tex, m in parts.items():
            add(m.transformed(Mh), tex)
        add(win.transformed(Mh), "white", emissive=0.9)
        self.obstacles.append((hx, hy, 3.4))
        # farol junto al camino
        lp, glow = lantern_post()
        Ml = translate(2.6, 2.0, H(2.6, 2.0)) @ rot_z(math.pi)
        add(lp.transformed(Ml), "planks")
        add(glow.transformed(Ml), "white", emissive=1.1)
        self.obstacles.append((2.6, 2.0, 0.5))
        # muro de piedra a la derecha, detrás
        for (x, y, a, L) in [(6.5, 6.0, -0.35, 6.5), (11.6, 4.6, -0.15, 4.0)]:
            add(stone_wall(L, seed=int(x)).transformed(translate(x, y, H(x, y)) @ rot_z(a)), "stone")
            self.obstacles.append((x, y, L / 2))
        # valla a la izquierda delante
        for (x, y, a, L) in [(-6.0, -3.5, 1.2, 5.0), (-8.6, 0.8, 1.0, 4.0)]:
            add(fence(L, seed=int(-x * 10)).transformed(translate(x, y, H(x, y)) @ rot_z(a)), "planks")
        # árboles
        placed = []
        targets = [(-1.5, 12.5), (4.5, 14), (-11, 3), (10, 9), (-10.5, 12), (13, 0), (-13.5, -4), (7, 22),
                   (-4, 20), (16, 12), (-17, 8), (2, 26), (-9, 26), (19, 20), (-20, -2)]
        for k in range(30):
            if k < len(targets):
                x, y = targets[k]
            else:
                a = rng.uniform(0, 2 * math.pi)
                rr = rng.uniform(14, 34)
                x, y = math.cos(a) * rr, math.sin(a) * rr + 8
            if not self.free(x, y, clear) or any(math.hypot(x - px, y - py) < 3.2 for px, py in placed):
                continue
            placed.append((x, y))
            h = rng.uniform(0.85, 1.25)
            Mt = translate(x, y, H(x, y) - 0.05) @ rot_z(rng.uniform(0, 6.28))
            if rng.random() < 0.38 or math.hypot(x, y - 8) > 24:
                t, l = tree_pine(k, h * 1.15)
                pine.extend(l.transformed(Mt))
            else:
                t, l = tree_round(k, h)
                leaves.extend(l.transformed(Mt))
            bark.extend(t.transformed(Mt))
            self.obstacles.append((x, y, 1.6 * h))
        add(bark, "bark")
        add(leaves, "leaves")
        add(pine, "pine")
        # rocas
        for k in range(10):
            if k < 5:
                x, y = [(4.2, -2.5), (-4.5, 2.8), (5.6, 1.2), (-2.2, 9.5), (3.0, 8.4)][k]
            else:
                a = rng.uniform(0, 6.28)
                rr = rng.uniform(6, 22)
                x, y = math.cos(a) * rr, math.sin(a) * rr + 4
                if not self.free(x, y, [(0, 0, 5.5), (-6.5, 6.5, 4.0)]):
                    continue
            s = rng.uniform(0.5, 1.3) if k >= 5 else [0.9, 0.7, 0.5, 1.1, 0.6][k]
            rocks.extend(rock(k, s).transformed(translate(x, y, H(x, y)) @ rot_z(rng.uniform(0, 6.28))))
            if s > 0.7:
                self.obstacles.append((x, y, 0.7 * s))
        add(rocks, "rock")
        # matojos y flores
        tufts = {"tuft": Mesh(), "flower_r": Mesh(), "flower_w": Mesh(), "flower_p": Mesh()}
        for k in range(150):
            x = rng.uniform(-20, 20)
            y = rng.uniform(-12, 28)
            d = _dist_to_path(x, y)
            if d < 1.5 or math.hypot(x - (-6.6), y - 6.8) < 3.2:
                continue
            if math.hypot(x, y) < 1.2:
                continue
            kind = "tuft"
            rr = rng.random()
            if rr < 0.05:
                kind = "flower_r"
            elif rr < 0.08:
                kind = "flower_w"
            elif rr < 0.10:
                kind = "flower_p"
            s = rng.uniform(0.7, 1.3) * (1.15 if d < 2.6 else 1.0)
            tufts[kind].extend(tuft(k, s).transformed(translate(x, y, H(x, y) - 0.02)))
        for kind, m in tufts.items():
            add(m, kind, shadow=False, alpha_test=0.5, flip=False)
