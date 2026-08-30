"""FIKILE Growth Engine: learn from observed post performance.

The learner normalizes raw engagement by reach so large pages do not
automatically dominate. It does not fabricate engagement or interact with
accounts; it only analyzes supplied performance data.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List


@dataclass
class PostPerformance:
    post_id: str
    reach: int
    reactions: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    qualified_views: int = 0
    watch_seconds: float = 0.0
    variant: str = "control"


@dataclass
class PerformanceScore:
    post_id: str
    variant: str
    score: float
    engagement_rate: float
    qualified_view_rate: float
    avg_watch_seconds: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def evaluate_post(p: PostPerformance) -> PerformanceScore:
    reach = max(p.reach, 1)
    weighted_engagement = p.reactions + (2 * p.comments) + (3 * p.shares) + (2 * p.saves)
    engagement_rate = weighted_engagement / reach
    qualified_view_rate = p.qualified_views / reach
    avg_watch = p.watch_seconds / max(p.qualified_views, 1)

    # 0-100 heuristic score. We will recalibrate these weights with real data.
    score = min(100.0, (
        min(engagement_rate / 0.12, 1.0) * 45
        + min(qualified_view_rate / 0.50, 1.0) * 35
        + min(avg_watch / 20.0, 1.0) * 20
    ))
    return PerformanceScore(
        p.post_id,
        p.variant,
        round(score, 2),
        round(engagement_rate, 4),
        round(qualified_view_rate, 4),
        round(avg_watch, 2),
    )


def rank_experiments(posts: Iterable[PostPerformance]) -> List[PerformanceScore]:
    """Return strongest observed variants first; never auto-publish a winner."""
    return sorted((evaluate_post(p) for p in posts), key=lambda x: x.score, reverse=True)
