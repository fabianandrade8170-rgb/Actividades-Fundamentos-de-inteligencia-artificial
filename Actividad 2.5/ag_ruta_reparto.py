"""
Proyecto final - Algoritmos Geneticos con DEAP
Problema: optimizacion de la ruta de reparto de una distribuidora local (TSP).

Un camion sale del almacen, visita N_CLIENTES clientes exactamente una vez
y regresa al almacen. Objetivo: minimizar la distancia total recorrida.

Uso:
    pip install deap matplotlib numpy
    python ag_ruta_reparto.py
"""
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from deap import algorithms, base, creator, tools

# ----------------------------------------------------------------------
# 1. Parametros
# ----------------------------------------------------------------------
SEMILLA = 42
N_CLIENTES = 25          # paradas (sin contar el almacen)
TAM_POBLACION = 200
N_GENERACIONES = 30
P_CRUCE = 0.9
P_MUTACION = 0.2         # probabilidad de mutar un individuo
P_MUT_GEN = 0.05         # probabilidad de intercambiar cada gen al mutar
TAM_TORNEO = 3
N_ELITE = 2              # mejores individuos que pasan intactos (Salon de la Fama)

random.seed(SEMILLA)
np.random.seed(SEMILLA)

# ----------------------------------------------------------------------
# 2. Datos del problema: coordenadas (km) en una zona de 20 x 20 km
#    Indice 0 = almacen, 1..N = clientes
# ----------------------------------------------------------------------
coords = np.random.uniform(0, 20, size=(N_CLIENTES + 1, 2))
coords[0] = (10, 10)  # almacen al centro
dist = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)


def longitud_ruta(ruta):
    """Distancia total: almacen -> clientes en orden -> almacen.
    El cromosoma usa indices 0..N-1 (requisito de cxOrdered); el cliente k
    corresponde a la fila k+1 de la matriz de distancias (la fila 0 es el almacen)."""
    camino = [0] + [g + 1 for g in ruta] + [0]
    return float(sum(dist[camino[i], camino[i + 1]] for i in range(len(camino) - 1)))


# ----------------------------------------------------------------------
# 3. Configuracion de DEAP
#    Cromosoma: permutacion de 0..N-1 (gen g = cliente g+1, aparece una sola vez)
#    Fitness: distancia total (se MINIMIZA -> weights = -1.0)
# ----------------------------------------------------------------------
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individuo", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("permutacion", random.sample, range(N_CLIENTES), N_CLIENTES)
toolbox.register("individuo", tools.initIterate, creator.Individuo, toolbox.permutacion)
toolbox.register("poblacion", tools.initRepeat, list, toolbox.individuo)


def evaluar(individuo):
    return (longitud_ruta(individuo),)


toolbox.register("evaluate", evaluar)
toolbox.register("select", tools.selTournament, tournsize=TAM_TORNEO)
toolbox.register("mate", tools.cxOrdered)                       # cruce que preserva permutaciones
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=P_MUT_GEN)

# ----------------------------------------------------------------------
# 4. Estadisticas por generacion
# ----------------------------------------------------------------------
stats = tools.Statistics(lambda ind: ind.fitness.values[0])
stats.register("min", np.min)
stats.register("avg", np.mean)
stats.register("max", np.max)


def ejecutar():
    pob = toolbox.poblacion(n=TAM_POBLACION)
    salon_fama = tools.HallOfFame(N_ELITE)

    # eaSimple con elitismo: se re-inyectan los mejores en cada generacion.
    # Para mantenerlo transparente, se programa el ciclo a mano.
    for ind in pob:
        ind.fitness.values = toolbox.evaluate(ind)
    salon_fama.update(pob)

    historial = {"gen": [], "min": [], "avg": [], "max": []}

    def registrar(g, poblacion):
        r = stats.compile(poblacion)
        historial["gen"].append(g)
        for k in ("min", "avg", "max"):
            historial[k].append(float(r[k]))
        print(f"Gen {g:2d} | mejor {r['min']:7.2f} km | promedio {r['avg']:7.2f} km | peor {r['max']:7.2f} km")

    registrar(0, pob)

    for g in range(1, N_GENERACIONES + 1):
        # Seleccion
        descendencia = toolbox.select(pob, len(pob) - N_ELITE)
        descendencia = [toolbox.clone(i) for i in descendencia]

        # Cruce
        for h1, h2 in zip(descendencia[::2], descendencia[1::2]):
            if random.random() < P_CRUCE:
                toolbox.mate(h1, h2)
                del h1.fitness.values, h2.fitness.values

        # Mutacion
        for m in descendencia:
            if random.random() < P_MUTACION:
                toolbox.mutate(m)
                del m.fitness.values

        # Evaluar solo los modificados
        invalidos = [i for i in descendencia if not i.fitness.valid]
        for ind in invalidos:
            ind.fitness.values = toolbox.evaluate(ind)

        # Elitismo + nueva poblacion
        pob = descendencia + [toolbox.clone(e) for e in salon_fama]
        salon_fama.update(pob)
        registrar(g, pob)

    return pob, salon_fama[0], historial


# ----------------------------------------------------------------------
# 5. Referencias para comparar
# ----------------------------------------------------------------------
def vecino_mas_cercano():
    """Heuristica voraz: siempre ir al cliente no visitado mas cercano."""
    no_visitados = set(range(1, N_CLIENTES + 1))
    actual, ruta = 0, []
    while no_visitados:
        sig = min(no_visitados, key=lambda j: dist[actual, j])
        ruta.append(sig - 1)          # se guarda como gen (indice 0..N-1)
        no_visitados.remove(sig)
        actual = sig
    return ruta


def ruta_aleatoria_promedio(n=1000):
    return float(np.mean([longitud_ruta(random.sample(range(N_CLIENTES), N_CLIENTES))
                          for _ in range(n)]))


# ----------------------------------------------------------------------
# 6. Graficas
# ----------------------------------------------------------------------
def graficar_convergencia(h, archivo="convergencia.png"):
    plt.figure(figsize=(8, 5))
    plt.plot(h["gen"], h["max"], "--", color="gray", label="Peor")
    plt.plot(h["gen"], h["avg"], color="tab:orange", label="Promedio")
    plt.plot(h["gen"], h["min"], color="tab:blue", linewidth=2.2, label="Mejor")
    plt.xlabel("Generacion")
    plt.ylabel("Distancia total (km)")
    plt.title("Convergencia del AG - Ruta de reparto")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(archivo, dpi=150)
    plt.close()


def graficar_ruta(ruta, titulo, archivo):
    camino = [0] + [g + 1 for g in ruta] + [0]
    xy = coords[camino]
    plt.figure(figsize=(7, 7))
    plt.plot(xy[:, 0], xy[:, 1], "-o", color="tab:blue", markersize=5, linewidth=1.3)
    plt.scatter(*coords[0], color="red", s=140, marker="s", zorder=5, label="Almacen")
    for i in range(1, N_CLIENTES + 1):
        plt.annotate(str(i), coords[i], textcoords="offset points", xytext=(4, 4), fontsize=8)
    plt.title(titulo)
    plt.xlabel("km")
    plt.ylabel("km")
    plt.legend()
    plt.axis("equal")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(archivo, dpi=150)
    plt.close()


# ----------------------------------------------------------------------
# 7. Programa principal
# ----------------------------------------------------------------------
if __name__ == "__main__":
    pob_final, mejor, hist = ejecutar()

    d_ag = longitud_ruta(mejor)
    d_vmc = longitud_ruta(vecino_mas_cercano())
    d_azar = ruta_aleatoria_promedio()

    print("\n=== RESULTADOS ===")
    print(f"Ruta aleatoria (promedio de 1000): {d_azar:7.2f} km")
    print(f"Vecino mas cercano (voraz):        {d_vmc:7.2f} km")
    print(f"Algoritmo genetico ({N_GENERACIONES} gen.):       {d_ag:7.2f} km")
    print(f"Mejora del AG vs. ruta aleatoria:  {100 * (d_azar - d_ag) / d_azar:5.1f} %")
    print(f"Mejor ruta: 0 -> {' -> '.join(str(g + 1) for g in mejor)} -> 0")

    graficar_convergencia(hist)
    graficar_ruta(vecino_mas_cercano(), f"Vecino mas cercano: {d_vmc:.1f} km", "ruta_voraz.png")
    graficar_ruta(mejor, f"Mejor ruta del AG: {d_ag:.1f} km", "ruta_ag.png")
    print("\nGraficas guardadas: convergencia.png, ruta_voraz.png, ruta_ag.png")
