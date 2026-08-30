"""Credential-free Trend Scout primitives for FIKILE Growth Engine.

Sources can be entered manually or supplied later by RSS/search/platform
connectors. Ranking is deterministic and explainable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass
class TrendOpportunity:
    topic: str
    source: str
    audience_fit: int
    freshness: int
    evidence_strength: int
    originality_room: int
    commercial_relevance: int = 0
    notes: str = ""

    def score(self) -> float:
        values = {
            "audience_fit": self.audience_fit,
            "freshness": self.freshness,
            "evidence_strength": self.evidence_strength,
            "originality_room": self.originality_room,
            "commercial_relevance": self.commercial_relevance,
        }
        for name, value in values.items():
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
        weighted = (
            self.audience_fit * 0.30
            + self.freshness * 0.20
            + self.evidence_strength * 0.20
            + self.originality_room * 0.20
            + self.commercial_relevance * 0.10
        )
        return round(weighted, 2)

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["opportunity_score"] = self.score()
        return row


def rank_opportunities(items: Iterable[TrendOpportunity]) -> list[dict[str, Any]]:
    """Return strongest opportunities first."""
    rows = [item.to_dict() for item in items]
    return sorted(rows, key=lambda row: row["opportunity_score"], reverse=True)


def should_test(opportunity: TrendOpportunity, threshold: float = 65.0) -> bool:
    """Gate weak trends before content generation."""
    return opportunity.score() >= threshold
