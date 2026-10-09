from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from google.genai import types

from .base import PromptBundle, Strategy


@dataclass(frozen=True)
class Example:
    user: str
    assistant: str


class FewShot(Strategy):
    def __init__(self, examples: Sequence[Example], system_hint: str | None = None):
        self.examples = list(examples)
        self.system_hint = system_hint

    def build(self, user_text: str, images: List[types.Part] | None = None) -> PromptBundle:
        images = images or []
        contents: list = []
        if self.system_hint:
            contents.append(f"System instruction: {self.system_hint}")

        # Simple “transcript style” few-shot (easy to iterate on)
        for ex in self.examples:
            contents.append(f"User: {ex.user}")
            contents.append(f"Assistant: {ex.assistant}")

        contents.append(f"User: {user_text}")
        contents.extend(images)
        return PromptBundle(contents=contents)
