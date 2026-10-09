from __future__ import annotations
from typing import List
from google.genai import types
from .base import PromptBundle, Strategy


class ZeroShot(Strategy):
    def __init__(self, system_hint: str | None = None):
        self.system_hint = system_hint

    def build(self, user_text: str, images: List[types.Part] | None = None) -> PromptBundle:
        images = images or []
        contents: list = []
        if self.system_hint:
            contents.append(f"System instruction: {self.system_hint}")
        contents.append(user_text)
        contents.extend(images)
        return PromptBundle(contents=contents)
