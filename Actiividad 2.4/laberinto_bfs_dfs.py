"""
Actividad 2.4 - Algoritmos de búsqueda ciega (BFS / DFS)
Resolución de un laberinto con BFS y DFS + comparativa.

Representación: laberinto = matriz (0 = pasillo, 1 = muro).
Grafo implícito: cada celda libre es un nodo; hay arista entre celdas
libres adyacentes (arriba, abajo, izquierda, derecha), costo 1.
"""
import random
import time
from collections import deque

# ---------------------------------------------------------------- Laberinto
def generar_laberinto(filas=21, cols=41, seed=7, extra_huecos=40):
    """Backtracker recursivo (iterativo) + huecos extra para crear ciclos."""
    rnd = random.Random(seed)
    m = [[1] * cols for _ in range(filas)]
    m[1][1] = 0
    pila = [(1, 1)]
    while pila:
        f, c = pila[-1]
        vecinos = [(f + df, c + dc, df, dc) for df, dc in ((2, 0), (-2, 0), (0, 2), (0, -2))
                   if 0 < f + df < filas - 1 and 0 < c + dc < cols - 1 and m[f + df][c + dc] == 1]
        if vecinos:
            nf, nc, df, dc = rnd.choice(vecinos)
            m[f + df // 2][c + dc // 2] = 0
            m[nf][nc] = 0
            pila.append((nf, nc))
        else:
            pila.pop()
    # Derribar muros al azar -> varios caminos posibles (BFS y DFS difieren)
    for _ in range(extra_huecos):
        f, c = rnd.randrange(1, filas - 1), rnd.randrange(1, cols - 1)
        if m[f][c] == 1 and ((m[f-1][c] == 0 and m[f+1][c] == 0) or (m[f][c-1] == 0 and m[f][c+1] == 0)):
            m[f][c] = 0
    return m, (1, 1), (filas - 2, cols - 2)


def vecinos(m, nodo):
    f, c = nodo
    for df, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):  # orden fijo: N, E, S, O
        nf, nc = f + df, c + dc
        if 0 <= nf < len(m) and 0 <= nc < len(m[0]) and m[nf][nc] == 0:
            yield (nf, nc)


def reconstruir(padres, meta):
    camino, n = [], meta
    while n is not None:
        camino.append(n)
        n = padres[n]
    return camino[::-1]

# ---------------------------------------------------------------- Algoritmos
def bfs(m, inicio, meta):
    frontera = deque([inicio])
    padres = {inicio: None}
    expandidos, max_front = 0, 1
    while frontera:
        max_front = max(max_front, len(frontera))
        n = frontera.popleft()          # FIFO
        expandidos += 1
        if n == meta:
            return reconstruir(padres, meta), expandidos, max_front
        for v in vecinos(m, n):
            if v not in padres:
                padres[v] = n
                frontera.append(v)
    return None, expandidos, max_front


def dfs(m, inicio, meta):
    frontera = [inicio]
    padres = {inicio: None}
    visitados = set()
    expandidos, max_front = 0, 1
    while frontera:
        max_front = max(max_front, len(frontera))
        n = frontera.pop()              # LIFO
        if n in visitados:
            continue
        visitados.add(n)
        expandidos += 1
        if n == meta:
            return reconstruir(padres, meta), expandidos, max_front
        for v in vecinos(m, n):
            if v not in visitados:
                padres[v] = n           # último padre que lo apila
                frontera.append(v)
    return None, expandidos, max_front

# ---------------------------------------------------------------- Utilidades
def dibujar(m, inicio, meta, camino=None):
    ruta = set(camino or [])
    out = []
    for f, fila in enumerate(m):
        s = ""
        for c, v in enumerate(fila):
            if (f, c) == inicio: s += "S"
            elif (f, c) == meta: s += "G"
            elif (f, c) in ruta: s += "·"
            else: s += "█" if v else " "
        out.append(s)
    return "\n".join(out)


def medir(alg, m, ini, meta, repeticiones=200):
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        res = alg(m, ini, meta)
    return res, (time.perf_counter() - t0) / repeticiones * 1000  # ms


if __name__ == "__main__":
    lab, ini, meta = generar_laberinto()
    libres = sum(v == 0 for fila in lab for v in fila)
    print(f"Laberinto {len(lab)}x{len(lab[0])} | celdas libres (nodos): {libres}\n")
    print(dibujar(lab, ini, meta), "\n")

    resultados = {}
    for nombre, alg in (("BFS", bfs), ("DFS", dfs)):
        (camino, exp, front), ms = medir(alg, lab, ini, meta)
        resultados[nombre] = (camino, exp, front, ms)
        print(f"=== {nombre} ===")
        print(dibujar(lab, ini, meta, camino), "\n")

    print(f"{'Algoritmo':<10}{'Long. camino':>14}{'Nodos exp.':>12}{'Frontera máx.':>15}{'Tiempo (ms)':>13}")
    for n, (cam, exp, fr, ms) in resultados.items():
        print(f"{n:<10}{len(cam) - 1:>14}{exp:>12}{fr:>15}{ms:>13.3f}")
