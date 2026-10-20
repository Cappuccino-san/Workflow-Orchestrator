"""LangChain LLM classifier — the primary classifier when an API key is set.

Design notes:
- LangChain is imported lazily so the rest of the project (and CI) never
  needs the LLM dependencies or a key.
- `with_structured_output(Classification)` forces the model to return
  exactly our Pydantic schema — no free-text parsing, no regex extraction.
- The model only *describes* the item (category/urgency/confidence).
  It never decides priority or triggers actions; that is the rules
  engine's job (see rules/engine.py and DESIGN.md).
"""

from __future__ import annotations

from ..schemas import Classification, WorkItem

SYSTEM_PROMPT = """You triage incoming work items for an operations team.
Classify the item into exactly one category and one urgency level.
Be conservative: if the item is ambiguous, say so through a low confidence
score rather than guessing — low-confidence items go to a human reviewer."""


class LLMClassifier:
    """Classify WorkItems with a LangChain chat model + structured output."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "LLM mode needs the 'llm' extra: pip install -e '.[llm]'"
            ) from exc

        llm = ChatOpenAI(model=model, temperature=0)
        self._chain = llm.with_structured_output(Classification)

    def classify(self, item: WorkItem) -> Classification:
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Source: {item.source.value}\n"
            f"Subject: {item.subject or '(none)'}\n"
            f"Text: {item.text}"
        )
        result = self._chain.invoke(prompt)
        return Classification.model_validate(result)
