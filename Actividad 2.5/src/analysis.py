"""Análisis de admisibilidad/consistencia y benchmark Dijkstra vs A*."""
from __future__ import annotations

import statistics
from itertools import permutations

import pandas as pd

from .graph_data import Graph
from .heuristics import Coords, haversine_km, make_heuristic
from .search import astar, dijkstra, distances_from

# Variantes comparadas: nombre -> escala de la heurística (None = Dijkstra)
VARIANTS: dict[str, float | None] = {
    "Dijkstra": None,
    "A* (haversine)": 1.0,
    "A* ponderado (h×1.5)": 1.5,
    "A* ponderado (h×3)": 3.0,
}


def run_variant(graph: Graph, coords: Coords, start: str, goal: str, variant: str, repeats: int = 1):
    """Ejecuta una variante; el tiempo reportado es la mediana de `repeats` corridas."""
    scale = VARIANTS[variant]
    runs = []
    for _ in range(repeats):
        if scale is None:
            runs.append(dijkstra(graph, start, goal))
        else:
            runs.append(astar(graph, start, goal, make_heuristic(coords, goal, scale), name=variant))
    res = runs[0]
    res.algorithm = variant
    res.time_ms = statistics.median(r.time_ms for r in runs)
    return res


def admissibility_table(graph: Graph, coords: Coords, scale: float = 1.0) -> pd.DataFrame:
    """Para cada par (n, meta): h(n), h*(n) real y holgura h* - h.

    Admisible  <=>  h(n) <= h*(n)  para todo n (holgura >= 0).
    """
    rows = []
    for goal in graph:
        h_star = distances_from(graph, goal)
        for n in graph:
            if n == goal:
                continue
            h = scale * haversine_km(coords[n], coords[goal])
            rows.append({"nodo": n, "meta": goal, "h": h, "h_star": h_star[n],
                         "holgura": h_star[n] - h, "admisible": h <= h_star[n] + 1e-9})
    return pd.DataFrame(rows)


def consistency_violations(graph: Graph, coords: Coords, scale: float = 1.0) -> int:
    """Cuenta violaciones de consistencia h(u) <= w(u,v) + h(v) sobre todas las metas."""
    v = 0
    for goal in graph:
        h = make_heuristic(coords, goal, scale)
        for u, nbrs in graph.items():
            for w_node, w in nbrs:
                if h(u) > w + h(w_node) + 1e-9:
                    v += 1
    return v


def benchmark_all_pairs(graph: Graph, coords: Coords, repeats: int = 5) -> pd.DataFrame:
    """Corre todas las variantes sobre todos los pares origen-destino ordenados."""
    rows = []
    for s, g in permutations(graph, 2):
        optimal = dijkstra(graph, s, g).cost
        for variant in VARIANTS:
            r = run_variant(graph, coords, s, g, variant, repeats)
            rows.append({"origen": s, "destino": g, "algoritmo": variant, "costo_km": r.cost,
                         "expandidos": r.expanded, "generados": r.generated,
                         "max_frontera": r.max_frontier, "tiempo_ms": r.time_ms,
                         "optimo": abs(r.cost - optimal) < 1e-9,
                         "sobrecosto_pct": (r.cost / optimal - 1) * 100})
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen por algoritmo sobre todos los pares."""
    out = df.groupby("algoritmo", sort=False).agg(
        expandidos_prom=("expandidos", "mean"),
        generados_prom=("generados", "mean"),
        frontera_max_prom=("max_frontera", "mean"),
        tiempo_ms_prom=("tiempo_ms", "mean"),
        rutas_optimas_pct=("optimo", lambda s: 100 * s.mean()),
        sobrecosto_prom_pct=("sobrecosto_pct", "mean"),
        sobrecosto_max_pct=("sobrecosto_pct", "max"),
    )
    return out.round(3)
