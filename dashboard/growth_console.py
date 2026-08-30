"""Standalone visual console for the FIKILE Growth Engine.

Run with: python -m dashboard.growth_console
Open: http://127.0.0.1:7652

Safe simulation remains non-publishing, but experiments and Strategy Brain memory
are now persisted in SQLite and survive application restarts.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from growth_engine.experiment_engine import ControlledExperiment, DecisionRule, Trial, evaluate_experiment
from growth_engine.registry import ExperimentRegistry
from growth_engine.strategy_brain import Evidence, StrategyBrain

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title="FIKILE Growth Control Center")
registry = ExperimentRegistry()


def build_demo_snapshot() -> dict:
    exp = ControlledExperiment(
        experiment_id="FIKILE-SIM-001",
        hypothesis="A direct problem-first hook increases qualified watch time.",
        platform="tiktok", variable="hook",
        control_value="generic safety intro",
        challenger_value="problem-first contractor hook",
        controlled_fields=("topic", "length", "format", "posting_window", "cta"),
        rule=DecisionRule(primary_metric="qualified_watch_time", minimum_effect_pct=20.0,
                          guardrail_metric="completion_rate", max_guardrail_decline_pct=5.0,
                          repetitions_required=3),
    )
    pairs = [(100.0,128.0,52.0,54.0),(110.0,142.0,51.0,52.0),(95.0,123.0,50.0,51.0)]
    for repetition, (cw,xw,cc,xc) in enumerate(pairs, start=1):
        exp.record(Trial("control", repetition, {"qualified_watch_time": cw, "completion_rate": cc}))
        exp.record(Trial("challenger", repetition, {"qualified_watch_time": xw, "completion_rate": xc}))
    result = evaluate_experiment(exp)
    registry.save_experiment(exp, result)

    brain = StrategyBrain(memory=registry.load_strategy_memory())
    # Seed evidence only until the rule is promoted. Reopening the app will not
    # inflate evidence counts: persisted memory is reused instead of relearned.
    if "problem-first hooks" not in brain.memory.promoted_rules:
        brain.ingest([
            Evidence("problem-first hooks", "win", 3, 25.0, "simulation-1"),
            Evidence("problem-first hooks", "win", 3, 24.0, "simulation-2"),
            Evidence("problem-first hooks", "win", 3, 28.0, "simulation-3"),
        ])
    if brain.memory.operator_preferences.get("keep it specific", 0) < 3:
        brain.ingest_operator_feedback(["keep it specific"] * 3)
    registry.save_strategy_memory(brain.memory)

    return {
        "mode": "SAFE SIMULATION + PERSISTENT MEMORY",
        "experiment": exp.to_dict(), "result": result,
        "strategy": brain.direction(),
        "registry": {"stats": registry.stats(), "experiments": registry.list_experiments(10)},
        "platforms": {
            "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()),
            "tiktok": bool(os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()),
            "youtube": bool(os.getenv("YOUTUBE_ACCESS_TOKEN", "").strip()),
            "facebook": bool(os.getenv("FACEBOOK_ACCESS_TOKEN", "").strip()),
        },
        "safety": {"publishing_performed": False, "human_approval_required": True, "secrets_exposed": False},
    }


@app.get("/", response_class=HTMLResponse)
async def growth_console(request: Request):
    return templates.TemplateResponse(request, "growth_console.html", {"snapshot": build_demo_snapshot()})

@app.get("/api/growth/overview")
async def growth_overview():
    return JSONResponse(build_demo_snapshot())

@app.get("/api/growth/experiments")
async def growth_experiments():
    return JSONResponse({"stats": registry.stats(), "experiments": registry.list_experiments()})

@app.get("/api/growth/memory")
async def growth_memory():
    brain = StrategyBrain(memory=registry.load_strategy_memory())
    return JSONResponse(brain.direction())


def main() -> None:
    import uvicorn
    uvicorn.run("dashboard.growth_console:app", host="127.0.0.1", port=7652, reload=False)

if __name__ == "__main__":
    main()
