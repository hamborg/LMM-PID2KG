# run_query.py

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from rdflib import Graph
import json
import csv
import questionary

from sparql_queries.PCLA.pcla_queries import PCLA
from utils.runner_utils import validate_inputs_and_find_folder

from sparql_queries.query_logger import QueryLogger, QueryMetrics
from experiments.run_logger import Timer


def select_ttl_file(exp_dir: Path) -> Path:
    """
    Present a list of TTL files in the experiment folder and let the user select which one to analyze.
    """
    ttl_files = sorted(exp_dir.glob("*.ttl"))

    if not ttl_files:
        raise FileNotFoundError("No TTL files found in experiment folder:\n" + str(exp_dir))

    choices = [f.name for f in ttl_files]

    selected = questionary.select(
        "Select TTL file to analyze:",
        choices=choices
    ).ask()

    return exp_dir / selected


def shorten_iri(value: str) -> str:
    s = str(value)

    # Step 1: replace # with :
    if "#" in s:
        s = s.replace("#", ":")

    # Step 2: if no # was present, replace the last / with :
    elif "/" in s:
        left, right = s.rsplit("/", 1)

        # Specific changes:
        if "rdf-syntax" in left.lower():
            left = "rdf"
        if "rdf-schema" in left.lower():
            left = "rdfs"
        if "mybuilding" in left.lower():
            left = "inst"

        s = f"{left}:{right}"

    # Step 3: remove everything before the last remaining /
    if "/" in s:
        s = s.rsplit("/", 1)[-1]

    return s


def load_query(query_input: str) -> tuple[str, str]:
    """
    Load a SPARQL query from the queries folder based on a query identifier (e.g. "V_01") or filename.
    Returns the query string and the query name (filename without extension).
    """
    query_dir = Path("sparql_queries/queries")

    sparql_files = sorted(query_dir.glob("*.rq")) + sorted(query_dir.glob("*.sparql"))
    if not sparql_files:
        raise FileNotFoundError("No SPARQL/RQ files found in sparql_queries folder")

    # --- NORMALIZE INPUT ---
    q = query_input.upper().replace(" ", "").replace("-", "").replace("__", "_")

    letter = q[0]
    number = int(q[1:].replace("_", ""))

    prefix = f"{letter}_{number:02d}"

    # --- FIND MATCHING FILE ---
    matches = [
        p for p in query_dir.iterdir()
        if p.is_file() and p.name.upper().startswith(prefix)
    ]

    if not matches:
        print(f"\nNo SPARQL file found matching '{prefix}'. Please select from the list.")
        choices = [f.name for f in sparql_files]

        selected = questionary.select(
            "Select SPARQL file to use for query:",
            choices=choices
        ).ask()

        matches = [query_dir / selected]

    query_path = matches[0]

    return query_path.read_text(encoding="utf-8"), query_path.stem


def get_query_list(args: Namespace) -> tuple[list[tuple[str, int | None]], str]:
    """
    Get a list of queries to run based on the provided arguments.
    Returns a list of tuples containing the query filename and the associated PCLA group (or None if not from a PCLA group), as well as a string for pcla-printing.
    """
    if args.hitl:
        query_list = [(q, None) for q in args.hitl]
        pcla_print = ""
        print("Chosen PCLA's and queries will be overwritten by the specified HITL queries.")
    elif args.pcla:
        pcla_lookup = PCLA()
        query_list = pcla_lookup.get_queries(args.pcla)
        print("Chosen queries will be overwritten by the specified PCLA groups.")
        print("> Running queries from PCLA groups:", args.pcla)
        pcla_print = "- PCLA's: " + ", ".join(args.pcla) + " "
    else:
        query_list = [(q, None) for q in args.sparql]
        pcla_print = ""

    return query_list, pcla_print


def run_query(args: Namespace):
    """
    Main function to run SPARQL queries on a specified experiment's TTL data.
    Handles loading the graph, running queries, and saving results.
    """
    # Locate experiment
    exp_dir = validate_inputs_and_find_folder(args.level, args.exp)

    # Select TTL interactively
    ttl_path = select_ttl_file(exp_dir)
    
    print(f"\n> Querying TTL: {ttl_path.name}")

    # Load RDF graph
    g = Graph()
    g.parse(ttl_path)

    print(f"Loaded graph with {len(g)} triples.")

    # Load queries from PCLA groups (or default HITL queries) if specified, otherwise use queries
    query_list, pcla_print = get_query_list(args)

    # Logger for query metrics lives inside the experiment folder
    logger = QueryLogger(exp_dir / "sparql_runs.jsonl")

    # Loop through queries (if multiple specified) and run them sequentially, saving results to separate files
    summary = []

    for q, pcla_id in query_list:
        query, results = _run_individual_query(
            args,
            exp_dir=exp_dir,
            graph=g,
            pcla=pcla_id,
            sparql_filename=q,
            ttl_path=ttl_path,
            logger=logger,
        )
        summary.append((query, results))
    
    # Print summary of all queries
    print(f"\n=== QUERY SUMMARY - Level {args.level}, Experiment {args.exp} {pcla_print}===")
    for qid, result in sorted(summary):
        qid = "_".join(qid.split("_", 2)[:2])
        print(f" {qid:<6} : {result} result(s)")


def _run_individual_query(
        args: Namespace,
        exp_dir: Path,
        graph: Graph,
        pcla: int | None,
        sparql_filename: str,
        ttl_path: Path,
        logger: QueryLogger,
) -> tuple[str, int | str]:
    """Run a single SPARQL query on the specified experiment's TTL data and save results to CSV or JSON."""

    # --- PARSE ARGS ---
    note = " ".join(args.note).strip()+" " if len(args.note[0]) > 0 else ""
    output = args.output

    
    # --- Run SPARQL ---
    # Load query
    query, query_name = load_query(sparql_filename)
    print(f"\nRunning query '{query_name}'")
    
    # Run query and catch any errors
    try:
        with Timer() as t:
            results = graph.query(query)
        elapsed = float(t.elapsed)
    except Exception as e:
        print(f"\n\n>>> Error occurred while running query '{query_name}': \n{e} <<<\n\n")
        return query_name, "ERROR. No"


    # --- SAVE RESULTS ---
    # Convert results
    rows = []
    for row in results:
        rows.append([shorten_iri(str(v)) for v in row])
    num_results = len(rows)

    # Save results
    results_dir = exp_dir / "Query_results"
    results_dir.mkdir(exist_ok=True)

    # Output filenaming and path
    query_naming = f"PCLA_{pcla} Q_{query_name}" if pcla else f"Q_{query_name}"
    result_file_name = f"{ttl_path.stem} - {note}{query_naming}"
    out_file_path = results_dir / result_file_name

    # Save in chosen format
    if output == "json":
        # Save to JSON
        out_file = out_file_path.parent / (out_file_path.name + ".json")

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

    elif output == "csv":
        # Save to CSV
        out_file = out_file_path.parent / (out_file_path.name + ".csv")

        with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")

            # write column headers from SPARQL variables
            writer.writerow([str(v) for v in results.vars])

            # write rows
            writer.writerows(rows)


    # --- LOG METRICS ---
    metrics = QueryMetrics(
        level=args.level,
        exp=args.exp,
        ttl_file=ttl_path.name,
        query=query_name,
        output_file=out_file.name,
        num_results=num_results,
        elapsed_seconds=elapsed,
    )
    logger.append(metrics)

    # --- PRINT SUMMARY ---
    if num_results == 0:
        print(f"> OBS! The query returned NO RESULTS.")
    else:
        print(f"> The query returned {num_results} result(s).")

    print(f"\nSaved results to:\n{out_file.resolve()}")

    return query_name, num_results