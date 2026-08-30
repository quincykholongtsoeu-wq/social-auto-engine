"""Persistent registry for FIKILE Growth Engine experiments and learned strategy.

SQLite keeps experiment definitions, trials, decisions, and Strategy Brain memory
across process restarts. No credentials or platform secrets are stored here.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from growth_engine.experiment_engine import ControlledExperiment, DecisionRule, Trial
from growth_engine.strategy_brain import StrategyMemory

DEFAULT_DB = Path.home() / ".social-auto-engine" / "fikile_growth.db"


class ExperimentRegistry:
    def __init__(self, path: str | Path = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                hypothesis TEXT NOT NULL,
                platform TEXT NOT NULL,
                variable TEXT NOT NULL,
                control_value TEXT NOT NULL,
                challenger_value TEXT NOT NULL,
                controlled_fields_json TEXT NOT NULL,
                rule_json TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS trials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
                variant TEXT NOT NULL,
                repetition INTEGER NOT NULL,
                metrics_json TEXT NOT NULL,
                context_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(experiment_id, variant, repetition)
            );
            CREATE TABLE IF NOT EXISTS strategy_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                memory_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """)

    def save_experiment(self, exp: ControlledExperiment, result: dict[str, Any] | None = None) -> None:
        rule_json = json.dumps(asdict(exp.rule), sort_keys=True)
        fields_json = json.dumps(list(exp.controlled_fields))
        result_json = None if result is None else json.dumps(result, sort_keys=True)
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO experiments (
                    experiment_id, hypothesis, platform, variable, control_value,
                    challenger_value, controlled_fields_json, rule_json, status, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(experiment_id) DO UPDATE SET
                    hypothesis=excluded.hypothesis, platform=excluded.platform,
                    variable=excluded.variable, control_value=excluded.control_value,
                    challenger_value=excluded.challenger_value,
                    controlled_fields_json=excluded.controlled_fields_json,
                    rule_json=excluded.rule_json, status=excluded.status,
                    result_json=excluded.result_json, updated_at=CURRENT_TIMESTAMP
            """, (
                exp.experiment_id, exp.hypothesis, exp.platform, exp.variable,
                exp.control_value, exp.challenger_value, fields_json, rule_json,
                exp.status, result_json,
            ))
            for trial in exp.trials:
                conn.execute("""
                    INSERT INTO trials (experiment_id, variant, repetition, metrics_json, context_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(experiment_id, variant, repetition) DO UPDATE SET
                        metrics_json=excluded.metrics_json, context_json=excluded.context_json
                """, (
                    exp.experiment_id, trial.variant, trial.repetition,
                    json.dumps(trial.metrics, sort_keys=True),
                    json.dumps(trial.context, sort_keys=True),
                ))

    def load_experiment(self, experiment_id: str) -> tuple[ControlledExperiment, dict[str, Any] | None] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
            if row is None:
                return None
            rule = DecisionRule(**json.loads(row["rule_json"]))
            exp = ControlledExperiment(
                experiment_id=row["experiment_id"], hypothesis=row["hypothesis"],
                platform=row["platform"], variable=row["variable"],
                control_value=row["control_value"], challenger_value=row["challenger_value"],
                controlled_fields=tuple(json.loads(row["controlled_fields_json"])),
                rule=rule, status=row["status"],
            )
            trials = conn.execute(
                "SELECT * FROM trials WHERE experiment_id=? ORDER BY repetition, id", (experiment_id,)
            ).fetchall()
            exp.trials = [Trial(t["variant"], t["repetition"], json.loads(t["metrics_json"]), json.loads(t["context_json"])) for t in trials]
            result = json.loads(row["result_json"]) if row["result_json"] else None
            return exp, result

    def list_experiments(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT e.*, COUNT(t.id) AS trial_count
                FROM experiments e LEFT JOIN trials t ON t.experiment_id=e.experiment_id
                GROUP BY e.experiment_id ORDER BY e.updated_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [{
            "experiment_id": r["experiment_id"], "hypothesis": r["hypothesis"],
            "platform": r["platform"], "variable": r["variable"], "status": r["status"],
            "trial_count": r["trial_count"],
            "result": json.loads(r["result_json"]) if r["result_json"] else None,
            "updated_at": r["updated_at"],
        } for r in rows]

    def save_strategy_memory(self, memory: StrategyMemory) -> None:
        payload = json.dumps(asdict(memory), sort_keys=True)
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO strategy_state (id, memory_json) VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET memory_json=excluded.memory_json, updated_at=CURRENT_TIMESTAMP
            """, (payload,))

    def load_strategy_memory(self) -> StrategyMemory:
        with self.connect() as conn:
            row = conn.execute("SELECT memory_json FROM strategy_state WHERE id=1").fetchone()
        return StrategyMemory(**json.loads(row["memory_json"])) if row else StrategyMemory()

    def stats(self) -> dict[str, int]:
        with self.connect() as conn:
            experiments = conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
            trials = conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM experiments WHERE status='completed'").fetchone()[0]
        return {"experiments": experiments, "trials": trials, "completed": completed}
