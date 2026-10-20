"""Command-line demo: triage the sample data and print a readable summary.

Usage:
    python -m workflow_orchestrator.cli data/sample_items.json
"""

from __future__ import annotations

import sys

from .audit import AuditLog
from .config import Settings
from .ingest import load_items
from .orchestrator import Orchestrator


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = argv[0] if argv else "data/sample_items.json"

    settings = Settings.from_env()
    orchestrator = Orchestrator(settings=settings, audit_log=AuditLog(":memory:"))

    items = load_items(path)
    results = orchestrator.process_batch(items)

    for item, result in zip(items, results):
        c, d = result.classification, result.decision
        route = "auto-routed" if result.auto_routed else "HUMAN REVIEW"
        print(
            f"{item.id:<10} {item.source.value:<7} -> {c.category.value:<18} "
            f"{c.urgency.value:<9} {d.priority.value}  queue={d.queue:<17} "
            f"rule={d.rule_fired:<32} conf={c.confidence:.2f}  [{route}]"
        )
    print(f"\nProcessed {len(results)} items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
