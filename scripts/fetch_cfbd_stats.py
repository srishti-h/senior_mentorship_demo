"""
scripts/fetch_cfbd_stats.py

Fills in missing season stats in sec_final_training_data.csv using
the College Football Data API (https://collegefootballdata.com).

Usage:
    CFBD_API_KEY=your_key python3 scripts/fetch_cfbd_stats.py

    # dry-run (print what would change, don't write):
    CFBD_API_KEY=your_key python3 scripts/fetch_cfbd_stats.py --dry-run

Requires a free API key from https://collegefootballdata.com/key
"""

import csv
import json
import os
import sys
import urllib.request
from difflib import get_close_matches

DRY_RUN  = "--dry-run" in sys.argv
API_KEY  = os.environ.get("CFBD_API_KEY", "")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT_DIR, "sec_final_training_data.csv")

if not API_KEY:
    sys.exit("ERROR: set CFBD_API_KEY env var before running.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

# Map CSV position codes → CFBD stat categories to fetch
CATEGORY_MAP = {
    "passing":   ["QB"],
    "rushing":   ["QB", "RB", "WR", "TE"],
    "receiving": ["WR", "RB", "TE"],
    "defensive": ["CB", "S", "DB", "LB", "DL", "DE", "EDGE", "EDG", "ILB", "OLB", "DT", "BCK"],
}


def cfbd_get(path: str) -> list:
    url = f"https://api.collegefootballdata.com/{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_stats(category: str) -> list:
    print(f"  Fetching {category} stats ...", end=" ", flush=True)
    data = cfbd_get(f"stats/player/season?year=2024&conference=SEC&category={category}")
    print(f"{len(data)} rows")
    return data


def normalise(name: str) -> str:
    return name.strip().lower()


def best_match(name: str, candidates: set):
    n = normalise(name)
    if n in candidates:
        return n
    close = get_close_matches(n, candidates, n=1, cutoff=0.82)
    return close[0] if close else None


def main():
    # ── Load CSV ──────────────────────────────────────────────────────────────
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

    csv_names = {normalise(r["name"]): i for i, r in enumerate(rows)}

    # ── Fetch all stat categories ─────────────────────────────────────────────
    raw: dict[str, dict] = {}   # normalised_name → {stat_type: value}
    for category in CATEGORY_MAP:
        for entry in fetch_stats(category):
            player = normalise(entry.get("player", ""))
            stat_type = entry.get("statType", "").upper()
            stat_val  = entry.get("stat", 0)
            if player not in raw:
                raw[player] = {}
            raw[player][f"{category}_{stat_type}"] = stat_val

    # ── Map CFBD stat keys → CSV column names ─────────────────────────────────
    STAT_MAP = {
        "passing_YDS":   ("season_pass_yards",  "career_pass_yards"),
        "passing_TD":    ("season_scoring_td",  "career_scoring_td"),
        "rushing_YDS":   ("season_rush_yards",  "career_rush_yards"),
        "rushing_TD":    ("season_scoring_td",  "career_scoring_td"),
        "receiving_YDS": ("season_rec_yards",   "career_rec_yards"),
        "receiving_TD":  ("season_scoring_td",  "career_scoring_td"),
        "defensive_TOT": ("season_def_tackles", "career_def_tackles"),
        "defensive_SACKS": ("season_def_sacks", "career_def_sacks"),
        "defensive_TFL": (None, None),   # tracked but not in CSV
    }

    # ── Merge into rows ───────────────────────────────────────────────────────
    updates = 0
    matched = 0
    candidates = set(csv_names.keys())

    for cfbd_name, stats in raw.items():
        idx_key = best_match(cfbd_name, candidates)
        if idx_key is None:
            continue
        idx = csv_names[idx_key]
        row = rows[idx]
        matched += 1

        for cfbd_key, (season_col, _career_col) in STAT_MAP.items():
            if season_col is None or cfbd_key not in stats:
                continue
            val = stats[cfbd_key]
            existing = row.get(season_col, "").strip()
            is_missing = existing in ("", "0", "NA")
            if is_missing and val:
                if DRY_RUN:
                    print(f"  [{row['name']}] {season_col}: {existing!r} → {val}")
                else:
                    row[season_col] = str(val)
                updates += 1

    print(f"\nMatched {matched} CFBD players to CSV rows")
    print(f"{'Would update' if DRY_RUN else 'Updated'} {updates} stat fields")

    if DRY_RUN:
        print("\nDry run — CSV not modified. Re-run without --dry-run to apply.")
        return

    # ── Also try to fill instagram_user from CFBD social data if missing ──────
    # (CFBD doesn't have social data — skip)

    # ── Write updated CSV ─────────────────────────────────────────────────────
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV updated: {CSV_PATH}")


if __name__ == "__main__":
    main()
