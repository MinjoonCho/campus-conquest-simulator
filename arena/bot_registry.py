"""Persistent local bot registrations."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

from .storage import ArenaStorage


class BotNotFound(KeyError):
    pass


class BotRegistry:
    def __init__(self, storage: ArenaStorage):
        self.storage = storage

    def add(
        self,
        bot_id: str,
        name: str,
        command: str,
        working_dir: str,
        language: str = "unknown",
    ) -> dict[str, str]:
        if not bot_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in bot_id):
            raise ValueError("bot id may contain only letters, numbers, hyphen, and underscore")
        if not name.strip():
            raise ValueError("bot name must not be empty")
        directory = Path(working_dir).expanduser().resolve()
        if not directory.is_dir():
            raise ValueError(f"working directory does not exist: {directory}")
        tokens = shlex.split(command)
        if not tokens:
            raise ValueError("bot command must not be empty")
        executable = Path(tokens[0]).expanduser()
        if not executable.is_file() and shutil.which(tokens[0]) is None:
            raise ValueError(f"bot executable not found: {tokens[0]}")
        return self.storage.upsert_bot(
            {
                "id": bot_id,
                "name": name.strip(),
                "command": command,
                "working_dir": str(directory),
                "language": language,
            }
        )

    def get(self, bot_id: str) -> dict[str, str]:
        record = self.storage.get_bot(bot_id)
        if record is None:
            raise BotNotFound(bot_id)
        return record

    def list(self) -> list[dict[str, str]]:
        return self.storage.list_bots()

    def remove(self, bot_id: str) -> bool:
        return self.storage.remove_bot(bot_id)

    def validate(self, bot_id: str) -> dict[str, object]:
        record = self.get(bot_id)
        directory_ok = Path(record["working_dir"]).is_dir()
        tokens = shlex.split(record["command"])
        executable_ok = bool(tokens) and (Path(tokens[0]).is_file() or shutil.which(tokens[0]) is not None)
        return {"id": bot_id, "valid": directory_ok and executable_ok}


def launch_command(record: dict[str, str]) -> str:
    """Return a shell command that starts the bot in its registered directory."""
    directory = record["working_dir"]
    if os.name == "nt":
        escaped = directory.replace('"', '""')
        return f'cd /d "{escaped}" && {record["command"]}'
    return f"cd -- {shlex.quote(directory)} && exec {record['command']}"
