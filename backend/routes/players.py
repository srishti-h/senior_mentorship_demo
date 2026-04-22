"""
routes/players.py

GET /players          List all players (search, position filter, pagination)
GET /players/<name>   Single player detail (optional live IG refresh)
"""

from flask import Blueprint, request, jsonify
from utils.data_loader import get_players
from utils.scraper import scrape_instagram_followers

players_bp = Blueprint("players", __name__)


@players_bp.get("/players")
def list_players():
    """
    Query params:
      q         — search name or team (case-insensitive)
      position  — position code: QB WR RB TE DB LB DL OL EDGE DE CB
      limit     — results per page (default 50, max 200)
      offset    — pagination offset (default 0)
    """
    q        = request.args.get("q", "").lower().strip()
    position = request.args.get("position", "").upper().strip()
    limit    = min(int(request.args.get("limit",  50)), 200)
    offset   = max(int(request.args.get("offset",  0)),   0)

    results = get_players()

    if q:
        results = [
            p for p in results
            if q in p["name"].lower() or q in p["team"].lower()
        ]

    if position and position != "ALL":
        results = [p for p in results if p["position"] == position]

    results = sorted(results, key=lambda p: p["nil_value"] or -1, reverse=True)

    total = len(results)
    page  = results[offset: offset + limit]

    return jsonify({"total": total, "offset": offset, "limit": limit, "players": page})


@players_bp.get("/players/<path:name>")
def get_player(name: str):
    """
    Lookup a player by name (URL-encoded, case-insensitive).
    Add ?refresh_ig=true to attempt a live Instagram follower count fetch.
    """
    refresh_ig  = request.args.get("refresh_ig", "false").lower() == "true"
    name_lower  = name.lower().replace("-", " ").replace("%20", " ")
    all_players = get_players()

    player = next((p for p in all_players if p["name"].lower() == name_lower), None)
    if not player:
        player = next((p for p in all_players if name_lower in p["name"].lower()), None)
    if not player:
        return jsonify({"error": f"Player '{name}' not found"}), 404

    result = dict(player)

    if refresh_ig and player["instagram_user"]:
        live = scrape_instagram_followers(player["instagram_user"])
        result["follower_count"]      = live if live is not None else player["follower_count"]
        result["follower_count_live"] = live is not None
    else:
        result["follower_count_live"] = False

    return jsonify(result)
