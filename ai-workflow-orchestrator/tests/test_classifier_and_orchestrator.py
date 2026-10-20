"""Tests for the fallback classifier and the end-to-end pipeline."""

from workflow_orchestrator.audit import AuditLog
from workflow_orchestrator.classify.rules_classifier import RulesClassifier
from workflow_orchestrator.config import Settings
from workflow_orchestrator.orchestrator import Orchestrator
from workflow_orchestrator.schemas import Category, Priority, SourceType, WorkItem


def item(text: str, subject: str = "", source: SourceType = SourceType.TICKET) -> WorkItem:
    return WorkItem(id="T-1", source=source, subject=subject, text=text)


def test_phishing_classifies_as_security():
    result = RulesClassifier().classify(item("Possible phishing email, looks like a breach attempt"))
    assert result.category == Category.SECURITY
    assert result.confidence >= 0.65


def test_unknown_text_is_low_confidence_other():
    result = RulesClassifier().classify(item("Hello, general question, thanks"))
    assert result.category == Category.OTHER
    assert result.confidence < 0.65


def make_orchestrator() -> Orchestrator:
    settings = Settings(classifier_mode="rules", confidence_threshold=0.65)
    return Orchestrator(settings=settings, audit_log=AuditLog(":memory:"))


def test_low_confidence_goes_to_human_review():
    result = make_orchestrator().process(item("Hello, general question, thanks"))
    assert result.auto_routed is False
    assert result.actions[0].action_type == "human_review"


def test_security_item_auto_routes_to_security_queue_as_p1():
    result = make_orchestrator().process(
        item("Urgent phishing breach attempt", subject="Phishing")
    )
    assert result.auto_routed is True
    assert result.decision.queue == "security"
    assert result.decision.priority == Priority.P1


def test_every_result_is_audited():
    orchestrator = make_orchestrator()
    orchestrator.process(item("My invoice was charged twice, refund please"))
    stored = orchestrator._audit.list_results()
    assert len(stored) == 1
    assert stored[0].item_id == "T-1"
