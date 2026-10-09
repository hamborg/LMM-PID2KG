# hitl_refinement/run_hitl.py

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import shutil

from hitl_refinement.evaluation_scheme_manipulator.update_scheme import copy_evaluation_template
from hitl_refinement.graph_evaluation import run_hitl_evaluation
from utils.runner_utils import validate_inputs_and_find_folder
from hitl_refinement.workspace import create_hitl_workspace, make_session_name
from hitl_refinement.hitl_session import HITLSession
from sparql_queries.run_query import select_ttl_file


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _find_images_dir(exp_dir: Path) -> Path:
    images_dir = exp_dir / "images"
    if not images_dir.exists():
        raise FileNotFoundError(f"Missing images folder in experiment:\n{images_dir}")
    return images_dir


def _copy_source_images(images_dir: Path, target_dir: Path) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for f in sorted(images_dir.iterdir(), key=lambda x: x.name.lower()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
            shutil.copy2(f, target_dir / f.name)
            copied.append(f.name)

    return copied


def _copy_source_ttl(ttl_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)

    target_ttl = target_dir / ttl_path.name
    shutil.copy2(ttl_path, target_ttl)

    return target_ttl


def _run_initial_evaluation(ttl_path: Path, session_paths: dict[str, Path], args: Namespace) -> dict[str, int | str]:
    source_eval_dir = session_paths["source"] / "evaluations"
    source_eval_dir.mkdir(parents=True, exist_ok=True)
    queries = list(args.sparql)  # Ensure it's a list for multiple iterations

    if args.sparql:
        try:
            evaluation_summary = run_hitl_evaluation(
                ttl_path=ttl_path,
                queries=queries,
                eval_dir=source_eval_dir,
                file_suffix="T0",
            )
            print("\n=== SOURCE TTL EVALUATED (T0) ===")
            for qid, result in sorted(evaluation_summary.items(), key=lambda x: x[0]):
                print(f" {qid:<6} : {result} result(s)")
            return evaluation_summary
        except Exception as e:
            print(f"\n[WARNING] Failed to evaluate source TTL baseline:\n{e}\n")
            return {}

def run_hitl(args: Namespace) -> HITLSession:
    """
    Initialize a HITL session from an existing experiment and selected TTL file.
    """

    # --- Locate experiment ---
    exp_dir = validate_inputs_and_find_folder(args.level, args.exp)

    # --- Select TTL interactively ---
    ttl_path = select_ttl_file(exp_dir)

    # --- Find images ---
    images_dir = _find_images_dir(exp_dir)

    # --- Create workspace/session ---
    session_name = make_session_name(args)
    session_paths = create_hitl_workspace(
        level=args.level,
        exp=args.exp,
        session_name=session_name,
    )

    # --- Copy source artifacts into workspace ---
    copied_ttl = _copy_source_ttl(ttl_path, session_paths["source"])
    copied_images = _copy_source_images(images_dir, session_paths["images"])
    copy_evaluation_template(session_paths["evaluations"])

    # --- Evaluate the copied source TTL as baseline (Turn 0) ---
    _run_initial_evaluation(copied_ttl, session_paths, args)        
            
    # --- Build session object ---
    session = HITLSession(
        level=args.level,
        exp=args.exp,
        provider=args.provider,
        mode=args.mode,
        source_experiment_dir=str(exp_dir),
        source_ttl=str(ttl_path),
        working_ttl=str(copied_ttl),
        selected_queries=list(args.sparql),
        note=" ".join(args.note).strip(),
        workspace_dir=str(session_paths["root"]),
        turns_dir=str(session_paths["turns"]),
        evaluations_dir=str(session_paths["evaluations"]),
        images_dir=str(session_paths["images"]),
        session_config_path=str(session_paths["config"]),
        turn_index=1,
    )

    # --- Save initial session manifest ---
    session.save(session_paths["config"])

    # --- Print summary ---
    print("\n=== HITL SESSION INITIALIZED ===")
    print(f"Experiment      : L{args.level} E{args.exp}")
    print(f"Provider        : {args.provider}")
    print(f"Mode            : {args.mode}")
    print(f"Source TTL      : {ttl_path.name}")
    print(f"Copied TTL      : {copied_ttl}")
    print(f"Images copied   : {len(copied_images)}")
    print(f"Queries         : {', '.join(args.sparql) if args.sparql else '(none)'}")
    print(f"Workspace       : {session_paths['root']}")
    print("\nSession is ready. Refinement loop not implemented yet.")

    return session