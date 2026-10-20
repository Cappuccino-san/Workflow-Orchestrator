# Design Notes — AI Workflow Orchestrator

## The core decision: the LLM describes, the rules decide

The pipeline splits responsibility on purpose:

- **The classifier (LLM or fallback)** answers *"what is this?"* — category,
  urgency, sentiment, and how confident it is. This is a language task, and
  being wrong here is recoverable.
- **The rules engine (plain Python)** answers *"how much does it matter and
  who owns it?"* — priority and queue. This is a business decision with SLA
  and audit consequences, so it must be:
  - **Deterministic** — same classification in, same priority out, every run.
  - **Explainable** — every decision names the rule that fired.
  - **Testable** — changing a rule breaks a unit test, loudly, before it
    silently changes an SLA in production.

An LLM-decided priority fails all three: it can drift between runs, it
cannot name its rule, and it cannot be unit-tested.

## The confidence gate

Automation without a gate is how a misclassified ticket becomes a missed
incident. The rule is simple:

- `confidence >= 0.65` → auto-route (plus a drafted acknowledgement for P1/P2)
- `confidence < 0.65` → human review queue, with the score recorded

The threshold is configuration, not code, because different teams will set
it differently — and a security queue might set it higher than a billing queue.

## Priority rules (in evaluation order)

| # | Rule | Result |
|---|---|---|
| 1 | Urgency is critical | P1 |
| 2 | High urgency + security or outage | P1 |
| 3 | Security or outage (any urgency) | at least P2 |
| 4 | VIP sender + high urgency | P2 |
| 5 | High urgency | P2 |
| 6 | Low urgency, or feature request | P4 |
| 7 | Default | P3 |

First match wins. The full logic lives in `src/workflow_orchestrator/rules/engine.py`.

## Why a rules-based fallback classifier?

1. The pipeline and its tests run in CI with **no API key and no cost**.
2. If the LLM provider is down, triage degrades instead of stopping.
3. It gives the eval harness a baseline: the LLM must beat the fallback
   measurably, or it isn't earning its place.

## Why SQLite for the audit log?

Zero dependencies (standard library), a real queryable store, and the right
size for a portfolio demo. The `AuditLog` class is the only place that knows
it's SQLite — swapping in Postgres changes one file.

## Why mocked actions?

A portfolio project that can actually send email or open tickets is a
liability, not a feature. Each action records exactly what *would* happen.
In a real deployment, `actions.py` is where Jira/ServiceNow/Slack calls go —
one function each, nothing else in the pipeline changes.

## What production would add

- A message queue between ingestion and processing (SQS / Celery / Kafka)
- Per-source connectors (helpdesk API, IMAP/Gmail, log stream) instead of JSON files
- Per-queue confidence thresholds and rule sets, managed as configuration
- A review UI where human decisions feed back into the eval set
- Embedding-based duplicate/related-item detection (vector DB) before routing

## Interview cheat-sheet: likely questions

- *"Why not let the LLM set priority directly?"* — See core decision above.
- *"How do you know the classifier is good enough?"* — Labeled eval set,
  accuracy by category, and the auto-route vs. human-review rate; the
  fallback classifier is the baseline to beat.
- *"What breaks first at 100x volume?"* — Synchronous processing; that's
  why the queue is the first production addition, and why ingestion is
  already separated from processing.
