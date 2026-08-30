from dashboard.growth_console import build_demo_snapshot


def test_growth_console_simulation_proves_experiment_and_strategy_loop():
    snapshot = build_demo_snapshot()

    assert snapshot["mode"] == "SAFE SIMULATION"
    assert snapshot["safety"]["publishing_performed"] is False
    assert snapshot["safety"]["human_approval_required"] is True

    result = snapshot["result"]
    assert result["decision"] == "challenger_wins"
    assert result["paired_repetitions"] == 3
    assert result["effect_pct"] >= 20.0
    assert result["guardrail_ok"] is True

    strategy = snapshot["strategy"]
    assert "problem-first hooks" in strategy["promoted_rules"]
    assert "keep it specific" in strategy["operator_preferences"]


def test_growth_console_platform_status_is_boolean_only():
    snapshot = build_demo_snapshot()
    assert set(snapshot["platforms"]) == {"linkedin", "tiktok", "youtube", "facebook"}
    assert all(isinstance(value, bool) for value in snapshot["platforms"].values())
