import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FAST = ROOT / "tests" / "fixtures" / "bots" / "fast_bot.py"


class WebApiTests(unittest.TestCase):
    def setUp(self):
        from arena.web import create_server

        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.server = create_server(
            "127.0.0.1", 0, self.workspace, ROOT / "vendor" / "official"
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())

    def test_health_bots_and_runs_endpoints(self):
        status, health = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")

        status, created = self.request(
            "POST",
            "/api/bots",
            {
                "id": "fast",
                "name": "Fast Bot",
                "command": f"{sys.executable} {FAST}",
                "working_dir": str(ROOT),
                "language": "python",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(created["bot"]["id"], "fast")
        _, listing = self.request("GET", "/api/bots")
        self.assertEqual(listing["bots"][0]["id"], "fast")

    def test_run_creation_and_replay_are_available(self):
        for bot_id in ("a", "b"):
            self.request(
                "POST",
                "/api/bots",
                {
                    "id": bot_id,
                    "name": bot_id.upper(),
                    "command": f"{sys.executable} {FAST}",
                    "working_dir": str(ROOT),
                    "language": "python",
                },
            )
        status, created = self.request(
            "POST",
            "/api/runs",
            {
                "bot_a": "a",
                "bot_b": "b",
                "seeds": [11],
                "swap_sides": False,
                "max_turns": 1,
                "timing": {"mode": "strict", "first_turn_ms": 500, "turn_ms": 200, "safety_timeout_ms": 1000},
            },
        )
        self.assertEqual(status, 202)
        run_id = created["run_id"]
        for _ in range(50):
            _, detail = self.request("GET", f"/api/runs/{run_id}")
            if detail["run"]["status"] in {"completed", "failed"}:
                break
            time.sleep(0.02)
        self.assertEqual(detail["run"]["status"], "completed")
        self.assertEqual(len(detail["matches"]), 1)

        status, replay = self.request("GET", f"/api/runs/{run_id}/replays/0")
        self.assertEqual(status, 200)
        self.assertEqual(replay["seed"], 11)
        self.assertEqual(len(replay["turns"]), 1)

    def test_artifact_endpoint_does_not_accept_paths(self):
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.request("GET", "/api/runs/../../../../etc/passwd/replays/0")
        self.assertIn(raised.exception.code, (400, 404))
        raised.exception.close()


if __name__ == "__main__":
    unittest.main()
