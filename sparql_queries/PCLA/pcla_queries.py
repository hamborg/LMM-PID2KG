from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import yaml


class PCLA:
    """
    Handles lookup of query groups defined in pclas.yaml.
    """

    def __init__(self, yaml_path: Path | None = None):
        if yaml_path is None:
            yaml_path = Path("sparql_queries/PCLA/pcla_groups.yaml")

        if not yaml_path.exists():
            raise FileNotFoundError(f"PCLA definition file not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = yaml.safe_load(f)


    def get_queries(self, pcla_ids: List[int]) -> List[tuple[str, int]]:
        """
        Return a list of (query_prefix, pcla_id) for the provided PCLA ids.

        Example:
            [3] -> [("A04",3), ("A05",3), ("V04",3)]
        """

        queries: List[tuple[str, int]] = []

        for pid in pcla_ids:
            key = f"PCLA_{int(pid):02d}"

            if key not in self.data:
                print(f"PCLA group not defined: {pid}")
                continue

            checks = self.data[key]["checks"]

            for check in checks:
                queries.append((check["query"], pid))

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []

        for q in queries:
            if q[0] not in seen:
                seen.add(q[0])
                unique_queries.append(q)

        return unique_queries