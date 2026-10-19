"""
Actividad 2.1 y 2.2 - Problemas de búsqueda y espacios de búsqueda
Modelado de 2 problemas reales como problemas de búsqueda + grafo con NetworkX.

Problema A: Ruta mínima entre ciudades (estado = ciudad).
Problema B: Viaje en vehículo eléctrico con recargas (estado = (ciudad, batería)).

Ejecución:  python busqueda_grafos.py
Requiere:   pip install networkx matplotlib
"""
import math
from collections import deque
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx


# ---------------------------------------------------------------------------
# 1. Definición formal genérica de un problema de búsqueda
# ---------------------------------------------------------------------------
class ProblemaBusqueda:
    """Estado inicial, acciones, modelo de transición, costo y prueba de meta."""

    def __init__(self, inicial):
        self.inicial = inicial

    def acciones(self, estado):          # -> lista de (accion, nuevo_estado, costo)
        raise NotImplementedError

    def es_meta(self, estado):           # -> bool
        raise NotImplementedError


# Distancias aproximadas por carretera en km (valores ilustrativos)
CARRETERAS = {
    ("Veracruz", "Xalapa"): 105,
    ("Veracruz", "Córdoba"): 125,
    ("Córdoba", "Orizaba"): 20,
    ("Orizaba", "Puebla"): 125,
    ("Xalapa", "Puebla"): 190,
    ("Puebla", "CDMX"): 130,
    ("Xalapa", "CDMX"): 315,
}


def vecinos(ciudad):
    """Carreteras de doble sentido: se generan ambos arcos dirigidos."""
    for (a, b), km in CARRETERAS.items():
        if a == ciudad:
            yield b, km
        elif b == ciudad:
            yield a, km


# ---------------------------------------------------------------------------
# 2. Problema A: ruta mínima entre ciudades
# ---------------------------------------------------------------------------
class RutaCiudades(ProblemaBusqueda):
    """
    Estado   : ciudad actual
    Acciones : viajar a una ciudad conectada
    Costo    : kilómetros del tramo
    Meta     : llegar a la ciudad destino
    """

    def __init__(self, inicial, destino):
        super().__init__(inicial)
        self.destino = destino

    def acciones(self, estado):
        return [(f"ir a {c}", c, km) for c, km in vecinos(estado)]

    def es_meta(self, estado):
        return estado == self.destino


# ---------------------------------------------------------------------------
# 3. Problema B: vehículo eléctrico con recargas
# ---------------------------------------------------------------------------
UNIDAD_KM = 50          # 1 unidad de batería = 50 km de autonomía
CAPACIDAD = 4           # batería máxima = 4 unidades (200 km)
VELOCIDAD = 80          # km/h promedio
HORAS_POR_UNIDAD = 0.25  # tiempo de carga por unidad


class ViajeEV(ProblemaBusqueda):
    """
    Estado   : (ciudad, unidades_de_bateria)
    Acciones : conducir a ciudad vecina (si alcanza la batería) o cargar 1 unidad
    Costo    : horas (conducción = km/velocidad; carga = 0.25 h por unidad)
    Meta     : estar en la ciudad destino con cualquier nivel de batería
    """

    def __init__(self, inicial, destino):
        super().__init__(inicial)
        self.destino = destino

    def acciones(self, estado):
        ciudad, bat = estado
        resultado = []
        for c, km in vecinos(ciudad):
            gasto = math.ceil(km / UNIDAD_KM)
            if gasto <= bat:                               # precondición
                resultado.append((f"conducir a {c}", (c, bat - gasto), km / VELOCIDAD))
        if bat < CAPACIDAD:                                # precondición
            resultado.append(("cargar +1", (ciudad, bat + 1), HORAS_POR_UNIDAD))
        return resultado

    def es_meta(self, estado):
        return estado[0] == self.destino


# ---------------------------------------------------------------------------
# 4. Generador de estados -> grafo dirigido y ponderado (NetworkX)
# ---------------------------------------------------------------------------
def generar_grafo(problema):
    """
    Expansión por anchura (BFS) del espacio de estados alcanzable.
    Cada estado es un nodo; cada acción, un arco dirigido con peso = costo.
    Complejidad: O(V + E) en tiempo y O(V) en memoria.
    """
    G = nx.DiGraph()
    G.add_node(problema.inicial)
    visitados = {problema.inicial}
    cola = deque([problema.inicial])
    while cola:
        s = cola.popleft()
        for accion, s2, costo in problema.acciones(s):
            G.add_edge(s, s2, weight=round(costo, 3), accion=accion)
            if s2 not in visitados:
                visitados.add(s2)
                cola.append(s2)
    return G


def solucion_optima(G, problema):
    """Dijkstra sobre el grafo generado: O((V + E) log V)."""
    metas = [n for n in G.nodes if problema.es_meta(n)]
    mejor = None
    for m in metas:
        try:
            costo, camino = nx.single_source_dijkstra(G, problema.inicial, m, weight="weight")
        except nx.NetworkXNoPath:
            continue
        if mejor is None or costo < mejor[0]:
            mejor = (costo, camino)
    return mejor


# ---------------------------------------------------------------------------
# 5. Dibujo de los grafos
# ---------------------------------------------------------------------------
def dibujar_rutas(G, camino, archivo):
    pos = {"Veracruz": (5, 0), "Córdoba": (3, 0.5), "Orizaba": (2, 1),
           "Xalapa": (4.5, 3), "Puebla": (0.5, 2), "CDMX": (2, 4)}
    fig, ax = plt.subplots(figsize=(9, 6))
    aristas_opt = set(zip(camino, camino[1:]))
    colores = ["#d62728" if e in aristas_opt else "#999999" for e in G.edges]
    anchos = [3 if e in aristas_opt else 1 for e in G.edges]
    nx.draw_networkx_nodes(G, pos, node_color="#cfe2f3", node_size=2200, edgecolors="#1f4e79", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color=colores, width=anchos, arrows=True,
                           arrowsize=14, node_size=2200, connectionstyle="arc3,rad=0.12", ax=ax)
    etiquetas = {(u, v): f"{d['weight']:.0f}" for u, v, d in G.edges(data=True) if u < v}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=etiquetas, font_size=8, label_pos=0.5, ax=ax)
    ax.set_title("Problema A - Grafo dirigido y ponderado (km). Ruta óptima en rojo")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(archivo, dpi=150)
    plt.close(fig)


def dibujar_ev(G, camino, archivo):
    ciudades = ["Veracruz", "Córdoba", "Orizaba", "Xalapa", "Puebla", "CDMX"]
    pos = {n: (ciudades.index(n[0]) * 2.2, n[1]) for n in G.nodes}
    fig, ax = plt.subplots(figsize=(14, 7))
    aristas_opt = set(zip(camino, camino[1:]))
    for u, v, d in G.edges(data=True):
        opt = (u, v) in aristas_opt
        carga = d["accion"].startswith("cargar")
        color = "#d62728" if opt else ("#2ca02c" if carga else "#1f77b4")
        rad = 0.0 if carga else 0.25
        ax.annotate("", xy=pos[v], xytext=pos[u],
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.5 if opt else 0.8,
                                    alpha=1 if opt else 0.45,
                                    connectionstyle=f"arc3,rad={rad}", shrinkA=14, shrinkB=14))
    for n, (x, y) in pos.items():
        ax.scatter(x, y, s=700, c="#fff2cc" if n == camino[0] else ("#d9ead3" if n[0] == camino[-1][0] else "#cfe2f3"),
                   edgecolors="#1f4e79", zorder=3)
        ax.text(x, y, str(n[1]), ha="center", va="center", fontsize=9, zorder=4)
    ax.set_xticks([i * 2.2 for i in range(len(ciudades))])
    ax.set_xticklabels(ciudades)
    ax.set_yticks(range(CAPACIDAD + 1))
    ax.set_ylabel("Batería (unidades de 50 km)")
    ax.set_title("Problema B - Espacio de estados (ciudad, batería). Azul: conducir, verde: cargar, rojo: óptimo")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(archivo, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6. Programa principal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    directorio_salida = Path(__file__).resolve().parent / "outputs"
    directorio_salida.mkdir(exist_ok=True)

    # Problema A
    A = RutaCiudades("Veracruz", "CDMX")
    GA = generar_grafo(A)
    costo_a, camino_a = solucion_optima(GA, A)
    print("== Problema A: ruta mínima ==")
    print(f"Nodos: {GA.number_of_nodes()}  Arcos: {GA.number_of_edges()}")
    print("Camino:", " -> ".join(camino_a), f"| {costo_a:.0f} km")
    dibujar_rutas(GA, camino_a, directorio_salida / "grafo_rutas.png")

    # Problema B
    B = ViajeEV(("Veracruz", CAPACIDAD), "CDMX")
    GB = generar_grafo(B)
    costo_b, camino_b = solucion_optima(GB, B)
    print("\n== Problema B: viaje en vehículo eléctrico ==")
    print(f"Nodos (estados): {GB.number_of_nodes()}  Arcos (acciones): {GB.number_of_edges()}")
    print(f"Costo óptimo: {costo_b:.2f} horas")
    for u, v in zip(camino_b, camino_b[1:]):
        print(f"  {u} --{GB[u][v]['accion']} ({GB[u][v]['weight']} h)--> {v}")
    dibujar_ev(GB, camino_b, directorio_salida / "grafo_ev.png")
