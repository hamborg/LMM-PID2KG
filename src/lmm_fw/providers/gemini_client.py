from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Union
from typing import List, Sequence

from pathlib import Path
from google import genai
from google.genai import types

from ..settings import AppConfig, export_env_from_config, load_config
from ..multimodal.parts import ContentPart, TextPart, ImagePart
from .base import BaseLMMClient

ContentItem = Union[str, types.Part]


class GeminiClient(BaseLMMClient):
    def __init__(
        self,
        cfg: AppConfig | None = None,
    ):
        self.cfg = cfg
        export_env_from_config(self.cfg)

        # Pass the resolved key explicitly, the way OpenAIClient does. Relying
        # on genai.Client() reading GEMINI_API_KEY made the client ignore a key
        # set in auth/config.yaml whenever a different one was already exported,
        # because export_env_from_config uses setdefault and will not overwrite.
        self._client = genai.Client(api_key=self.cfg.gemini.api_key)
        self._model = self.cfg.gemini.model
        self._temperature = self.cfg.gemini.temperature
        self._thinking_level = self.cfg.gemini.thinking_level
    

    def _to_gemini_contents(self, parts: Sequence[ContentPart]) -> List[object]:
        out: List[object] = []
        for p in parts:
            if isinstance(p, TextPart):
                out.append(p.text)
            elif isinstance(p, ImagePart):
                out.append(types.Part.from_bytes(data=p.data, mime_type=p.mime_type))
            else:
                raise TypeError(f"Unsupported part: {type(p)}")
        return out
    

    def generate(self, parts: Sequence[ContentPart]) -> str:
        config = types.GenerateContentConfig(
            temperature=self._temperature,
            thinking_config=types.ThinkingConfig(thinking_level=self._thinking_level),
        )

        resp = self._client.models.generate_content(
            model=self._model,
            contents=self._to_gemini_contents(parts),
            config=config,
        )
        return resp.text or ""

    def stream(self, contents: Union[str, List[ContentItem]]) -> Iterable[str]:
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=self._thinking_level)
        )

        for chunk in self._client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    @property
    def model_name(self) -> str:
        return self._model
