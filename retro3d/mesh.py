"""Geometría low-poly: sopa de triángulos con normales planas, UV y color por vértice.

Todo se construye por código. Las formas facetadas (cabezas, rocas, copas de
árbol) se obtienen como envolvente convexa de una nube de puntos: así cada cara
es un plano limpio y el sombreado plano da el aspecto «tallado» típico de 2003.
"""
import math
import numpy as np
from scipy.spatial import ConvexHull

from .mathutil import normalize

_rng = np.random.default_rng(7)


def hexcol(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def as_col(c):
    if isinstance(c, str):
        return hexcol(c)
    c = tuple(c)
    return c if len(c) == 4 else (*c, 1.0)


class Mesh:
    """Triángulos sueltos. Atributos por vértice: pos3 nrm3 uv2 col4."""

    def __init__(self):
        self.p, self.n, self.uv, self.c = [], [], [], []

    # -- construcción ------------------------------------------------------
    def tri(self, a, b, c, col, uvs=None, uv_scale=1.0, jitter=0.0):
        a, b, c = (np.asarray(v, "f8") for v in (a, b, c))
        nrm = np.cross(b - a, c - a)
        ln = np.linalg.norm(nrm)
        if ln < 1e-12:
            return
        nrm /= ln
        col = as_col(col)
        if jitter:
            j = 1.0 + _rng.uniform(-jitter, jitter)
            col = (min(col[0] * j, 1), min(col[1] * j, 1), min(col[2] * j, 1), col[3])
        if uvs is None:
            uvs = [box_uv(v, nrm, uv_scale) for v in (a, b, c)]
        for v, t in zip((a, b, c), uvs):
            self.p.append(v)
            self.n.append(nrm)
            self.uv.append(t)
            self.c.append(col)

    def quad(self, a, b, c, d, col, uvs=None, **kw):
        if uvs is None:
            self.tri(a, b, c, col, **kw)
            self.tri(a, c, d, col, **kw)
        else:
            self.tri(a, b, c, col, uvs=[uvs[0], uvs[1], uvs[2]], **kw)
            self.tri(a, c, d, col, uvs=[uvs[0], uvs[2], uvs[3]], **kw)

    def extend(self, other):
        self.p += other.p
        self.n += other.n
        self.uv += other.uv
        self.c += other.c
        return self

    def transformed(self, M):
        m = Mesh()
        if not self.p:
            return m
        P = np.asarray(self.p)
        N = np.asarray(self.n)
        P = P @ M[:3, :3].T + M[:3, 3]
        nm = np.linalg.inv(M[:3, :3]).T
        N = N @ nm.T
        N /= np.linalg.norm(N, axis=1, keepdims=True)
        if np.linalg.det(M[:3, :3]) < 0:  # espejo: invertir orden de vértices
            P = P.reshape(-1, 3, 3)[:, ::-1].reshape(-1, 3)
            N = N.reshape(-1, 3, 3)[:, ::-1].reshape(-1, 3)
            uv = np.asarray(self.uv).reshape(-1, 3, 2)[:, ::-1].reshape(-1, 2)
            c = np.asarray(self.c).reshape(-1, 3, 4)[:, ::-1].reshape(-1, 4)
            m.uv, m.c = list(uv), list(c)
        else:
            m.uv, m.c = list(self.uv), list(self.c)
        m.p, m.n = list(P), list(N)
        return m

    def recolor(self, fn):
        """fn(color, normal, pos) -> color, aplicado por triángulo."""
        for i in range(0, len(self.p), 3):
            ctr = (self.p[i] + self.p[i + 1] + self.p[i + 2]) / 3
            nc = as_col(fn(self.c[i], self.n[i], ctr))
            self.c[i] = self.c[i + 1] = self.c[i + 2] = nc
        return self

    @property
    def tris(self):
        return len(self.p) // 3

    def arrays(self):
        """Array intercalado float32 (N, 12)."""
        if not self.p:
            return np.zeros((0, 12), "f4")
        return np.hstack([np.asarray(self.p), np.asarray(self.n), np.asarray(self.uv),
                          np.asarray(self.c)]).astype("f4")

    def bounds(self):
        P = np.asarray(self.p)
        return P.min(0), P.max(0)


def box_uv(v, n, s):
    ax = np.argmax(np.abs(n))
    if ax == 2:
        return (v[0] * s, v[1] * s)
    if ax == 0:
        return (v[1] * s, v[2] * s)
    return (v[0] * s, v[2] * s)


# ---------------------------------------------------------------- primitivas

def hull(points, col, uv_scale=1.0, jitter=0.03, color_fn=None):
    """Envolvente convexa facetada de una nube de puntos."""
    pts = np.asarray(points, "f8")
    h = ConvexHull(pts)
    m = Mesh()
    ctr = pts.mean(0)
    for simp, eq in zip(h.simplices, h.equations):
        a, b, c = pts[simp]
        if np.dot(np.cross(b - a, c - a), eq[:3]) < 0:
            b, c = c, b
        cc = col
        if color_fn is not None:
            cc = color_fn(eq[:3], (a + b + c) / 3 - ctr)
        m.tri(a, b, c, cc, uv_scale=uv_scale, jitter=jitter)
    return m


def box(sx, sy, sz, col, center=(0, 0, 0), bevel=0.0, taper=(1.0, 1.0), shift_top=(0, 0),
        uv_scale=1.0, jitter=0.03, color_fn=None, bottom_taper=(1.0, 1.0)):
    """Caja (opcionalmente biselada y con la tapa superior estrechada)."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    pts = []
    b = bevel
    for zs in (-1, 1):
        tx, ty = taper if zs > 0 else bottom_taper
        ox, oy = shift_top if zs > 0 else (0, 0)
        for xs in (-1, 1):
            for ys in (-1, 1):
                if b > 0:
                    pts += [
                        (xs * (hx - b) * tx + ox, ys * hy * ty + oy, zs * (hz - b)),
                        (xs * hx * tx + ox, ys * (hy - b) * ty + oy, zs * (hz - b)),
                        (xs * (hx - b) * tx + ox, ys * (hy - b) * ty + oy, zs * hz),
                    ]
                else:
                    pts.append((xs * hx * tx + ox, ys * hy * ty + oy, zs * hz))
    pts = np.asarray(pts) + np.asarray(center)
    return hull(pts, col, uv_scale, jitter, color_fn)


def cylinder(r0, r1, h, segs, col, center=(0, 0, 0), caps=True, uv_scale=1.0, jitter=0.03,
             rot=0.0, cap_col=None, sx=1.0, sy=1.0):
    m = Mesh()
    cx, cy, cz = center
    ring = [(math.cos(rot + 2 * math.pi * i / segs), math.sin(rot + 2 * math.pi * i / segs))
            for i in range(segs)]
    z0, z1 = cz - h / 2, cz + h / 2
    for i in range(segs):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % segs]
        p0 = (cx + ax * r0 * sx, cy + ay * r0 * sy, z0)
        p1 = (cx + bx * r0 * sx, cy + by * r0 * sy, z0)
        p2 = (cx + bx * r1 * sx, cy + by * r1 * sy, z1)
        p3 = (cx + ax * r1 * sx, cy + ay * r1 * sy, z1)
        u0, u1 = i / segs * 2, (i + 1) / segs * 2
        m.quad(p0, p1, p2, p3, col, uvs=[(u0, 0), (u1, 0), (u1, h * uv_scale), (u0, h * uv_scale)],
               jitter=jitter)
        if caps:
            cc = cap_col or col
            if r1 > 0:
                m.tri((cx, cy, z1), p3, p2, cc, uv_scale=uv_scale)
            if r0 > 0:
                m.tri((cx, cy, z0), p1, p0, cc, uv_scale=uv_scale)
    return m


def ellipsoid_points(rx, ry, rz, n=24, noise=0.0, seed=0, flat_bottom=None):
    rng = np.random.default_rng(seed)
    # puntos casi uniformes (espiral de Fibonacci) + ruido -> facetas irregulares
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    d = np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)
    d *= (1 + rng.uniform(-noise, noise, (n, 1)))
    pts = d * (rx, ry, rz)
    if flat_bottom is not None:
        pts[:, 2] = np.maximum(pts[:, 2], flat_bottom)
    return pts


def blob(rx, ry, rz, col, n=24, noise=0.15, seed=0, center=(0, 0, 0), jitter=0.05,
         color_fn=None, flat_bottom=None, uv_scale=1.0):
    pts = ellipsoid_points(rx, ry, rz, n, noise, seed, flat_bottom) + np.asarray(center)
    return hull(pts, col, uv_scale=uv_scale, jitter=jitter, color_fn=color_fn)


def decal(w, h, center=(0, 0, 0), col=(1, 1, 1, 1), uv_rect=(0, 0, 1, 1), axis="y"):
    """Rectángulo plano orientado hacia -Y (frente del personaje) con UV explícitas."""
    m = Mesh()
    cx, cy, cz = center
    u0, v0, u1, v1 = uv_rect
    if axis == "y":  # mira hacia -Y
        a = (cx - w / 2, cy, cz - h / 2)
        b = (cx + w / 2, cy, cz - h / 2)
        c = (cx + w / 2, cy, cz + h / 2)
        d = (cx - w / 2, cy, cz + h / 2)
    else:  # mira hacia +Z
        a = (cx - w / 2, cy - h / 2, cz)
        b = (cx + w / 2, cy - h / 2, cz)
        c = (cx + w / 2, cy + h / 2, cz)
        d = (cx - w / 2, cy + h / 2, cz)
    m.quad(a, b, c, d, col, uvs=[(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    return m


def _ear_clip(poly):
    pts = [np.asarray(p, "f8") for p in poly]
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    idx = list(range(len(pts)))
    if area < 0:
        idx.reverse()
    tris = []

    def inside(p, a, b, c):
        def s(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12:
                continue
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return pts, tris


def extrude(poly, depth, col, side_col=None, bevel=0.0, jitter=0.02):
    """Extruye un polígono 2D (plano XZ) a lo largo de Y. Cara frontal mira a -Y."""
    pts, tris = _ear_clip(poly)
    m = Mesh()
    side_col = side_col or col
    y0, y1 = -depth / 2, depth / 2
    # escala para el bisel: la cara frontal un poco más pequeña
    ctr = np.mean(pts, 0)
    inner = [ctr + (p - ctr) * (1 - bevel) for p in pts] if bevel else pts
    for a, b, c in tris:
        A, B, C = inner[a], inner[b], inner[c]
        m.tri((A[0], y0, A[1]), (C[0], y0, C[1]), (B[0], y0, B[1]), col, jitter=0)
        m.tri((A[0], y1, A[1]), (B[0], y1, B[1]), (C[0], y1, C[1]), col, jitter=0)
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    order = range(n) if area > 0 else range(n - 1, -1, -1)
    order = list(order)
    for k in range(n):
        i, j = order[k], order[(k + 1) % n]
        p, q = pts[i], pts[j]
        if bevel:
            pi, qi = inner[i], inner[j]
            ym0, ym1 = y0 + depth * 0.18, y1 - depth * 0.18
            m.quad((p[0], ym0, p[1]), (q[0], ym0, q[1]), (q[0], ym1, q[1]), (p[0], ym1, p[1]),
                   side_col, jitter=jitter)
            m.quad((pi[0], y0, pi[1]), (qi[0], y0, qi[1]), (q[0], ym0, q[1]), (p[0], ym0, p[1]),
                   side_col, jitter=jitter)
            m.quad((p[0], ym1, p[1]), (q[0], ym1, q[1]), (qi[0], y1, qi[1]), (pi[0], y1, pi[1]),
                   side_col, jitter=jitter)
        else:
            m.quad((p[0], y0, p[1]), (q[0], y0, q[1]), (q[0], y1, q[1]), (p[0], y1, p[1]),
                   side_col, jitter=jitter)
    return m


def voxels(rows, cell, depth, col, side_col=None, center=True):
    """Bitmap (lista de strings, '#' = lleno) extruido en cubos, sin caras internas.
    Plano XZ, cara frontal hacia -Y."""
    side_col = side_col or col
    H = len(rows)
    W = max(len(r) for r in rows)
    filled = {(x, H - 1 - y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "#"}
    ox = -W * cell / 2 if center else 0
    oz = -H * cell / 2 if center else 0
    m = Mesh()
    y0, y1 = -depth / 2, depth / 2
    for (x, z) in filled:
        X0, X1 = ox + x * cell, ox + (x + 1) * cell
        Z0, Z1 = oz + z * cell, oz + (z + 1) * cell
        m.quad((X0, y0, Z0), (X1, y0, Z0), (X1, y0, Z1), (X0, y0, Z1), col, jitter=0)
        m.quad((X1, y1, Z0), (X0, y1, Z0), (X0, y1, Z1), (X1, y1, Z1), col, jitter=0)
        if (x - 1, z) not in filled:
            m.quad((X0, y1, Z0), (X0, y0, Z0), (X0, y0, Z1), (X0, y1, Z1), side_col, jitter=0)
        if (x + 1, z) not in filled:
            m.quad((X1, y0, Z0), (X1, y1, Z0), (X1, y1, Z1), (X1, y0, Z1), side_col, jitter=0)
        if (x, z - 1) not in filled:
            m.quad((X0, y1, Z0), (X1, y1, Z0), (X1, y0, Z0), (X0, y0, Z0), side_col, jitter=0)
        if (x, z + 1) not in filled:
            m.quad((X0, y0, Z1), (X1, y0, Z1), (X1, y1, Z1), (X0, y1, Z1), side_col, jitter=0)
    return m


def merge(*meshes):
    m = Mesh()
    for x in meshes:
        m.extend(x)
    return m


def shade_top(top_col, side_col, threshold=0.55):
    """color_fn: caras que miran arriba con top_col (musgo, nieve, hierba)."""
    def fn(n, rel):
        return top_col if n[2] > threshold else side_col
    return fn
