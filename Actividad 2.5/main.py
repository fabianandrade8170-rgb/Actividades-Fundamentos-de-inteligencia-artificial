"""Punto de entrada: corre el caso, el benchmark y genera el dashboard.

Uso:
    python main.py                                  # Xico -> Oaxaca
    python main.py --origen Xalapa --destino Tuxpan
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.analysis import (VARIANTS, admissibility_table, benchmark_all_pairs,
                          consistency_violations, run_variant, summarize)
from src.dashboard import build_dashboard
from src.graph_data import build_graph

OUT = Path("output")


def main() -> None:
    ap = argparse.ArgumentParser(description="A* vs Dijkstra en la red carretera centro-oriente de México")
    ap.add_argument("--origen", default="Xico")
    ap.add_argument("--destino", default="Oaxaca")
    ap.add_argument("--repeticiones", type=int, default=200, help="repeticiones para medir tiempo del caso destacado")
    args = ap.parse_args()

    graph, coords = build_graph()
    for c in (args.origen, args.destino):
        if c not in graph:
            raise SystemExit(f"Ciudad desconocida: {c}. Opciones: {', '.join(sorted(graph))}")
    OUT.mkdir(exist_ok=True)

    # 1) Caso destacado -------------------------------------------------------
    case = {v: run_variant(graph, coords, args.origen, args.destino, v, args.repeticiones) for v in VARIANTS}
    opt = case["Dijkstra"].cost
    case_df = pd.DataFrame([{
        "Algoritmo": v, "Costo (km)": round(r.cost, 1), "Nodos expandidos": r.expanded,
        "Nodos generados": r.generated, "Frontera máx.": r.max_frontier,
        "Tiempo (ms)": round(r.time_ms, 3), "¿Óptima?": "Sí" if abs(r.cost - opt) < 1e-9 else "No",
        "Ruta": " → ".join(r.path)} for v, r in case.items()])
    case_df.to_csv(OUT / "tabla_caso.csv", index=False)

    # 2) Admisibilidad / consistencia -------------------------------------------
    adm = {s: admissibility_table(graph, coords, s) for s in (1.0, 1.5, 3.0)}
    adm[1.0].to_csv(OUT / "admisibilidad_haversine.csv", index=False)
    cons = {s: consistency_violations(graph, coords, s) for s in (1.0, 1.5, 3.0)}

    # 3) Benchmark todos los pares ----------------------------------------------
    bench = benchmark_all_pairs(graph, coords, repeats=5)
    bench.to_csv(OUT / "benchmark_todos_los_pares.csv", index=False)
    summary = summarize(bench)
    summary.to_csv(OUT / "tabla_resumen.csv")

    # 4) Reporte en consola + markdown ----------------------------------------------
    print(f"\n=== Caso: {args.origen} → {args.destino} ===")
    print(case_df.drop(columns="Ruta").to_string(index=False))
    print(f"\nRuta óptima: {case_df.loc[0, 'Ruta']}")
    print("\n=== Admisibilidad (todas las metas) ===")
    for s, t in adm.items():
        print(f"h×{s}: {t['admisible'].mean()*100:.1f}% de los pares cumplen h ≤ h*  |  "
              f"violaciones de consistencia: {cons[s]}")
    print("\n=== Resumen sobre todos los pares origen-destino ===")
    print(summary.to_string())

    with open(OUT / "tablas.md", "w", encoding="utf-8") as f:
        f.write(f"## Caso {args.origen} → {args.destino}\n\n")
        f.write(case_df.drop(columns="Ruta").to_markdown(index=False) + "\n\n")
        f.write(f"Ruta óptima: {case_df.loc[0, 'Ruta']}\n\n")
        f.write("## Resumen en todos los pares origen-destino\n\n")
        f.write(summary.to_markdown() + "\n")

    # 5) Dashboard ------------------------------------------------------------------
    build_dashboard(graph, coords, args.origen, args.destino, case, case_df, adm, cons, bench, summary,
                    OUT / "dashboard.png")
    print(f"\nArchivos generados en ./{OUT}/ (dashboard.png, tablas, CSV)")


if __name__ == "__main__":
    main()
