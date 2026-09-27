"""Validated immutable configuration models used across Arena."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TimingConfig:
    mode: str = "strict"
    first_turn_ms: int = 3000
    turn_ms: int = 300
    safety_timeout_ms: int = 60000

    def __post_init__(self) -> None:
        if self.mode not in {"strict", "observe", "off"}:
            raise ValueError("timing mode must be strict, observe, or off")
        for name in ("first_turn_ms", "turn_ms", "safety_timeout_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.mode == "strict" and self.safety_timeout_ms < max(
            self.first_turn_ms, self.turn_ms
        ):
            raise ValueError("safety timeout must cover every strict competition budget")


@dataclass(frozen=True)
class GamePlan:
    timing: TimingConfig = field(default_factory=TimingConfig)
    ruleset_mode: str = "official"
    balance_overrides: dict[str, Any] = field(default_factory=dict)
    max_turns: int = 160
    seeds: tuple[int, ...] = (0,)
    swap_sides: bool = False
    repetitions: int = 1
    jobs: int = 1
    on_bot_error: str = "forfeit"
    replay_policy: str = "all"

    def __post_init__(self) -> None:
        if self.ruleset_mode not in {"official", "custom"}:
            raise ValueError("ruleset mode must be official or custom")
        if self.ruleset_mode == "official" and self.balance_overrides:
            raise ValueError("official ruleset does not allow balance overrides")
        for name in ("max_turns", "repetitions", "jobs"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not self.seeds or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in self.seeds):
            raise ValueError("seeds must contain at least one integer")
        if self.on_bot_error not in {"forfeit", "continue"}:
            raise ValueError("on_bot_error must be forfeit or continue")
        if self.replay_policy not in {"all", "failures", "none"}:
            raise ValueError("replay_policy must be all, failures, or none")


@dataclass(frozen=True)
class ArenaConfig:
    plan: GamePlan
    workspace: Path
    official_root: Path

    @property
    def official_comparable(self) -> bool:
        return self.plan.ruleset_mode == "official" and self.plan.timing.mode == "strict"

