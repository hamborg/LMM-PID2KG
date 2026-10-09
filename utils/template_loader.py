# utils/template_loader.py

"""
Loads template files from various locations in the framework.

NOTE: The functions in this module return `Path` objects, assuming that the files exist.
Future improvements could include returning only the `resources` object and handle the `as_file()` context in the calling code. 
"""

from importlib import resources
from pathlib import Path

def hitl_template(name: str) -> Path:
    return Path(resources.files("hitl_refinement.templates") / name)

def sparql_queries(name: str) -> Path:
    # NOTE: so far, unused...
    return Path(resources.files("sparql_queries.queries") / name)