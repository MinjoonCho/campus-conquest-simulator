"""Command-line and JSON interface for the offline arena."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bot_registry import BotNotFound, BotRegistry
from .config import PROJECT_ROOT, resolve_official_root
from .models import ArenaConfig, GamePlan, TimingConfig
from .series import run_series
from .storage import ArenaStorage


class CliError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _emit(payload: dict, machine: bool) -> None:
    if machine:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", dest="machine")


def _add_timing(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timing", choices=("strict", "observe", "off"), default="strict")
    parser.add_argument("--first-turn-ms", type=int, default=3000)
    parser.add_argument("--turn-ms", type=int, default=300)
    parser.add_argument("--safety-timeout-ms", type=int, default=60000)
    parser.add_argument("--max-turns", type=int, default=160)


def _parse_seeds(value: str) -> tuple[int, ...]:
    if ":" in value:
        parts = value.split(":")
        if len(parts) not in (2, 3):
            raise argparse.ArgumentTypeError("seed range must be START:STOP[:STEP]")
        start, stop = int(parts[0]), int(parts[1])
        step = int(parts[2]) if len(parts) == 3 else 1
        values = tuple(range(start, stop, step))
    else:
        values = tuple(int(item) for item in value.split(",") if item)
    if not values:
        raise argparse.ArgumentTypeError("at least one seed is required")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arena", description=__doc__)
    parser.add_argument("--workspace", default=str(PROJECT_ROOT / "workspace"))
    parser.add_argument("--official-root", default=str(PROJECT_ROOT / "vendor" / "official"))
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="validate local Arena prerequisites")
    _add_json(doctor)

    bots = sub.add_parser("bots", help="manage registered bots")
    bot_sub = bots.add_subparsers(dest="bot_command", required=True)
    add = bot_sub.add_parser("add")
    add.add_argument("--id", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--command", required=True, dest="bot_launch_command")
    add.add_argument("--cwd", required=True)
    add.add_argument("--language", default="unknown")
    _add_json(add)
    for name in ("list", "show", "validate", "remove"):
        item = bot_sub.add_parser(name)
        if name != "list":
            item.add_argument("--id", required=True)
        _add_json(item)

    match = sub.add_parser("match", help="run one match")
    match.add_argument("--bot-y", required=True)
    match.add_argument("--bot-k", required=True)
    match.add_argument("--seed", type=int, required=True)
    _add_timing(match)
    _add_json(match)

    series = sub.add_parser("series", help="run a repeatable multi-seed series")
    series.add_argument("--bot-a", required=True)
    series.add_argument("--bot-b", required=True)
    series.add_argument("--seeds", type=_parse_seeds, required=True)
    series.add_argument("--swap-sides", action="store_true")
    series.add_argument("--repetitions", type=int, default=1)
    series.add_argument("--jobs", type=int, default=1)
    series.add_argument("--resume")
    _add_timing(series)
    _add_json(series)

    runs = sub.add_parser("runs", help="inspect runs")
    run_sub = runs.add_subparsers(dest="run_command", required=True)
    listing = run_sub.add_parser("list")
    _add_json(listing)
    show = run_sub.add_parser("show")
    show.add_argument("--id", required=True)
    _add_json(show)
    return parser


def _arena_config(args, workspace: Path, official_root: Path, seeds: tuple[int, ...], swap: bool, reps: int, jobs: int) -> ArenaConfig:
    timing = TimingConfig(
        mode=args.timing,
        first_turn_ms=args.first_turn_ms,
        turn_ms=args.turn_ms,
        safety_timeout_ms=args.safety_timeout_ms,
    )
    return ArenaConfig(
        plan=GamePlan(
            timing=timing,
            max_turns=args.max_turns,
            seeds=seeds,
            swap_sides=swap,
            repetitions=reps,
            jobs=jobs,
        ),
        workspace=workspace,
        official_root=official_root,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    machine = getattr(args, "machine", False)
    storage = None
    try:
        workspace = Path(args.workspace).expanduser().resolve()
        official_root = Path(args.official_root).expanduser().resolve()
        storage = ArenaStorage(workspace)
        registry = BotRegistry(storage)
        if args.command == "doctor":
            resolve_official_root(official_root)
            _emit({"status": "ok", "official_tools": True, "workspace": str(workspace)}, machine)
        elif args.command == "bots":
            if args.bot_command == "add":
                payload = {"bot": registry.add(args.id, args.name, args.bot_launch_command, args.cwd, args.language)}
            elif args.bot_command == "list":
                payload = {"bots": registry.list()}
            elif args.bot_command == "show":
                payload = {"bot": registry.get(args.id)}
            elif args.bot_command == "validate":
                payload = registry.validate(args.id)
            else:
                payload = {"removed": registry.remove(args.id), "id": args.id}
            _emit(payload, machine)
        elif args.command in {"match", "series"}:
            if args.command == "match":
                bot_a, bot_b = args.bot_y, args.bot_k
                seeds, swap, reps, jobs = (args.seed,), False, 1, 1
                resume = None
            else:
                bot_a, bot_b = args.bot_a, args.bot_b
                seeds, swap, reps, jobs = args.seeds, args.swap_sides, args.repetitions, args.jobs
                resume = args.resume
            try:
                registry.get(bot_a)
                registry.get(bot_b)
            except BotNotFound as exc:
                raise CliError("bot_not_found", f"bot not found: {exc.args[0]}") from exc
            cfg = _arena_config(args, workspace, official_root, seeds, swap, reps, jobs)
            _emit(run_series(cfg, registry, storage, bot_a, bot_b, run_id=resume), machine)
        elif args.command == "runs":
            if args.run_command == "list":
                payload = {"runs": storage.list_runs()}
            else:
                run = storage.get_run(args.id)
                if run is None:
                    raise CliError("run_not_found", f"run not found: {args.id}")
                payload = {"run": run, "matches": storage.list_matches(args.id)}
            _emit(payload, machine)
        return 0
    except CliError as exc:
        _emit({"error": {"code": exc.code, "message": str(exc)}}, True)
        return 2
    except (ValueError, OSError) as exc:
        _emit({"error": {"code": "invalid_request", "message": str(exc)}}, True)
        return 2
    finally:
        if storage is not None:
            storage.close()
