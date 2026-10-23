"""
Actividad: Implementación + Optimización
Hill Climbing (HC) vs Simulated Annealing (SA) para minimizar la longitud de
una ruta cerrada que visita 20 ciudades de México (problema del viajante, TSP).

Ejecución:  python hc_vs_sa.py
Requiere:   pip install numpy matplotlib
"""
import math
import random
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# 1. Datos: ciudades (latitud, longitud) aproximadas
# ---------------------------------------------------------------------------
CIUDADES = {
    "CDMX": (19.43, -99.13), "Guadalajara": (20.67, -103.35), "Monterrey": (25.67, -100.31),
    "Puebla": (19.04, -98.20), "Veracruz": (19.17, -96.13), "Xalapa": (19.54, -96.91),
    "Mérida": (20.97, -89.62), "Cancún": (21.16, -86.85), "Oaxaca": (17.07, -96.73),
    "Tijuana": (32.51, -117.04), "Chihuahua": (28.63, -106.07), "León": (21.12, -101.68),
    "Querétaro": (20.59, -100.39), "Morelia": (19.70, -101.19), "Acapulco": (16.85, -99.88),
    "San Luis Potosí": (22.15, -100.98), "Villahermosa": (17.99, -92.93),
    "Tuxtla Gutiérrez": (16.75, -93.12), "Hermosillo": (29.07, -110.96), "Mazatlán": (23.25, -106.41),
}
NOMBRES = list(CIUDADES)
N = len(NOMBRES)


def haversine(a, b):
    """Distancia en km sobre la esfera terrestre."""
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


D = [[haversine(CIUDADES[a], CIUDADES[b]) for b in NOMBRES] for a in NOMBRES]


# ---------------------------------------------------------------------------
# 2. Función objetivo y vecindad
# ---------------------------------------------------------------------------
def costo(ruta):
    """f(ruta) = suma de distancias del ciclo cerrado (km). Se MINIMIZA."""
    return sum(D[ruta[i]][ruta[(i + 1) % N]] for i in range(N))


def vecino_2opt(ruta):
    """Vecindad 2-opt: invierte un segmento ruta[i..j]."""
    i, j = sorted(random.sample(range(N), 2))
    return ruta[:i] + ruta[i:j + 1][::-1] + ruta[j + 1:]


# ---------------------------------------------------------------------------
# 3. Algoritmos (1 iteración = 1 vecino evaluado, para comparación justa)
# ---------------------------------------------------------------------------
def hill_climbing(ruta, iteraciones):
    """Acepta el vecino solo si mejora. Se queda atascado en óptimos locales."""
    f = costo(ruta)
    hist = []
    for _ in range(iteraciones):
        v = vecino_2opt(ruta)
        fv = costo(v)
        if fv < f:
            ruta, f = v, fv
        hist.append(f)
    return ruta, f, hist


def simulated_annealing(ruta, iteraciones, T0, eta):
    """
    Acepta mejoras siempre y empeoramientos con prob. exp(-delta / T).
    Enfriamiento geométrico: T <- eta * T, con 0 < eta < 1.
    """
    f = costo(ruta)
    mejor, f_mejor = ruta, f
    T = T0
    hist, temps = [], []
    for _ in range(iteraciones):
        v = vecino_2opt(ruta)
        fv = costo(v)
        delta = fv - f
        if delta < 0 or random.random() < math.exp(-delta / T):
            ruta, f = v, fv
            if f < f_mejor:
                mejor, f_mejor = ruta, f
        T *= eta
        hist.append(f_mejor)
        temps.append(T)
    return mejor, f_mejor, hist, temps


# ---------------------------------------------------------------------------
# 4. Experimento
# ---------------------------------------------------------------------------
ITER = 20000     # iteraciones por corrida
T0 = 500.0       # temperatura inicial (km): ~ escala de un empeoramiento típico
ETA = 0.9995     # factor de enfriamiento (T_final = T0 * ETA^ITER ~ 0.02)
CORRIDAS = 30

if __name__ == "__main__":
    res_hc, res_sa, curvas_hc, curvas_sa = [], [], [], []
    mejor_global = (float("inf"), None)
    for semilla in range(CORRIDAS):
        random.seed(semilla)
        inicial = random.sample(range(N), N)
        r1, f1, h1 = hill_climbing(inicial[:], ITER)
        r2, f2, h2, temps = simulated_annealing(inicial[:], ITER, T0, ETA)
        res_hc.append(f1); res_sa.append(f2)
        curvas_hc.append(h1); curvas_sa.append(h2)
        for r, f in ((r1, f1), (r2, f2)):
            if f < mejor_global[0]:
                mejor_global = (f, r)

    print(f"{'':22}{'HC':>10}{'SA':>10}")
    for nombre, fn in (("Mejor (km)", min), ("Peor (km)", max),
                       ("Media (km)", st.mean), ("Desv. est. (km)", st.stdev)):
        print(f"{nombre:22}{fn(res_hc):10.0f}{fn(res_sa):10.0f}")
    mejor_conocido = mejor_global[0]
    print(f"{'Gap medio vs mejor':22}{(st.mean(res_hc)/mejor_conocido-1)*100:9.1f}%"
          f"{(st.mean(res_sa)/mejor_conocido-1)*100:9.1f}%")
    print(f"{'Corridas en el mejor':22}{sum(abs(x-mejor_conocido)<1 for x in res_hc):10d}"
          f"{sum(abs(x-mejor_conocido)<1 for x in res_sa):10d}")
    print("Mejor ruta:", " -> ".join(NOMBRES[i] for i in mejor_global[1]), f"| {mejor_conocido:.0f} km")

    # --- Gráfica de convergencia ---
    fig, ax = plt.subplots(1, 3, figsize=(17, 5))
    x = np.arange(1, ITER + 1)
    for c, color, lab in ((curvas_hc, "#d62728", "Hill Climbing"), (curvas_sa, "#1f77b4", "Simulated Annealing")):
        a = np.array(c)
        ax[0].plot(x, a.mean(0), color=color, label=f"{lab} (media de {CORRIDAS})")
        ax[0].fill_between(x, a.min(0), a.max(0), color=color, alpha=0.15)
    ax[0].set_xscale("log"); ax[0].set_xlabel("Iteración (log)"); ax[0].set_ylabel("Mejor costo (km)")
    ax[0].set_title("Convergencia"); ax[0].legend(); ax[0].grid(alpha=0.3)

    ax[1].plot(x, temps, color="#ff7f0e")
    ax[1].set_xlabel("Iteración"); ax[1].set_ylabel("Temperatura T"); ax[1].set_yscale("log")
    ax[1].set_title(f"Enfriamiento SA (T0={T0:.0f}, η={ETA})"); ax[1].grid(alpha=0.3)

    ax[2].boxplot([res_hc, res_sa], tick_labels=["HC", "SA"])
    ax[2].set_ylabel("Costo final (km)"); ax[2].set_title("Resultados finales (30 corridas)")
    ax[2].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig("convergencia_hc_sa.png", dpi=150)

    # --- Mejor ruta sobre el mapa de coordenadas ---
    fig, ax = plt.subplots(figsize=(8, 6))
    ruta = mejor_global[1] + [mejor_global[1][0]]
    ax.plot([CIUDADES[NOMBRES[i]][1] for i in ruta], [CIUDADES[NOMBRES[i]][0] for i in ruta], "o-", color="#1f77b4")
    for n, (la, lo) in CIUDADES.items():
        ax.annotate(n, (lo, la), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_title(f"Mejor ruta encontrada: {mejor_conocido:.0f} km"); ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud")
    fig.tight_layout(); fig.savefig("mejor_ruta.png", dpi=150)
