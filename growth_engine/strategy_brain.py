"""Evidence-based Strategy Brain for FIKILE Growth Engine.

Takes repeated experiment outcomes and operator feedback, then emits bounded
strategy directives. It does not publish, fabricate metrics, or rewrite rules
from a single result.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from collections import Counter
from typing import Any, Iterable


@dataclass
class StrategyMemory:
    working_patterns: dict[str, int] = field(default_factory=dict)
    weak_patterns: dict[str, int] = field(default_factory=dict)
    operator_preferences: dict[str, int] = field(default_factory=dict)
    promoted_rules: list[str] = field(default_factory=list)
    retired_rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Evidence:
    pattern: str
    outcome: str  # win, loss, tie
    repetitions: int
    effect_pct: float
    source: str = "experiment"


class StrategyBrain:
    """Conservative strategy updater: patterns must repeat before promotion."""

    def __init__(self, memory: StrategyMemory | None = None, promotion_threshold: int = 3):
        self.memory = memory or StrategyMemory()
        self.promotion_threshold = max(3, promotion_threshold)

    def ingest(self, evidence: Iterable[Evidence]) -> StrategyMemory:
        for item in evidence:
            if item.repetitions < 3:
                continue
            if item.outcome == "win" and item.effect_pct >= 20.0:
                self.memory.working_patterns[item.pattern] = self.memory.working_patterns.get(item.pattern, 0) + 1
            elif item.outcome == "loss" and item.effect_pct <= -20.0:
                self.memory.weak_patterns[item.pattern] = self.memory.weak_patterns.get(item.pattern, 0) + 1
        self._promote_stable_patterns()
        return self.memory

    def ingest_operator_feedback(self, notes: Iterable[str]) -> None:
        """Accumulate repeated human preferences; never infer a rule from one note."""
        counts = Counter(n.strip().lower() for n in notes if n and n.strip())
        for note, count in counts.items():
            self.memory.operator_preferences[note] = self.memory.operator_preferences.get(note, 0) + count

    def _promote_stable_patterns(self) -> None:
        for pattern, count in self.memory.working_patterns.items():
            if count >= self.promotion_threshold and pattern not in self.memory.promoted_rules:
                self.memory.promoted_rules.append(pattern)
        for pattern, count in self.memory.weak_patterns.items():
            if count >= self.promotion_threshold and pattern not in self.memory.retired_rules:
                self.memory.retired_rules.append(pattern)

    def direction(self) -> dict[str, Any]:
        working = sorted(self.memory.working_patterns.items(), key=lambda x: (-x[1], x[0]))
        weak = sorted(self.memory.weak_patterns.items(), key=lambda x: (-x[1], x[0]))
        prefs = sorted(self.memory.operator_preferences.items(), key=lambda x: (-x[1], x[0]))
        return {
            "prioritize": [p for p, _ in working[:5]],
            "deprioritize": [p for p, _ in weak[:5]],
            "promoted_rules": list(self.memory.promoted_rules),
            "retired_rules": list(self.memory.retired_rules),
            "operator_preferences": [p for p, count in prefs if count >= 3][:5],
            "next_action": "design a one-variable experiment against the highest-value unresolved hypothesis",
            "memory": asdict(self.memory),
        }
