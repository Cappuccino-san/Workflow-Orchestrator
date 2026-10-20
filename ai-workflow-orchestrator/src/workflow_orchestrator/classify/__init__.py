"""Classification: turn a WorkItem into a structured Classification."""

from .rules_classifier import RulesClassifier

__all__ = ["RulesClassifier", "get_classifier"]


def get_classifier(mode: str, model: str = "gpt-4o-mini"):
    """Return the classifier for the configured mode.

    "rules" -> deterministic keyword fallback (no API key, used in tests/CI)
    "llm"   -> LangChain classifier (requires OPENAI_API_KEY)
    """
    if mode == "llm":
        from .llm_classifier import LLMClassifier

        return LLMClassifier(model=model)
    return RulesClassifier()
