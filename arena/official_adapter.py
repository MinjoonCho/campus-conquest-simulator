"""Arena adapter that delegates game semantics to the official runner."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ArenaConfig
from .timing import TimedBot


@dataclass(frozen=True)
class MatchOutcome:
    replay: dict[str, Any]
    result: dict[str, Any]
    telemetry: tuple[dict[str, object], ...]


def _load_official(root: Path):
    root = root.resolve()
    required = (root / "engine" / "pipeline.py", root / "runner" / "match.py")
    if not all(path.is_file() for path in required):
        raise ValueError(f"invalid official tool root: {root}")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from runner import SubprocessBot, run_match

    return SubprocessBot, run_match


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _game_config(config: ArenaConfig) -> dict[str, Any]:
    path = config.official_root / "config" / "balance.json"
    base = json.loads(path.read_text(encoding="utf-8"))
    if config.plan.ruleset_mode == "custom":
        base = _deep_merge(base, config.plan.balance_overrides)
    base["first_turn_timeout_ms"] = config.plan.timing.first_turn_ms
    return base


def run_official_match(
    config: ArenaConfig,
    bot_y: str,
    bot_k: str,
    seed: int,
    *,
    name_y: str | None = None,
    name_k: str | None = None,
) -> MatchOutcome:
    SubprocessBot, run_match = _load_official(config.official_root)
    raw_y = SubprocessBot(bot_y, name=bot_y)
    raw_k = SubprocessBot(bot_k, name=bot_k)
    timed_y = TimedBot(raw_y, config.plan.timing, "Y")
    timed_k = TimedBot(raw_k, config.plan.timing, "K")
    replay, result = run_match(
        seed,
        _game_config(config),
        timed_y,
        timed_k,
        turn_timeout_ms=config.plan.timing.turn_ms,
        max_turns=config.plan.max_turns,
        names={"Y": name_y, "K": name_k},
        on_bot_error=config.plan.on_bot_error,
    )
    telemetry = tuple(timed_y.telemetry + timed_k.telemetry)
    return MatchOutcome(replay=replay, result=result, telemetry=telemetry)

