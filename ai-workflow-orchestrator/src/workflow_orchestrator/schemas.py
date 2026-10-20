"""Data schemas — the single source of truth for every pipeline boundary.

Every module in this project speaks in these Pydantic models, never in raw
dicts. That is what makes the LLM output, the API, and the audit log safe to
connect to each other: if it validates here, it is well-formed everywhere.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Where an incoming work item came from."""

    TICKET = "ticket"
    EMAIL = "email"
    LOG = "log"


class Category(str, Enum):
    """What kind of work an item is. Assigned by the classifier."""

    SECURITY = "security"
    OUTAGE = "outage"
    BILLING = "billing"
    ACCOUNT_ACCESS = "account_access"
    TECHNICAL_SUPPORT = "technical_support"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class Urgency(str, Enum):
    """How time-sensitive an item is. Assigned by the classifier."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Numeric rank so rules can compare urgency with >= instead of string tricks."""
        return {"low": 0, "medium": 1, "high": 2, "critical": 3}[self.value]


class Priority(str, Enum):
    """Final priority. Assigned ONLY by the deterministic rules engine, never the LLM."""

    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class WorkItem(BaseModel):
    """One normalized incoming item, whatever its source."""

    id: str
    source: SourceType
    text: str
    subject: str | None = None
    sender: str | None = None
    is_vip: bool = False
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)


class Classification(BaseModel):
    """Structured classifier output. The LLM (or fallback) must fill exactly this."""

    category: Category
    urgency: Urgency
    sentiment: str = "neutral"  # positive | neutral | negative
    entities: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class RuleDecision(BaseModel):
    """What the rules engine decided, and which rule fired — for the audit trail."""

    priority: Priority
    rule_fired: str
    queue: str


class ActionRecord(BaseModel):
    """A mocked side effect. Nothing in this project sends real email or opens real tickets."""

    action_type: str  # route_to_queue | human_review | draft_response
    detail: str


class TriageResult(BaseModel):
    """The full, auditable outcome of processing one WorkItem."""

    item_id: str
    classification: Classification
    decision: RuleDecision
    auto_routed: bool
    actions: list[ActionRecord]
    run_id: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
