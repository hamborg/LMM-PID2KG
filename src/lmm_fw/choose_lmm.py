from __future__ import annotations

from pathlib import Path

from .settings import AppConfig, load_config
from .providers.base import BaseLMMClient
from .providers.gemini_client import GeminiClient
from .providers.openai_client import OpenAIClient

path_to_config = "auth/config.yaml"

def choose_LMM(provider: str | None = None, cfg: AppConfig | None = None) -> BaseLMMClient:
    cfg = cfg or load_config(path_to_config)
    name = (provider or cfg.default_provider).strip().lower()

    if name in {"gemini", "gem", "google"}:
        return GeminiClient(cfg)
    if name in {"openai", "gpt", "chatgpt"}:
        return OpenAIClient(cfg)

    raise ValueError(f"Unknown provider '{name}'. Use 'gemini' or 'openai'.")
