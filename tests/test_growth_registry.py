from growth_engine.experiment_engine import ControlledExperiment, DecisionRule, Trial, evaluate_experiment
from growth_engine.registry import ExperimentRegistry
from growth_engine.strategy_brain import StrategyMemory


def test_experiment_survives_registry_restart(tmp_path):
    db_path = tmp_path / "growth.db"
    first = ExperimentRegistry(db_path)
    exp = ControlledExperiment(
        experiment_id="EXP-PERSIST-1", hypothesis="Specific hooks win", platform="tiktok",
        variable="hook", control_value="generic", challenger_value="specific",
        controlled_fields=("topic", "length"),
        rule=DecisionRule(primary_metric="watch", repetitions_required=3),
    )
    for i in range(1, 4):
        exp.record(Trial("control", i, {"watch": 100.0}))
        exp.record(Trial("challenger", i, {"watch": 130.0}))
    result = evaluate_experiment(exp)
    first.save_experiment(exp, result)

    reopened = ExperimentRegistry(db_path)
    loaded, loaded_result = reopened.load_experiment("EXP-PERSIST-1")
    assert loaded.experiment_id == exp.experiment_id
    assert len(loaded.trials) == 6
    assert loaded_result["decision"] == "challenger_wins"
    assert reopened.stats() == {"experiments": 1, "trials": 6, "completed": 1}


def test_strategy_memory_survives_registry_restart(tmp_path):
    db_path = tmp_path / "growth.db"
    first = ExperimentRegistry(db_path)
    memory = StrategyMemory(
        working_patterns={"problem-first hooks": 3},
        operator_preferences={"keep it specific": 3},
        promoted_rules=["problem-first hooks"],
    )
    first.save_strategy_memory(memory)

    reopened = ExperimentRegistry(db_path)
    loaded = reopened.load_strategy_memory()
    assert loaded.working_patterns["problem-first hooks"] == 3
    assert loaded.operator_preferences["keep it specific"] == 3
    assert loaded.promoted_rules == ["problem-first hooks"]


def test_upsert_does_not_duplicate_trials(tmp_path):
    registry = ExperimentRegistry(tmp_path / "growth.db")
    exp = ControlledExperiment(
        experiment_id="EXP-IDEMPOTENT", hypothesis="test", platform="youtube",
        variable="title", control_value="a", challenger_value="b",
        controlled_fields=("topic",), rule=DecisionRule(primary_metric="views"),
    )
    exp.record(Trial("control", 1, {"views": 10.0}))
    registry.save_experiment(exp)
    registry.save_experiment(exp)
    assert registry.stats()["trials"] == 1
