"""Heurísticas para A*: distancia haversine (gran círculo) en km."""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Callable

EARTH_RADIUS_KM = 6371.0088

Coords = dict[str, tuple[float, float]]


def haversine_km(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Distancia en línea recta sobre la esfera terrestre (km)."""
    lat1, lon1, lat2, lon2 = map(radians, (*p1, *p2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def make_heuristic(coords: Coords, goal: str, scale: float = 1.0) -> Callable[[str], float]:
    """h(n) = scale * haversine(n, goal).

    scale = 1.0 -> admisible y consistente (la lectura "estándar").
    scale > 1.0 -> heurística ponderada: más rápida pero puede dejar de ser admisible.
    """
    g = coords[goal]
    return lambda n: scale * haversine_km(coords[n], g)
