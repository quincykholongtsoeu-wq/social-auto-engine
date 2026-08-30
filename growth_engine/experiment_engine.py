"""Rigorous organic experiment engine for FIKILE Growth Engine.

Inspired by the TEST discipline from social-media-skills/skills (MIT):
Target one variable, Establish the rule before publishing, Set controls/sample,
Tally/repeat/scale. Organic results are directional, never lab-grade proof.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class DecisionRule:
    primary_metric: str
    minimum_effect_pct: float = 20.0
    guardrail_metric: str | None = None
    max_guardrail_decline_pct: float = 0.0
    repetitions_required: int = 3


@dataclass
class Trial:
    variant: str
    repetition: int
    metrics: dict[str, float]
    context: dict[str, str] = field(default_factory=dict)


@dataclass
class ControlledExperiment:
    experiment_id: str
    hypothesis: str
    platform: str
    variable: str
    control_value: str
    challenger_value: str
    controlled_fields: tuple[str, ...]
    rule: DecisionRule
    trials: list[Trial] = field(default_factory=list)
    status: str = "designed"

    def validate_design(self) -> list[str]:
        errors: list[str] = []
        if not self.hypothesis.strip():
            errors.append("hypothesis is required")
        if not self.variable.strip():
            errors.append("exactly one test variable must be named")
        if self.control_value == self.challenger_value:
            errors.append("control and challenger must differ")
        if self.rule.repetitions_required < 3:
            errors.append("at least 3 paired repetitions are required")
        if self.rule.minimum_effect_pct < 0:
            errors.append("minimum effect cannot be negative")
        if not self.controlled_fields:
            errors.append("controlled context must be declared")
        return errors

    def record(self, trial: Trial) -> None:
        if trial.variant not in {"control", "challenger"}:
            raise ValueError("variant must be control or challenger")
        if self.rule.primary_metric not in trial.metrics:
            raise ValueError("primary metric missing from trial")
        self.trials.append(trial)
        self.status = "running"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _paired_values(exp: ControlledExperiment, metric: str) -> tuple[list[float], list[float]]:
    control = {t.repetition: t.metrics[metric] for t in exp.trials if t.variant == "control" and metric in t.metrics}
    challenger = {t.repetition: t.metrics[metric] for t in exp.trials if t.variant == "challenger" and metric in t.metrics}
    paired = sorted(set(control) & set(challenger))
    return [control[i] for i in paired], [challenger[i] for i in paired]


def evaluate_experiment(exp: ControlledExperiment) -> dict[str, Any]:
    """Evaluate only paired repetitions against the pre-registered rule."""
    design_errors = exp.validate_design()
    if design_errors:
        return {"decision": "invalid", "reasons": design_errors}

    controls, challengers = _paired_values(exp, exp.rule.primary_metric)
    n = len(controls)
    if n < exp.rule.repetitions_required:
        return {"decision": "keep_testing", "paired_repetitions": n, "required": exp.rule.repetitions_required}

    c_mean, x_mean = mean(controls), mean(challengers)
    if c_mean <= 0:
        return {"decision": "inconclusive", "reason": "control baseline is zero or negative"}
    effect_pct = ((x_mean - c_mean) / c_mean) * 100.0

    guardrail_ok = True
    guardrail_effect = None
    if exp.rule.guardrail_metric:
        gc, gx = _paired_values(exp, exp.rule.guardrail_metric)
        if len(gc) < exp.rule.repetitions_required:
            return {"decision": "keep_testing", "reason": "guardrail observations incomplete"}
        gc_mean, gx_mean = mean(gc), mean(gx)
        if gc_mean > 0:
            guardrail_effect = ((gx_mean - gc_mean) / gc_mean) * 100.0
            guardrail_ok = guardrail_effect >= -exp.rule.max_guardrail_decline_pct

    consistent_wins = sum(x > c for c, x in zip(controls, challengers))
    majority_required = (n // 2) + 1
    wins = effect_pct >= exp.rule.minimum_effect_pct and consistent_wins >= majority_required and guardrail_ok

    decision = "challenger_wins" if wins else "no_winner"
    exp.status = "completed"
    return {
        "decision": decision,
        "paired_repetitions": n,
        "control_mean": round(c_mean, 4),
        "challenger_mean": round(x_mean, 4),
        "effect_pct": round(effect_pct, 2),
        "minimum_effect_pct": exp.rule.minimum_effect_pct,
        "challenger_pair_wins": consistent_wins,
        "guardrail_ok": guardrail_ok,
        "guardrail_effect_pct": None if guardrail_effect is None else round(guardrail_effect, 2),
        "scope": "directional organic evidence; not statistical proof",
    }
