from __future__ import annotations
import base64
from typing import Sequence, List, Dict, Any

from pathlib import Path
from openai import OpenAI

from ..settings import AppConfig, export_env_from_config, load_config
from ..multimodal.parts import ContentPart, TextPart, ImagePart
from .base import BaseLMMClient


class OpenAIClient(BaseLMMClient):
    def __init__(
        self,
        cfg: AppConfig | None = None,
    ):
        self.cfg = cfg
        export_env_from_config(self.cfg)

        # OpenAI Python SDK picks up api_key; we pass explicitly.
        self._client = OpenAI(api_key=cfg.openai.api_key)
        self._model = cfg.openai.model
        self._temperature = cfg.openai.temperature

    def _to_openai_input(self, parts: Sequence[ContentPart]) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []
        for p in parts:
            if isinstance(p, TextPart):
                content.append({"type": "input_text", "text": p.text})
            elif isinstance(p, ImagePart):
                b64 = base64.b64encode(p.data).decode("utf-8")
                content.append(
                    {
                        "type": "input_image",
                        "image_url": f"data:{p.mime_type};base64,{b64}",
                    }
                )
            else:
                raise TypeError(f"Unsupported part: {type(p)}")
        return content

    def generate(self, parts: Sequence[ContentPart]) -> str:
        # Responses API call shape: input=[{"role":"user","content":[...]}]
        # (Exact fields vary slightly across SDK versions, but this structure is canonical.)
        resp = self._client.responses.create(
            model="gpt-5.2-pro",
            input=[{"role": "user", "content": self._to_openai_input(parts)}],
            # temperature=self._temperature,
        )
        # The SDK provides a convenience output_text on Responses objects in most versions.
        return getattr(resp, "output_text", "") or ""

    @property
    def model_name(self) -> str:
        return self._model
