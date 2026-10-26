"""
Caso real: red carretera del centro-oriente de México.

Nodos  : 29 ciudades con coordenadas GPS (lat, lon) en grados decimales.
Aristas: tramos carreteros con distancia aproximada por carretera (km).

NOTA: las distancias son aproximadas (tomadas de rutas carreteras comunes) y
deben ser >= a la distancia en línea recta (haversine). Esa condición es la que
garantiza que la heurística sea admisible; `tests/test_search.py` la verifica.
"""
from __future__ import annotations

# nombre: (latitud, longitud)
CITIES: dict[str, tuple[float, float]] = {
    "Xico": (19.4200, -96.9900),
    "Coatepec": (19.4528, -96.9622),
    "Xalapa": (19.5438, -96.9102),
    "Perote": (19.5614, -97.2411),
    "Huatusco": (19.1500, -96.9667),
    "Cardel": (19.3667, -96.3667),
    "Veracruz": (19.1738, -96.1342),
    "Córdoba": (18.8942, -96.9347),
    "Orizaba": (18.8506, -97.1031),
    "Tehuacán": (18.4623, -97.3927),
    "Puebla": (19.0414, -98.2063),
    "Tlaxcala": (19.3139, -98.2404),
    "Apizaco": (19.4167, -98.1442),
    "Teziutlán": (19.8167, -97.3567),
    "Martínez de la Torre": (20.0667, -97.0572),
    "Poza Rica": (20.5331, -97.4592),
    "Tuxpan": (20.9560, -97.4008),
    "Huauchinango": (20.1747, -98.0547),
    "Tulancingo": (20.0833, -98.3667),
    "Pachuca": (20.1011, -98.7591),
    "CDMX": (19.4326, -99.1332),
    "Toluca": (19.2826, -99.6557),
    "Cuernavaca": (18.9242, -99.2216),
    "Cosamaloapan": (18.3667, -95.8000),
    "Tuxtepec": (18.0911, -96.1197),
    "San Andrés Tuxtla": (18.4472, -95.2139),
    "Acayucan": (17.9500, -94.9167),
    "Coatzacoalcos": (18.1500, -94.4167),
    "Oaxaca": (17.0732, -96.7266),
}

# (ciudad_a, ciudad_b, km por carretera aprox.) -- carreteras bidireccionales
EDGES: list[tuple[str, str, float]] = [
    ("Xico", "Coatepec", 9),
    ("Coatepec", "Xalapa", 15),
    ("Xico", "Huatusco", 55),
    ("Xalapa", "Huatusco", 75),
    ("Huatusco", "Córdoba", 45),
    ("Xalapa", "Perote", 55),
    ("Xalapa", "Cardel", 80),
    ("Cardel", "Veracruz", 38),
    ("Xalapa", "Veracruz", 105),
    ("Xalapa", "Martínez de la Torre", 125),
    ("Veracruz", "Córdoba", 125),
    ("Córdoba", "Orizaba", 25),
    ("Orizaba", "Puebla", 140),
    ("Orizaba", "Tehuacán", 85),
    ("Córdoba", "Tehuacán", 100),
    ("Tehuacán", "Puebla", 125),
    ("Perote", "Puebla", 125),
    ("Perote", "Teziutlán", 60),
    ("Perote", "Apizaco", 105),
    ("Teziutlán", "Martínez de la Torre", 70),
    ("Teziutlán", "Puebla", 150),
    ("Martínez de la Torre", "Poza Rica", 100),
    ("Poza Rica", "Tuxpan", 60),
    ("Poza Rica", "Huauchinango", 130),
    ("Huauchinango", "Tulancingo", 75),
    ("Tulancingo", "Pachuca", 50),
    ("Pachuca", "CDMX", 95),
    ("Puebla", "CDMX", 135),
    ("Puebla", "Tlaxcala", 40),
    ("Tlaxcala", "Apizaco", 25),
    ("CDMX", "Toluca", 65),
    ("CDMX", "Cuernavaca", 85),
    ("Cuernavaca", "Toluca", 95),
    ("Veracruz", "Cosamaloapan", 135),
    ("Veracruz", "San Andrés Tuxtla", 155),
    ("San Andrés Tuxtla", "Cosamaloapan", 85),
    ("San Andrés Tuxtla", "Acayucan", 110),
    ("Cosamaloapan", "Acayucan", 160),
    ("Acayucan", "Coatzacoalcos", 105),
    ("Cosamaloapan", "Tuxtepec", 70),
    ("Tuxtepec", "Oaxaca", 220),
    ("Tehuacán", "Oaxaca", 250),
]

Graph = dict[str, list[tuple[str, float]]]


def build_graph() -> tuple[Graph, dict[str, tuple[float, float]]]:
    """Devuelve (lista de adyacencia no dirigida, coordenadas)."""
    graph: Graph = {c: [] for c in CITIES}
    for a, b, w in EDGES:
        graph[a].append((b, float(w)))
        graph[b].append((a, float(w)))
    return graph, dict(CITIES)
