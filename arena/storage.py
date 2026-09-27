"""SQLite metadata and filesystem artifact storage."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Any


class ArenaStorage:
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        for name in ("replays", "telemetry", "logs", "exports"):
            (self.workspace / name).mkdir(exist_ok=True)
        self.connection = sqlite3.connect(self.workspace / "arena.sqlite3")
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS bots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                working_dir TEXT NOT NULL,
                language TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                bot_a TEXT NOT NULL,
                bot_b TEXT NOT NULL,
                official_comparable INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS matches (
                run_id TEXT NOT NULL REFERENCES runs(id),
                job_index INTEGER NOT NULL,
                seed INTEGER NOT NULL,
                bot_y TEXT NOT NULL,
                bot_k TEXT NOT NULL,
                result_json TEXT NOT NULL,
                replay_path TEXT,
                telemetry_path TEXT,
                PRIMARY KEY (run_id, job_index)
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def upsert_bot(self, record: dict[str, str]) -> dict[str, str]:
        self.connection.execute(
            """
            INSERT INTO bots (id, name, command, working_dir, language)
            VALUES (:id, :name, :command, :working_dir, :language)
            ON CONFLICT(id) DO UPDATE SET
              name=excluded.name, command=excluded.command,
              working_dir=excluded.working_dir, language=excluded.language,
              updated_at=CURRENT_TIMESTAMP
            """,
            record,
        )
        self.connection.commit()
        return self.get_bot(record["id"])

    def get_bot(self, bot_id: str) -> dict[str, str] | None:
        row = self.connection.execute(
            "SELECT id, name, command, working_dir, language FROM bots WHERE id=?", (bot_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_bots(self) -> list[dict[str, str]]:
        rows = self.connection.execute(
            "SELECT id, name, command, working_dir, language FROM bots ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    def remove_bot(self, bot_id: str) -> bool:
        cursor = self.connection.execute("DELETE FROM bots WHERE id=?", (bot_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def create_run(
        self,
        config: dict[str, Any],
        bot_a: str,
        bot_b: str,
        official_comparable: bool,
    ) -> str:
        run_id = uuid.uuid4().hex
        self.connection.execute(
            "INSERT INTO runs (id,status,config_json,bot_a,bot_b,official_comparable) VALUES (?,?,?,?,?,?)",
            (run_id, "running", json.dumps(config, ensure_ascii=False), bot_a, bot_b, int(official_comparable)),
        )
        self.connection.commit()
        return run_id

    def update_run_status(self, run_id: str, status: str) -> None:
        self.connection.execute(
            "UPDATE runs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, run_id)
        )
        self.connection.commit()

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["config"] = json.loads(result.pop("config_json"))
        result["official_comparable"] = bool(result["official_comparable"])
        return result

    def list_runs(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT id FROM runs ORDER BY created_at DESC, id DESC").fetchall()
        return [self.get_run(row["id"]) for row in rows]

    def add_match(
        self,
        run_id: str,
        job_index: int,
        seed: int,
        bot_y: str,
        bot_k: str,
        result: dict[str, Any],
        replay_path: Path | None,
        telemetry_path: Path | None,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO matches
              (run_id,job_index,seed,bot_y,bot_k,result_json,replay_path,telemetry_path)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                run_id,
                job_index,
                seed,
                bot_y,
                bot_k,
                json.dumps(result, ensure_ascii=False),
                str(replay_path) if replay_path else None,
                str(telemetry_path) if telemetry_path else None,
            ),
        )
        self.connection.commit()

    def list_matches(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM matches WHERE run_id=? ORDER BY job_index", (run_id,)
        ).fetchall()
        matches = []
        for row in rows:
            item = dict(row)
            item["result"] = json.loads(item.pop("result_json"))
            matches.append(item)
        return matches

    def completed_job_indices(self, run_id: str) -> set[int]:
        rows = self.connection.execute(
            "SELECT job_index FROM matches WHERE run_id=?", (run_id,)
        ).fetchall()
        return {row["job_index"] for row in rows}

    def write_json(self, path: Path, payload: Any) -> Path:
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
        return path

