#!/usr/bin/env python3
"""
simulate_reactions.py — Generate simulated user activity for the analytics dashboard.

Loads agent_personas.json, fetches live SEC news, matches player name mentions,
and writes realistic view/star events to analytics.db.

Usage:
    cd senior_mentorship_demo
    python3 scripts/simulate_reactions.py            # simulate 1 day
    python3 scripts/simulate_reactions.py --days 30  # backfill 30 days of history
    python3 scripts/simulate_reactions.py --dry-run  # preview counts without writing
"""

import argparse
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
BACKEND    = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, SCRIPT_DIR)

from utils.analytics   import init_db, log_events_bulk
from utils.data_loader import load_players
from utils.scraper     import scrape_sec_news
from news_parser       import parse_articles

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

PERSONAS_FILE = os.path.join(SCRIPT_DIR, "agent_personas.json")

# How strongly each archetype responds to each news event type
ARCHETYPE_NEWS_AFFINITY = {
    "brand_manager":   {"nil":0.9, "performance":0.7, "transfer":0.5, "injury":0.3, "general":0.3},
    "die_hard_fan":    {"nil":0.5, "performance":0.9, "transfer":0.8, "injury":0.9, "general":0.6},
    "fantasy_analyst": {"nil":0.3, "performance":0.9, "transfer":0.6, "injury":0.9, "general":0.4},
    "sports_agent":    {"nil":0.8, "performance":0.7, "transfer":0.9, "injury":0.8, "general":0.5},
    "casual_browser":  {"nil":0.4, "performance":0.6, "transfer":0.3, "injury":0.4, "general":0.3},
}


def load_personas():
    with open(PERSONAS_FILE) as f:
        return json.load(f)


def save_personas(personas):
    with open(PERSONAS_FILE, "w") as f:
        json.dump(personas, f, indent=2)


def base_interest(agent, player):
    score = 0.0
    if player["team"] in agent.get("team_affinity", []):
        score += 0.35
    score += agent.get("position_weights", {}).get(player.get("position", ""), 0.1)
    score += agent.get("interest_scores", {}).get(player["name"], 0.0) * 0.25
    return min(score, 1.0)


def rand_ts(day_offset):
    base = datetime.now(timezone.utc) - timedelta(days=day_offset)
    base = base.replace(
        hour=random.randint(7, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )
    return base.isoformat()


def simulate_day(personas, players, news_events, day_offset):
    events = []

    for agent in personas:
        archetype     = agent.get("archetype", "casual_browser")
        eng_rate      = agent.get("engagement_rate", 0.2)
        news_sens     = agent.get("news_sensitivity", 0.5)
        agent_id      = agent["id"]
        news_affinity = ARCHETYPE_NEWS_AFFINITY.get(archetype, {})

        # Base browsing: each agent spontaneously views 1-10 profiles per day,
        # weighted by their interest in each player
        n_browse = random.randint(1, 10)
        weights  = [base_interest(agent, p) + 0.05 for p in players]
        browsed  = random.choices(players, weights=weights, k=min(n_browse, len(players)))

        for p in browsed:
            ts = rand_ts(day_offset)
            events.append({
                "event_type": "view", "player_name": p["name"],
                "team": p["team"], "position": p.get("position", ""),
                "agent_id": agent_id, "timestamp": ts,
            })
            # Star if interest × engagement rate passes threshold
            if random.random() < min(base_interest(agent, p) * eng_rate * 3.0, 0.85):
                events.append({
                    "event_type": "star", "player_name": p["name"],
                    "team": p["team"], "position": p.get("position", ""),
                    "agent_id": agent_id, "timestamp": ts,
                })

        # News-driven views: agent reacts to news that matches their interests
        for ne in news_events:
            p = next((x for x in players if x["name"] == ne["player_name"]), None)
            if not p:
                continue
            interest   = base_interest(agent, p)
            type_boost = news_affinity.get(ne["event_type"], 0.3)
            react_prob = min((interest + type_boost) * news_sens * ne["impact"] * 0.6, 0.9)
            if random.random() < react_prob:
                events.append({
                    "event_type": "view", "player_name": p["name"],
                    "team": p["team"], "position": p.get("position", ""),
                    "agent_id": agent_id, "timestamp": rand_ts(day_offset),
                })

    # Update interest scores: boost for news mentions, decay everything by 10%
    for agent in personas:
        scores = agent.get("interest_scores", {})
        for ne in news_events:
            boost = ne["impact"] * ne["sentiment"] * agent.get("news_sensitivity", 0.5) * 0.15
            scores[ne["player_name"]] = min(1.0, max(0.0, scores.get(ne["player_name"], 0.0) + boost))
        for k in list(scores.keys()):
            scores[k] = round(scores[k] * 0.90, 4)
            if scores[k] < 0.005:
                del scores[k]
        agent["interest_scores"] = scores

    return events


def main():
    ap = argparse.ArgumentParser(description="Simulate user activity for analytics")
    ap.add_argument("--days",    type=int, default=1, help="Days to simulate (default: 1)")
    ap.add_argument("--dry-run", action="store_true",  help="Print counts without writing")
    args = ap.parse_args()

    init_db()

    if not os.path.exists(PERSONAS_FILE):
        log.error(f"Personas file not found: {PERSONAS_FILE}")
        log.error("Run: python3 scripts/generate_personas.py")
        sys.exit(1)

    personas = load_personas()
    players  = [p for p in load_players() if p.get("nil_value")]
    log.info(f"{len(personas)} agents | {len(players)} players")

    articles     = scrape_sec_news(limit=20)
    player_names = [p["name"] for p in players]
    news_events  = parse_articles(articles, player_names)
    log.info(f"News: {len(articles)} articles → {len(news_events)} player mentions")

    all_events = []
    for day in range(args.days - 1, -1, -1):
        day_events = simulate_day(personas, players, news_events, day)
        views = sum(1 for e in day_events if e["event_type"] == "view")
        stars = sum(1 for e in day_events if e["event_type"] == "star")
        all_events.extend(day_events)
        log.info(f"  Day -{day:02d}: {views} views  {stars} stars")

    total_v = sum(1 for e in all_events if e["event_type"] == "view")
    total_s = sum(1 for e in all_events if e["event_type"] == "star")
    log.info(f"Total: {len(all_events)} events  ({total_v} views, {total_s} stars)")

    if not args.dry_run:
        log_events_bulk(all_events)
        save_personas(personas)
        log.info("Written to analytics.db  |  personas updated")
    else:
        log.info("Dry run — nothing written")


if __name__ == "__main__":
    main()
