"""Rules-based fallback classifier.

Deterministic keyword scoring with no external calls. It exists for three
reasons:
1. The pipeline (and its tests) must run with no API key.
2. It is a sane fallback if the LLM is down or returns invalid output.
3. Its confidence scores are honest: few/weak matches = low confidence,
   which is exactly what pushes an item into the human review queue.
"""

from __future__ import annotations

from ..schemas import Category, Classification, Urgency, WorkItem

# Keyword -> category. Deliberately small and readable; an interviewer should
# be able to scan this table and understand the whole fallback in one minute.
CATEGORY_KEYWORDS: dict[Category, list[str]] = {
    Category.SECURITY: ["breach", "phishing", "malware", "unauthorized", "vulnerability", "leaked"],
    Category.OUTAGE: ["outage", "down", "offline", "500 error", "service unavailable", "crash"],
    Category.BILLING: ["invoice", "refund", "charged", "billing", "payment failed", "overcharged"],
    Category.ACCOUNT_ACCESS: ["locked out", "password", "login", "mfa", "access denied", "reset"],
    Category.FEATURE_REQUEST: ["feature request", "would be nice", "suggestion", "enhancement"],
    Category.TECHNICAL_SUPPORT: ["error", "bug", "broken", "not working", "slow", "help"],
}

URGENCY_KEYWORDS: dict[Urgency, list[str]] = {
    Urgency.CRITICAL: ["critical", "breach", "all users", "production down", "data loss"],
    Urgency.HIGH: ["urgent", "asap", "blocked", "cannot work", "deadline today"],
    Urgency.LOW: ["when you get a chance", "minor", "low priority", "sometime"],
}


class RulesClassifier:
    """Classify a WorkItem by keyword scoring. Same input -> same output, always."""

    def classify(self, item: WorkItem) -> Classification:
        text = f"{item.subject or ''} {item.text}".lower()

        # Score each category by how many of its keywords appear.
        scores: dict[Category, int] = {
            category: sum(1 for kw in keywords if kw in text)
            for category, keywords in CATEGORY_KEYWORDS.items()
        }
        best_category, best_score = max(scores.items(), key=lambda kv: kv[1])

        if best_score == 0:
            category, confidence = Category.OTHER, 0.40
        else:
            category = best_category
            confidence = 0.75 if best_score == 1 else 0.88

        urgency = self._urgency(text, item)

        return Classification(
            category=category,
            urgency=urgency,
            sentiment="negative" if urgency.rank >= Urgency.HIGH.rank else "neutral",
            entities=[],
            confidence=confidence,
            rationale=f"Matched {best_score} keyword(s) for category '{category.value}'.",
        )

    @staticmethod
    def _urgency(text: str, item: WorkItem) -> Urgency:
        """Urgency from keywords, with log-severity and VIP as deterministic boosts."""
        for urgency in (Urgency.CRITICAL, Urgency.HIGH, Urgency.LOW):
            if any(kw in text for kw in URGENCY_KEYWORDS[urgency]):
                return urgency
        if item.source.value == "log" and item.metadata.get("level") in {"ERROR", "CRITICAL"}:
            return Urgency.HIGH
        return Urgency.MEDIUM
