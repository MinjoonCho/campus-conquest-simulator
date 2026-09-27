"""Load and validate versioned Arena JSON configurations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ArenaConfig, GamePlan, TimingConfig


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_official_root(path: str | Path | None = None) -> Path:
    root = Path(path) if path is not None else PROJECT_ROOT / "vendor" / "official"
    root = root.expanduser().resolve()
    required = ("engine/pipeline.py", "runner/match.py", "config/balance.json")
    if not all((root / item).is_file() for item in required):
        raise ValueError(f"invalid official tool root: {root}")
    return root


def _object(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def load_run_config(path: str | Path) -> ArenaConfig:
    source = Path(path).expanduser().resolve()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load run configuration: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("run configuration must be a JSON object")

    timing_data = _object(data.get("timing"), "timing")
    timing = TimingConfig(
        mode=timing_data.get("mode", "strict"),
        first_turn_ms=timing_data.get("first_turn_ms", 3000),
        turn_ms=timing_data.get("turn_ms", 300),
        safety_timeout_ms=timing_data.get("safety_timeout_ms", 60000),
    )
    ruleset = _object(data.get("ruleset"), "ruleset")
    games = _object(data.get("games"), "games")
    execution = _object(data.get("execution"), "execution")
    artifacts = _object(data.get("artifacts"), "artifacts")
    plan = GamePlan(
        timing=timing,
        ruleset_mode=ruleset.get("mode", "official"),
        balance_overrides=_object(ruleset.get("balance_overrides"), "balance_overrides"),
        max_turns=games.get("max_turns", 160),
        seeds=tuple(games.get("seeds", [0])),
        swap_sides=games.get("swap_sides", False),
        repetitions=games.get("repetitions", 1),
        jobs=execution.get("jobs", 1),
        on_bot_error=execution.get("on_bot_error", "forfeit"),
        replay_policy=artifacts.get("replay_policy", "all"),
    )
    workspace = Path(data.get("workspace", PROJECT_ROOT / "workspace")).expanduser().resolve()
    official_root = Path(data.get("official_root", PROJECT_ROOT / "vendor" / "official")).expanduser().resolve()
    return ArenaConfig(plan=plan, workspace=workspace, official_root=official_root)

