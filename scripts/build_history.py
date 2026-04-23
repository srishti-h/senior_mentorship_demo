#!/usr/bin/env python3
"""
scripts/build_history.py — Build sec_history.csv with year-by-year NIL data.

For every athlete in sec_final_training_data.csv, this script:
  1. Determines their college career span from class year (FR=1yr, SR=4yrs, etc.)
  2. Fetches real season stats from the College Football Data API for each prior year
  3. Back-calculates estimated follower counts using 28% annual growth
  4. Runs the trained NIL model on each year's data and applies a market scale factor
     (NIL market was ~32% of current size in 2021, growing to 100% by 2025)
  5. Writes sec_history.csv — current year uses actual nil_value from the CSV,
     historical years are model estimates (flagged with nil_estimated=1)

Usage:
    cd senior_mentorship_demo
    python scripts/build_history.py --api-key YOUR_CFBD_KEY

Get a free API key: https://collegefootballdata.com/key  (takes ~2 minutes)
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time

import joblib
import numpy as np
import requests

# ── Path setup ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
BACKEND    = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND)

from utils.features import engineer_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── Model artifacts ───────────────────────────────────────────────────────────
ARTIFACTS = os.path.join(BACKEND, "model_artifacts")
_model  = joblib.load(os.path.join(ARTIFACTS, "nil_model.pkl"))
_scaler = joblib.load(os.path.join(ARTIFACTS, "scaler.pkl"))
with open(os.path.join(ARTIFACTS, "meta.json")) as f:
    _meta = json.load(f)

# ── Constants ─────────────────────────────────────────────────────────────────
CFBD_BASE    = "https://api.collegefootballdata.com"
CURRENT_YEAR = 2025   # label we attach to rows from sec_final_training_data.csv

# NIL market size relative to 2025 model calibration.
# Sources: Opendorse Activity Report, On3 NIL annual estimates.
MARKET_FACTOR = {2021: 0.32, 2022: 0.50, 2023: 0.68, 2024: 0.86, 2025: 1.00}

FOLLOWER_GROWTH = 0.28   # estimated annual IG follower growth for active CFB players

CLASS_ORDER = ["FR", "SO", "JR", "SR", "GR"]

# CFBD short name → our full team name
CFBD_TO_FULL = {
    "Alabama":          "Alabama Crimson Tide",
    "Arkansas":         "Arkansas Razorbacks",
    "Auburn":           "Auburn Tigers",
    "Florida":          "Florida Gators",
    "Georgia":          "Georgia Bulldogs",
    "Kentucky":         "Kentucky Wildcats",
    "LSU":              "LSU Tigers",
    "Mississippi State":"Mississippi State Bulldogs",
    "Missouri":         "Missouri Tigers",
    "Oklahoma":         "Oklahoma Sooners",
    "Ole Miss":         "Ole Miss Rebels",
    "South Carolina":   "South Carolina Gamecocks",
    "Tennessee":        "Tennessee Volunteers",
    "Texas":            "Texas Longhorns",
    "Texas A&M":        "Texas A&M Aggies",
    "Vanderbilt":       "Vanderbilt Commodores",
}

# ── CFBD helpers ──────────────────────────────────────────────────────────────

def cfbd_get(path: str, api_key: str, params: dict | None = None, delay: float = 1.1) -> list:
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(f"{CFBD_BASE}{path}", headers=headers, params=params or {}, timeout=20)
    if resp.status_code == 429:
        log.warning("Rate-limited — sleeping 60 s")
        time.sleep(60)
        resp = requests.get(f"{CFBD_BASE}{path}", headers=headers, params=params or {}, timeout=20)
    resp.raise_for_status()
    time.sleep(delay)
    return resp.json()


def norm(name: str) -> str:
    """Lowercase + strip punctuation for fuzzy name matching."""
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def fetch_year_stats(year: int, api_key: str) -> dict[str, dict]:
    """
    Pull all SEC player stats for one season from CFBD and pivot to:
      { normalized_name → { team, games_played, pass_yards, rush_yards,
                             rec_yards, scoring_td, def_tackles, def_sacks } }
    """
    result: dict[str, dict] = {}

    # (cfbd category, stat_type in API, our field, accumulate?)
    mappings = [
        ("passing",   "YDS",     "pass_yards",  False),
        ("passing",   "TD",      "pass_td",     False),
        ("passing",   "GAMES",   "games_played",False),
        ("rushing",   "YDS",     "rush_yards",  False),
        ("rushing",   "TD",      "rush_td",     False),
        ("rushing",   "GAMES",   "games_played",False),   # overwrite with rushing games if higher
        ("receiving", "YDS",     "rec_yards",   False),
        ("receiving", "TD",      "rec_td",      False),
        ("defensive", "TACKLES", "def_tackles", False),
        ("defensive", "TOT",     "def_tackles", False),   # alternate name same stat
        ("defensive", "SACKS",   "def_sacks",   False),
        ("defensive", "GAMES",   "games_played",False),
    ]

    fetched: dict[str, list] = {}
    for category in ("passing", "rushing", "receiving", "defensive"):
        try:
            rows = cfbd_get("/stats/player/season", api_key, {
                "year": year, "seasonType": "regular",
                "conference": "SEC", "category": category,
            })
            fetched[category] = rows
            log.info(f"  {year} {category}: {len(rows)} stat rows")
        except Exception as e:
            log.warning(f"  {year} {category} fetch failed: {e}")
            fetched[category] = []

    for category, cat_rows in fetched.items():
        for row in cat_rows:
            raw_name   = row.get("player", "")
            key        = norm(raw_name)
            stat_type  = row.get("statType", "")
            stat_val   = float(row.get("stat", 0) or 0)
            team_short = row.get("team", "")

            if key not in result:
                result[key] = {
                    "_raw_name":   raw_name,
                    "team":        CFBD_TO_FULL.get(team_short, team_short),
                    "games_played": 0,
                    "pass_yards":   0, "pass_td":  0,
                    "rush_yards":   0, "rush_td":  0,
                    "rec_yards":    0, "rec_td":   0,
                    "def_tackles":  0, "def_sacks": 0,
                }

            for (c, st, field, _) in mappings:
                if c == category and st == stat_type:
                    if field == "games_played":
                        result[key][field] = max(result[key][field], int(stat_val))
                    else:
                        result[key][field] = stat_val
                    break

    # Compute consolidated scoring_td (avoid double-counting QB rushing TDs)
    for key, d in result.items():
        d["scoring_td"] = d["pass_td"] + d["rec_td"] + d.get("rush_td", 0)
        if d["games_played"] == 0:
            d["games_played"] = 11   # safe default

    return result


# ── Model helpers ─────────────────────────────────────────────────────────────

def estimate_nil(payload: dict, year: int) -> int | None:
    try:
        X    = engineer_features(payload, _meta)
        logy = _model.predict(_scaler.transform(X))[0]
        base = float(np.exp(logy))
        return round(base * MARKET_FACTOR.get(year, 1.0))
    except Exception as e:
        log.debug(f"estimate_nil: {e}")
        return None


def class_at_offset(current_class: str, years_ago: int) -> str | None:
    """Return historical class given current class and years back. None if pre-college."""
    try:
        idx = CLASS_ORDER.index(current_class) - years_ago
        return CLASS_ORDER[idx] if idx >= 0 else None
    except ValueError:
        return None


def hist_followers(current: int, years_ago: int) -> int:
    if years_ago == 0:
        return current
    return max(500, round(current / ((1 + FOLLOWER_GROWTH) ** years_ago)))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Build sec_history.csv from CFBD API")
    ap.add_argument("--api-key", required=True,
                    help="CFBD API key — free at https://collegefootballdata.com/key")
    ap.add_argument("--years",   default="2021,2022,2023,2024",
                    help="Comma-separated historical seasons to fetch (default: 2021-2024)")
    ap.add_argument("--out",     default=os.path.join(ROOT_DIR, "sec_history.csv"))
    args = ap.parse_args()

    historical_years = sorted(int(y) for y in args.years.split(","))

    # ── Load current CSV ───────────────────────────────────────────────────────
    src = os.path.join(ROOT_DIR, "sec_final_training_data.csv")
    current: list[dict] = []
    with open(src, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nil_raw = row.get("nil_value", "")
            try:
                nil_val = int(str(nil_raw).replace(",", ""))
                if nil_val > 0:
                    current.append({**row, "nil_value": nil_val})
            except (ValueError, TypeError):
                pass
    log.info(f"Loaded {len(current)} athletes from {src}")

    # ── Fetch historical stats year by year ───────────────────────────────────
    year_db: dict[int, dict[str, dict]] = {}
    for year in historical_years:
        log.info(f"Fetching {year} season stats from CFBD...")
        year_db[year] = fetch_year_stats(year, args.api_key)

    # ── Build output rows ─────────────────────────────────────────────────────
    out_rows: list[dict] = []
    matched_count = 0

    for p in current:
        name      = p["name"].strip()
        team      = p["team"].strip()
        position  = p["position"].strip()
        cur_class = p.get("class", "SR").strip()
        nil_val   = p["nil_value"]
        cur_foll  = int(str(p.get("follower_count", 0)).replace(",", "") or 0)
        fpi       = float(p.get("team_FPI", 10) or 10)
        tier      = int(p.get("program_tier", 5) or 5)
        height    = float(p.get("height_in", 72) or 72)
        weight    = float(p.get("weight_lb", 210) or 210)

        def make_row(year, class_yr, nil, is_est, followers, gp,
                     s_pass=0, s_rec=0, s_rush=0, s_td=0, s_tack=0, s_sack=0.0):
            return {
                "name": name, "team": team, "position": position,
                "season_year": year, "class": class_yr,
                "nil_value": nil, "nil_estimated": int(is_est),
                "follower_count": followers, "games_played": gp,
                "season_pass_yards": int(s_pass),
                "season_rec_yards":  int(s_rec),
                "season_rush_yards": int(s_rush),
                "season_scoring_td": int(s_td),
                "season_def_tackles":int(s_tack),
                "season_def_sacks":  round(float(s_sack), 1),
                "team_FPI": fpi, "program_tier": tier,
            }

        # Current year — use actual nil_value from CSV
        out_rows.append(make_row(
            CURRENT_YEAR, cur_class, nil_val, False, cur_foll,
            int(p.get("games_played", 12) or 12),
            p.get("season_pass_yards", 0) or 0,
            p.get("season_rec_yards",  0) or 0,
            p.get("season_rush_yards", 0) or 0,
            p.get("season_scoring_td", 0) or 0,
            p.get("season_def_tackles",0) or 0,
            p.get("season_def_sacks",  0) or 0,
        ))

        # Historical years
        name_key   = norm(name)
        name_parts = name.lower().split()

        for year in sorted(historical_years, reverse=True):
            years_ago  = CURRENT_YEAR - year
            hist_class = class_at_offset(cur_class, years_ago)
            if hist_class is None:
                continue   # player wasn't in college this year

            db = year_db.get(year, {})

            # Name matching: exact → parts fallback
            stats = db.get(name_key)
            if not stats:
                for k, v in db.items():
                    if len(name_parts) >= 2 and name_parts[0] in k and name_parts[-1] in k:
                        stats = v
                        matched_count += 1
                        break

            followers = hist_followers(cur_foll, years_ago)
            gp = stats["games_played"] if stats else 11

            payload = {
                "position": position,
                "class":    hist_class,
                "height_in": height, "weight_lb": weight,
                "follower_count": followers,
                "games_played":   gp,
                "program_tier":   tier,
                "team_FPI":       fpi,
                "team":           team,
                # season = career (we only have one year of data at a time)
                "season_pass_yards":  float(stats["pass_yards"]  if stats else 0),
                "career_pass_yards":  float(stats["pass_yards"]  if stats else 0),
                "season_rec_yards":   float(stats["rec_yards"]   if stats else 0),
                "career_rec_yards":   float(stats["rec_yards"]   if stats else 0),
                "season_rush_yards":  float(stats["rush_yards"]  if stats else 0),
                "career_rush_yards":  float(stats["rush_yards"]  if stats else 0),
                "season_scoring_td":  float(stats["scoring_td"]  if stats else 0),
                "career_scoring_td":  float(stats["scoring_td"]  if stats else 0),
                "season_def_tackles": float(stats["def_tackles"] if stats else 0),
                "career_def_tackles": float(stats["def_tackles"] if stats else 0),
                "season_def_sacks":   float(stats["def_sacks"]  if stats else 0),
                "career_def_sacks":   float(stats["def_sacks"]  if stats else 0),
            }

            nil_est = estimate_nil(payload, year)
            if nil_est is None:
                continue

            out_rows.append(make_row(
                year, hist_class, nil_est, True, followers, gp,
                payload["season_pass_yards"], payload["season_rec_yards"],
                payload["season_rush_yards"], payload["season_scoring_td"],
                payload["season_def_tackles"], payload["season_def_sacks"],
            ))

    # ── Write output ───────────────────────────────────────────────────────────
    out_rows.sort(key=lambda r: (r["name"], r["season_year"]))
    fieldnames = list(out_rows[0].keys()) if out_rows else []

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    actual_rows = sum(1 for r in out_rows if not r["nil_estimated"])
    hist_rows   = sum(1 for r in out_rows if r["nil_estimated"])
    log.info(f"Done — wrote {len(out_rows)} rows to {args.out}")
    log.info(f"  {actual_rows} current-year rows (actual NIL from CSV)")
    log.info(f"  {hist_rows} historical rows (model-estimated + market factor)")
    log.info(f"  {matched_count} historical rows matched real CFBD stats by name")


if __name__ == "__main__":
    main()
