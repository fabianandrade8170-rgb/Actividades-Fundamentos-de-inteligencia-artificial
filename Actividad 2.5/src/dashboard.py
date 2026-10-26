"""Dashboard en matplotlib: mapa de la búsqueda, métricas, admisibilidad y tabla comparativa."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

C_DIJ, C_AST, C_W15, C_W3 = "#e07b00", "#1f6fd1", "#2a9d5c", "#9b3fc1"
C_PATH, C_EDGE = "#d62828", "#c9c9c9"
ALGO_COLORS = {"Dijkstra": C_DIJ, "A* (haversine)": C_AST,
               "A* ponderado (h×1.5)": C_W15, "A* ponderado (h×3)": C_W3}
SHORT = {"Dijkstra": "Dijkstra", "A* (haversine)": "A*", "A* ponderado (h×1.5)": "A* h×1.5",
         "A* ponderado (h×3)": "A* h×3"}


def _draw_map(ax, graph, coords, res, color, title, start, goal):
    drawn = set()
    for u, nbrs in graph.items():
        for v, _ in nbrs:
            if (v, u) in drawn:
                continue
            drawn.add((u, v))
            ax.plot([coords[u][1], coords[v][1]], [coords[u][0], coords[v][0]], color=C_EDGE, lw=0.9, zorder=1)
    lons = [coords[n][1] for n in graph]
    lats = [coords[n][0] for n in graph]
    ax.scatter(lons, lats, s=22, c="#8a8a8a", zorder=2)
    exp = res.expanded_order
    ax.scatter([coords[n][1] for n in exp], [coords[n][0] for n in exp], s=75, c=color,
               alpha=0.85, edgecolor="white", linewidth=0.6, zorder=3)
    ax.plot([coords[n][1] for n in res.path], [coords[n][0] for n in res.path],
            color=C_PATH, lw=2.8, zorder=4, solid_capstyle="round")
    ax.scatter(*coords[start][::-1], marker="*", s=260, c="#1b9e3e", edgecolor="black", zorder=6)
    ax.scatter(*coords[goal][::-1], marker="*", s=260, c="#7b2cbf", edgecolor="black", zorder=6)
    for n in graph:
        ax.annotate(n, (coords[n][1], coords[n][0]), xytext=(3, 3), textcoords="offset points",
                    fontsize=6, color="#333333", zorder=7)
    ax.set_title(f"{title}\n{res.expanded} nodos expandidos · {res.cost:.0f} km", fontsize=10, fontweight="bold")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_aspect("auto")
    ax.grid(alpha=0.2)


def build_dashboard(graph, coords, start, goal, case, case_df, adm, cons, bench, summary, path: Path) -> None:
    fig = plt.figure(figsize=(22, 15), constrained_layout=True)
    gs = GridSpec(3, 4, figure=fig, height_ratios=[1.25, 1, 0.9])
    fig.suptitle(f"A* vs Dijkstra · Red carretera centro-oriente de México · {start} → {goal}",
                 fontsize=17, fontweight="bold")

    # --- Fila 1: mapas + métricas del caso -----------------------------------
    ax1 = fig.add_subplot(gs[0, 0:2])
    ax2 = fig.add_subplot(gs[0, 2:4])
    _draw_map(ax1, graph, coords, case["Dijkstra"], C_DIJ, "Dijkstra (h = 0)", start, goal)
    _draw_map(ax2, graph, coords, case["A* (haversine)"], C_AST, "A* (heurística haversine)", start, goal)
    legend = [Line2D([], [], marker="o", ls="", color="#8a8a8a", label="Ciudad"),
              Line2D([], [], marker="o", ls="", color="#888", markersize=10, alpha=.8, label="Nodo expandido (color del algoritmo)"),
              Line2D([], [], color=C_PATH, lw=3, label="Ruta encontrada"),
              Line2D([], [], marker="*", ls="", color="#1b9e3e", markersize=14, markeredgecolor="k", label="Origen"),
              Line2D([], [], marker="*", ls="", color="#7b2cbf", markersize=14, markeredgecolor="k", label="Destino")]
    ax1.legend(handles=legend, loc="lower left", fontsize=7, framealpha=0.9)

    # --- Fila 2 ------------------------------------------------------------------
    names = list(case)
    labels = [SHORT[n] for n in names]
    cols = [ALGO_COLORS[n] for n in names]

    ax3 = fig.add_subplot(gs[1, 0])
    vals = [case[n].expanded for n in names]
    b = ax3.bar(labels, vals, color=cols)
    ax3.bar_label(b, padding=2, fontsize=9)
    ax3.set_title(f"Nodos expandidos (caso {start}→{goal})", fontweight="bold")
    ax3.set_ylabel("nodos")
    ax3.tick_params(axis="x", labelsize=8)

    ax4 = fig.add_subplot(gs[1, 1])
    all_h = adm[1.0]
    ax4.scatter(all_h["h_star"], all_h["h"], s=7, alpha=0.35, c=C_AST, label="h×1.0 (haversine)")
    for s, c in ((1.5, C_W15), (3.0, C_W3)):
        t = adm[s]
        viol = t[~t["admisible"]]
        ax4.scatter(viol["h_star"], viol["h"], s=7, alpha=0.5, c=c,
                    label=f"h×{s}: {len(viol)} violaciones ({100*len(viol)/len(t):.0f}%)")
    mx = float(all_h["h_star"].max()) * 1.02
    ax4.plot([0, mx], [0, mx], "k--", lw=1.2, label="h = h*  (frontera de admisibilidad)")
    ax4.set_title("Admisibilidad: h(n) vs costo real h*(n)\n(admisible = bajo la diagonal)", fontweight="bold", fontsize=10)
    ax4.set_xlabel("h*(n)  costo óptimo real a la meta (km)")
    ax4.set_ylabel("h(n)  estimación (km)")
    ax4.set_ylim(0, mx * 1.6 if mx else 1)
    ax4.legend(fontsize=7, loc="upper left")
    ax4.grid(alpha=0.25)

    ax5 = fig.add_subplot(gs[1, 2])
    piv = bench.pivot_table(index=["origen", "destino"], columns="algoritmo", values="expandidos")
    red = (1 - piv["A* (haversine)"] / piv["Dijkstra"]) * 100
    ax5.hist(red, bins=18, color=C_AST, edgecolor="white")
    ax5.axvline(red.mean(), color=C_PATH, ls="--", lw=2, label=f"promedio {red.mean():.1f}%")
    ax5.axvline(0, color="k", lw=1)
    ax5.set_title(f"Reducción de nodos expandidos de A* vs Dijkstra\n({len(red)} pares origen-destino)",
                  fontweight="bold", fontsize=10)
    ax5.set_xlabel("% menos nodos expandidos con A*")
    ax5.set_ylabel("número de pares")
    ax5.legend(fontsize=8)

    ax6 = fig.add_subplot(gs[1, 3])
    x = np.arange(len(names))
    exp_mean = [summary.loc[n, "expandidos_prom"] for n in names]
    opt_pct = [summary.loc[n, "rutas_optimas_pct"] for n in names]
    bars = ax6.bar(x, exp_mean, color=cols)
    ax6.set_xticks(x, labels, fontsize=8)
    ax6.set_ylabel("nodos expandidos (promedio)")
    ax6.set_title("Promedio en todos los pares\n(etiqueta: % de rutas óptimas)", fontweight="bold", fontsize=10)
    for rect, p in zip(bars, opt_pct):
        ax6.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.2, f"{p:.0f}% óptimas",
                 ha="center", fontsize=8, fontweight="bold",
                 color="#1b7a2f" if p >= 99.99 else C_PATH)

    # --- Fila 3: tabla comparativa + análisis ----------------------------------------
    ax7 = fig.add_subplot(gs[2, 0:3])
    ax7.axis("off")
    ax7.set_title("Tabla comparativa (caso destacado)", fontweight="bold", loc="left")
    tbl = case_df.drop(columns="Ruta")
    t = ax7.table(cellText=tbl.values, colLabels=tbl.columns, loc="upper center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(10)
    t.scale(1, 2.0)
    for (r, c), cell in t.get_celld().items():
        if r == 0:
            cell.set_facecolor("#2b2d42")
            cell.set_text_props(color="white", fontweight="bold")
        elif r > 0:
            cell.set_facecolor(ALGO_COLORS[names[r - 1]] + "22")
            if tbl.columns[c] == "¿Óptima?" and tbl.iloc[r - 1, c] == "No":
                cell.set_text_props(color=C_PATH, fontweight="bold")

    ax8 = fig.add_subplot(gs[2, 3])
    ax8.axis("off")
    pct1 = adm[1.0]["admisible"].mean() * 100
    txt = (
        "Análisis de admisibilidad\n\n"
        f"• h = haversine (línea recta). Cada tramo\n  cumple w(u,v) ≥ h → h nunca sobrestima.\n"
        f"• Pares con h ≤ h*: {pct1:.0f}%  → ADMISIBLE\n"
        f"• Violaciones de consistencia: {cons[1.0]}\n  → CONSISTENTE (no reabre nodos)\n"
        f"• h×1.5 viola admisibilidad en\n  {(~adm[1.5]['admisible']).mean()*100:.0f}% de los pares; h×3 en {(~adm[3.0]['admisible']).mean()*100:.0f}%.\n"
        f"  Costo: rutas {summary.loc['A* ponderado (h×3)','sobrecosto_prom_pct']:.2f}% más largas (h×3).\n"
        "• Con h admisible A* es óptimo,\n  igual que Dijkstra, pero expande menos."
    )
    ax8.text(0.0, 1.0, txt, va="top", ha="left", fontsize=9.5, family="monospace",
             bbox=dict(boxstyle="round", facecolor="#f4f4f8", edgecolor="#bbbbcc"))

    fig.savefig(path, dpi=130)
    plt.close(fig)
