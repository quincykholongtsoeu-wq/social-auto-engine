from growth_engine.linkedin_experiment import (
    LinkedInExperiment,
    first_fikile_experiment,
    prepare_linkedin_experiment,
)


def test_first_experiment_is_linkedin_ready():
    exp = first_fikile_experiment()
    assert exp.target_metric == "qualified_comments"
    assert "?" in exp.hook
    assert "FIKILE Safety Solutions" in exp.body
    assert exp.message.endswith("?")


def test_rejected_experiment_does_not_enter_queue(monkeypatch):
    exp = LinkedInExperiment(
        hypothesis="empty content should fail",
        hook="",
        body="",
        cta="",
    )

    called = False

    def fake_create_post(**kwargs):
        nonlocal called
        called = True
        return 999

    monkeypatch.setattr("growth_engine.linkedin_experiment.db.create_post", fake_create_post)
    result = prepare_linkedin_experiment(exp)
    assert result["score"]["verdict"] == "REJECT"
    assert result["queued"] is False
    assert called is False


def test_viable_experiment_enters_linkedin_approval_queue(monkeypatch):
    captured = {}

    def fake_create_post(**kwargs):
        captured.update(kwargs)
        return 42

    monkeypatch.setattr("growth_engine.linkedin_experiment.db.create_post", fake_create_post)
    result = prepare_linkedin_experiment(first_fikile_experiment())

    assert result["score"]["verdict"] in {"APPROVE", "REVISE"}
    assert result["queued"] is True
    assert result["post_id"] == 42
    assert captured["platform"] == "linkedin"
    assert captured["account_name"] == "LinkedIn"
