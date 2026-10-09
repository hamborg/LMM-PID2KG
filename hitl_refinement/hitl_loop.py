# hitl_refinement/hitl_loop.py

from __future__ import annotations

from pathlib import Path

from lmm_fw.choose_lmm import choose_LMM
from experiments.run_logger import Timer

from utils.default_settings import Default

from hitl_refinement.hitl_session import HITLSession
from hitl_refinement.hitl_logger import HITLLogger, HITLMetrics
from hitl_refinement.hitl_prompting import build_hitl_parts
from hitl_refinement.ttl_manager import read_ttl, prepare_turn_artifacts
from hitl_refinement.workspace import make_dir
from hitl_refinement.graph_evaluation import run_hitl_evaluation
from hitl_refinement.evaluation_scheme_manipulator.update_scheme import update_excel_scheme


def prompt_user_instruction(turn_index: int) -> str | None:
    """
    Ask the user for the next HITL instruction.

    Empty input ends the session loop.
    """
    print(f"\n=== HITL TURN {turn_index:02d} ===")
    print("Enter a refinement instruction:")

    instruction = input("> ").strip()
    return instruction if instruction else None


def make_history_block(turn_index: int, instruction_text: str) -> str:
    """
    Simple textual history unit for conversational mode A.
    """
    return f"Turn {turn_index:02d} instruction:\n{instruction_text.strip()}"


def rebuild_history_blocks(session: HITLSession) -> list[str]:
    """
    Rebuild conversational history for mode A from existing copied turns.
    Only prior instructions are included for now.

    NOTE: Changes need to be made if the history block structure is extended to include model outputs or other turn artifacts. 
    """
    history_blocks: list[str] = []

    turns_dir = Path(session.turns_dir)
    if not turns_dir.exists():
        return history_blocks

    for turn_dir in sorted(turns_dir.iterdir(), key=lambda p: p.name.lower()):
        if not turn_dir.is_dir() or not turn_dir.name.startswith("turn_"):
            continue

        instruction_file = turn_dir / "instruction.txt"
        if not instruction_file.exists():
            continue

        try:
            turn_index = int(turn_dir.name.split("_", 1)[1])
        except Exception:
            continue

        instruction_text = instruction_file.read_text(encoding="utf-8").strip()
        if instruction_text:
            history_blocks.append(make_history_block(turn_index, instruction_text))

    return history_blocks


def run_hitl_loop(session: HITLSession) -> None:
    """
    Execute the iterative HITL refinement loop for an existing session.
    """
    # session = HITLSession.load(session_path)

    logger = HITLLogger(Path(session.workspace_dir) / "session_log.jsonl")
    client = choose_LMM(session.provider)

    print("\n=== HITL LOOP STARTED ===")
    print(f"Workspace   : {session.workspace_dir}")
    print(f"Provider    : {session.provider}")
    print(f"Mode        : {session.mode}")
    print(f"Current TTL : {session.working_ttl}")
    print(f"Queries     : {', '.join(session.selected_queries) if session.selected_queries else '(none)'}")
    print("\n\nPress ENTER on an empty line to stop the HITL session.")

    history_blocks: list[str] = rebuild_history_blocks(session) if session.mode == "A" else []
    if history_blocks:
        print(f"Rebuilt {len(history_blocks)} prior history block(s) for mode A.")

    while True:
        instruction_text = prompt_user_instruction(session.turn_index)
        if (instruction_text is None) or \
            (instruction_text.lower() in ["exit", "quit", "tak", "thanks", "stop", "end"]):
                print("\nHITL loop ended by user.")
                break

        current_ttl = read_ttl(session.working_ttl)
        turn_dir = make_dir(session.turns_dir, session.turn_index)
        turn_eval_dir = make_dir(session.evaluations_dir, session.turn_index)

        # Build prompt parts for the current turn 
        parts = build_hitl_parts(
            session=session,
            instruction_text=instruction_text,
            current_ttl=current_ttl,
            history_blocks=history_blocks,
        )

        # Call and send the prompt parts to the LMM model, and measure elapsed time.
        try:
            with Timer() as t:
                raw_output = client.generate(parts)
            elapsed = float(t.elapsed)
        except Exception as e:
            print(f"\n[ERROR] HITL model call failed:\n{e}\n")
            break

        # Prepare and save turn artifacts (input TTL, instruction, raw output, refined TTL)
        try:
            artifacts = prepare_turn_artifacts(
                turn_dir=turn_dir,
                input_ttl_text=current_ttl,
                instruction_text=instruction_text,
                raw_output=raw_output, 
            )
        except Exception as e:
            print(f"\n[ERROR] Failed to save HITL turn artifacts:\n{e}\n")
            break

        # Update session state
        session.working_ttl = str(artifacts["output_ttl"])
        
        # History append for conversational mode A.
        if session.mode == "A":
            history_blocks.append(make_history_block(session.turn_index, instruction_text))
        # NOTE: Currently, the history includes only the user instructions, not the model outputs or turn artifacts. This can be extended in the future if desired.
        # Option 1: include model output response (only comment, not ttl) in history block. E.g. "Model response: Found one extra air terminal in room R01.02."
        # Option 2: include full model output (comment response and ttl) in history block with chat roles etc. Requires a redesign of the history block structure and formatting.


        # Evaluate the newly generated TTL with the selected queries and save results in the evaluations folder.
        if session.selected_queries:
            try:
                evaluation_summary = run_hitl_evaluation(
                    ttl_path=artifacts["output_ttl"],
                    queries=session.selected_queries,
                    eval_dir=turn_eval_dir,
                )
            except Exception as e:
                print(f"\n[ERROR] HITL evaluation failed:\n{e}\n")
                evaluation_summary = {"ERROR": "evaluation failed"}
        else:
            evaluation_summary = {}

        # Log turn before incrementing
        metrics = HITLMetrics(
            level=session.level,
            exp=session.exp,
            turn_index=session.turn_index,
            provider=session.provider,
            mode=session.mode,
            input_ttl=Path(artifacts["input_ttl"]).name,
            output_ttl=Path(artifacts["output_ttl"]).name,
            raw_output_file=Path(artifacts["raw_output"]).name,
            instruction_file=Path(artifacts["instruction"]).name,
            num_queries=len(session.selected_queries),
            elapsed_seconds=elapsed,
            evaluation_summary=evaluation_summary,
        )
        logger.append(metrics)

        session.turn_index += 1
        session.save(Path(session.workspace_dir) / Default.SESSION_CONFIG)

        # Update manual Excel evaluation scheme so it contains one block per HITL state
        update_excel_scheme(session, instruction_text=instruction_text)


        # --- Print summaries ---
        print("\nTurn completed.")
        print(f"Refined TTL saved to:\n{artifacts['output_ttl']}")
        print(f"Raw model output saved to:\n{artifacts['raw_output']}")
        print(f"Turn time: {elapsed:.2f} sec")
        
        if evaluation_summary:
            print("\n=== SPARQL SUMMARY ===")
            for qid, result in sorted(evaluation_summary.items(), key=lambda x: x[0]):
                print(f" {qid:<6} : {result} result(s)")

    print("\nFinal working TTL:")
    print(session.working_ttl)

