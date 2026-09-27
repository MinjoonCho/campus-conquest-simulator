"""Deterministic multi-seed, side-swapped series execution."""

from __future__ import annotations

import dataclasses
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .bot_registry import BotRegistry
from .models import ArenaConfig
from .official_adapter import MatchOutcome, run_official_match
from .stats import aggregate_results
from .storage import ArenaStorage


@dataclass(frozen=True)
class MatchJob:
    index: int
    seed: int
    bot_y: str
    bot_k: str


def expand_jobs(
    seeds: tuple[int, ...],
    bot_a: str,
    bot_b: str,
    *,
    swap_sides: bool,
    repetitions: int,
) -> list[MatchJob]:
    jobs: list[MatchJob] = []
    for _ in range(repetitions):
        for seed in seeds:
            jobs.append(MatchJob(len(jobs), seed, bot_a, bot_b))
            if swap_sides:
                jobs.append(MatchJob(len(jobs), seed, bot_b, bot_a))
    return jobs


def _config_payload(config: ArenaConfig) -> dict:
    payload = dataclasses.asdict(config.plan)
    payload["workspace"] = str(config.workspace)
    payload["official_root"] = str(config.official_root)
    return payload


def _play(config: ArenaConfig, registry: BotRegistry, job: MatchJob) -> MatchOutcome:
    y = registry.get(job.bot_y)
    k = registry.get(job.bot_k)
    return run_official_match(
        config,
        y["command"],
        k["command"],
        job.seed,
        name_y=y["name"],
        name_k=k["name"],
    )


def run_series(
    config: ArenaConfig,
    registry: BotRegistry,
    storage: ArenaStorage,
    bot_a: str,
    bot_b: str,
    *,
    run_id: str | None = None,
    progress: Callable[[dict], None] | None = None,
) -> dict:
    registry.get(bot_a)
    registry.get(bot_b)
    if run_id is None:
        run_id = storage.create_run(
            _config_payload(config), bot_a, bot_b, config.official_comparable
        )
    elif storage.get_run(run_id) is None:
        raise ValueError(f"run not found: {run_id}")
    jobs = expand_jobs(
        config.plan.seeds,
        bot_a,
        bot_b,
        swap_sides=config.plan.swap_sides,
        repetitions=config.plan.repetitions,
    )
    completed = storage.completed_job_indices(run_id)
    pending = [job for job in jobs if job.index not in completed]

    def store(job: MatchJob, outcome: MatchOutcome) -> None:
        replay_path = None
        if config.plan.replay_policy != "none":
            replay_path = storage.write_json(
                storage.workspace / "replays" / run_id / f"{job.index:06d}.json",
                outcome.replay,
            )
        telemetry_path = storage.write_json(
            storage.workspace / "telemetry" / run_id / f"{job.index:06d}.json",
            list(outcome.telemetry),
        )
        storage.add_match(
            run_id,
            job.index,
            job.seed,
            job.bot_y,
            job.bot_k,
            outcome.result,
            replay_path,
            telemetry_path,
        )
        if progress:
            progress({"run_id": run_id, "job_index": job.index, "status": "completed"})

    try:
        if config.plan.jobs == 1 or len(pending) < 2:
            for job in pending:
                store(job, _play(config, registry, job))
        else:
            with ThreadPoolExecutor(max_workers=config.plan.jobs) as pool:
                futures = {pool.submit(_play, config, registry, job): job for job in pending}
                for future in as_completed(futures):
                    store(futures[future], future.result())
        storage.update_run_status(run_id, "completed")
    except BaseException:
        storage.update_run_status(run_id, "failed")
        raise
    records = storage.list_matches(run_id)
    return {
        "run_id": run_id,
        "status": storage.get_run(run_id)["status"],
        "scheduled": len(jobs),
        "completed": len(records),
        "skipped": len(completed),
        "stats": aggregate_results(records, (bot_a, bot_b)),
    }

