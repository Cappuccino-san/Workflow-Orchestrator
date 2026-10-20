"""Deterministic priority rules engine.

This module is the heart of the project, and it deliberately contains no AI.

Priority is a business decision with audit and SLA consequences, so it is
made by plain, ordered, testable rules: the same classification always
produces the same priority, the rule that fired is recorded by name, and a
reviewer can replay any decision exactly. An LLM cannot offer any of that.

Rules are evaluated top to bottom; the first match wins.
"""

from __future__ import annotations

from ..schemas import Category, Classification, Priority, RuleDecision, Urgency, WorkItem

# Category -> owning team queue.
QUEUES: dict[Category, str] = {
    Category.SECURITY: "security",
    Category.OUTAGE: "platform-oncall",
    Category.BILLING: "billing-support",
    Category.ACCOUNT_ACCESS: "it-helpdesk",
    Category.TECHNICAL_SUPPORT: "support",
    Category.FEATURE_REQUEST: "product-feedback",
    Category.OTHER: "general-triage",
}


def decide(classification: Classification, item: WorkItem) -> RuleDecision:
    """Apply the ordered business rules and return the decision + rule name."""
    category = classification.category
    urgency = classification.urgency
    queue = QUEUES[category]

    def result(priority: Priority, rule: str) -> RuleDecision:
        return RuleDecision(priority=priority, rule_fired=rule, queue=queue)

    # 1. Anything critical is P1, whatever it is.
    if urgency == Urgency.CRITICAL:
        return result(Priority.P1, "critical_urgency")

    # 2. High-urgency security or outage work is P1.
    if urgency == Urgency.HIGH and category in {Category.SECURITY, Category.OUTAGE}:
        return result(Priority.P1, "high_urgency_security_or_outage")

    # 3. Security and outage work is at least P2, even at normal urgency.
    if category in {Category.SECURITY, Category.OUTAGE}:
        return result(Priority.P2, "security_or_outage_floor")

    # 4. A VIP sender with high urgency jumps the queue.
    if item.is_vip and urgency == Urgency.HIGH:
        return result(Priority.P2, "vip_high_urgency")

    # 5. Remaining high-urgency work is P2.
    if urgency == Urgency.HIGH:
        return result(Priority.P2, "high_urgency")

    # 6. Low-urgency work and feature requests are P4.
    if urgency == Urgency.LOW or category == Category.FEATURE_REQUEST:
        return result(Priority.P4, "low_urgency_or_feature_request")

    # 7. Default: everything else is P3.
    return result(Priority.P3, "default")
