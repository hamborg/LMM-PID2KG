from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import os
import yaml


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str
    temperature: float = 0.0
    thinking_level: str = "high"


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str
    temperature: float = 0.0


@dataclass(frozen=True)
class AppConfig:
    default_provider: str
    gemini: GeminiConfig
    openai: OpenAIConfig


ENV_VAR_FOR_PROVIDER = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
}

# Values that mean "I have not filled this in yet". A copy of
# auth/config.example.yaml carries these, so treating them as absent lets the
# example file be used unedited alongside environment variables.
_PLACEHOLDER_PREFIXES = ("YOUR_", "<", "CHANGEME", "REPLACE_ME")


def _is_placeholder(value: str) -> bool:
    return value.upper().startswith(_PLACEHOLDER_PREFIXES)


def _load_dotenv(path: str | Path = ".env") -> None:
    """Load KEY=VALUE lines from a .env file into os.environ.

    Minimal parser (no extra dependency). Variables already set in the real
    environment are not overridden. A missing file is silently ignored.
    """
    env_path = Path(path)
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.lower().startswith("export "):
            key = key[7:].strip()
        value = value.strip()
        if value[:1] in ("'", '"') and value.count(value[0]) >= 2:
            value = value[1:value.index(value[0], 1)]  # quoted: take text between quotes
        else:
            value = value.split(" #", 1)[0].strip()  # unquoted: drop inline comment
        if key:
            os.environ.setdefault(key, value)


def _expand_env_ref(value: str) -> str:
    """Resolve a '${VAR}' reference to the value of environment variable VAR."""
    if value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1].strip(), "").strip()
    return value


def _resolve_api_key(block: Dict[str, Any], provider: str) -> str:
    """Return the API key for one provider.

    The YAML file wins when it holds a real value; otherwise the provider's
    environment variable is used. Keeping keys in the environment is the safer
    option here, since the project directory is synced to OneDrive and anything
    written into auth/config.yaml is replicated with it.

    Never log or echo the return value.
    """
    from_file = _expand_env_ref(str(block.get("api_key", "") or "").strip())
    if from_file and not _is_placeholder(from_file):
        return from_file

    env_var = ENV_VAR_FOR_PROVIDER[provider]
    return os.environ.get(env_var, "").strip()


def _missing_key_message(provider: str) -> str:
    env_var = ENV_VAR_FOR_PROVIDER[provider]
    return (
        f"No {provider} API key found. Set {env_var} in .env in the current "
        f"directory (run from the project root), or export it in your "
        f"environment. auth/config.yaml should reference it as "
        f"api_key: ${{{env_var}}} (copy auth/config.example.yaml to start)."
    )


def load_config(path: str | Path = "auth/config.yaml") -> AppConfig:
    _load_dotenv()
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. "
            "Copy auth/config.example.yaml to auth/config.yaml and fill it in."
        )

    raw: Dict[str, Any] = yaml.safe_load(config_path.read_text()) or {}

    default_provider = str(raw.get("default_provider", "gemini")).strip().lower()

    g = raw.get("gemini", {}) or {}
    o = raw.get("openai", {}) or {}

    gemini = GeminiConfig(
        api_key=_resolve_api_key(g, "gemini"),
        model=str(g.get("model", "gemini-3-flash-preview")).strip(),
        # model=str(g.get("model", "gemini-3.1-pro-preview")).strip(),

        # Gemini 3 Pro Preview is deprecated and will be shut down March 9, 2026. Migrate to Gemini 3.1 Pro Preview to avoid service disruption.
        # https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview
        
        temperature=float(g.get("temperature", 0.0)),
        thinking_level=str(g.get("thinking_level", "high")).strip(),
    )
    openai = OpenAIConfig(
        api_key=_resolve_api_key(o, "openai"),
        model=str(o.get("model", "gpt-5-mini")).strip(),
        temperature=float(o.get("temperature", 0.0)),
    )

    # Unchanged behaviour: both keys are required, even for a single-provider
    # run. See the note in README.md - relaxing this is a separate change.
    if not gemini.api_key:
        raise ValueError(_missing_key_message("gemini"))
    if not openai.api_key:
        raise ValueError(_missing_key_message("openai"))

    return AppConfig(
        default_provider=default_provider,
        gemini=gemini,
        openai=openai,
    )


def export_env_from_config(cfg: AppConfig) -> None:
    os.environ.setdefault("GEMINI_API_KEY", cfg.gemini.api_key)
    os.environ.setdefault("OPENAI_API_KEY", cfg.openai.api_key)
