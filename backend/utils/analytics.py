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
