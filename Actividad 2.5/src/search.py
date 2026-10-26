"""Dijkstra y A* con instrumentación de métricas."""
from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from typing import Callable

from .graph_data import Graph


@dataclass
class SearchResult:
    algorithm: str
    path: list[str]
    cost: float
    expanded: int                 # nodos extraídos de la frontera y expandidos
    generated: int                # nodos insertados en la frontera
    max_frontier: int             # tamaño máximo de la frontera
    time_ms: float
    expanded_order: list[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return bool(self.path)


def _reconstruct(parent: dict[str, str | None], goal: str) -> list[str]:
    path, node = [], goal
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]


def astar(graph: Graph, start: str, goal: str,
          h: Callable[[str], float] | None = None,
          name: str = "A*") -> SearchResult:
    """A* genérico: f(n) = g(n) + h(n).

    Con h = 0 se comporta exactamente como Dijkstra. Se permite reabrir nodos
    (si se encuentra un g menor) para que también funcione con heurísticas
    inconsistentes o ponderadas.
    """
    h = h or (lambda _n: 0.0)
    t0 = time.perf_counter()
    counter = itertools.count()                       # desempate estable en el heap
    g = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    frontier = [(h(start), next(counter), start)]
    generated, max_frontier = 1, 1
    expanded_order: list[str] = []
    closed_g: dict[str, float] = {}                   # g con el que se expandió cada nodo

    while frontier:
        f, _, node = heapq.heappop(frontier)
        if node in closed_g and closed_g[node] <= g[node]:
            continue                                  # entrada obsoleta
        closed_g[node] = g[node]
        expanded_order.append(node)
        if node == goal:
            return SearchResult(name, _reconstruct(parent, goal), g[goal],
                                len(expanded_order), generated, max_frontier,
                                (time.perf_counter() - t0) * 1000, expanded_order)
        for nbr, w in graph[node]:
            new_g = g[node] + w
            if nbr not in g or new_g < g[nbr]:
                g[nbr] = new_g
                parent[nbr] = node
                heapq.heappush(frontier, (new_g + h(nbr), next(counter), nbr))
                generated += 1
        max_frontier = max(max_frontier, len(frontier))

    return SearchResult(name, [], float("inf"), len(expanded_order), generated,
                        max_frontier, (time.perf_counter() - t0) * 1000, expanded_order)


def dijkstra(graph: Graph, start: str, goal: str) -> SearchResult:
    """Dijkstra = A* con heurística nula."""
    return astar(graph, start, goal, h=None, name="Dijkstra")


def distances_from(graph: Graph, source: str) -> dict[str, float]:
    """Dijkstra completo desde `source` (distancias óptimas h*). Grafo no dirigido."""
    dist = {source: 0.0}
    pq = [(0.0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist
