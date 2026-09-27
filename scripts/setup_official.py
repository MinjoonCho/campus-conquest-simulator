"""Safely extract the provided official development tools."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path


EXPECTED = (
    Path("engine/pipeline.py"),
    Path("runner/match.py"),
    Path("config/balance.json"),
)


def _safe_members(bundle: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = bundle.infolist()
    for member in members:
        path = Path(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive path: {member.filename}")
    return members


def extract_official(archive: Path, destination: Path) -> Path:
    archive = Path(archive).resolve()
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        stage = Path(tmp) / "official"
        stage.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(stage, members=_safe_members(bundle))
        if not all((stage / expected).is_file() for expected in EXPECTED):
            raise ValueError("archive does not contain the expected official tool layout")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(stage), str(destination))
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="yk-development-tools.zip")
    parser.add_argument("--destination", default="vendor/official")
    args = parser.parse_args(argv)
    root = extract_official(Path(args.archive), Path(args.destination))
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

