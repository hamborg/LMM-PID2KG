# run.py
import argparse
from experiments.run_experiment import run_experiments
from utils.default_settings import Default

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("-l", "--lvl", "--level", dest="level", default=Default.LEVEL, type=int, help="Level number 1-4")
    ap.add_argument("-e", "--exp", "--experiment", dest="exp", required=True, nargs="+", help="Experiment number (e.g. 3, 12 or 03). Multiple experiments are allowed.")  # No default, must specify at least one experiment
    ap.add_argument("-m", "--provider", "--llm", "--lmm", dest="provider", type=str.lower, default=Default.PROVIDER, help="LMM: Gemini or Gpt (Default: Gemini)")
    ap.add_argument("-p", "--prompt", "--version", "--file", dest="prompt", nargs="+", default=Default.PROMPT, help="Prompt for the LMM. If not specified, will use 'prompt.md' in the experiment folder. If specified, will look for 'prompt_{prompt}.md' (e.g. prompt_v2.md) in the experiment folder.")
    ap.add_argument("-t", "--no-timestamp", action="store_true", help="Do not append timestamp to output filename")
    ap.add_argument("-r", "--runs", dest="tests", type=int, default=Default.RUNS, help="Number of runs/tests for each exp. (default 1, max 25)")
    ap.add_argument("-n", "--comment", "--note", dest="note", nargs="+", default=Default.NOTE, help="Append a comment/note to the output filename (e.g. 'fewshot' or 'v2prompt')")

    args = ap.parse_args()

    # Call the experiment runner
    run_experiments(args)


if __name__ == "__main__":
    main()
