# hitl_refinement/hitl_prompting.py

from __future__ import annotations

from pathlib import Path

from lmm_fw.multimodal.parts import TextPart
from lmm_fw.multimodal.image_parts import load_image
from hitl_refinement.hitl_session import HITLSession
from utils.default_settings import Default
from utils.template_loader import hitl_template


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def load_initial_prompt(prompt: str | Path = Default.INITIAL_PROMPT) -> str:
    """
    Load the fixed HITL introduction prompt from disk.
    """
    path = hitl_template(prompt)
    
    if not path.exists():
        raise FileNotFoundError(f"Missing HITL prompt file:\n{path}")

    return path.read_text(encoding="utf-8")


def load_session_images(images_dir: str | Path) -> list:
    """
    Load all copied source images for the HITL session as multimodal parts.
    """
    images_dir = Path(images_dir)
    if not images_dir.exists():
        raise FileNotFoundError(f"Missing HITL images folder:\n{images_dir}")

    image_parts = []
    for p in sorted(images_dir.iterdir(), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            image_parts.append(load_image(p))

    return image_parts


def build_turn_instruction_block(
    instruction_text: str,
    current_ttl: str,
) -> str:
    """
    Build the per-turn user input block for TTL refinement.
    """
    return (
        f"Human instruction:\n"
        f"{instruction_text.strip()}\n\n"
        f"Current graph:\n"
        f"```ttl\n{current_ttl.strip()}\n```"
    )


def build_hitl_parts(
    session: HITLSession,
    instruction_text: str,
    current_ttl: str,
    history_blocks: list[str] | None = None,
    # prompt: str | Path = Default.INITIAL_PROMPT,
) -> list:
    """
    Session Mode A:
    Build a conversational HITL turn input.
    - fixed initial prompt
    - optional prior turn history (as text blocks)
    - current instruction
    - current TTL
    - source images

    Session Mode B:
    Build a stateless HITL turn input.
    - fixed initial prompt
    - current instruction
    - current TTL
    - source images
    """
    intro_prompt = load_initial_prompt()
    images = load_session_images(session.images_dir)

    parts = [TextPart(intro_prompt)]

    if history_blocks and session.mode == "A":
        history_text = "\n\n".join(history_blocks).strip()
        if history_text:
            parts.append(TextPart(f"Conversation history:\n{history_text}"))

    parts.append(TextPart(build_turn_instruction_block(instruction_text, current_ttl)))
    parts.extend(images)

    return parts