import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class DocumentedCommandTests(unittest.TestCase):
    def test_required_operating_guides_exist(self):
        required = (
            ROOT / "README.md",
            ROOT / "docs" / "USER_GUIDE.md",
            ROOT / "docs" / "AGENT_GUIDE.md",
            ROOT / "docs" / "CONFIG_REFERENCE.md",
            ROOT / "docs" / "ARCHITECTURE.md",
        )
        self.assertEqual([str(path) for path in required if not path.is_file()], [])

    def test_quickstart_doctor_command_is_machine_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "-m", "arena", "--workspace", tmp, "doctor", "--json"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "ok")

    def test_documented_cli_surfaces_have_help(self):
        for command in ("bots", "match", "series", "tournament", "runs", "serve"):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "-m", "arena", command, "--help"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)

if __name__ == "__main__":
    unittest.main()
