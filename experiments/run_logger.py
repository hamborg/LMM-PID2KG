# run_logger.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RunMetrics:
    provider: str
    level: int
    exp: str
    test_index: int

    output_file: str

    prompt: str
    prompt_chars: int
    num_images: int

    elapsed_seconds: float

    model_name: Optional[str] = None
    timestamp_utc: str = ""


class ExperimentLogger:
    """
    Appends one JSON object per run to a log file (JSONL).
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, metrics: RunMetrics, extra: Optional[Dict[str, Any]] = None) -> None:
        record = asdict(metrics)
        if extra:
            record.update(extra)

        # Ensure timestamp exists
        if not record.get("timestamp_utc"):
            record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class Timer:
    """
    Simple context manager timer using a monotonic clock.
    """
    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self._t0
        return False
