from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Union

from google.genai import types

ContentItem = Union[str, types.Part]


@dataclass(frozen=True)
class PromptBundle:
    contents: List[ContentItem]


class Strategy(ABC):
    @abstractmethod
    def build(self, user_text: str, images: List[types.Part] | None = None) -> PromptBundle:
        raise NotImplementedError
