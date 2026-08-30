from growth_engine.experiment_engine import ControlledExperiment, DecisionRule, Trial, evaluate_experiment
from growth_engine.strategy_brain import Evidence, StrategyBrain


def _experiment():
    return ControlledExperiment(
        experiment_id="FIKILE-EXP-001",
        hypothesis="Question hooks increase qualified comments",
        platform="linkedin",
        variable="hook",
        control_value="statement",
        challenger_value="question",
        controlled_fields=("topic", "format", "length", "posting_window"),
        rule=DecisionRule(primary_metric="comments_per_1000_reach", minimum_effect_pct=20, guardrail_metric="saves_per_1000_reach", repetitions_required=3),
    )


def test_experiment_refuses_early_winner():
    exp = _experiment()
    exp.record(Trial("control", 1, {"comments_per_1000_reach": 10, "saves_per_1000_reach": 5}))
    exp.record(Trial("challenger", 1, {"comments_per_1000_reach": 20, "saves_per_1000_reach": 5}))
    assert evaluate_experiment(exp)["decision"] == "keep_testing"


def test_experiment_promotes_repeated_large_effect():
    exp = _experiment()
    for rep, control, challenger in [(1, 10, 14), (2, 12, 16), (3, 11, 15)]:
        exp.record(Trial("control", rep, {"comments_per_1000_reach": control, "saves_per_1000_reach": 5}))
        exp.record(Trial("challenger", rep, {"comments_per_1000_reach": challenger, "saves_per_1000_reach": 5}))
    result = evaluate_experiment(exp)
    assert result["decision"] == "challenger_wins"
    assert result["effect_pct"] >= 20


def test_strategy_brain_requires_repeated_experiment_wins_before_rule():
    brain = StrategyBrain(promotion_threshold=3)
    evidence = Evidence("question_hook", "win", 3, 25)
    brain.ingest([evidence])
    assert "question_hook" not in brain.direction()["promoted_rules"]
    brain.ingest([evidence, evidence])
    assert "question_hook" in brain.direction()["promoted_rules"]


def test_operator_preference_requires_three_repeats():
    brain = StrategyBrain()
    brain.ingest_operator_feedback(["larger mobile text", "larger mobile text"])
    assert brain.direction()["operator_preferences"] == []
    brain.ingest_operator_feedback(["larger mobile text"])
    assert brain.direction()["operator_preferences"] == ["larger mobile text"]
