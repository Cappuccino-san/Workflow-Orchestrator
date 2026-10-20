# AI Workflow Orchestrator

Unified triage for **tickets, emails, and log alerts**: every incoming item is
classified, prioritized by **deterministic business rules**, routed to the
right team, and recorded in a full audit trail.

> Most AI demos stop at "the model answered." This one shows the part real
> operations teams actually need: classification → rules → action → audit,
> with a human gate wherever the model isn't confident enough to act.

## What it does

1. **Ingest** — tickets, emails, and log alerts are normalized into one schema.
2. **Classify** — a LangChain LLM (or a deterministic fallback) returns a
   structured classification: category, urgency, sentiment, confidence.
3. **Prioritize** — a plain-Python rules engine assigns P1–P4 and picks the
   owning queue. The LLM never decides priority. Same input → same priority, every run.
4. **Gate** — confidence below threshold → human review queue instead of auto-routing.
5. **Act** — mocked, safe actions: route to queue, draft an acknowledgement.
6. **Audit** — every step is stored in SQLite: item, classification, rule fired,
   actions, timestamp. Any decision can be replayed and explained.

## Quick start (no API key needed)

```bash
pip install -e ".[dev]"
python -m workflow_orchestrator.cli data/sample_items.json
pytest -q
```

Run the API:

```bash
uvicorn workflow_orchestrator.api:app --reload
# then open http://127.0.0.1:8000/docs
```

Run with Docker:

```bash
docker build -t ai-workflow-orchestrator .
docker run -p 8000:8000 ai-workflow-orchestrator
```

To use the LLM classifier instead of the fallback, copy `.env.example` to
`.env`, set `CLASSIFIER_MODE=llm` and your `OPENAI_API_KEY`, and install the
LLM extra: `pip install -e ".[llm]"`.

## Sample output

```
T-1001     ticket  -> security           high      P1  queue=security          rule=high_urgency_security_or_outage  conf=0.88  [auto-routed]
L-2001     log     -> outage             critical  P1  queue=platform-oncall   rule=critical_urgency                  conf=0.88  [auto-routed]
T-1003     ticket  -> other              medium    P3  queue=general-triage    rule=default                           conf=0.40  [HUMAN REVIEW]
```

## Architecture

```
            ┌────────────┐   ┌──────────────┐   ┌─────────────┐
 WorkItem ─▶│ Classifier │──▶│ Rules engine │──▶│ Confidence  │
            │ LLM/rules  │   │ deterministic│   │ gate        │
            └────────────┘   └──────────────┘   └──────┬──────┘
                                                       │
                                        ┌──────────────▼──────────────┐
                                        │ Actions (mocked) + Audit log │
                                        └─────────────────────────────┘
```

| Module | Job |
|---|---|
| `schemas.py` | Pydantic models — the contract at every boundary |
| `ingest.py` | Load + normalize raw items into `WorkItem`s |
| `classify/` | LLM classifier (LangChain, structured output) + rules fallback |
| `rules/engine.py` | Ordered deterministic rules → priority, queue, rule fired |
| `orchestrator.py` | Wires the stages together, owns the run ID |
| `actions.py` | Mocked side effects (swap one function for a real integration) |
| `audit.py` | SQLite audit log (standard library only) |
| `api.py` | FastAPI: `/triage`, `/triage/batch`, `/audit`, `/health` |

See [DESIGN.md](DESIGN.md) for the design decisions and tradeoffs.

## Tech

Python · LangChain (structured outputs) · Pydantic · FastAPI · SQLite ·
pytest · Docker · GitHub Actions

## Roadmap

- [ ] Labeled eval set with category/priority accuracy scoring
- [ ] Streamlit dashboard for the review queue
- [ ] Duplicate detection via embeddings + vector DB
- [ ] Real integration behind `actions.py` (Jira / ServiceNow / Slack)

## Limitations

Actions are mocked by design — nothing here sends email or opens real
tickets. Sample data is synthetic. In production this would sit behind a
queue (e.g. SQS/Celery) with per-source ingestion connectors; see DESIGN.md.
