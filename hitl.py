# hitl.py

import argparse
from utils.default_settings import Default

from hitl_refinement.run_hitl import run_hitl
from hitl_refinement.hitl_loop import run_hitl_loop
from hitl_refinement.continue_hitl import continue_hitl_session


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("-m", "--provider", "--llm", "--lmm", dest="provider", type=str.lower, default=Default.PROVIDER, help="LMM: Gemini or Gpt (Default: Gemini)")
    ap.add_argument("-l", "--lvl", "--level", dest="level", default=Default.LEVEL, type=int, help="Level number 1-4")
    ap.add_argument("-e", "--exp", "--experiment", dest="exp", default=Default.HITL_EXPERIMENT, help="Experiment number (e.g. 3, 12 or 03). Multiple experiments are not allowed.")
    ap.add_argument("-q", "--query", "--sparql", dest="sparql", nargs="+", default=Default.HITL_QUERIES, help="Sparql queries to run. Should correspond to a .sparql file in the 'sparql_queries/queries' folder (e.g. 'A_00.rq'). Default is 'A_00: Components'.")
    # ap.add_argument("-g", "-p", "--query-group", "--pcla", "--group", dest="pcla", nargs="+", choices=["0","1","2","3","4","5","6","7"], help="Run all queries in a PCLA group [1-7]. This will override the -q/--query argument.")
    ap.add_argument("-n", "--comment", "--note", dest="note", nargs="+", default=Default.NOTE, help="Append a comment/note to the output filename.")
    ap.add_argument("-s", "--mode", "--session", dest="mode", type=str.upper, choices=["A", "B"], default=Default.HITL_MODE, help="HITL session mode. A = conversational memory, B = stateless iterative refinement. Default is A.")
    ap.add_argument("-c", "--con", "--old", "--continue", dest="continue_mode", nargs="?", const="interactive",  default=None, help="Continue a HITL session from an existing session. Add 'latest' to continue from the latest turn.")

    args = ap.parse_args()

    # Decide how to start session
    if args.continue_mode:
        hitl_session = continue_hitl_session(args)
    else:
        # Initialize the HITL session and workspace
        hitl_session = run_hitl(args)

    if hitl_session is None:
        raise RuntimeError("HITL session initialization failed.")

    # Run the HITL loop
    run_hitl_loop(hitl_session)

if __name__ == "__main__":
    main()
