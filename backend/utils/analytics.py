"""
utils/analytics.py — SQLite-backed event store for aggregate user activity analytics.
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone

from config import ROOT_DIR

logger  = logging.getLogger(__name__)
DB_PATH = os.path.join(ROOT_DIR, "analytics.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type  TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team        TEXT DEFAULT '',
                position    TEXT DEFAULT '',
                agent_id    TEXT DEFAULT '',
                timestamp   TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ev_player ON events(player_name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ev_type   ON events(event_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ev_ts     ON events(timestamp)")
    logger.info(f"Analytics DB ready: {DB_PATH}")


def log_event(event_type: str, player_name: str, team: str = "",
              position: str = "", agent_id: str = "real_user",
              timestamp: str = None):
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO events (event_type,player_name,team,position,agent_id,timestamp)"
            " VALUES (?,?,?,?,?,?)",
            (event_type, player_name, team, position, agent_id, ts),
        )


def log_events_bulk(rows: list):
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as c:
        c.executemany(
            "INSERT INTO events (event_type,player_name,team,position,agent_id,timestamp)"
            " VALUES (?,?,?,?,?,?)",
            [
                (
                    r["event_type"],
                    r["player_name"],
                    r.get("team", ""),
                    r.get("position", ""),
                    r.get("agent_id", ""),
                    r.get("timestamp", now),
                )
                for r in rows
            ],
        )


def get_top_searched(limit: int = 10, days: int = None) -> list:
    query  = "SELECT player_name,team,position,COUNT(*) AS views FROM events WHERE event_type='view'"
    params = []
    if days:
        query += " AND timestamp >= datetime('now', ?)"
        params.append(f"-{days} days")
    query += " GROUP BY player_name ORDER BY views DESC LIMIT ?"
    params.append(limit)
    with _conn() as c:
        return [dict(r) for r in c.execute(query, params).fetchall()]


def get_top_starred(limit: int = 10, days: int = None) -> list:
    query  = "SELECT player_name,team,position,COUNT(*) AS stars FROM events WHERE event_type='star'"
    params = []
    if days:
        query += " AND timestamp >= datetime('now', ?)"
        params.append(f"-{days} days")
    query += " GROUP BY player_name ORDER BY stars DESC LIMIT ?"
    params.append(limit)
    with _conn() as c:
        return [dict(r) for r in c.execute(query, params).fetchall()]


def get_event_count() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM events").fetchone()[0]


def seed_events(players: list, days: int = 30):
    """
    Generate synthetic baseline activity so the analytics tab has data from the
    first deploy. Skips if events already exist.
    """
    import random
    from datetime import datetime, timedelta, timezone

    if get_event_count() > 0:
        return

    random.seed(42)

    POSITION_WEIGHTS = {
        "QB": 1.0, "WR": 0.85, "RB": 0.75, "TE": 0.6,
        "CB": 0.5, "DB": 0.45, "LB": 0.55, "DL": 0.4,
        "DE": 0.5, "EDGE": 0.5, "OL": 0.3,
    }

    max_val = max((p.get("nil_value") or 1) for p in players)
    weights = []
    for p in players:
        pos_w = POSITION_WEIGHTS.get(p.get("position", ""), 0.3)
        val_w = ((p.get("nil_value") or 1) / max_val) ** 0.5
        weights.append(pos_w * val_w + 0.1)

    events = []
    n_agents = 100

    for day in range(days - 1, -1, -1):
        base = datetime.now(timezone.utc) - timedelta(days=day)
        for agent_idx in range(n_agents):
            agent_id = f"agent_{agent_idx + 1:03d}"
            viewed = random.choices(players, weights=weights, k=random.randint(2, 8))
            for p in viewed:
                ts = base.replace(
                    hour=random.randint(7, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                    microsecond=0,
                ).isoformat()
                events.append({
                    "event_type": "view",
                    "player_name": p["name"],
                    "team": p.get("team", ""),
                    "position": p.get("position", ""),
                    "agent_id": agent_id,
                    "timestamp": ts,
                })
                pos_w = POSITION_WEIGHTS.get(p.get("position", ""), 0.3)
                if random.random() < pos_w * 0.25:
                    events.append({
                        "event_type": "star",
                        "player_name": p["name"],
                        "team": p.get("team", ""),
                        "position": p.get("position", ""),
                        "agent_id": agent_id,
                        "timestamp": ts,
                    })

    log_events_bulk(events)
    logger.info(f"Analytics seeded: {len(events)} events ({days} days, {n_agents} agents)")


def get_trending(limit: int = 10) -> list:
    """Players with biggest view-count increase in the last 7 days vs the prior 7."""
    with _conn() as c:
        recent = dict(c.execute("""
            SELECT player_name, COUNT(*) FROM events
            WHERE event_type='view' AND timestamp >= datetime('now','-7 days')
            GROUP BY player_name
        """).fetchall())
        prior = dict(c.execute("""
            SELECT player_name, COUNT(*) FROM events
            WHERE event_type='view'
              AND timestamp >= datetime('now','-14 days')
              AND timestamp <  datetime('now','-7 days')
            GROUP BY player_name
        """).fetchall())
        meta = {r[0]: (r[1], r[2]) for r in c.execute(
            "SELECT player_name, team, position FROM events GROUP BY player_name"
        ).fetchall()}

    scores = []
    for name, cnt in recent.items():
        prev  = prior.get(name, 0)
        delta = cnt - prev
        if delta > 0:
            t, p = meta.get(name, ("", ""))
            scores.append({
                "player_name":  name,
                "team":         t,
                "position":     p,
                "recent_views": cnt,
                "prior_views":  prev,
                "delta":        delta,
            })
    scores.sort(key=lambda x: x["delta"], reverse=True)
    return scores[:limit]
