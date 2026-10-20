"""Orchestrator: the pipeline that connects every stage.

    WorkItem
      -> classify      (LLM or rules fallback: what is this?)
      -> rules engine  (deterministic: how important is it, who owns it?)
      -> confidence gate (confident enough to act, or a human decides?)
      -> actions       (mocked routing / draft)
      -> audit log     (everything above, recorded)

Each stage is a separate module with one job; this file only wires them
together, in order, and owns the run ID that ties a result to its audit row.
"""

from __future__ import annotations

import uuid

from . import actions
from .audit import AuditLog
from .config import Settings
from .rules import engine
from .schemas import Priority, TriageResult, WorkItem


class Orchestrator:
    """Run the full triage pipeline for incoming work items."""

    def __init__(
        self,
        classifier=None,
        settings: Settings | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self._settings = settings or Settings.from_env()
        if classifier is None:
            from .classify import get_classifier

            classifier = get_classifier(
                self._settings.classifier_mode, model=self._settings.llm_model
            )
        self._classifier = classifier
        self._audit = audit_log or AuditLog(self._settings.audit_db_path)

    def process(self, item: WorkItem) -> TriageResult:
        """Triage one item end-to-end and record the result in the audit log."""
        classification = self._classifier.classify(item)
        decision = engine.decide(classification, item)

        threshold = self._settings.confidence_threshold
        auto_routed = classification.confidence >= threshold

        if auto_routed:
            taken = [actions.route_to_queue(decision, item)]
        else:
            taken = [actions.send_to_human_review(item, classification.confidence, threshold)]

        result = TriageResult(
            item_id=item.id,
            classification=classification,
            decision=decision,
            auto_routed=auto_routed,
            actions=taken,
            run_id=str(uuid.uuid4()),
        )

        # Urgent, auto-routed work also gets a (mock) acknowledgement draft.
        if auto_routed and decision.priority in {Priority.P1, Priority.P2}:
            result.actions.append(actions.draft_response(result, item))

        self._audit.record(result)
        return result

    def process_batch(self, items: list[WorkItem]) -> list[TriageResult]:
        """Triage a list of items, in order."""
        return [self.process(item) for item in items]
