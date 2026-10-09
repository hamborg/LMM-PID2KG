# hitl_refinement/continue_hitl.py

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from utils.default_settings import Default

from hitl_refinement.hitl_session import HITLSession
from hitl_refinement.workspace import *
from hitl_refinement.evaluation_scheme_manipulator.duplicate_evaluation_blocks import trim_evaluation_blocks


def continue_hitl_session(args: Namespace) -> HITLSession:
    """
    Interactively select a previous HITL session and a checkpoint turn,
    then create a new branched session continuing from that point.
    """
    # --- Select old session ---
    session_dirs = list_session_dirs()
    old_session_dir = select_session(session_dirs)

    old_config = old_session_dir / Default.SESSION_CONFIG
    if not old_config.exists():
        raise FileNotFoundError(f"Missing session config:\n{old_config}")

    # --- Load old session ---
    old_session = HITLSession.load(old_config)
    # print(f"DEBUG: Loaded old session from {old_config} with turn index {old_session.turn_index} and turns dir {old_session.turns_dir}")                      # DEBUG statement
    
    # --- Select checkpoint turn ---
    turn_dirs = list_turn_dirs(old_session.turns_dir)
    if args.continue_mode == "latest":
        selected_turn_dir = turn_dirs[-1]
    else:
        selected_turn_dir = select_turn(turn_dirs)

    selected_turn_name = selected_turn_dir.name
    selected_turn_index = extract_turn_index(selected_turn_name)
    selected_output_ttl = selected_turn_dir / "output_ttl.ttl"
    if not selected_output_ttl.exists():
        raise FileNotFoundError(
            f"Selected turn has no output_ttl.ttl file:\n{selected_output_ttl}"
        )

    # --- Create new branched workspace ---
    session_name = make_branched_session_name(old_session, old_session_dir.name, selected_turn_index)
    session_paths = create_hitl_workspace(
        level=old_session.level,
        exp=old_session.exp,
        session_name=session_name,
    )

    # --- Copy source artifacts ---
    old_source_dir = Path(old_session.workspace_dir) / "source"
    if not old_source_dir.exists():
        raise FileNotFoundError(f"Missing source folder in old session:\n{old_source_dir}")

    copy_tree_contents(old_source_dir, session_paths["source"])

    # --- Copy previous turns/evaluations up to chosen checkpoint ---
    copy_turns_up_to(
        old_turns_dir=Path(old_session.turns_dir),
        new_turns_dir=session_paths["turns"],
        max_turn_name=selected_turn_name,
    )
    copy_evaluations_up_to(
        old_eval_dir=Path(old_session.evaluations_dir),
        new_eval_dir=session_paths["evaluations"],
        max_turn_name=selected_turn_name,
    )
    copy_session_log_up_to(
        old_session_dir / "session_log.jsonl",
        session_paths["root"] / "session_log.jsonl",
        selected_turn_index,
    )
    # Trim evaluation scheme blocks to match turn interception point.
    trim_evaluation_blocks(
        session_paths=session_paths,
        turn_index=selected_turn_index,
    )

    # --- Point working TTL to the copied checkpoint output ---
    new_working_ttl = session_paths["turns"] / selected_turn_name / "output_ttl.ttl"
    if not new_working_ttl.exists():
        raise FileNotFoundError(
            f"Copied checkpoint TTL not found in new session:\n{new_working_ttl}"
        )

    # --- Build new branched session ---
    new_note = " ".join(args.note).strip() if args.note else ""
    if not new_note:
        new_note = f"continued_from_{old_session_dir.name}_{selected_turn_name}"

    new_session = HITLSession(
        level=old_session.level,
        exp=old_session.exp,
        provider=args.provider or old_session.provider,
        mode=args.mode or old_session.mode,
        source_experiment_dir=old_session.source_experiment_dir,
        source_ttl=old_session.source_ttl,
        working_ttl=str(new_working_ttl),
        selected_queries=list(args.sparql) if args.sparql else list(old_session.selected_queries),
        note=new_note,
        workspace_dir=str(session_paths["root"]),
        turns_dir=str(session_paths["turns"]),
        evaluations_dir=str(session_paths["evaluations"]),
        images_dir=str(session_paths["images"]),
        session_config_path=str(session_paths["config"]),
        turn_index=selected_turn_index + 1,
        parent_session=old_session_dir.name,
        parent_turn=selected_turn_index,
    )

    new_session.save(session_paths["config"])

    print("\n=== HITL SESSION BRANCHED ===")
    print(f"Old session      : {old_session_dir}")
    print(f"Checkpoint turn  : {selected_turn_name}")
    print(f"New session      : {session_paths['root']}")
    print(f"Working TTL      : {new_working_ttl}")
    print(f"Next turn index  : {new_session.turn_index}")

    return new_session