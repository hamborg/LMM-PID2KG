# run_experiment.py
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from datetime import datetime

from lmm_fw.choose_lmm import choose_LMM
from lmm_fw.multimodal.parts import TextPart
from lmm_fw.multimodal.image_parts import load_image
from lmm_fw.providers.base import BaseLMMClient

from experiments.run_logger import ExperimentLogger, RunMetrics, Timer
from experiments.ttl_extract import *
from utils.default_settings import Default
from utils.runner_utils import *

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def run_experiments(
    args: Namespace,
):
    """Validate arguments. Loop over experiments"""

    # Validate runs argument
    if args.tests < 1:
        raise ValueError("--runs must be >= 1")
    if args.tests > 25:
        raise ValueError("--runs max is 25. No more than 25 runs allowed per minute (API limit)")

    # Validate multiple runs with multiple experiments
    validate_multiple_runs(args)


    # Choose the LMM client (once)
    client = choose_LMM(args.provider)

    # --- LOOP OVER EXPERIMENTS ---
    run_no = 1
    for exp in args.exp:
        for prompt_version in args.prompt:
            _run_individual_experiment(
                client=client,
                args=args,
                exp=exp,
                prompt=prompt_version,
                run_no=run_no
            )
            run_no += 1


def _run_individual_experiment(
    *,
    client: BaseLMMClient,
    args: Namespace,
    exp: str,
    prompt: str = "",
    run_no: int = 1,
):
    """Run a single experiment the specified number of times."""

    # --- PARSE ARGS ---
    level = args.level
    provider = args.provider
    timestamp = (not args.no_timestamp)
    tests = args.tests
    note = " ".join(args.note).strip() if args.note else ""
    prompt_suffix = prompt or ""

    # --- VALIDATE PATH INPUTS AND FIND FOLDER ---
    exp_dir = validate_inputs_and_find_folder(level, exp)

    # --- BUILD PROMPT AND IMAGE INPUT ---
    prompt_name = f"prompt_{prompt_suffix}.md" if prompt_suffix else "prompt.md"
    prompt_path = exp_dir / prompt_name
    
    images_dir = exp_dir / "images"
    
    if not prompt_path.exists():
        print(f"Missing {prompt_name}")
        return  # Skip this experiment but continue with others
    if not images_dir.exists():
        print(f"Missing {images_dir}")
        return  # Skip this experiment but continue with others

    # Load prompt
    prompt_text = prompt_path.read_text(encoding="utf-8")
    prompt_chars = len(prompt_text)

    parts = [TextPart(prompt_text)]

    # Load images
    image_paths = sorted(
        (p for p in images_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTS),
        key=lambda p: p.name.lower()
    )
    num_images = len(image_paths)

    for p in image_paths:
        parts.append(load_image(p))

    
    # Log file lives inside the experiment folder
    logger = ExperimentLogger(exp_dir / "runs.jsonl")


    # --- RUN MODEL ---
    # Run the experiment the specified number of times
    for t in range(tests):
        run_no += t
        test = t + 1

        # Get model name 
        model_name = getattr(client, "model_name", None)

        # Print summary of what is about to run
        print(f"\n--- Experiment run number {run_no} ---",
            f"\nLevel {level}, Exp {exp},",
            f"{'Test ' + str(test) + ' ' if tests > 1 else ''}is running with:",
            f"\n> MODEL: {model_name or provider}",
            f"\n> PROMPT: {prompt_name}.")
        
        # RUN THE MODEL:
        try:
            # Time the call
            with Timer() as t:
                # Call the LMM and get output text
                output = client.generate(parts)
            elapsed = float(t.elapsed)
        except Exception as e:
            print("[ERROR] Model call failed:", repr(e))
            raise SystemExit(2)
        

        # --- SAVE COMPLETE OUTPUT ---
        time = datetime.now().strftime(Default.TIMESTAMP_FORMAT) if timestamp else ""

        # Output file name
        name = (f"L{level}E{exp}"
            # f" {provider}" # LLM provider
            f"{' ' + prompt_suffix if len(prompt_suffix) > 0 else ''}"
            f"{' ' + test if tests > 1 else ''}"
            f"{' - ' + time if time else ''}"
            f"{' ' + note if note else ''}"
            ".txt"
        )
        out_path = exp_dir / "Outputs" / name
        out_path.write_text(output, encoding="utf-8")


        # --- LOG METRICS ---
        metrics = RunMetrics(
            provider=provider,
            level=level,
            exp=str(exp),
            test_index=test,
            output_file=out_path.name,
            prompt=prompt_name,
            prompt_chars=prompt_chars,
            num_images=num_images,
            elapsed_seconds=elapsed,
            model_name=model_name() if callable(model_name) else model_name,
            timestamp_utc="",  # logger fills if empty
        )
        logger.append(metrics)


        # --- PRINT SUMMARY ---
        print(f"\nSaved output to: \n{out_path.resolve()} \n(Call took {elapsed:.2f} sec.)\n")


        # --- EXTRACT & SAVE TTL ---
        ttl = extract_ttl_from_output(output)

        # Save TTL if found and print summary
        if ttl is not None:
            ttl_name = out_path.with_suffix(".ttl").name  # same base name, .ttl extension
            ttl_path = exp_dir / ttl_name
            ttl_path.write_text(ttl + "\n", encoding="utf-8")
            print(f"Saved TTL to: \n{ttl_path.resolve()}")
        else:
            print("No TTL block found; .ttl not written.")