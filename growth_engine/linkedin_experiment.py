"""FIKILE Growth Engine — LinkedIn experiment preparation.

This module connects the deterministic growth scorer to SocialBlast's existing
LinkedIn publishing path without bypassing the human approval queue.

Flow:
    experiment hypothesis -> LinkedIn draft -> score -> approval queue -> publish

No Meta credentials are required.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dashboard import db
from growth_engine.scorer import score_post


@dataclass
class LinkedInExperiment:
    hypothesis: str
    hook: str
    body: str
    cta: str
    target_metric: str = "comments"
    account_name: str = "LinkedIn"

    @property
    def message(self) -> str:
        return "\n\n".join(
            part.strip() for part in (self.hook, self.body, self.cta) if part.strip()
        )


def prepare_linkedin_experiment(experiment: LinkedInExperiment) -> dict[str, Any]:
    """Score an experiment and, when viable, place it in human approval.

    APPROVE and REVISE drafts enter the existing SocialBlast pending queue.
    REJECT drafts are not queued. This keeps autonomous generation separated
    from the irreversible act of publishing.
    """
    score = score_post(experiment.message)
    payload: dict[str, Any] = {
        "experiment": asdict(experiment),
        "message": experiment.message,
        "score": score.to_dict(),
        "queued": False,
        "post_id": None,
    }

    if score.verdict == "REJECT":
        return payload

    post_id = db.create_post(
        message=experiment.message,
        account_name=experiment.account_name,
        platform="linkedin",
    )
    payload["queued"] = True
    payload["post_id"] = post_id
    return payload


def first_fikile_experiment() -> LinkedInExperiment:
    """Return experiment #001: conversation-led founder/safety insight."""
    return LinkedInExperiment(
        hypothesis=(
            "A specific operational-safety question will generate more qualified "
            "conversation than a generic company promotion."
        ),
        hook="What is the most expensive safety problem a contractor discovers too late?",
        body=(
            "For many teams, the real cost starts before an incident: missing legal "
            "appointments, weak risk assessments, outdated safety files, or controls "
            "that exist on paper but not on site. We are testing a simple idea at "
            "FIKILE Safety Solutions: find the compliance gap before the gate, audit, "
            "or shift exposes it."
        ),
        cta="Contractors and safety professionals: which gap causes the most pain on your sites?",
        target_metric="qualified_comments",
    )


def queue_first_fikile_experiment() -> dict[str, Any]:
    """Convenience entry point for experiment #001."""
    return prepare_linkedin_experiment(first_fikile_experiment())
