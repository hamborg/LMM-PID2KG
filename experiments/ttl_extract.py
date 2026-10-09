from __future__ import annotations
# ttl_extract.py
import re
from typing import Optional

# Find Final phase
# TTL_MARKER = "===FINAL_TTL===" 

# Regex to find ```ttl and ```turtle fenced blocks
_TTL_FENCE_RE = re.compile(
    r"```ttl\s*\n(.*?)\n```",
    flags=re.DOTALL | re.IGNORECASE,
)
_TURTLE_FENCE_RE = re.compile(
    r"```turtle\s*\n(.*?)\n```",
    flags=re.DOTALL | re.IGNORECASE,
)

def extract_ttl_from_output(full_output: str) -> Optional[str]:
    """
    Extract TTL code block.

    Strategy:
      1) If TTL_MARKER exists → search only that section.
      2) Otherwise search entire output.
      3) If multiple TTL blocks exist → return the last one.
    """

    matches_ttl = list(_TTL_FENCE_RE.finditer(full_output))
    matches_turtle = list(_TURTLE_FENCE_RE.finditer(full_output))

    if not matches_ttl and not matches_turtle:
        print("No TTL/Turtle block was found in output.")
        print("Returning without extracting TTL file. - PROCEED TO MANUAL EXTRACTION!")
        return None
    
    matches = matches_ttl if matches_ttl else matches_turtle
    ttl = matches[-1].group(1).strip()

    lines = ttl.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("@"):
            ttl = "\n".join(lines[i:])
            break
    
    return ttl if ttl else None