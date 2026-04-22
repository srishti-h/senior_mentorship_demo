"""
utils/data_loader.py — Loads and caches the SEC player CSV into memory.

CSV is expected at: SENIOR_MENTORSHIP_DEMO/sec_final_training_data.csv
"""

import csv
import logging
from config import CSV_PATH

logger = logging.getLogger(__name__)

_players: list[dict] = []


def _int(v: str, default: int = 0) -> int:
    try:
        return int(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return default


def _float(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def load_players() -> list[dict]:
    """
    Parse sec_final_training_data.csv and populate the in-memory player list.
    Safe to call multiple times — only reads the file once.
    """
    global _players
    if _players:
        return _players

    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nil_raw = row.get("nil_value", "")
                try:
                    nil_val = int(nil_raw) if nil_raw not in ("NA", "", None) else None
                except (ValueError, TypeError):
                    nil_val = None

                _players.append({
                    "name":               row["name"].strip(),
                    "team":               row["team"].strip(),
                    "position":           row["position"].strip(),
                    "class":              row.get("class", "").strip(),
                    "height_in":          _int(row.get("height_in")),
                    "weight_lb":          _int(row.get("weight_lb")),
                    "games_played":       _int(row.get("games_played")),
                    "follower_count":     _int(row.get("follower_count")),
                    "instagram_user":     row.get("instagram_user", "").strip(),
                    "engagement_rate":    _float(row.get("engagement_rate")),
                    "team_FPI":           _float(row.get("team_FPI")),
                    "team_RK":            _int(row.get("team_RK")),
                    "program_tier":       _int(row.get("program_tier"), 5),
                    "season_pass_yards":  _int(row.get("season_pass_yards")),
                    "career_pass_yards":  _int(row.get("career_pass_yards")),
                    "season_rec_yards":   _int(row.get("season_rec_yards")),
                    "career_rec_yards":   _int(row.get("career_rec_yards")),
                    "season_rush_yards":  _int(row.get("season_rush_yards")),
                    "career_rush_yards":  _int(row.get("career_rush_yards")),
                    "season_scoring_td":  _int(row.get("season_scoring_td")),
                    "career_scoring_td":  _int(row.get("career_scoring_td")),
                    "season_def_tackles": _int(row.get("season_def_tackles")),
                    "career_def_tackles": _int(row.get("career_def_tackles")),
                    "season_def_sacks":   _float(row.get("season_def_sacks")),
                    "career_def_sacks":   _float(row.get("career_def_sacks")),
                    "nil_value":          nil_val,
                })

        logger.info(f"Loaded {len(_players)} players from {CSV_PATH}")

    except FileNotFoundError:
        logger.error(
            f"CSV not found at {CSV_PATH}\n"
            "Make sure sec_final_training_data.csv is in the project root."
        )

    return _players


def get_players() -> list[dict]:
    """Return cached player list (loads from disk on first call)."""
    return _players if _players else load_players()
