# hitl_refinement/workspace.py

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from datetime import datetime
import json
import shutil
import questionary


from hitl_refinement.hitl_session import HITLSession
from utils.default_settings import Default

HITL_FOLDER = "hitl"

def make_branched_session_name(old_session: HITLSession, old_session_dir_name: str, turn_index: int) -> str:
    base_name = old_session_dir_name.split("__from_t")[0]
    branch_base = f"{base_name}__from_t{turn_index:02d}"
    session_name = branch_base

    session_root = Path(HITL_FOLDER) / f"L{old_session.level}_E{int(old_session.exp):02d}"
    counter = 2
    while (session_root / session_name).exists():
        session_name = f"{branch_base}__b{counter}"
        counter += 1

    return session_name


### --- Start up HITL session --- 
# Helper functions for creating a new HITL session workspace and folder structure.
# These are used in hitl_prompting.py when starting a new HITL session from the initial prompt.

def make_session_name(args: Namespace) -> str:
    """
    Build a readable session folder name.

    Example:
        ses_04.09_14.30_gemini_A_(comment-about-session)
    """
    timestamp = datetime.now().strftime(Default.TIMESTAMP_FORMAT)

    provider_part = f"_{args.provider}" if (args.provider != Default.PROVIDER) else ""

    note = " ".join(args.note).strip() if args.note else ""
    note_part = f"_{_safe_name(note)}" if note else ""

    return f"ses_{timestamp}{provider_part}_{args.mode}{note_part}"


def create_hitl_workspace(level: int, exp: str, session_name: str) -> dict[str, Path]:
    """
    Create the folder structure for a HITL session and return the important paths.
    """
    exp_num = int(exp)
    exp_two = f"{exp_num:02d}"

    root = Path(HITL_FOLDER) / f"L{level}_E{exp_two}" / session_name

    source_dir = root / "source"
    images_dir = source_dir / "images"
    turns_dir = root / "turns"
    evaluations_dir = root / "evaluations"
    config_path = root / Default.SESSION_CONFIG

    for p in [root, source_dir, images_dir, turns_dir, evaluations_dir]:
        p.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "source": source_dir,
        "images": images_dir,
        "turns": turns_dir,
        "evaluations": evaluations_dir,
        "config": config_path,
    }


def make_dir(dir: str | Path, turn_index: int) -> Path:
    """
    Return and create the folder for a specific HITL turn.

    Example:
        turns/turn_00
        turns/turn_01
    """
    new_dir = Path(dir) / f"turn_{turn_index:02d}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def _safe_name(text: str) -> str:
    """
    Make a filesystem-friendly string.
    """
    text = text.strip().replace(" ", "_")
    bad_chars = '<>:"/\\|?*'
    for ch in bad_chars:
        text = text.replace(ch, "")
    return text


### --- Continue HITL session --- 
# Helper functions for copying artifacts from old session to new branched session.
# These are used in continue_hitl.py when creating a branched session from an existing session and checkpoint turn.

def _session_display_label(session_dir: Path) -> str:
    """
    Build a readable label for a HITL session.
    Example:
        L1_E04 | ses_26.03_17.45_A | turns: 3 | created: 17:52
    """
    turns_dir = session_dir / "turns"

    turn_count = 0
    if turns_dir.exists():
        turn_count = len([
            p for p in turns_dir.iterdir()
            if p.is_dir() and p.name.startswith("turn_")
        ])

    last_edit = datetime.fromtimestamp(
        session_dir.stat().st_mtime
    ).strftime("%H:%M")

    # Extract experiment folder name (L1_E04)
    exp_name = session_dir.parent.name

    return f"{exp_name} | {session_dir.name} | turns: {turn_count} | created: {last_edit}"


def list_session_dirs(root: str | Path = HITL_FOLDER) -> list[Path]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"No HITL runs folder found:\n{root}")

    sessions: list[Path] = []

    for exp_dir in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not exp_dir.is_dir():
            continue
        for session_dir in sorted(exp_dir.iterdir(), key=lambda p: p.name.lower()):
            if session_dir.is_dir():
                sessions.append(session_dir)

    if not sessions:
        raise FileNotFoundError(f"No HITL sessions found in:\n{root}")

    # Newest first is usually most helpful
    sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return sessions


def select_session(session_dirs: list[Path]) -> Path:
    """
    Show sessions with readable labels but return the correct folder.
    """

    choices = {
        _session_display_label(p): p
        for p in session_dirs
    }

    selected_label = questionary.select(
        "Select HITL session to continue from:",
        choices=list(choices.keys()),
    ).ask()

    if not selected_label:
        raise SystemExit("No session selected.")

    return choices[selected_label]


def list_turn_dirs(turns_dir: str | Path) -> list[Path]:
    turns_dir = Path(turns_dir)
    if not turns_dir.exists():
        raise FileNotFoundError(f"No turns folder found:\n{turns_dir}")

    turn_dirs = [
        p for p in turns_dir.iterdir()
        if p.is_dir() and p.name.lower().startswith("turn_")
    ]

    if not turn_dirs:
        raise FileNotFoundError(f"No turn folders found in:\n{turns_dir}")

    turn_dirs.sort(key=lambda p: p.name.lower())
    return turn_dirs


def select_turn(turn_dirs: list[Path]) -> Path:
    choices = [p.name for p in turn_dirs]

    selected = questionary.select(
        "Select checkpoint turn to branch from:",
        choices=choices,
    ).ask()

    if not selected:
        raise SystemExit("No turn selected.")

    for p in turn_dirs:
        if p.name == selected:
            return p

    raise RuntimeError("Selected turn could not be resolved.")


def copy_tree_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def copy_turns_up_to(old_turns_dir: Path, new_turns_dir: Path, max_turn_name: str) -> None:
    """"
    Copy turn subfolders up to the selected turn.
    """
    new_turns_dir.mkdir(parents=True, exist_ok=True)

    for turn_dir in sorted(old_turns_dir.iterdir(), key=lambda p: p.name.lower()):
        if not turn_dir.is_dir() or not turn_dir.name.startswith("turn_"):
            continue
        if turn_dir.name <= max_turn_name:
            shutil.copytree(turn_dir, new_turns_dir / turn_dir.name, dirs_exist_ok=True)

def copy_evaluations_up_to(old_eval_dir: Path, new_eval_dir: Path, max_turn_name: str) -> None:
    """
    Copy evaluation root files and evaluation subfolders up to the selected turn.
    """
    if not old_eval_dir.exists():
        return

    new_eval_dir.mkdir(parents=True, exist_ok=True)

    # Copy root-level files in evaluations/, e.g. "Evaluation scheme.xlsx"
    for item in old_eval_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, new_eval_dir / item.name)

    # Copy turn subfolders up to the selected turn
    for eval_dir in sorted(old_eval_dir.iterdir(), key=lambda p: p.name.lower()):
        if not eval_dir.is_dir() or not eval_dir.name.startswith("turn_"):
            continue
        if eval_dir.name <= max_turn_name:
            shutil.copytree(eval_dir, new_eval_dir / eval_dir.name, dirs_exist_ok=True)

def copy_session_log_up_to(src_log: Path, dst_log: Path, max_turn: int) -> None:
    """
    Copy session_log.jsonl entries up to the selected turn.
    """
    if not src_log.exists():
        return

    dst_log.parent.mkdir(parents=True, exist_ok=True)

    with src_log.open("r", encoding="utf-8") as src, \
         dst_log.open("w", encoding="utf-8") as dst:

        for line in src:
            try:
                record = json.loads(line)
            except Exception:
                continue

            turn = record.get("turn_index")

            if turn is None:
                continue

            if int(turn) <= max_turn:
                dst.write(line)


def extract_turn_index(turn_dir_name: str) -> int:
    # turn_01 -> 1
    return int(turn_dir_name.split("_", 1)[1])