"""Standalone visual console for the FIKILE Growth Engine.

Run with:
    python -m dashboard.growth_console
Then open:
    http://127.0.0.1:7652

This console intentionally uses a safe simulation by default: it exercises the
Experiment Engine and Strategy Brain without publishing to any social platform.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from growth_engine.experiment_engine import (
    ControlledExperiment,
    DecisionRule,
    Trial,
    evaluate_experiment,
)
from growth_engine.strategy_brain import Evidence, StrategyBrain

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title="FIKILE Growth Control Center")


def build_demo_snapshot() -> dict:
    """Run a deterministic, credential-free experiment + strategy simulation."""
    exp = ControlledExperiment(
        experiment_id="FIKILE-SIM-001",
        hypothesis="A direct problem-first hook increases qualified watch time.",
        platform="tiktok",
        variable="hook",
        control_value="generic safety intro",
        challenger_value="problem-first contractor hook",
        controlled_fields=("topic", "length", "format", "posting_window", "cta"),
        rule=DecisionRule(
            primary_metric="qualified_watch_time",
            minimum_effect_pct=20.0,
            guardrail_metric="completion_rate",
            max_guardrail_decline_pct=5.0,
            repetitions_required=3,
        ),
    )

    pairs = [
        (100.0, 128.0, 52.0, 54.0),
        (110.0, 142.0, 51.0, 52.0),
        (95.0, 123.0, 50.0, 51.0),
    ]
    for repetition, (c_watch, x_watch, c_completion, x_completion) in enumerate(pairs, start=1):
        exp.record(Trial("control", repetition, {
            "qualified_watch_time": c_watch,
            "completion_rate": c_completion,
        }))
        exp.record(Trial("challenger", repetition, {
            "qualified_watch_time": x_watch,
            "completion_rate": x_completion,
        }))

    result = evaluate_experiment(exp)

    brain = StrategyBrain()
    # Three independent qualifying experiment outcomes are required before
    # a pattern becomes a promoted rule in the Strategy Brain.
    brain.ingest([
        Evidence("problem-first hooks", "win", 3, 25.0, "simulation-1"),
        Evidence("problem-first hooks", "win", 3, 24.0, "simulation-2"),
        Evidence("problem-first hooks", "win", 3, 28.0, "simulation-3"),
    ])
    brain.ingest_operator_feedback([
        "keep it specific",
        "keep it specific",
        "keep it specific",
    ])

    return {
        "mode": "SAFE SIMULATION",
        "experiment": exp.to_dict(),
        "result": result,
        "strategy": brain.direction(),
        "platforms": {
            "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()),
            "tiktok": bool(os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()),
            "youtube": bool(os.getenv("YOUTUBE_ACCESS_TOKEN", "").strip()),
            "facebook": bool(os.getenv("FACEBOOK_ACCESS_TOKEN", "").strip()),
        },
        "safety": {
            "publishing_performed": False,
            "human_approval_required": True,
            "secrets_exposed": False,
        },
    }


@app.get("/", response_class=HTMLResponse)
async def growth_console(request: Request):
    return templates.TemplateResponse(
        request,
        "growth_console.html",
        {"snapshot": build_demo_snapshot()},
    )


@app.get("/api/growth/overview")
async def growth_overview():
    return JSONResponse(build_demo_snapshot())


def main() -> None:
    import uvicorn
    uvicorn.run("dashboard.growth_console:app", host="127.0.0.1", port=7652, reload=False)


if __name__ == "__main__":
    main()
