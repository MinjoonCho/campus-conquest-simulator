import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class PackagingTests(unittest.TestCase):
    def test_shipped_default_config_is_official_comparable(self):
        from arena.config import load_run_config

        config = load_run_config(ROOT / "config" / "arena.default.json")
        bots = json.loads((ROOT / "config" / "bots.example.json").read_text(encoding="utf-8"))

        self.assertTrue(config.official_comparable)
        self.assertEqual(config.plan.timing.first_turn_ms, 3000)
        self.assertGreaterEqual(len(bots["bots"]), 2)


if __name__ == "__main__":
    unittest.main()
