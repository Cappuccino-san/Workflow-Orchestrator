"""Tests for the deterministic rules engine.

These are the most important tests in the repo: if a rule changes, a test
should break loudly, because a silent priority change is an SLA change.
"""

from workflow_orchestrator.rules.engine import decide
from workflow_orchestrator.schemas import (
    Category,
    Classification,
    Priority,
    SourceType,
    Urgency,
    WorkItem,
)


def make(category: Category, urgency: Urgency, is_vip: bool = False):
    item = WorkItem(id="X-1", source=SourceType.TICKET, text="test", is_vip=is_vip)
    classification = Classification(category=category, urgency=urgency, confidence=0.9)
    return decide(classification, item)


def test_critical_is_always_p1():
    decision = make(Category.BILLING, Urgency.CRITICAL)
    assert decision.priority == Priority.P1
    assert decision.rule_fired == "critical_urgency"


def test_high_urgency_security_is_p1():
    decision = make(Category.SECURITY, Urgency.HIGH)
    assert decision.priority == Priority.P1
    assert decision.queue == "security"


def test_security_floor_is_p2():
    decision = make(Category.SECURITY, Urgency.MEDIUM)
    assert decision.priority == Priority.P2
    assert decision.rule_fired == "security_or_outage_floor"


def test_vip_high_urgency_is_p2():
    decision = make(Category.TECHNICAL_SUPPORT, Urgency.HIGH, is_vip=True)
    assert decision.priority == Priority.P2
    assert decision.rule_fired == "vip_high_urgency"


def test_feature_request_is_p4():
    decision = make(Category.FEATURE_REQUEST, Urgency.MEDIUM)
    assert decision.priority == Priority.P4


def test_default_is_p3():
    decision = make(Category.BILLING, Urgency.MEDIUM)
    assert decision.priority == Priority.P3
    assert decision.rule_fired == "default"


def test_same_input_same_output():
    """Determinism: deciding twice must give identical results."""
    assert make(Category.OUTAGE, Urgency.HIGH) == make(Category.OUTAGE, Urgency.HIGH)
