"""Evaluation harness (starter).

Runs the pipeline over the sample items and prints a triage summary.
Extend this into a real eval by adding expected category/priority labels
next to each sample item and scoring the pipeline against them — see DESIGN.md.

Usage:
    python eval/evaluate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from workflow_orchestrator.audit import AuditLog  # noqa: E402
from workflow_orchestrator.cli import main as demo_main  # noqa: E402
from workflow_orchestrator.config import Settings  # noqa: E402
from workflow_orchestrator.ingest import load_items  # noqa: E402
from workflow_orchestrator.orchestrator import Orchestrator  # noqa: E402


def main() -> int:
    orchestrator = Orchestrator(
        settings=Settings(classifier_mode="rules"), audit_log=AuditLog(":memory:")
    )
    items = load_items(Path(__file__).resolve().parents[1] / "data" / "sample_items.json")
    results = orchestrator.process_batch(items)

    auto = sum(1 for r in results if r.auto_routed)
    print(f"Items: {len(results)}  auto-routed: {auto}  human review: {len(results) - auto}")
    print("\nFull detail:\n")
    return demo_main(["data/sample_items.json"])


if __name__ == "__main__":
    raise SystemExit(main())
