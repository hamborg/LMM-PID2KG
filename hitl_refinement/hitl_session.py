# hitl_refinement/hitl_session.py

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class HITLSession:
    """
    Stores the state of a HITL refinement session.
    """

    level: int
    exp: str
    provider: str
    mode: str

    source_experiment_dir: str
    source_ttl: str
    working_ttl: str

    selected_queries: list[str]
    note: str

    workspace_dir: str
    turns_dir: str
    evaluations_dir: str
    images_dir: str
    session_config_path: str

    turn_index: int = 1

    parent_session: str | None = None
    parent_turn: int | None = None

    def save(self, path: str | Path) -> None:
        """
        Save the current session to JSON.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path) -> "HITLSession":
        """
        Load a session from JSON.
        """
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)