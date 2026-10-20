"""Configuration, loaded from environment variables.

Defaults are chosen so the project runs end-to-end with no API key:
the rules-based fallback classifier is the default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Frozen so a run's config cannot change mid-pipeline."""

    classifier_mode: str = "rules"  # "rules" | "llm"
    llm_model: str = "gpt-4o-mini"
    confidence_threshold: float = 0.65
    audit_db_path: str = "data/audit.db"

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from the environment (see .env.example)."""
        return cls(
            classifier_mode=os.getenv("CLASSIFIER_MODE", "rules"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.65")),
            audit_db_path=os.getenv("AUDIT_DB_PATH", "data/audit.db"),
        )
