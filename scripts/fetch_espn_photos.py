"""
scripts/fetch_espn_photos.py

Fetches athlete headshot URLs from ESPN's public roster API for all 16 SEC teams.
Writes backend/data/photo_map.json  →  { "Player Name": "https://a.espncdn.com/..." }

Usage:
    python3 scripts/fetch_espn_photos.py
"""

import json
import os
import time
import urllib.request

ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT     = os.path.join(ROOT_DIR, "backend", "data", "photo_map.json")

SEC_TEAMS = {
    "Alabama Crimson Tide":      333,
    "Arkansas Razorbacks":       8,
    "Auburn Tigers":             2,
    "Florida Gators":            57,
    "Georgia Bulldogs":          61,
    "Kentucky Wildcats":         96,
    "LSU Tigers":                99,
    "Mississippi State Bulldogs":344,
    "Missouri Tigers":           142,
    "Oklahoma Sooners":          201,
    "Ole Miss Rebels":           145,
    "South Carolina Gamecocks":  2579,
    "Tennessee Volunteers":      2633,
    "Texas A&M Aggies":          245,
    "Texas Longhorns":           251,
    "Vanderbilt Commodores":     238,
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NILPlatform/1.0)"}


def fetch_roster(team_id: int) -> list:
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/roster"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    players = []
    for group in data.get("athletes", []):
        players.extend(group.get("items", []))
    return players


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    photo_map = {}
    for team_name, team_id in SEC_TEAMS.items():
        print(f"  {team_name} ...", end=" ", flush=True)
        try:
            players = fetch_roster(team_id)
            found = 0
            for p in players:
                headshot = p.get("headshot", {})
                url = headshot.get("href", "") if isinstance(headshot, dict) else ""
                if url:
                    photo_map[p["fullName"]] = url
                    found += 1
            print(f"{found}/{len(players)} photos")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.3)

    with open(OUTPUT, "w") as f:
        json.dump(photo_map, f, indent=2)

    print(f"\nSaved {len(photo_map)} photos → {OUTPUT}")


if __name__ == "__main__":
    main()
