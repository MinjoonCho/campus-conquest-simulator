"""Round-robin tournaments composed from resumable Arena series."""

from __future__ import annotations

from itertools import combinations
from typing import Callable

from .bot_registry import BotRegistry
from .models import ArenaConfig
from .series import run_series
from .storage import ArenaStorage


def round_robin_pairs(bot_ids: tuple[str, ...]) -> list[tuple[str, str]]:
    if len(bot_ids) < 2:
        raise ValueError("a tournament requires at least two bots")
    if len(set(bot_ids)) != len(bot_ids):
        raise ValueError("tournament bot ids must be unique")
    return list(combinations(bot_ids, 2))


def run_tournament(
    config: ArenaConfig,
    registry: BotRegistry,
    storage: ArenaStorage,
    bot_ids: tuple[str, ...],
    *,
    progress: Callable[[dict], None] | None = None,
) -> dict:
    pairs = round_robin_pairs(bot_ids)
    for bot_id in bot_ids:
        registry.get(bot_id)
    standings = {
        bot_id: {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "games": 0,
            "score_for": 0,
            "score_against": 0,
        }
        for bot_id in bot_ids
    }
    series_results = []
    for pair_index, (bot_a, bot_b) in enumerate(pairs):
        if progress:
            progress({"pair_index": pair_index, "bot_a": bot_a, "bot_b": bot_b, "status": "started"})
        result = run_series(config, registry, storage, bot_a, bot_b, progress=progress)
        series_results.append(result)
        for bot_id, values in result["stats"]["bots"].items():
            for key in standings[bot_id]:
                standings[bot_id][key] += values[key]
        if progress:
            progress({"pair_index": pair_index, "bot_a": bot_a, "bot_b": bot_b, "status": "completed"})
    ordered = sorted(
        ({"bot_id": bot_id, **values} for bot_id, values in standings.items()),
        key=lambda row: (-row["wins"], row["losses"], -(row["score_for"] - row["score_against"]), row["bot_id"]),
    )
    return {"format": "round_robin", "pairs": len(pairs), "series": series_results, "standings": ordered}
