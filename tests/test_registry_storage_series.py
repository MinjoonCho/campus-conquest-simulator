import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from arena.models import ArenaConfig, GamePlan, TimingConfig


ROOT = Path(__file__).resolve().parent.parent
FAST = ROOT / "tests" / "fixtures" / "bots" / "fast_bot.py"


class RegistryStorageSeriesTests(unittest.TestCase):
    def test_registry_persists_bot_after_reopen(self):
        from arena.bot_registry import BotRegistry
        from arena.storage import ArenaStorage

        with tempfile.TemporaryDirectory() as tmp:
            store = ArenaStorage(Path(tmp))
            registry = BotRegistry(store)
            registry.add("fast", "Fast Bot", shlex.join([sys.executable, str(FAST)]), str(ROOT), "python")
            store.close()

            reopened = ArenaStorage(Path(tmp))
            bot = BotRegistry(reopened).get("fast")
            reopened.close()

        self.assertEqual(bot["name"], "Fast Bot")
        self.assertEqual(bot["language"], "python")

    def test_registry_rejects_missing_working_directory(self):
        from arena.bot_registry import BotRegistry
        from arena.storage import ArenaStorage

        with tempfile.TemporaryDirectory() as tmp:
            store = ArenaStorage(Path(tmp))
            with self.assertRaisesRegex(ValueError, "working directory"):
                BotRegistry(store).add("bad", "Bad", "python bad.py", str(Path(tmp) / "missing"), "python")
            store.close()

    def test_side_swapped_jobs_pair_same_seed(self):
        from arena.series import expand_jobs

        jobs = expand_jobs((4, 9), "alpha", "beta", swap_sides=True, repetitions=1)

        self.assertEqual(
            [(job.seed, job.bot_y, job.bot_k) for job in jobs],
            [(4, "alpha", "beta"), (4, "beta", "alpha"), (9, "alpha", "beta"), (9, "beta", "alpha")],
        )

    def test_aggregate_uses_bot_identity_not_team_letter(self):
        from arena.stats import aggregate_results

        records = [
            {"bot_y": "alpha", "bot_k": "beta", "result": {"winner": "Y", "score": {"Y": 8, "K": 3}}},
            {"bot_y": "beta", "bot_k": "alpha", "result": {"winner": "K", "score": {"Y": 2, "K": 7}}},
        ]
        stats = aggregate_results(records, ("alpha", "beta"))

        self.assertEqual(stats["bots"]["alpha"]["wins"], 2)
        self.assertEqual(stats["bots"]["beta"]["losses"], 2)
        self.assertEqual(stats["bots"]["alpha"]["score_for"], 15)

    def test_series_resume_skips_completed_jobs(self):
        from arena.bot_registry import BotRegistry
        from arena.series import run_series
        from arena.storage import ArenaStorage

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            store = ArenaStorage(workspace)
            registry = BotRegistry(store)
            command = shlex.join([sys.executable, str(FAST)])
            registry.add("a", "A", command, str(ROOT), "python")
            registry.add("b", "B", command, str(ROOT), "python")
            cfg = ArenaConfig(
                plan=GamePlan(
                    timing=TimingConfig(mode="strict", first_turn_ms=500, turn_ms=200, safety_timeout_ms=1000),
                    max_turns=1,
                    seeds=(1,),
                ),
                workspace=workspace,
                official_root=ROOT / "vendor" / "official",
            )
            first = run_series(cfg, registry, store, "a", "b")
            second = run_series(cfg, registry, store, "a", "b", run_id=first["run_id"])
            matches = store.list_matches(first["run_id"])
            store.close()

        self.assertEqual(len(matches), 1)
        self.assertEqual(second["skipped"], 1)


if __name__ == "__main__":
    unittest.main()

