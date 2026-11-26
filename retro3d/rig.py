"""Jerarquía de huesos rígidos (segmentos), como los modelos de principios de los 2000.

Cada Node tiene una posición de reposo relativa a su padre (el pivote de la
articulación), y en cada fotograma recibe rotación/traslación/escala de pose.
Las mallas se cuelgan de los nodos en coordenadas locales del pivote.
"""
import numpy as np

from .mathutil import translate, euler, scale
from .mesh import Mesh
from .render import Item


class Node:
    def __init__(self, name, offset=(0, 0, 0)):
        self.name = name
        self.offset = np.asarray(offset, "f8")
        self.children = []
        self.meshes = {}       # tex -> Mesh (CPU, antes de subir)
        self.gpu = []          # (GPUMesh, tex, opts)
        self.decals = []       # (GPUMesh, tex, key) uvrect dinámico
        self.reset()

    def reset(self):
        self.rot = np.zeros(3)
        self.pos = np.zeros(3)
        self.scl = np.ones(3)

    def add(self, child):
        self.children.append(child)
        return child

    def attach(self, mesh, tex="white"):
        self.meshes.setdefault(tex, Mesh()).extend(mesh)
        return self

    def local(self):
        return translate(self.offset + self.pos) @ euler(self.rot) @ scale(self.scl)


class Rig:
    """Conjunto de nodos con nombre. Subclases: personajes."""

    def __init__(self, root):
        self.root = root
        self.nodes = {}
        self._index(root)
        self.decal_state = {}
        self.decal_uv = {}
        self.transform = np.eye(4)   # colocación en el mundo
        self.tint = (1, 1, 1, 1)

    def _index(self, n):
        self.nodes[n.name] = n
        for c in n.children:
            self._index(c)

    def __getitem__(self, k):
        return self.nodes[k]

    def upload(self, r, opts=None):
        opts = opts or {}
        for n in self.nodes.values():
            for tex, m in n.meshes.items():
                if m.tris:
                    n.gpu.append((r.upload(m), tex, opts.get(tex, {})))
            n.meshes = {}
        for n in self.nodes.values():
            n.decals = [(r.upload(m), tex, key) for (m, tex, key) in n.decals]

    def tri_count(self):
        t = 0
        for n in self.nodes.values():
            t += sum(g.tris for g, _, _ in n.gpu)
            t += sum(g.tris for g, _, _ in n.decals)
        return t

    def reset_pose(self):
        for n in self.nodes.values():
            n.reset()

    def world_matrices(self):
        out = {}

        def rec(n, M):
            W = M @ n.local()
            out[n.name] = W
            for c in n.children:
                rec(c, W)
        rec(self.root, self.transform)
        return out

    def items(self):
        mats = self.world_matrices()
        res = []
        for name, n in self.nodes.items():
            M = mats[name]
            for gm, tex, o in n.gpu:
                res.append(Item(gm, M, tex=tex, tint=self.tint, **o))
            for gm, tex, key in n.decals:
                st = self.decal_state.get(key)
                uv = self.decal_uv.get(f"{key}_{st}", (0, 0, 1, 1))
                res.append(Item(gm, M, tex=tex, uvrect=uv, alpha_test=0.5, shadow=False, tint=self.tint))
        return res

    def point(self, node, local=(0, 0, 0)):
        """Posición en el mundo de un punto local a un nodo."""
        M = self.world_matrices()[node]
        return (M @ np.array([*local, 1.0]))[:3]
