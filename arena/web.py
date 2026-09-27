"""Loopback-only HTTP API and static dashboard for Arena."""

from __future__ import annotations

import json
import mimetypes
import re
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .bot_registry import BotNotFound, BotRegistry
from .models import ArenaConfig, GamePlan, TimingConfig
from .series import run_series
from .storage import ArenaStorage


STATIC_ROOT = Path(__file__).resolve().parent / "static"
RUN_ID = re.compile(r"^[a-f0-9]{32}$")


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0 or length > 1024 * 1024:
        raise ValueError("request body must be non-empty JSON below 1 MiB")
    try:
        payload = json.loads(handler.rfile.read(length))
    except json.JSONDecodeError as exc:
        raise ValueError("request body is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    return payload


def _config_from_payload(payload: dict, workspace: Path, official_root: Path) -> ArenaConfig:
    timing_data = payload.get("timing", {})
    if not isinstance(timing_data, dict):
        raise ValueError("timing must be an object")
    seeds = payload.get("seeds", [0])
    if not isinstance(seeds, list):
        raise ValueError("seeds must be an array")
    timing = TimingConfig(
        mode=timing_data.get("mode", "strict"),
        first_turn_ms=timing_data.get("first_turn_ms", 3000),
        turn_ms=timing_data.get("turn_ms", 300),
        safety_timeout_ms=timing_data.get("safety_timeout_ms", 60000),
    )
    return ArenaConfig(
        plan=GamePlan(
            timing=timing,
            max_turns=payload.get("max_turns", 160),
            seeds=tuple(seeds),
            swap_sides=payload.get("swap_sides", True),
            repetitions=payload.get("repetitions", 1),
            jobs=payload.get("jobs", 1),
            replay_policy=payload.get("replay_policy", "all"),
        ),
        workspace=workspace,
        official_root=official_root,
    )


def _run_background(
    workspace: Path,
    official_root: Path,
    config: ArenaConfig,
    bot_a: str,
    bot_b: str,
    run_id: str,
) -> None:
    storage = ArenaStorage(workspace)
    try:
        run_series(config, BotRegistry(storage), storage, bot_a, bot_b, run_id=run_id)
    finally:
        storage.close()


def _handler_factory(workspace: Path, official_root: Path):
    class ArenaHandler(BaseHTTPRequestHandler):
        server_version = "CampusConquestArena/0.1"

        def log_message(self, format: str, *args) -> None:
            return

        def _json(self, status: int, payload: dict | list) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: int, code: str, message: str) -> None:
            self._json(status, {"error": {"code": code, "message": message}})

        def _static(self, name: str) -> None:
            if name not in {"index.html", "styles.css", "app.js"}:
                self._error(404, "not_found", "resource not found")
                return
            path = STATIC_ROOT / name
            if not path.is_file():
                self._error(404, "not_found", "resource not found")
                return
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._static("index.html")
                return
            if path in {"/styles.css", "/app.js"}:
                self._static(path[1:])
                return
            storage = ArenaStorage(workspace)
            try:
                if path == "/api/health":
                    self._json(200, {"status": "ok", "official_tools": official_root.is_dir()})
                elif path == "/api/bots":
                    self._json(200, {"bots": BotRegistry(storage).list()})
                elif path == "/api/runs":
                    self._json(200, {"runs": storage.list_runs()})
                else:
                    replay_match = re.fullmatch(r"/api/runs/([a-f0-9]{32})/replays/(\d+)", path)
                    run_match = re.fullmatch(r"/api/runs/([a-f0-9]{32})", path)
                    if replay_match:
                        run_id, index_text = replay_match.groups()
                        records = {row["job_index"]: row for row in storage.list_matches(run_id)}
                        record = records.get(int(index_text))
                        if not record or not record.get("replay_path"):
                            self._error(404, "replay_not_found", "replay not found")
                            return
                        replay_path = Path(record["replay_path"]).resolve()
                        allowed = (workspace / "replays").resolve()
                        if allowed not in replay_path.parents:
                            self._error(400, "unsafe_artifact", "artifact path is outside replay storage")
                            return
                        self._json(200, json.loads(replay_path.read_text(encoding="utf-8")))
                    elif run_match:
                        run_id = run_match.group(1)
                        run = storage.get_run(run_id)
                        if run is None:
                            self._error(404, "run_not_found", "run not found")
                        else:
                            self._json(200, {"run": run, "matches": storage.list_matches(run_id)})
                    else:
                        self._error(404, "not_found", "resource not found")
            finally:
                storage.close()

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            storage = ArenaStorage(workspace)
            try:
                payload = _read_json(self)
                registry = BotRegistry(storage)
                if path == "/api/bots":
                    bot = registry.add(
                        payload.get("id", ""),
                        payload.get("name", ""),
                        payload.get("command", ""),
                        payload.get("working_dir", ""),
                        payload.get("language", "unknown"),
                    )
                    self._json(201, {"bot": bot})
                elif path == "/api/runs":
                    bot_a = payload.get("bot_a", "")
                    bot_b = payload.get("bot_b", "")
                    registry.get(bot_a)
                    registry.get(bot_b)
                    config = _config_from_payload(payload, workspace, official_root)
                    run_id = storage.create_run(payload, bot_a, bot_b, config.official_comparable)
                    worker = threading.Thread(
                        target=_run_background,
                        args=(workspace, official_root, config, bot_a, bot_b, run_id),
                        daemon=True,
                    )
                    worker.start()
                    self._json(202, {"run_id": run_id, "status": "running"})
                else:
                    self._error(404, "not_found", "resource not found")
            except BotNotFound as exc:
                self._error(404, "bot_not_found", f"bot not found: {exc.args[0]}")
            except (ValueError, OSError) as exc:
                self._error(400, "invalid_request", str(exc))
            finally:
                storage.close()

    return ArenaHandler


def create_server(host: str, port: int, workspace: Path, official_root: Path) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Arena web server must bind to a loopback address")
    workspace = Path(workspace).expanduser().resolve()
    official_root = Path(official_root).expanduser().resolve()
    return ThreadingHTTPServer((host, port), _handler_factory(workspace, official_root))


def serve(host: str, port: int, workspace: Path, official_root: Path) -> None:
    server = create_server(host, port, workspace, official_root)
    print(f"Arena dashboard: http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

