from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Sequence

from ..multimodal.parts import ContentPart


class BaseLMMClient(ABC):
    @abstractmethod
    def generate(self, parts: Sequence[ContentPart]) -> str:
        """Return model text output."""
        raise NotImplementedError

    @property
    def model_name(self) -> Optional[str]:
        return None