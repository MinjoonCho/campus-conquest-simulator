"""Aggregate match results by stable bot identity."""

from __future__ import annotations

from typing import Iterable


def aggregate_results(records: Iterable[dict], bot_ids: tuple[str, ...]) -> dict:
    bots = {
        bot_id: {"wins": 0, "losses": 0, "draws": 0, "score_for": 0, "score_against": 0}
        for bot_id in bot_ids
    }
    matches = 0
    forfeits = 0
    for record in records:
        matches += 1
        y, k = record["bot_y"], record["bot_k"]
        result = record["result"]
        bots[y]["score_for"] += result["score"]["Y"]
        bots[y]["score_against"] += result["score"]["K"]
        bots[k]["score_for"] += result["score"]["K"]
        bots[k]["score_against"] += result["score"]["Y"]
        winner = result["winner"]
        if winner == "DRAW":
            bots[y]["draws"] += 1
            bots[k]["draws"] += 1
        else:
            winner_id = y if winner == "Y" else k
            loser_id = k if winner == "Y" else y
            bots[winner_id]["wins"] += 1
            bots[loser_id]["losses"] += 1
        if result.get("reason") == "forfeit":
            forfeits += 1
    for values in bots.values():
        values["games"] = values["wins"] + values["losses"] + values["draws"]
        values["win_rate"] = values["wins"] / values["games"] if values["games"] else 0.0
    return {"matches": matches, "forfeits": forfeits, "bots": bots}

