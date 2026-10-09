# sparql.py

import argparse
from sparql_queries.run_query import run_query
from utils.default_settings import Default

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("-l", "--lvl", "--level", dest="level", default=Default.LEVEL, type=int, help="Level number 1-4")
    ap.add_argument("-e", "--exp", "--experiment", dest="exp", required=True, help="Experiment number (e.g. 3, 12 or 03). Multiple experiments are not allowed.")  # No default for experiment, as it's required.
    ap.add_argument("-q", "--query", "--sparql", dest="sparql", nargs="+", default=Default.QUERIES, help="Sparql queries to run. Should correspond to a .sparql file in the 'sparql_queries/queries' folder (e.g. 'A_00.rq'). Default is 'A_00: Components'.")
    ap.add_argument("-g", "-p", "--query-group", "--pcla", "--group", dest="pcla", nargs="+", choices=["0","1","2","3","4","5","6","7"], help="Run all queries in a PCLA group [1-7]. This will override the -q/--query argument.")
    ap.add_argument("-n", "--comment", "--note", dest="note", nargs="+", default=Default.NOTE, help="Append a comment/note to the output filename.")
    ap.add_argument("-f", "--file", "--format", "--output", dest="output", choices=["csv", "json"], default=Default.OUTPUT_FORMAT, help="Output file format. Default is csv.")

    # --- Optional HITL flag for running the default HITL evaluation queries (A_01, V_01, A_06, V_12, Z_01) on the TTL. ---
    # This is a convenience flag to quickly run the standard HITL evaluation queries without having to specify them all in the -q argument.
    # It will look for the default HITL query files in the 'sparql_queries/queries' folder (e.g. 'A_01.rq', 'V_01.rq', etc.).
    # If this flag is used, it will override any queries specified in the -q argument and run the default HITL queries instead.
    ap.add_argument("--hitl", action="store_const", const=Default.HITL_QUERIES, default=False, help="Sparql for the default HITL evaluations.")

    args = ap.parse_args()

    # Call the experiment runner
    run_query(args)


if __name__ == "__main__":
    main()
