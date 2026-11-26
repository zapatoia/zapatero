"""Contactos y colisiones (regla fija del pipeline).

- Volúmenes de colisión simplificados: una caja orientada (OBB) por pieza de cada nodo.
- Interpenetraciones: prueba de ejes separadores (SAT) con prefiltro de esferas;
  entre personajes y dentro de cada personaje (pares no adyacentes).
- Apoyo en el suelo: el pie más bajo toca el suelo (sin flotar ni hundirse), salvo en el aire.
- Contacto lengua-superficie: la lengua apunta a un punto de la superficie objetivo y se
  detiene en ella (margen pequeño, ligero aplastamiento); si la cabeza invade el objetivo, retrocede.
"""
import math
import numpy as np

TOL = 0.02           # penetración tolerada (las cajas son algo mayores que las formas biseladas)


class OBB:
    __slots__ = ("c", "R", "h", "r", "owner", "node")

    def __init__(self, c, R, h, owner, node):
        self.c, self.R, self.h, self.owner, self.node = c, R, h, owner, node
        self.r = float(np.linalg.norm(h))

    def corners(self):
        s = np.array([[i, j, k] for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)], "f8")
        return self.c + (s * self.h) @ self.R.T


def rig_obbs(rig, owner, skip=()):
    """OBBs en el mundo de todas las piezas de un rig (tras update)."""
    mats = rig.world_matrices()
    out = []
    for name, node in rig.nodes.items():
        if name in skip:
            continue
        M = mats[name]
        A = M[:3, :3]
        sc = np.linalg.norm(A, axis=0)
        R = A / np.where(sc > 1e-9, sc, 1)
        for (mn, mx) in node.parts:
            cl = (mn + mx) / 2
            h = (mx - mn) / 2 * sc
            c = M[:3, :3] @ cl + M[:3, 3]
            out.append(OBB(c, R, np.maximum(h, 1e-4), owner, name))
    return out


def sat_depth(a, b):
    """Penetración mínima entre dos OBB (0 si están separadas)."""
    d = b.c - a.c
    axes = [a.R[:, i] for i in range(3)] + [b.R[:, i] for i in range(3)]
    for i in range(3):
        for j in range(3):
            v = np.cross(a.R[:, i], b.R[:, j])
            n = np.linalg.norm(v)
            if n > 1e-6:
                axes.append(v / n)
    best = 1e9
    for ax in axes:
        ra = np.sum(a.h * np.abs(a.R.T @ ax))
        rb = np.sum(b.h * np.abs(b.R.T @ ax))
        ov = ra + rb - abs(d @ ax)
        if ov <= 0:
            return 0.0
        best = min(best, ov)
    return best


def penetrations(groups, pairs_ok, tol=TOL):
    """groups: lista de listas de OBB. pairs_ok(a, b) decide si el par se comprueba.
    Devuelve [(a, b, profundidad)] con profundidad > tol."""
    allb = [o for g in groups for o in g]
    hits = []
    n = len(allb)
    C = np.array([o.c for o in allb])
    Rr = np.array([o.r for o in allb])
    for i in range(n):
        dd = np.linalg.norm(C[i + 1:] - C[i], axis=1)
        cand = np.nonzero(dd < Rr[i + 1:] + Rr[i])[0] + i + 1
        for j in cand:
            a, b = allb[i], allb[j]
            if not pairs_ok(a, b):
                continue
            dep = sat_depth(a, b)
            if dep > tol:
                hits.append((a, b, dep))
    return hits


def make_pair_filter(rigs):
    """Pares a comprobar: entre personajes distintos siempre; dentro de un personaje,
    solo nodos no adyacentes (ni padre-hijo ni de un mismo grupo articulado)."""
    parent = {}
    groups = {}
    for owner, rig in rigs.items():
        def rec(n, p=None):
            parent[(owner, n.name)] = p
            for c in n.children:
                rec(c, n.name)
        rec(rig.root)
        groups[owner] = getattr(rig, "COLLISION_GROUPS", [])

    def same_group(owner, a, b):
        for g in groups[owner]:
            if a in g and b in g:
                return True
        return False

    def ok(a, b):
        if a.owner != b.owner:
            return True
        if a.node == b.node:
            return False
        o = a.owner
        if parent.get((o, a.node)) == b.node or parent.get((o, b.node)) == a.node:
            return False
        if parent.get((o, a.node)) == parent.get((o, b.node)) and same_group(o, a.node, b.node):
            return False
        return not same_group(o, a.node, b.node)
    return ok


# ---------------------------------------------------------------- suelo

def lowest(rig, nodes):
    mats = rig.world_matrices()
    z = 1e9
    for name in nodes:
        node = rig.nodes[name]
        M = mats[name]
        for (mn, mx) in node.parts:
            for x in (mn[0], mx[0]):
                for y in (mn[1], mx[1]):
                    for zz in (mn[2], mx[2]):
                        z = min(z, (M @ np.array([x, y, zz, 1.0]))[2])
    return z


def ground_snap(rig, feet, ground_z, airborne=False):
    """Ajusta la altura del rig para que el pie más bajo toque el suelo.
    En el aire solo impide que se hunda. Devuelve la corrección aplicada."""
    z = lowest(rig, feet)
    dz = ground_z - z
    if airborne and dz < 0:
        return 0.0
    rig.transform = rig.transform.copy()
    rig.transform[2, 3] += dz
    return dz


# ---------------------------------------------------------------- contacto lengua → superficie

def ray_obb(o, d, box):
    """Distancia a lo largo del rayo (o + s·d) hasta entrar en la OBB (None si no la toca)."""
    lo = box.R.T @ (o - box.c)
    ld = box.R.T @ d
    tmin, tmax = -1e9, 1e9
    for i in range(3):
        if abs(ld[i]) < 1e-9:
            if abs(lo[i]) > box.h[i]:
                return None
            continue
        t1 = (-box.h[i] - lo[i]) / ld[i]
        t2 = (box.h[i] - lo[i]) / ld[i]
        t1, t2 = min(t1, t2), max(t1, t2)
        tmin, tmax = max(tmin, t1), min(tmax, t2)
    if tmax < max(tmin, 0):
        return None
    return max(tmin, 0.0)


def closest_on_obb(p, box):
    lp = box.R.T @ (p - box.c)
    lp = np.clip(lp, -box.h, box.h)
    return box.c + box.R @ lp


def solve_lick(dog, target_boxes, out_amount, margin=0.003, max_len=0.3, push_back=True, ground_z=0.0):
    """Hace que la lengua del perro apunte a la superficie objetivo y se detenga en ella.

    dog: rig del perro ya actualizado; target_boxes: OBBs de la superficie (mano o pata).
    out_amount (0..1): fase de extensión de la animación de lamer.
    Devuelve dict con distancia de contacto y si hay contacto."""
    info = {"contact": False, "gap": None, "retreat": 0.0}
    if not target_boxes:
        return info
    # 1) la cabeza (hocico, mandíbula) nunca invade el objetivo: retroceder a lo largo de la mirada
    head_nodes = ("head", "jaw", "neck")
    for it in range(12 if push_back else 0):
        hb = [o for o in rig_obbs(dog, "dog") if o.node in head_nodes]
        dep = max((sat_depth(a, b) for a in hb for b in target_boxes), default=0.0)
        if dep <= 0.002:
            break
        yaw = math.atan2(-dog.transform[0, 1], dog.transform[1, 1])
        back = np.array([-math.sin(yaw), math.cos(yaw), 0.0])  # -frente del perro
        step = min(0.03, dep + 0.004)
        dog.transform = dog.transform.copy()
        dog.transform[:3, 3] += back * step
        info["retreat"] += step
    # 2) apuntar la lengua al punto más cercano de la superficie
    mats = dog.world_matrices()
    Mj = mats["jaw"]
    tn = dog.nodes["tongue"]
    base = (Mj @ np.array([*(tn.offset + tn.pos), 1.0]))[:3]
    tgt = min((closest_on_obb(base, b) for b in target_boxes), key=lambda q: np.linalg.norm(q - base))
    v = tgt - base
    dist = np.linalg.norm(v)
    if dist < 1e-6:
        return info
    # dirección deseada en el espacio local de la mandíbula
    lv = np.linalg.inv(Mj[:3, :3]) @ (v / dist)
    lv /= np.linalg.norm(lv)
    # la lengua apunta a -Y local: rx inclina en Y-Z, rz gira en X-Y
    rx = math.atan2(-lv[2], -lv[1])
    rz = math.atan2(lv[0], max(1e-6, math.hypot(lv[1], lv[2])))
    rx = max(-0.9, min(0.9, rx))
    rz = max(-0.6, min(0.6, rz))
    k = out_amount
    tn.rot = np.array([rx * min(1.0, k * 2), 0.0, rz * min(1.0, k * 2)])
    tn.pos = np.array([0.0, -0.03 * k, -0.01])
    # 3) longitud: la punta se detiene en la superficie (rayo contra las cajas objetivo)
    mats = dog.world_matrices()
    Mt = mats["tongue"]
    d = -Mt[:3, 1] / np.linalg.norm(Mt[:3, 1])
    ax = Mt[:3, 0] / np.linalg.norm(Mt[:3, 0])
    az_ = Mt[:3, 2] / np.linalg.norm(Mt[:3, 2])
    hits = []
    # 5 rayos: centro y bordes de la lengua (ancho 9,5 cm, grosor 2,2 cm)
    for ox, oz in ((0, 0), (0.045, 0), (-0.045, 0), (0, 0.011), (0, -0.011)):
        o = Mt[:3, 3] + ax * ox * np.linalg.norm(Mt[:3, 0]) + az_ * oz
        hits += [s for s in (ray_obb(o, d, b) for b in target_boxes) if s is not None]
    rest_len = 0.15
    free = rest_len * (0.3 + 1.6 * k)            # extensión libre de la animación
    if hits:
        s = max(0.0, min(hits) - margin)
        L = min(free, s, max_len)                 # se detiene en la superficie
        touching = free >= s and s <= max_len
    else:
        L = min(free, max_len * 0.7)
        touching = False
    sy = max(0.05, L / rest_len)
    squash = 1.0 + (0.18 if touching else 0.0)
    tn.scl = np.array([squash, sy, 1 / squash])
    info.update(contact=bool(touching), gap=float(min(hits) - L) if hits else None)
    return info


def _depth(rig, owner, movers, blockers):
    obs = rig_obbs(rig, owner)
    A = [o for o in obs if o.node in movers]
    B = [o for o in obs if o.node in blockers]
    dep = 0.0
    for a in A:
        for b in B:
            if np.linalg.norm(a.c - b.c) < a.r + b.r:
                dep = max(dep, sat_depth(a, b))
    return dep


def resolve_self(rig, owner, movers, blockers, joint, steps, max_iter=24, tol=0.004):
    """Restricción de no-interpenetración dentro de un personaje (búsqueda codiciosa):
    mientras `movers` invada `blockers`, prueba cada paso candidato de la articulación
    `joint` y aplica el que más reduce la penetración. Devuelve nº de pasos aplicados."""
    steps = [np.asarray(s_, "f8") for s_ in (steps if np.ndim(steps) == 2 else [steps])]
    node = rig.nodes[joint]
    dep = _depth(rig, owner, movers, blockers)
    n = 0
    while dep > tol and n < max_iter:
        base = node.rot.copy()
        best = (dep, None)
        for st in steps:
            node.rot = base + st
            d = _depth(rig, owner, movers, blockers)
            if d < best[0] - 1e-4:
                best = (d, st)
        if best[1] is None:
            node.rot = base
            break
        node.rot = base + best[1]
        dep = best[0]
        n += 1
    return n
