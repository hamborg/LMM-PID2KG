# hitl/ttl_manager.py

from __future__ import annotations

from pathlib import Path

from experiments.ttl_extract import extract_ttl_from_output


def read_ttl(ttl_path: str | Path) -> str:
    """
    Read a TTL file as text.
    """
    ttl_path = Path(ttl_path)
    if not ttl_path.exists():
        raise FileNotFoundError(f"TTL file not found:\n{ttl_path}")

    return ttl_path.read_text(encoding="utf-8")


def save_input_ttl(turn_dir: str | Path, ttl_text: str) -> Path:
    """
    Save the input TTL for a HITL turn.
    """
    turn_dir = Path(turn_dir)
    turn_dir.mkdir(parents=True, exist_ok=True)

    out_path = turn_dir / "input_ttl.ttl"
    out_path.write_text(ttl_text.strip() + "\n", encoding="utf-8")

    return out_path


def save_instruction(turn_dir: str | Path, instruction_text: str) -> Path:
    """
    Save the human instruction for a HITL turn.
    """
    turn_dir = Path(turn_dir)
    turn_dir.mkdir(parents=True, exist_ok=True)

    out_path = turn_dir / "instruction.txt"
    out_path.write_text(instruction_text.strip() + "\n", encoding="utf-8")

    return out_path


def save_raw_output(turn_dir: str | Path, raw_output: str) -> Path:
    """
    Save the raw LMM response for a HITL turn.
    """
    turn_dir = Path(turn_dir)
    turn_dir.mkdir(parents=True, exist_ok=True)

    out_path = turn_dir / "output_raw.txt"
    out_path.write_text(raw_output, encoding="utf-8")

    return out_path


def extract_and_save_output_ttl(turn_dir: str | Path, raw_output: str) -> Path:
    """
    Extract TTL from the raw LMM output and save it as the refined TTL.
    """
    turn_dir = Path(turn_dir)
    turn_dir.mkdir(parents=True, exist_ok=True)

    ttl = extract_ttl_from_output(raw_output)
    if ttl is None:
        raise ValueError("No TTL block could be extracted from the LMM output.")

    out_path = turn_dir / "output_ttl.ttl"
    out_path.write_text(ttl.strip() + "\n", encoding="utf-8")

    return out_path


def prepare_turn_artifacts(
    turn_dir: str | Path,
    input_ttl_text: str,
    instruction_text: str,
    raw_output: str,
) -> dict[str, Path]:
    """
    Save all standard HITL turn artifacts and return their paths.
    """
    turn_dir = Path(turn_dir)

    input_ttl_path = save_input_ttl(turn_dir, input_ttl_text)
    instruction_path = save_instruction(turn_dir, instruction_text)
    raw_output_path = save_raw_output(turn_dir, raw_output)
    output_ttl_path = extract_and_save_output_ttl(turn_dir, raw_output)

    return {
        "input_ttl": input_ttl_path,
        "instruction": instruction_path,
        "raw_output": raw_output_path,
        "output_ttl": output_ttl_path,
    }