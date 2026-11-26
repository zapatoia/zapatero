"""Matrices 4x4 (convención columna: v' = M @ v), Z arriba, mano derecha."""
import math
import numpy as np


def translate(x, y=0.0, z=0.0):
    if hasattr(x, "__len__"):
        x, y, z = x
    m = np.eye(4, dtype="f8")
    m[:3, 3] = (x, y, z)
    return m


def scale(sx, sy=None, sz=None):
    if hasattr(sx, "__len__"):
        sx, sy, sz = sx
    if sy is None:
        sy = sz = sx
    return np.diag([sx, sy, sz, 1.0])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], "f8")


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], "f8")


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "f8")


def euler(rx, ry=0.0, rz=0.0):
    """Rotación en orden Z·Y·X (primero X). Ángulos en radianes."""
    if hasattr(rx, "__len__"):
        rx, ry, rz = rx
    return rot_z(rz) @ rot_y(ry) @ rot_x(rx)


def look_at(eye, target, up=(0, 0, 1)):
    eye, target, up = (np.asarray(v, "f8") for v in (eye, target, up))
    f = target - eye
    f /= np.linalg.norm(f)
    s = np.cross(f, up)
    if np.linalg.norm(s) < 1e-6:
        s = np.cross(f, (0, 1, 0))
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = -m[:3, :3] @ eye
    return m


def perspective(fov_y, aspect, near, far):
    t = 1.0 / math.tan(fov_y / 2)
    return np.array([[t / aspect, 0, 0, 0], [0, t, 0, 0],
                     [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
                     [0, 0, -1, 0]], "f8")


def ortho(l, r, b, t, n, f):
    m = np.eye(4)
    m[0, 0], m[1, 1], m[2, 2] = 2 / (r - l), 2 / (t - b), -2 / (f - n)
    m[0, 3], m[1, 3], m[2, 3] = -(r + l) / (r - l), -(t + b) / (t - b), -(f + n) / (f - n)
    return m


def normalize(v):
    v = np.asarray(v, "f8")
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))
