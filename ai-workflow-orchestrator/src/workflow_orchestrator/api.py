"""FastAPI surface for the orchestrator.

Run locally with:
    uvicorn workflow_orchestrator.api:app --reload
Then open http://127.0.0.1:8000/docs for the interactive API page.
"""

from __future__ import annotations

from fastapi import FastAPI

from .audit import AuditLog
from .config import Settings
from .orchestrator import Orchestrator
from .schemas import TriageResult, WorkItem

settings = Settings.from_env()
audit_log = AuditLog(settings.audit_db_path)
orchestrator = Orchestrator(settings=settings, audit_log=audit_log)

app = FastAPI(title="AI Workflow Orchestrator", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "classifier_mode": settings.classifier_mode}


@app.post("/triage", response_model=TriageResult)
def triage(item: WorkItem) -> TriageResult:
    """Classify, prioritize, and route one item."""
    return orchestrator.process(item)


@app.post("/triage/batch", response_model=list[TriageResult])
def triage_batch(items: list[WorkItem]) -> list[TriageResult]:
    """Triage several items in one call."""
    return orchestrator.process_batch(items)


@app.get("/audit", response_model=list[TriageResult])
def audit(limit: int = 50) -> list[TriageResult]:
    """Most recent triage results, newest first."""
    return audit_log.list_results(limit=limit)
