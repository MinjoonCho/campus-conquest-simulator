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

    def test_series_jsonl_streams_progress_and_final_result(self):
        fast = ROOT / "tests" / "fixtures" / "bots" / "fast_bot.py"
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            for bot_id in ("a", "b"):
                added = self.run_cli(
                    workspace,
                    "bots", "add",
                    "--id", bot_id,
                    "--name", bot_id.upper(),
                    "--command", f"{sys.executable} {fast}",
                    "--cwd", str(ROOT),
                    "--json",
                )
                self.assertEqual(added.returncode, 0, added.stderr)
            result = self.run_cli(
                workspace,
                "series",
                "--bot-a", "a",
                "--bot-b", "b",
                "--seeds", "0",
                "--max-turns", "1",
                "--first-turn-ms", "500",
                "--turn-ms", "200",
                "--safety-timeout-ms", "1000",
                "--jsonl",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(rows[-1]["event"], "result")
        self.assertEqual(rows[-1]["result"]["completed"], 1)
        self.assertTrue(any(row.get("event") == "progress" for row in rows[:-1]))


if __name__ == "__main__":
    unittest.main()
