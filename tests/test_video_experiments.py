from pathlib import Path

from growth_engine.video_experiments import (
    VideoExperiment,
    dispatch_approved_video,
    first_short_form_experiment,
    prepare_video_experiment,
)


class FakeManager:
    def __init__(self):
        self.calls = []

    def post_to_tiktok(self, video_path=None, video_url=None):
        self.calls.append(("tiktok", video_path, video_url))
        return {"success": True, "id": "tt-publish-1"}

    def post_to_youtube(self, **kwargs):
        self.calls.append(("youtube", kwargs))
        return {
            "success": True,
            "id": "yt-video-1",
            "watch_url": "https://www.youtube.com/watch?v=yt-video-1",
            "privacy_status": kwargs.get("privacy_status"),
        }


def _video(tmp_path: Path) -> str:
    path = tmp_path / "experiment.mp4"
    path.write_bytes(b"not-a-real-video-but-nonempty-for-unit-test")
    return str(path)


def test_prepare_video_experiment_is_credential_free(tmp_path):
    exp = first_short_form_experiment(_video(tmp_path), "tiktok")
    result = prepare_video_experiment(exp)
    assert result["dispatch_mode"] == "tiktok_inbox_draft"
    assert result["video_exists"] is True
    assert result["ready_for_approval"] is True


def test_no_approval_means_no_platform_call(tmp_path):
    fake = FakeManager()
    exp = first_short_form_experiment(_video(tmp_path), "tiktok")
    result = dispatch_approved_video(exp, approved=False, manager=fake)
    assert result["blocked"] is True
    assert fake.calls == []


def test_tiktok_dispatch_only_sends_to_drafts(tmp_path):
    fake = FakeManager()
    exp = first_short_form_experiment(_video(tmp_path), "tiktok")
    result = dispatch_approved_video(exp, approved=True, manager=fake)
    assert result["success"] is True
    assert result["mode"] == "inbox_draft"
    assert result["publish_id"] == "tt-publish-1"
    assert fake.calls[0][0] == "tiktok"


def test_youtube_dispatch_is_forced_private(tmp_path):
    fake = FakeManager()
    exp = first_short_form_experiment(_video(tmp_path), "youtube")
    result = dispatch_approved_video(exp, approved=True, manager=fake)
    assert result["success"] is True
    assert result["mode"] == "private_upload"
    assert fake.calls[0][0] == "youtube"
    assert fake.calls[0][1]["privacy_status"] == "private"


def test_unsupported_platform_is_blocked(tmp_path):
    fake = FakeManager()
    exp = VideoExperiment(
        experiment_id="x",
        platform="unknown",
        hypothesis="x",
        hook="How can a contractor prevent 3 costly safety delays?",
        body="Build a strong file, verify legal appointments, and keep risk controls current before the site audit begins.",
        cta="Which one would you check first?",
        video_path=_video(tmp_path),
    )
    result = dispatch_approved_video(exp, approved=True, manager=fake)
    assert result["success"] is False
    assert result["blocked"] is True
    assert fake.calls == []
