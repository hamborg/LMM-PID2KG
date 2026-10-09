# hitl_refinement/graph_evaluation.py

from __future__ import annotations

from pathlib import Path
import csv
import json

from rdflib import Graph

from sparql_queries.run_query import load_query, shorten_iri
from utils.default_settings import Default


def run_hitl_evaluation(
    ttl_path: str | Path,
    queries: list[str],
    eval_dir: str | Path,
    output_format: str = Default.OUTPUT_FORMAT,
    file_suffix: str = "",
) -> dict[str, int | str]:
    """
    Run the selected SPARQL queries on a TTL file and save the results.

    Returns a summary dict like:
        {"A_01": 12, "V_03": 0, "H_02": "ERROR"}
    """
    ttl_path = Path(ttl_path)
    eval_dir = Path(eval_dir)
    eval_dir.mkdir(parents=True, exist_ok=True)

    if not ttl_path.exists():
        raise FileNotFoundError(f"TTL file not found - No evaluation could be done:\n{ttl_path}")

    g = Graph()
    g.parse(ttl_path)

    summary: dict[str, int | str] = {}

    for q in queries:
        query_text, query_index = load_query(q)

        try:
            results = g.query(query_text)
        except Exception:
            summary[query_index] = "ERROR in query execution"
            continue

        rows = []
        for row in results:
            rows.append([shorten_iri(str(v)) for v in row])

        num_results = len(rows)
        summary[query_index] = num_results

        suffix = f"_{file_suffix}" if file_suffix else ""
        out_stem = eval_dir / f"{query_index}{suffix}"

        if output_format == "json":
            out_file = out_stem.with_suffix(".json")
            with out_file.open("w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

        else:
            out_file = out_stem.with_suffix(".csv")
            with out_file.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([str(v) for v in results.vars])
                writer.writerows(rows)

    return summary