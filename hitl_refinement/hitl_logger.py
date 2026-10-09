# hitl/hitl_logger.py

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HITLMetrics:
    level: int
    exp: str
    turn_index: int

    provider: str
    mode: str

    input_ttl: str
    output_ttl: str
    raw_output_file: str

    instruction_file: str

    num_queries: int
    elapsed_seconds: float
    
    evaluation_summary: dict[str, int | str] | None = None
    timestamp_utc: str = ""


class HITLLogger:
    """
    Appends one JSON object per HITL turn to a JSONL log file.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, metrics: HITLMetrics, extra: dict[str, Any] | None = None) -> None:
        record = asdict(metrics)

        if extra:
            record.update(extra)

        if not record.get("timestamp_utc"):
            record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")