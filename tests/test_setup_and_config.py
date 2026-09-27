import json
import tempfile
import unittest
import zipfile
from pathlib import Path


class OfficialSetupTests(unittest.TestCase):
    def test_extract_official_rejects_parent_traversal(self):
        from scripts.setup_official import extract_official

        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../escaped.txt", "bad")

            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                extract_official(archive, Path(tmp) / "vendor")
            self.assertFalse((Path(tmp) / "escaped.txt").exists())

    def test_extract_official_requires_expected_layout(self):
        from scripts.setup_official import extract_official

        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "incomplete.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("README.md", "not the official kit")

            with self.assertRaisesRegex(ValueError, "official tool layout"):
                extract_official(archive, Path(tmp) / "vendor")


class ConfigTests(unittest.TestCase):
    def _write(self, root: Path, payload: dict) -> Path:
        path = root / "run.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_defaults_match_official_limits(self):
        from arena.config import load_run_config

        with tempfile.TemporaryDirectory() as tmp:
            config = load_run_config(self._write(Path(tmp), {}))

        self.assertEqual(config.plan.timing.mode, "strict")
        self.assertEqual(config.plan.timing.first_turn_ms, 3000)
        self.assertEqual(config.plan.timing.turn_ms, 300)
        self.assertEqual(config.plan.max_turns, 160)
        self.assertTrue(config.official_comparable)

    def test_official_ruleset_rejects_balance_overrides(self):
        from arena.config import load_run_config

        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                Path(tmp),
                {"ruleset": {"mode": "official", "balance_overrides": {"total_turns": 20}}},
            )
            with self.assertRaisesRegex(ValueError, "official ruleset"):
                load_run_config(path)

    def test_custom_ruleset_is_labeled_experimental(self):
        from arena.config import load_run_config

        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                Path(tmp),
                {"ruleset": {"mode": "custom", "balance_overrides": {"total_turns": 20}}},
            )
            config = load_run_config(path)

        self.assertFalse(config.official_comparable)
        self.assertEqual(config.plan.ruleset_mode, "custom")
        self.assertEqual(config.plan.balance_overrides, {"total_turns": 20})

    def test_safety_timeout_must_cover_strict_budget(self):
        from arena.config import load_run_config

        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                Path(tmp),
                {"timing": {"mode": "strict", "first_turn_ms": 3000, "turn_ms": 300, "safety_timeout_ms": 1000}},
            )
            with self.assertRaisesRegex(ValueError, "safety timeout"):
                load_run_config(path)


if __name__ == "__main__":
    unittest.main()
