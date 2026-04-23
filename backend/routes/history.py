"""
routes/history.py

GET /players/<name>/history   Year-by-year NIL career data for one player
GET /market/trends            Season-by-season SEC aggregate statistics
"""

import re
from flask import Blueprint, jsonify
from utils.history_loader import get_history, get_market_trends

history_bp = Blueprint("history", __name__)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


@history_bp.get("/players/<path:name>/history")
def player_history(name: str):
    target = _norm(name.replace("-", " ").replace("%20", " "))
    data   = get_history()

    seasons = [r for r in data if _norm(r["name"]) == target]
    if not seasons:
        seasons = [r for r in data if target in _norm(r["name"])]
    if not seasons:
        return jsonify({"error": f"No history for '{name}'", "seasons": []}), 404

    seasons.sort(key=lambda r: r["season_year"])

    return jsonify({
        "name":     seasons[0]["name"],
        "team":     seasons[-1]["team"],
        "position": seasons[0]["position"],
        "seasons":  [{
            "year":          r["season_year"],
            "class":         r["class"],
            "nil_value":     r["nil_value"],
            "nil_estimated": bool(r["nil_estimated"]),
            "follower_count":r["follower_count"],
            "games_played":  r["games_played"],
            "season_pass_yards":  r["season_pass_yards"],
            "season_rec_yards":   r["season_rec_yards"],
            "season_rush_yards":  r["season_rush_yards"],
            "season_scoring_td":  r["season_scoring_td"],
        } for r in seasons],
    })


@history_bp.get("/market/trends")
def market_trends():
    trends = get_market_trends()
    if not trends["years"]:
        return jsonify({"error": "History not loaded — run build_history.py first"}), 503
    return jsonify(trends)
