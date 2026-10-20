"""Ingestion: load raw items from disk and normalize them into WorkItems.

This is the only module that touches raw file formats. Everything downstream
receives validated WorkItem objects.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schemas import WorkItem


def load_items(path: str | Path) -> list[WorkItem]:
    """Load a JSON file containing a list of raw items and validate each one."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise TypeError(f"Expected a JSON list of items in {path}")
    return [WorkItem.model_validate(entry) for entry in raw]
