from __future__ import annotations
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class TextPart:
    text: str


@dataclass(frozen=True)
class ImagePart:
    data: bytes
    mime_type: str = "image/png"


ContentPart = Union[TextPart, ImagePart]
