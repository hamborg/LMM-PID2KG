from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class QueryMetrics:
    level: int
    exp: str

    ttl_file: str
    query: str

    output_file: str

    num_results: int
    elapsed_seconds: float

    timestamp_utc: str = ""


class QueryLogger:
    """
    Appends one JSON object per query run to a JSONL log file.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, metrics: QueryMetrics, extra: Dict[str, Any] | None = None) -> None:
        record = asdict(metrics)

        if extra:
            record.update(extra)

        if not record.get("timestamp_utc"):
            record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")