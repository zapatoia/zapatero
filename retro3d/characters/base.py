"""Personaje genérico: acciones con fundido, capas aditivas y cara por texturas.

Pose = dict:  "nodo" -> rotación (rx, ry, rz) en radianes
              "nodo.p" -> traslación extra, "nodo.s" -> escala
              "eyes" / "mouth" -> estado de textura (discreto)
"""
import math
import numpy as np

from ..rig import Rig
from ..anim import EASE, seg

FACE_KEYS = ("eyes", "mouth")


def blend(a, b, w):
    """Mezcla lineal de dos poses (w=0 → a, w=1 → b)."""
    out = {}
    for k in set(a) | set(b):
        if k in FACE_KEYS:
            out[k] = b.get(k, a.get(k)) if w >= 0.5 else a.get(k, b.get(k))
            continue
        d = np.ones(3) if k.endswith(".s") else np.zeros(3)
        va = np.asarray(a.get(k, d), "f8")
        vb = np.asarray(b.get(k, d), "f8")
        out[k] = va + (vb - va) * w
    return out


def add(base, extra):
    out = dict(base)
    for k, v in extra.items():
        if k in FACE_KEYS:
            if v is not None:
                out[k] = v
            continue
        if k.endswith(".s"):
            out[k] = np.asarray(out.get(k, np.ones(3)), "f8") * np.asarray(v, "f8")
        else:
            out[k] = np.asarray(out.get(k, np.zeros(3)), "f8") + np.asarray(v, "f8")
    return out


class Character(Rig):
    FADE = 0.28

    def __init__(self, root):
        super().__init__(root)
        self.timeline = []        # [(t0, accion, params)]
        self.springs = {}
        self._last_t = None
        self.place = (0.0, 0.0, 0.0, 0.0)   # x, y, z, yaw por defecto
        self.place_fn = None        # t -> (x, y, z, yaw)
        self.face_override = None   # t -> dict con eyes/mouth
        self.layers = []            # funciones t -> pose aditiva

    # ------------------------------------------------------- programación
    def play(self, t0, action, **params):
        self.timeline.append((t0, action, params))
        self.timeline.sort(key=lambda x: x[0])
        return self

    def _active(self, t):
        cur, prev = None, None
        for e in self.timeline:
            if e[0] <= t:
                prev, cur = cur, e
        return cur, prev

    def action_pose(self, name, lt, params, t):
        fn = getattr(self, "act_" + name)
        return fn(lt, t=t, **params)

    def pose_at(self, t):
        cur, prev = self._active(t)
        if cur is None:
            return self.act_idle(t, t=t)
        p_cur = self.action_pose(cur[1], t - cur[0], cur[2], t)
        fade = cur[2].get("fade", self.FADE)
        if prev is not None and t - cur[0] < fade:
            p_prev = self.action_pose(prev[1], t - prev[0], prev[2], t)
            w = EASE["inout"](seg(t, cur[0], cur[0] + fade))
            p_cur = blend(p_prev, p_cur, w)
        for layer in self.layers:
            p_cur = add(p_cur, layer(t, p_cur))
        return p_cur

    # ------------------------------------------------------- aplicación
    def update(self, t, dt=1 / 30):
        if self._last_t is None or t < self._last_t or t - self._last_t > 0.5:
            # pre-simular muelles para que no arranquen en frío
            self._last_t = None
            for s in self.springs.values():
                s.v[...] = 0
            pre = t - 1.0
            while pre < t - 1e-6:
                self._apply(pre, dt, springs_only=True)
                pre += dt
        self._apply(t, dt)
        self._last_t = t

    def _apply(self, t, dt, springs_only=False):
        pose = self.pose_at(t)
        pose = self.secondary(t, dt, pose)
        if springs_only:
            return
        self.reset_pose()
        for k, v in pose.items():
            if k in FACE_KEYS:
                continue
            if k.endswith(".p"):
                self.nodes[k[:-2]].pos = np.asarray(v, "f8")
            elif k.endswith(".s"):
                self.nodes[k[:-2]].scl = np.asarray(v, "f8")
            elif k in self.nodes:
                self.nodes[k].rot = np.asarray(v, "f8")
        face = {"eyes": pose.get("eyes", "open"), "mouth": pose.get("mouth", "X")}
        if self.face_override:
            o = self.face_override(t, face)
            if o:
                face.update({k: v for k, v in o.items() if v})
        self.decal_state.update(face)
        x, y, z, yaw = self.place_fn(t) if self.place_fn else self.place
        from ..mathutil import translate, rot_z
        self.transform = translate(x, y, z) @ rot_z(yaw)
        self.cur_pose = pose

    def secondary(self, t, dt, pose):
        return pose

    def act_idle(self, lt, t=0, **kw):
        return {}
