"""
routes/analytics.py

GET  /analytics/top-searched   Most viewed athletes
GET  /analytics/top-starred    Most starred athletes
GET  /analytics/trending       Biggest view-count movers (last 7 vs prior 7 days)
POST /events                   Log a single user event (view | star | unstar)
"""
from flask import Blueprint, jsonify, request
from utils.analytics import log_event, get_top_searched, get_top_starred, get_trending

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/top-searched")
def top_searched():
    limit = min(int(request.args.get("limit", 10)), 50)
    days  = request.args.get("days", type=int)
    return jsonify(get_top_searched(limit=limit, days=days))


@analytics_bp.get("/analytics/top-starred")
def top_starred():
    limit = min(int(request.args.get("limit", 10)), 50)
    days  = request.args.get("days", type=int)
    return jsonify(get_top_starred(limit=limit, days=days))


@analytics_bp.get("/analytics/trending")
def trending():
    limit = min(int(request.args.get("limit", 10)), 50)
    return jsonify(get_trending(limit=limit))


@analytics_bp.post("/events")
def post_event():
    body        = request.get_json(silent=True) or {}
    event_type  = body.get("event_type", "")
    player_name = body.get("player_name", "")
    if event_type not in ("view", "star", "unstar") or not player_name:
        return jsonify({"error": "event_type and player_name required"}), 400
    log_event(
        event_type  = event_type,
        player_name = player_name,
        team        = body.get("team", ""),
        position    = body.get("position", ""),
        agent_id    = "real_user",
    )
    return jsonify({"ok": True}), 201
