"""FIKILE Growth Engine — guarded video experiment dispatch.

TikTok uses the existing inbox/draft uploader. YouTube uploads are forced to
private. Both routes require an explicit human-approved flag before any network
publisher is called.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from manager import Manager
from .scorer import score_post


@dataclass
class VideoExperiment:
    experiment_id: str
    platform: str
    hypothesis: str
    hook: str
    body: str
    cta: str
    video_path: str
    title: str = ""
    target_metric: str = "qualified_views"

    @property
    def copy(self) -> str:
        return "\n\n".join(
            part.strip() for part in (self.hook, self.body, self.cta) if part.strip()
        )


def prepare_video_experiment(experiment: VideoExperiment) -> dict[str, Any]:
    """Prepare a video experiment without touching a platform API."""
    score = score_post(experiment.copy)
    path = Path(experiment.video_path).expanduser()
    return {
        "experiment": asdict(experiment),
        "score": score.to_dict(),
        "video_exists": path.is_file(),
        "ready_for_approval": score.verdict != "REJECT" and path.is_file(),
        "approved": False,
        "dispatch_mode": (
            "tiktok_inbox_draft" if experiment.platform == "tiktok"
            else "youtube_private" if experiment.platform == "youtube"
            else "unsupported"
        ),
    }


def dispatch_approved_video(
    experiment: VideoExperiment,
    *,
    approved: bool,
    manager: Manager | None = None,
) -> dict[str, Any]:
    """Dispatch only after explicit human approval.

    TikTok: uploads into TikTok inbox/drafts. The user still taps Publish.
    YouTube: uploads with privacy_status='private'. Public release remains a
    separate human action.
    """
    prepared = prepare_video_experiment(experiment)
    if not approved:
        return {"success": False, "blocked": True, "error": "Human approval required"}
    if not prepared["ready_for_approval"]:
        return {
            "success": False,
            "blocked": True,
            "error": "Experiment failed pre-publish checks or video file is missing",
            "prepared": prepared,
        }

    publisher = manager or Manager()
    if experiment.platform == "tiktok":
        result = publisher.post_to_tiktok(video_path=experiment.video_path)
        return {
            "success": bool(result.get("success")),
            "platform": "tiktok",
            "mode": "inbox_draft",
            "publish_id": result.get("id"),
            "result": result,
        }

    if experiment.platform == "youtube":
        result = publisher.post_to_youtube(
            video_path=experiment.video_path,
            title=(experiment.title or experiment.hook)[:100],
            description=experiment.copy,
            privacy_status="private",
        )
        return {
            "success": bool(result.get("success")),
            "platform": "youtube",
            "mode": "private_upload",
            "video_id": result.get("id"),
            "watch_url": result.get("watch_url"),
            "result": result,
        }

    return {"success": False, "blocked": True, "error": f"Unsupported platform: {experiment.platform}"}


def first_short_form_experiment(video_path: str, platform: str) -> VideoExperiment:
    """Experiment #002: short educational contractor-safety video."""
    return VideoExperiment(
        experiment_id="FIKILE-VID-002",
        platform=platform,
        hypothesis=(
            "A short, specific contractor-safety lesson will earn more qualified "
            "watch time than generic promotional content."
        ),
        hook="3 safety-file gaps that can stop a contractor before work starts",
        body=(
            "A missing legal appointment, an outdated risk assessment, and evidence "
            "that controls exist only on paper can turn a routine gate or audit into "
            "an expensive delay. The lesson: find the gap before the site finds it."
        ),
        cta="Which compliance gap causes the most delays on your projects?",
        video_path=video_path,
        title="3 Safety-File Gaps That Can Stop a Contractor",
        target_metric="qualified_watch_time",
    )
