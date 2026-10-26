"""Pruebas: corrección de Dijkstra/A*, admisibilidad y consistencia de la heurística."""
from itertools import permutations

import pytest

from src.analysis import admissibility_table, consistency_violations
from src.graph_data import EDGES, build_graph
from src.heuristics import haversine_km, make_heuristic
from src.search import astar, dijkstra

graph, coords = build_graph()


def test_grafo_conexo():
    for goal in graph:
        assert dijkstra(graph, "Xico", goal).found


def test_cada_arista_es_mayor_o_igual_a_linea_recta():
    """Condición base de admisibilidad: ningún tramo es 'más corto' que volar en línea recta."""
    for a, b, w in EDGES:
        assert w >= haversine_km(coords[a], coords[b]), f"{a}-{b}"


def test_heuristica_admisible_todos_los_pares():
    assert admissibility_table(graph, coords, 1.0)["admisible"].all()


def test_heuristica_consistente():
    assert consistency_violations(graph, coords, 1.0) == 0


def test_astar_igual_a_dijkstra_en_costo_todos_los_pares():
    for s, g in permutations(graph, 2):
        d = dijkstra(graph, s, g)
        a = astar(graph, s, g, make_heuristic(coords, g))
        assert a.cost == pytest.approx(d.cost), (s, g)


def test_astar_nunca_expande_mas_que_dijkstra_en_promedio():
    d = a = 0
    for s, g in permutations(graph, 2):
        d += dijkstra(graph, s, g).expanded
        a += astar(graph, s, g, make_heuristic(coords, g)).expanded
    assert a < d


def test_ruta_valida_y_costo_coincide():
    r = astar(graph, "Xico", "Oaxaca", make_heuristic(coords, "Oaxaca"))
    assert r.path[0] == "Xico" and r.path[-1] == "Oaxaca"
    w = {(a, b): c for a, b, c in EDGES} | {(b, a): c for a, b, c in EDGES}
    assert sum(w[(u, v)] for u, v in zip(r.path, r.path[1:])) == pytest.approx(r.cost)


def test_origen_igual_a_destino():
    r = dijkstra(graph, "Puebla", "Puebla")
    assert r.path == ["Puebla"] and r.cost == 0


def test_heuristica_inadmisible_puede_perder_optimalidad():
    """h×3 sobrestima: debe existir al menos un par con ruta subóptima."""
    subopt = [(s, g) for s, g in permutations(graph, 2)
              if astar(graph, s, g, make_heuristic(coords, g, 3.0)).cost
              > dijkstra(graph, s, g).cost + 1e-9]
    assert subopt
