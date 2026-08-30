from growth_engine.experiments import (
    ExperimentVariant,
    GrowthExperiment,
    choose_winner,
    record_manual_performance,
    score_experiment,
)


def _experiment():
    return GrowthExperiment(
        experiment_id="EXP-001",
        hypothesis="Question-led hooks outperform generic statements",
        topic="contractor safety compliance",
        target_metric="qualified_comments",
        platform="linkedin",
        variants=[
            ExperimentVariant(
                name="question-hook",
                hook="What safety gap costs contractors the most time at the gate?",
                body="Missing appointments, outdated files, and weak risk controls can stop work before the shift even starts.",
                cta="Which one hurts your team most?",
            ),
            ExperimentVariant(
                name="statement-hook",
                hook="Safety compliance gaps cost contractors time.",
                body="Missing appointments, outdated files, and weak risk controls can stop work before the shift even starts.",
                cta="Tell us what you see most often on site.",
            ),
        ],
    )


def test_score_experiment_scores_each_variant():
    exp = score_experiment(_experiment())
    assert all(v.pre_publish_score is not None for v in exp.variants)


def test_single_observation_cannot_declare_winner():
    exp = _experiment()
    for variant in exp.variants:
        record_manual_performance(variant, reach=100, comments=4, shares=1)
    result = choose_winner(exp)
    assert result["winner"] is None
    assert "observations" in result["reason"]


def test_repeated_manual_metrics_can_produce_provisional_winner():
    exp = _experiment()
    winner, loser = exp.variants

    for _ in range(2):
        record_manual_performance(
            winner,
            reach=100,
            reactions=10,
            comments=10,
            shares=5,
            saves=4,
            qualified_views=55,
            watch_seconds=700,
        )
        record_manual_performance(
            loser,
            reach=100,
            reactions=2,
            comments=1,
            shares=0,
            saves=0,
            qualified_views=10,
            watch_seconds=60,
        )

    result = choose_winner(exp)
    assert result["winner"] == "question-hook"
    assert result["margin"] >= 5
