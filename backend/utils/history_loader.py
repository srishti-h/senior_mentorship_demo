"""
utils/history_loader.py — Loads sec_history.csv into memory.

Run scripts/build_history.py once to generate sec_history.csv,
then commit it. The app loads it at startup.
"""

import csv
import logging
from config import HISTORY_CSV_PATH

log = logging.getLogger(__name__)
_history: list[dict] = []


def load_history() -> list[dict]:
    global _history
    if _history:
        return _history
    try:
        with open(HISTORY_CSV_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    _history.append({
                        "name":             row["name"].strip(),
                        "team":             row["team"].strip(),
                        "position":         row["position"].strip(),
                        "season_year":      int(row["season_year"]),
                        "class":            row["class"].strip(),
                        "nil_value":        int(row.get("nil_value", 0) or 0),
                        "nil_estimated":    int(row.get("nil_estimated", 1)),
                        "follower_count":   int(str(row.get("follower_count", 0)).replace(",", "") or 0),
                        "games_played":     int(row.get("games_played", 0) or 0),
                        "season_pass_yards": int(row.get("season_pass_yards", 0) or 0),
                        "season_rec_yards":  int(row.get("season_rec_yards",  0) or 0),
                        "season_rush_yards": int(row.get("season_rush_yards", 0) or 0),
                        "season_scoring_td": int(row.get("season_scoring_td", 0) or 0),
                    })
                except (ValueError, KeyError):
                    pass
        log.info(f"History: loaded {len(_history)} rows from {HISTORY_CSV_PATH}")
    except FileNotFoundError:
        log.warning(
            f"sec_history.csv not found at {HISTORY_CSV_PATH}. "
            "Run: python scripts/build_history.py --api-key YOUR_KEY"
        )
    return _history


def get_history() -> list[dict]:
    return _history if _history else load_history()


def get_market_trends() -> dict:
    """Aggregate NIL by season year across all players."""
    data = get_history()
    if not data:
        return {"years": [], "avg_nil": [], "total_nil": [], "athlete_count": []}

    by_year: dict[int, list[int]] = {}
    for row in data:
        y = row["season_year"]
        by_year.setdefault(y, []).append(row["nil_value"])

    years = sorted(by_year)
    return {
        "years":         years,
        "avg_nil":       [round(sum(by_year[y]) / len(by_year[y])) for y in years],
        "total_nil":     [sum(by_year[y]) for y in years],
        "athlete_count": [len(by_year[y]) for y in years],
    }
