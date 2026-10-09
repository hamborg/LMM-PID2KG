# excel_evaluation_scheme_updater/update_scheme.py

from __future__ import annotations

from pathlib import Path
import shutil

from utils.default_settings import Default

from hitl_refinement.hitl_session import HITLSession
from hitl_refinement.evaluation_scheme_manipulator.duplicate_evaluation_blocks import ensure_evaluation_blocks
from utils.template_loader import hitl_template


def _try_excel_update(workbook_path: Path, total_blocks: int, instruction_text: str | None = None):
    max_attempts = 3
    attempt = 1

    while attempt < max_attempts:
        try:
            ensure_evaluation_blocks(
                workbook_path=workbook_path,
                total_blocks=total_blocks,
                instruction_text=instruction_text,
            )
            break  # success → exit loop

        except PermissionError:

            if attempt >= max_attempts:
                print("[WARNING] Maximum retry attempts reached. Skipping Excel update.\n")
                break
            
            if attempt == 1:
                print(
                    "\n[WARNING] Could not update Excel evaluation scheme because the file is open.\n"
                    f"{workbook_path}\n"
                )
            else:
                print("\nFile is still open...")

            # Ask user to close the file and retry
            response = input("Please close the Excel file and press ENTER to retry (or type 'skip' to cancel update): ").strip().lower()

            if response in {"skip", "s", "no", "n"}:
                print("Skipping Excel update.\n")
                break

        except Exception as e:
            print(f"\n[WARNING] Failed to update Excel evaluation scheme:\n{e}\n")
            break

        attempt += 1


def copy_evaluation_template(target_dir: str | Path) -> Path:
    """
    Copy the Excel evaluation scheme template to the hitl session evaluation directory.
    """
    template_path = hitl_template("Evaluation scheme template.xlsx")
    
    if not template_path.exists():
        raise FileNotFoundError(f"Missing evaluation template:\n{template_path}")

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / Default.WORKBOOK_NAME

    shutil.copy2(template_path, out_path)
    return out_path


def update_excel_scheme(session: HITLSession, instruction_text: str | None = None):
    """
    Example:
    before any HITL turn -> HITL 0
    after turn 1         -> HITL 0, HITL 1
    after turn 2         -> HITL 0, HITL 1, HITL 2
    """
    evaluation_workbook = Path(session.evaluations_dir) / Default.WORKBOOK_NAME

    if evaluation_workbook.exists():
        _try_excel_update(
            workbook_path=evaluation_workbook,
            total_blocks=session.turn_index,
            instruction_text=instruction_text,
        )
            