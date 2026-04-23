#!/usr/bin/env python3
"""
generate_personas.py — One-time script to create agent_personas.json.
Generates 100 simulated user personas across 5 archetypes.

Usage:
    cd senior_mentorship_demo
    python3 scripts/generate_personas.py
"""

import json
import os
import random

random.seed(42)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE   = os.path.join(SCRIPT_DIR, "agent_personas.json")

SEC_TEAMS = [
    "Alabama", "Georgia", "LSU", "Tennessee", "Texas A&M",
    "Florida", "Auburn", "Ole Miss", "Texas", "Oklahoma",
    "Arkansas", "Missouri", "South Carolina", "Kentucky",
    "Mississippi State", "Vanderbilt",
]

FIRST_NAMES = [
    "James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles",
    "Christopher","Daniel","Matthew","Anthony","Mark","Donald","Steven","Paul","Andrew","Joshua",
    "Kevin","Brian","George","Timothy","Ronald","Jason","Edward","Jeffrey","Ryan","Jacob",
    "Gary","Nicholas","Eric","Jonathan","Stephen","Larry","Justin","Scott","Brandon","Benjamin",
    "Samuel","Raymond","Patrick","Frank","Gregory","Alexander","Jack","Dennis","Jerry","Tyler",
    "Aaron","Jose","Adam","Nathan","Henry","Douglas","Zachary","Peter","Kyle","Ethan",
    "Walter","Noah","Jeremy","Christian","Keith","Roger","Terry","Gerald","Harold","Sean",
    "Austin","Carl","Arthur","Lawrence","Dylan","Jesse","Jordan","Bryan","Billy","Joe",
    "Bruce","Gabriel","Logan","Albert","Willie","Alan","Juan","Wayne","Roy","Ralph",
    "Sarah","Jessica","Ashley","Emily","Hannah","Madison","Olivia","Emma","Sophia","Isabella",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Martinez",
    "Anderson","Taylor","Thomas","Hernandez","Moore","Martin","Jackson","Thompson","White","Lopez",
    "Lee","Gonzalez","Harris","Clark","Lewis","Robinson","Walker","Perez","Hall","Young",
    "Allen","Sanchez","Wright","King","Scott","Green","Baker","Adams","Nelson","Hill",
    "Ramirez","Campbell","Mitchell","Roberts","Carter","Phillips","Evans","Turner","Torres","Parker",
    "Collins","Edwards","Stewart","Flores","Morris","Nguyen","Murphy","Rivera","Cook","Rogers",
    "Morgan","Peterson","Cooper","Reed","Bailey","Bell","Gomez","Kelly","Howard","Ward",
    "Cox","Diaz","Richardson","Wood","Watson","Brooks","Bennett","Gray","James","Reyes",
    "Cruz","Hughes","Price","Myers","Long","Foster","Sanders","Ross","Morales","Powell",
    "Sullivan","Russell","Ortiz","Jenkins","Gutierrez","Perry","Butler","Barnes","Fisher","Henderson",
]

# position_weights: how much each archetype cares about each position (0-1)
# engagement_rate: probability of starring vs just viewing
# news_sensitivity: how strongly news events shift interest
ARCHETYPES = {
    "brand_manager": {
        "count": 10,
        "position_weights": {
            "QB":1.0,"WR":0.9,"RB":0.5,"TE":0.4,
            "CB":0.3,"DB":0.3,"LB":0.2,"DL":0.2,"DE":0.2,"EDGE":0.2,"OL":0.1,
        },
        "engagement_rate": (0.30, 0.50),
        "news_sensitivity": (0.60, 0.90),
        "team_count": 0,
    },
    "die_hard_fan": {
        "count": 40,
        "position_weights": {
            "QB":0.9,"WR":0.8,"RB":0.8,"TE":0.6,
            "CB":0.6,"DB":0.6,"LB":0.7,"DL":0.6,"DE":0.6,"EDGE":0.6,"OL":0.4,
        },
        "engagement_rate": (0.40, 0.70),
        "news_sensitivity": (0.70, 1.00),
        "team_count": 2,
    },
    "fantasy_analyst": {
        "count": 20,
        "position_weights": {
            "QB":0.9,"WR":0.9,"RB":0.8,"TE":0.6,
            "CB":0.2,"DB":0.2,"LB":0.2,"DL":0.1,"DE":0.1,"EDGE":0.1,"OL":0.1,
        },
        "engagement_rate": (0.20, 0.40),
        "news_sensitivity": (0.50, 0.80),
        "team_count": 0,
    },
    "sports_agent": {
        "count": 15,
        "position_weights": {
            "QB":0.8,"WR":0.7,"RB":0.7,"TE":0.6,
            "CB":0.5,"DB":0.5,"LB":0.7,"DL":0.6,"DE":0.7,"EDGE":0.7,"OL":0.4,
        },
        "engagement_rate": (0.15, 0.30),
        "news_sensitivity": (0.70, 0.95),
        "team_count": 0,
    },
    "casual_browser": {
        "count": 15,
        "position_weights": {
            "QB":0.8,"WR":0.7,"RB":0.5,"TE":0.3,
            "CB":0.2,"DB":0.2,"LB":0.2,"DL":0.1,"DE":0.1,"EDGE":0.1,"OL":0.1,
        },
        "engagement_rate": (0.05, 0.20),
        "news_sensitivity": (0.20, 0.50),
        "team_count": 1,
    },
}


def main():
    personas   = []
    used_names = set()
    agent_num  = 1

    for archetype, cfg in ARCHETYPES.items():
        for _ in range(cfg["count"]):
            # Unique name
            while True:
                first = random.choice(FIRST_NAMES)
                last  = random.choice(LAST_NAMES)
                full  = f"{first} {last}"
                if full not in used_names:
                    used_names.add(full)
                    break

            n = cfg["team_count"]
            team_affinity = random.sample(SEC_TEAMS, n) if n > 0 else []

            # Add jitter to position weights so each agent feels distinct
            pw = {}
            for pos, base_w in cfg["position_weights"].items():
                jitter = random.uniform(-0.10, 0.10)
                pw[pos] = round(min(1.0, max(0.05, base_w + jitter)), 2)

            personas.append({
                "id":               f"agent_{agent_num:03d}",
                "name":             full,
                "archetype":        archetype,
                "team_affinity":    team_affinity,
                "position_weights": pw,
                "engagement_rate":  round(random.uniform(*cfg["engagement_rate"]), 2),
                "news_sensitivity": round(random.uniform(*cfg["news_sensitivity"]), 2),
                "interest_scores":  {},
            })
            agent_num += 1

    random.shuffle(personas)

    with open(OUT_FILE, "w") as f:
        json.dump(personas, f, indent=2)

    print(f"Generated {len(personas)} personas → {OUT_FILE}")
    for arch in ARCHETYPES:
        n = sum(1 for p in personas if p["archetype"] == arch)
        print(f"  {arch}: {n}")


if __name__ == "__main__":
    main()
