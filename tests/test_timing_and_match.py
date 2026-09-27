import copy
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from arena.models import ArenaConfig, GamePlan, TimingConfig


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "bots"


def command(name: str, *args: str) -> str:
    return shlex.join([sys.executable, str(FIXTURES / name), *args])


def config(tmp: str, mode: str, *, first: int = 500, turn: int = 200, safety: int = 1000) -> ArenaConfig:
    return ArenaConfig(
        plan=GamePlan(
            timing=TimingConfig(mode=mode, first_turn_ms=first, turn_ms=turn, safety_timeout_ms=safety),
            max_turns=1,
        ),
        workspace=Path(tmp),
        official_root=ROOT / "vendor" / "official",
    )


class TimingMatchTests(unittest.TestCase):
    def test_strict_match_uses_official_replay_shape(self):
        from arena.official_adapter import run_official_match

        with tempfile.TemporaryDirectory() as tmp:
            outcome = run_official_match(
                config(tmp, "strict"), command("fast_bot.py"), command("fast_bot.py"), 7
            )

        self.assertEqual(outcome.result, outcome.replay["result"])
        self.assertEqual(outcome.result["turns"], 1)
        self.assertEqual(len(outcome.replay["turns"]), 1)
        self.assertEqual({row["team"] for row in outcome.telemetry}, {"Y", "K"})

    def test_observe_records_violation_and_finishes_match(self):
        from arena.official_adapter import run_official_match

        with tempfile.TemporaryDirectory() as tmp:
            outcome = run_official_match(
                config(tmp, "observe", first=30, turn=30, safety=500),
                command("sleep_bot.py", "0.08"),
                command("fast_bot.py"),
                3,
            )

        self.assertNotEqual(outcome.result["reason"], "forfeit")
        y_turn = next(row for row in outcome.telemetry if row["team"] == "Y")
        self.assertTrue(y_turn["competition_violation"])
        self.assertGreaterEqual(y_turn["elapsed_ms"], 60)

    def test_off_mode_measures_without_competition_violation(self):
        from arena.official_adapter import run_official_match

        with tempfile.TemporaryDirectory() as tmp:
            outcome = run_official_match(
                config(tmp, "off", first=20, turn=20, safety=500),
                command("sleep_bot.py", "0.05"),
                command("fast_bot.py"),
                3,
            )

        y_turn = next(row for row in outcome.telemetry if row["team"] == "Y")
        self.assertFalse(y_turn["competition_violation"])
        self.assertGreaterEqual(y_turn["elapsed_ms"], 35)

    def test_safety_timeout_stops_missing_end_bot(self):
        from arena.official_adapter import run_official_match

        with tempfile.TemporaryDirectory() as tmp:
            outcome = run_official_match(
                config(tmp, "observe", first=20, turn=20, safety=100),
                command("missing_end_bot.py"),
                command("fast_bot.py"),
                4,
            )

        self.assertEqual(outcome.result["reason"], "forfeit")
        self.assertEqual(outcome.result["forfeit"]["team"], "Y")
        self.assertEqual(outcome.result["forfeit"]["cause"], "timeout")

    def test_crash_is_forfeit(self):
        from arena.official_adapter import run_official_match

        with tempfile.TemporaryDirectory() as tmp:
            outcome = run_official_match(
                config(tmp, "observe"), command("crash_bot.py"), command("fast_bot.py"), 5
            )

        self.assertEqual(outcome.result["reason"], "forfeit")
        self.assertEqual(outcome.result["forfeit"]["team"], "Y")
        self.assertEqual(outcome.result["forfeit"]["cause"], "crash")

    def test_simultaneous_strict_timeout_is_draw(self):
        from arena.official_adapter import run_official_match

        with tempfile.TemporaryDirectory() as tmp:
            outcome = run_official_match(
                config(tmp, "strict", first=40, turn=40, safety=500),
                command("sleep_bot.py", "0.12"),
                command("sleep_bot.py", "0.12"),
                6,
            )

        self.assertEqual(outcome.result["winner"], "DRAW")
        self.assertEqual(outcome.result["forfeit"]["team"], "both")


if __name__ == "__main__":
    unittest.main()
