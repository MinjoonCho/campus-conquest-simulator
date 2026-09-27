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

    def test_registered_working_directory_is_used_for_relative_command(self):
        from arena.bot_registry import BotRegistry
        from arena.series import run_series
        from arena.storage import ArenaStorage

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bot_dir = Path(tmp) / "bot"
            bot_dir.mkdir()
            (bot_dir / "bot.py").write_text(FAST.read_text(encoding="utf-8"), encoding="utf-8")
            store = ArenaStorage(workspace)
            registry = BotRegistry(store)
            registry.add("a", "A", f"{shlex.quote(sys.executable)} bot.py", str(bot_dir), "python")
            registry.add("b", "B", f"{shlex.quote(sys.executable)} bot.py", str(bot_dir), "python")
            cfg = ArenaConfig(
                plan=GamePlan(
                    timing=TimingConfig(first_turn_ms=500, turn_ms=200, safety_timeout_ms=1000),
                    max_turns=1,
                ),
                workspace=workspace,
                official_root=ROOT / "vendor" / "official",
            )
            result = run_series(cfg, registry, store, "a", "b")
            match = store.list_matches(result["run_id"])[0]
            store.close()

        self.assertEqual(result["completed"], 1)
        self.assertNotEqual(match["result"]["reason"], "forfeit")

    def test_parallel_series_does_not_share_sqlite_connection_with_workers(self):
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
                    timing=TimingConfig(first_turn_ms=500, turn_ms=200, safety_timeout_ms=1000),
                    max_turns=1,
                    seeds=(1, 2),
                    jobs=2,
                ),
                workspace=workspace,
                official_root=ROOT / "vendor" / "official",
            )
            result = run_series(cfg, registry, store, "a", "b")
            store.close()

        self.assertEqual(result["completed"], 2)

    def test_round_robin_pairs_each_distinct_bot_once(self):
        from arena.tournament import round_robin_pairs

        self.assertEqual(
            round_robin_pairs(("a", "b", "c")),
            [("a", "b"), ("a", "c"), ("b", "c")],
        )

    def test_round_robin_tournament_aggregates_all_pairs(self):
        from arena.bot_registry import BotRegistry
        from arena.storage import ArenaStorage
        from arena.tournament import run_tournament

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            store = ArenaStorage(workspace)
            registry = BotRegistry(store)
            command = shlex.join([sys.executable, str(FAST)])
            for bot_id in ("a", "b", "c"):
                registry.add(bot_id, bot_id.upper(), command, str(ROOT), "python")
            cfg = ArenaConfig(
                plan=GamePlan(
                    timing=TimingConfig(first_turn_ms=500, turn_ms=200, safety_timeout_ms=1000),
                    max_turns=1,
                ),
                workspace=workspace,
                official_root=ROOT / "vendor" / "official",
            )
            result = run_tournament(cfg, registry, store, ("a", "b", "c"))
            store.close()

        self.assertEqual(result["pairs"], 3)
        self.assertEqual(len(result["series"]), 3)
        self.assertEqual(sum(row["games"] for row in result["standings"]), 6)


if __name__ == "__main__":
    unittest.main()
