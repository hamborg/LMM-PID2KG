# runner_utils.py

from pathlib import Path

def validate_inputs_and_find_folder(level: int, exp: str):
    # --- NORMALIZE AND VALIDATE ---
    if level < 0 or level > 4:
        raise ValueError("Level must be 1-4")

    exp_num = int(exp)
    exp_two = f"{exp_num:02d}"

    base_dir = Path("experiments")
    lvl_dir = base_dir / f"lvl_{level}"
    if not lvl_dir.exists():
        raise FileNotFoundError(lvl_dir)

    # --- FIND EXPERIMENT FOLDER ---
    matches = [
        p for p in lvl_dir.iterdir()
        if p.is_dir()
        and (p.name.startswith(exp_two + " ") or p.name == exp_two)
    ]

    if not matches:
        raise FileNotFoundError(
            f"No experiment folder starting with '{exp_two}' in {lvl_dir}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple experiment folders match '{exp_two}':\n" + "\n".join(p.name for p in matches)
        )

    return matches[0]


def validate_multiple_runs(args):
    total_runs = len(args.exp) * args.tests * len(args.prompt)
    if total_runs > 1:
        print("> OBS! When running multiple experiments and/or multiple runs and/or multiple prompts, the total number of runs increases significantly.")
        print(f"You are about to run {len(args.exp)} experiments with {args.tests} runs and {len(args.prompt)} prompts each ({total_runs} total runs). This may take a long time and hit API rate limits.\n")
        
        # Reduce number of runs?
        if args.tests > 1:
            while True:
                run_reduce_res = input("Do you want to reduce the number of runs to 1? (y/n): ").strip().lower()
                if run_reduce_res in ['y', 'yes', 'ok', 'j', 'ja', '']:
                    if run_reduce_res == "": print("(Defaulting to 'yes'.)")
                    args.tests = 1
                    break
                elif run_reduce_res in ['n', 'no', 'nej']:
                    print(f"> Continuing with {args.tests} runs per experiment!")
                    break
                else:
                    print("Please enter 'yes' or 'no'.")

        if total_runs > 4:
            while True:
                cont_res = input(f"Do you want to continue running {total_runs} experiments? (y/n): ").strip().lower()
                if cont_res in ['y', 'yes', 'ok', 'j', 'ja', '']:
                    if cont_res == "": print("(Defaulting to 'yes'.)")
                    break
                elif cont_res in ['n', 'no', 'nej']:
                    print("> Aborting experiment.")
                    raise SystemExit(0)
                else:
                    print("Please enter 'yes' or 'no'.")

        print(f"\n>>> {total_runs} runs will be executed. <<<\n")