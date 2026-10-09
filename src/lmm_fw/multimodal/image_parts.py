from __future__ import annotations
import mimetypes
from pathlib import Path

from .parts import ImagePart


def load_image(path: str | Path, mime_type: str | None = None) -> ImagePart:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p.resolve())

    mt = mime_type or (mimetypes.guess_type(p.name)[0] or "image/png")
    return ImagePart(data=p.read_bytes(), mime_type=mt)
