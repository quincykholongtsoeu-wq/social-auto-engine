"""FIKILE Growth Engine experiment orchestration.

Designed to work before any social-platform credentials exist. Experiments can
be prepared, scored, approved, published later, and measured manually.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any, Iterable

from .learner import PostPerformance, evaluate_post
from .scorer import score_post


@dataclass
class ExperimentVariant:
    name: str
    hook: str
    body: str
    cta: str
    format: str = "text"
    pre_publish_score: int | None = None
    post_id: str | None = None
    observations: list[dict[str, Any]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(x.strip() for x in (self.hook, self.body, self.cta) if x.strip())


@dataclass
class GrowthExperiment:
    experiment_id: str
    hypothesis: str
    topic: str
    target_metric: str
    platform: str
    variants: list[ExperimentVariant]
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_experiment(experiment: GrowthExperiment) -> GrowthExperiment:
    """Attach deterministic pre-publish scores to each variant."""
    for variant in experiment.variants:
        variant.pre_publish_score = score_post(variant.text).total
    return experiment


def record_manual_performance(
    variant: ExperimentVariant,
    *,
    reach: int,
    reactions: int = 0,
    comments: int = 0,
    shares: int = 0,
    saves: int = 0,
    qualified_views: int = 0,
    watch_seconds: float = 0.0,
) -> dict[str, Any]:
    """Record metrics copied manually from a platform dashboard.

    This is the credential-free bridge for Facebook/LinkedIn/TikTok/etc.
    """
    performance = PostPerformance(
        post_id=variant.post_id or variant.name,
        reach=reach,
        reactions=reactions,
        comments=comments,
        shares=shares,
        saves=saves,
        qualified_views=qualified_views,
        watch_seconds=watch_seconds,
        variant=variant.name,
    )
    result = evaluate_post(performance).to_dict()
    variant.observations.append(result)
    return result


def variant_mean_score(variant: ExperimentVariant) -> float | None:
    scores = [float(obs["score"]) for obs in variant.observations if "score" in obs]
    return round(mean(scores), 2) if scores else None


def choose_winner(
    experiment: GrowthExperiment,
    *,
    minimum_observations_per_variant: int = 2,
    minimum_margin: float = 5.0,
) -> dict[str, Any]:
    """Choose a provisional winner only after repeated evidence.

    A single post is never enough to declare a strategy winner.
    """
    if len(experiment.variants) < 2:
        return {"winner": None, "reason": "Need at least two variants"}

    ranked: list[tuple[ExperimentVariant, float]] = []
    for variant in experiment.variants:
        if len(variant.observations) < minimum_observations_per_variant:
            return {
                "winner": None,
                "reason": f"Need {minimum_observations_per_variant} observations per variant",
            }
        avg = variant_mean_score(variant)
        if avg is not None:
            ranked.append((variant, avg))

    ranked.sort(key=lambda item: item[1], reverse=True)
    if len(ranked) < 2:
        return {"winner": None, "reason": "Insufficient scored evidence"}

    best, runner_up = ranked[0], ranked[1]
    margin = round(best[1] - runner_up[1], 2)
    if margin < minimum_margin:
        return {
            "winner": None,
            "reason": "Result is too close; run another observation",
            "margin": margin,
        }

    return {
        "winner": best[0].name,
        "score": best[1],
        "runner_up": runner_up[0].name,
        "margin": margin,
        "reason": "Provisional winner based on repeated observations",
    }


def rank_variants(variants: Iterable[ExperimentVariant]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        rows.append({
            "variant": variant.name,
            "pre_publish_score": variant.pre_publish_score,
            "observed_score": variant_mean_score(variant),
            "observations": len(variant.observations),
        })
    return sorted(rows, key=lambda x: (x["observed_score"] is not None, x["observed_score"] or -1), reverse=True)
