"""Bot driver adapters for strict, observe, and off timing policies."""

from __future__ import annotations

import time
from typing import Any

from .models import TimingConfig


class TimedBot:
    """Wrap an official SubprocessBot while changing only deadline policy."""

    def __init__(self, delegate: Any, timing: TimingConfig, team: str):
        self.delegate = delegate
        self.timing = timing
        self.team = team
        self.turn = 0
        self.telemetry: list[dict[str, object]] = []
        self._budget_ms = timing.first_turn_ms

    @property
    def name(self) -> str:
        return self.delegate.name

    @property
    def dead(self) -> bool:
        return self.delegate.dead

    @dead.setter
    def dead(self, value: bool) -> None:
        self.delegate.dead = value

    def send_init(self, text: str) -> None:
        self.delegate.send_init(text)

    def send_turn(self, text: str, timeout_s: float) -> None:
        self.turn += 1
        self._budget_ms = round(timeout_s * 1000)
        effective = timeout_s if self.timing.mode == "strict" else self.timing.safety_timeout_ms / 1000.0
        self.delegate.send_turn(text, effective)

    def collect_turn(self):
        lines, status = self.delegate.collect_turn()
        elapsed_ms = max(0.0, (time.monotonic() - self.delegate._start) * 1000.0)
        violation = self.timing.mode == "observe" and elapsed_ms > self._budget_ms
        if self.timing.mode == "strict" and status == "timeout":
            violation = True
        self.telemetry.append(
            {
                "team": self.team,
                "turn": self.turn,
                "first_turn": self.turn == 1,
                "mode": self.timing.mode,
                "budget_ms": None if self.timing.mode == "off" else self._budget_ms,
                "elapsed_ms": round(elapsed_ms, 3),
                "competition_violation": violation,
                "status": status,
            }
        )
        return lines, status

    def close(self) -> None:
        self.delegate.close()

