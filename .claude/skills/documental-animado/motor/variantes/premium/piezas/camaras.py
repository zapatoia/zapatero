"""MOVIMIENTOS DE CÁMARA del estilo premium. Cada preset da la pose (ojo, mira, roll) RELATIVA a la estación de la escena
para un avance u ∈ [0, 1] de la escena. Las transiciones entre escenas (vuelo con desenfoque de movimiento) las hace el motor.

Para añadir uno: función preset(u, e) → (ojo, mira, roll) + entrada en CAMARAS + línea en LEEME.md.
`e` es el diccionario de la escena (spec) por si el preset necesita datos (p. ej. separación de tarjetas).
"""
import math
import numpy as np


def _io(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def _l(a, b, u): return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * u


def acercar(u, e):
    """Empuje lento hacia el protagonista con leve giro (lo más habitual)."""
    v = _io(u); D = e.get("dist", 2250)
    return _l((-150, 110, -D - 650), (70, 20, -D), v), _l((0, 50, 0), (0, 0, 0), v), -3 + 5 * v


def orbita(u, e):
    """Gira alrededor del protagonista (−28° → +22°)."""
    v = _io(u); D = e.get("dist", 2300); a = math.radians(-28 + 50 * v)
    return np.array([D * math.sin(a), 150 - 90 * v, -D * math.cos(a)]), np.array([0, 0, 0.0]), 2 - 4 * v


def lateral(u, e):
    """Travelling lateral de izquierda a derecha (para comparar dos o más elementos)."""
    v = _io(u); s = e.get("sep", 400); D = e.get("dist", 2350)
    return np.array([-s + 2 * s * v, 60, -D]), np.array([-s * .85 + 2 * s * .85 * v, 0, 0.0]), -2 + 4 * v


def grua(u, e):
    """Sube y se aleja para revelar desde arriba (apilados, mapas, conjuntos)."""
    v = _io(u)
    return _l((-600, 900, -2700), (-1000, 2400, -2500), v), _l((0, 150, 0), (60, 20, 0), v), 0.0


def picado(u, e):
    """Desde arriba bajando (entrada solemne)."""
    v = _io(u); D = e.get("dist", 2300)
    return _l((0, 1500, -D * .7), (0, 260, -D), v), np.array([0, 0, 0.0]), 0.0


def entrada(u, e):
    """Arranque de vídeo: viene de muy lejos con empuje rápido que frena (gancho)."""
    v = 1 - (1 - min(max(u * 1.6, 0), 1)) ** 3; D = e.get("dist", 2300)
    return _l((-250, 260, -D - 2600), (40, 30, -D), v), _l((0, 120, 0), (0, 0, 0), v), -6 + 6 * v


CAMARAS = dict(acercar=acercar, orbita=orbita, lateral=lateral, grua=grua, picado=picado, entrada=entrada)
