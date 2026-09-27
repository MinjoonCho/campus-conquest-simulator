import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class CliTests(unittest.TestCase):
    def run_cli(self, workspace: Path, *args: str):
        return subprocess.run(
            [sys.executable, "-m", "arena", "--workspace", str(workspace), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_doctor_json_reports_official_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(Path(tmp), "doctor", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["official_tools"])
        self.assertEqual(payload["status"], "ok")

    def test_bot_add_and_list_are_machine_readable(self):
        fast = ROOT / "tests" / "fixtures" / "bots" / "fast_bot.py"
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            added = self.run_cli(
                workspace,
                "bots",
                "add",
                "--id", "fast",
                "--name", "Fast",
                "--command", f"{sys.executable} {fast}",
                "--cwd", str(ROOT),
                "--language", "python",
                "--json",
            )
            listed = self.run_cli(workspace, "bots", "list", "--json")

        self.assertEqual(added.returncode, 0, added.stderr)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout)["bots"][0]["id"], "fast")

    def test_preflight_error_is_json_and_starts_no_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                Path(tmp), "match", "--bot-y", "missing", "--bot-k", "also-missing", "--seed", "0", "--json"
            )

        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["error"]["code"], "bot_not_found")


if __name__ == "__main__":
    unittest.main()
