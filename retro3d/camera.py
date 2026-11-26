"""Cámara dinámica: repertorio de planos definidos por beat en el guion JSON.

Tipos (`type`):
  establish  plano de situación lejano y picado → empuje rápido al sujeto (easeInOut fuerte)
  orbit      órbita alrededor del sujeto (`deg`: 180 por defecto, 360 posible, signo = sentido)
  crane      grúa que sube (`rise` > 0) o baja (`rise` < 0) en grados de elevación
  truck      travelling lateral (`move` metros, signo = sentido), con paralaje
  low        contrapicado (cámara baja mirando hacia arriba) para dar énfasis
  push/pull  empuje / alejamiento
Tamaños (`size`): wide (general), medium (medio), close (primer plano).
Transición (`transition`: "whip"): barrido rápido de entrada con desenfoque de movimiento.
Golpes de zoom: `zoom` (lista de anclas) en el plano o en el segmento.
"""
import math
import numpy as np

from .anim import EASE, seg, noise1


def ease_in_out_quart(t):
    return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2


EASE.setdefault("inout4", ease_in_out_quart)

# distancia por tamaño de plano y tipo de sujeto (formato vertical 9:16, fov 38-42)
SIZES = {
    "narr": {"wide": 6.5, "medium": 3.2, "close": 2.25},
    "dog": {"wide": 5.5, "medium": 2.8, "close": 2.05},
    "two": {"wide": 7.0, "medium": 4.3, "close": 3.3},
    "group": {"wide": 6.0, "medium": 3.3, "close": 2.4},
    "point": {"wide": 6.5, "medium": 3.8, "close": 2.6},
}
HEIGHTS = {"narr": {"wide": 1.0, "medium": 1.25, "close": 1.42}, "dog": {"wide": 0.5, "medium": 0.6, "close": 0.62},
           "two": {"wide": 0.9, "medium": 0.95, "close": 1.0}, "group": {"wide": 0.5, "medium": 0.5, "close": 0.55},
           "point": {"wide": 1.0, "medium": 1.0, "close": 1.0}}
TYPES = ("establish", "orbit", "crane", "truck", "low", "push", "pull")
WHIP_DUR = 0.3


def subject_kind(sub):
    if isinstance(sub, list):
        return "point"
    if sub == "two":
        return "two"
    if "." in sub:
        return "point"
    if "+" in sub:
        return "group"
    return "dog" if sub in ("dog", "pup", "mom") else "narr"


def shot_params(sh, u, lt):
    """Devuelve (az_deg, el_deg, dist, lateral_m, fov) para el progreso u (0-1) del plano."""
    typ = sh.get("type", "push")
    kind = subject_kind(sh.get("sub", "narr"))
    size = sh.get("size", "medium")
    D = sh.get("dist", SIZES[kind][size])
    az0 = sh.get("az", 0.0)
    el0 = sh.get("el", 12.0)
    fov = sh.get("fov", 40.0)
    e = EASE[sh.get("ease", "inout")](u)
    lat = 0.0
    if typ == "establish":
        k = EASE["inout4"](seg(u, 0.0, 0.6))          # empuje rápido en el primer 60 %
        far = sh.get("from", 3.2)
        dist = D * (far + (1 - far) * k) * (1 - 0.06 * seg(u, 0.6, 1.0))
        el = sh.get("el_from", 38.0) + (el0 - sh.get("el_from", 38.0)) * k
        az = az0 + sh.get("deg", 20.0) * e
    elif typ == "orbit":
        az = az0 + sh.get("deg", 180.0) * e
        el = el0
        dist = D
    elif typ == "crane":
        rise = sh.get("rise", 25.0)
        el = el0 + rise * e if rise > 0 else el0 - rise * (1 - e)
        az = az0 + sh.get("deg", 8.0) * e
        dist = D * (1.0 + 0.08 * (1 - e))
    elif typ == "truck":
        mv = sh.get("move", 1.2)
        lat = -mv / 2 + mv * e
        az = az0
        el = el0
        dist = D
    elif typ == "low":
        el = sh.get("el", -4.0) + 2.0 * e
        az = az0 + sh.get("deg", 10.0) * e
        dist = D * (1.12 - 0.12 * e)
    elif typ == "pull":
        az = az0 + sh.get("deg", 6.0) * e
        el = el0 + 4 * e
        dist = D * (0.8 + 0.35 * e)
    else:  # push
        az = az0 + sh.get("deg", 6.0) * e
        el = el0
        dist = D * (1.25 - 0.25 * e)
    return az, el, dist, lat, fov


def zoom_factor(t, zoom_times):
    """Golpe de zoom corto: entra en 0,08 s, aguanta, vuelve en 0,3 s (factor de fov)."""
    f = 1.0
    for tz in zoom_times:
        lt = t - tz
        if lt < 0 or lt > 0.9:
            continue
        if lt < 0.08:
            b = EASE["out"](lt / 0.08)
        elif lt < 0.55:
            b = 1.0
        else:
            b = 1 - EASE["inout"]((lt - 0.55) / 0.35)
        f = min(f, 1 - 0.17 * b)
    return f


def validate(shots, duration):
    """Reglas de montaje: no repetir tipo seguido, cambio cada 2-3 s, tamaños alternos."""
    issues = []
    for i, (t0, sh) in enumerate(shots):
        t1 = shots[i + 1][0] if i + 1 < len(shots) else duration
        d = t1 - t0
        if sh.get("type") not in TYPES:
            issues.append(f"plano {i + 1}: tipo desconocido {sh.get('type')}")
        if i and shots[i - 1][1].get("type") == sh.get("type"):
            issues.append(f"plano {i + 1}: mismo tipo que el anterior ({sh.get('type')})")
        if d > 3.4:
            issues.append(f"plano {i + 1}: dura {d:.1f} s (>3,4 s)")
        if d < 0.8:
            issues.append(f"plano {i + 1}: dura {d:.1f} s (<0,8 s)")
    sizes = [sh.get("size", "medium") for _, sh in shots]
    for i in range(2, len(sizes)):
        if sizes[i] == sizes[i - 1] == sizes[i - 2]:
            issues.append(f"planos {i - 1}-{i + 1}: tres seguidos de tamaño {sizes[i]}")
    return issues
