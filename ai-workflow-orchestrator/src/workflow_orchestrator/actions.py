"""Actions: the (mocked) side effects taken after a decision.

Every action here is safe by design: it records what *would* happen in a
real deployment instead of doing it. Swapping one for a real integration
(Jira, ServiceNow, Gmail, Slack) means replacing the body of one function —
the pipeline, rules, and audit trail do not change.
"""

from __future__ import annotations

from .schemas import ActionRecord, RuleDecision, TriageResult, WorkItem


def route_to_queue(decision: RuleDecision, item: WorkItem) -> ActionRecord:
    """Mock: place the item on its team's queue at its decided priority."""
    return ActionRecord(
        action_type="route_to_queue",
        detail=f"Routed item {item.id} to queue '{decision.queue}' at {decision.priority.value}.",
    )


def send_to_human_review(item: WorkItem, confidence: float, threshold: float) -> ActionRecord:
    """Place a low-confidence item in the human review queue instead of auto-routing."""
    return ActionRecord(
        action_type="human_review",
        detail=(
            f"Item {item.id} held for human review: confidence {confidence:.2f} "
            f"is below threshold {threshold:.2f}."
        ),
    )


def draft_response(result: TriageResult, item: WorkItem) -> ActionRecord:
    """Mock: draft (never send) an acknowledgement for P1/P2 items."""
    return ActionRecord(
        action_type="draft_response",
        detail=(
            f"Drafted acknowledgement for item {item.id} ({result.decision.priority.value}): "
            f"received, routed to {result.decision.queue}."
        ),
    )
