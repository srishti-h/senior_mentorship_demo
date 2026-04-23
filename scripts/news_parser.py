"""
news_parser.py — Rule-based extraction of player mentions and event types from news headlines.
No LLM required — pure keyword matching.
"""
import re
import logging

log = logging.getLogger(__name__)

PERFORMANCE_WORDS = {
    "touchdown", "td", "tds", "yards", "yard", "record", "heisman", "mvp",
    "sack", "sacks", "interception", "int", "rushing", "passing", "receiving",
    "scored", "score", "breakout", "star", "standout", "rushing", "stats",
}
INJURY_WORDS = {
    "injury", "injured", "injures", "hurt", "out", "misses", "miss", "surgery",
    "knee", "shoulder", "hamstring", "ankle", "torn", "acl", "mcl",
    "concussion", "questionable", "doubtful", "sidelined", "ruled", "setback",
}
NIL_WORDS = {
    "nil", "deal", "deals", "sponsor", "brand", "partnership", "endorsement",
    "contract", "signed", "sign", "collective", "money", "million",
    "valuation", "value", "bag", "payout", "earnings",
}
TRANSFER_WORDS = {
    "transfer", "portal", "commit", "commits", "decommit", "decommits",
    "entering", "leaving", "joins", "joining", "announced", "return",
    "returning", "stay", "staying", "visits", "visit",
}


def classify(headline):
    h     = headline.lower()
    words = set(re.sub(r"[^a-z ]", " ", h).split())
    if words & INJURY_WORDS:
        return "injury", -1
    if words & TRANSFER_WORDS:
        return "transfer", 0
    if words & NIL_WORDS:
        return "nil", 1
    if words & PERFORMANCE_WORDS:
        return "performance", 1
    return "general", 0


def extract_players(headline, player_names):
    h     = headline.lower()
    found = []
    for name in player_names:
        parts = name.lower().split()
        if len(parts) < 2:
            continue
        last  = parts[-1]
        first = parts[0]
        if name.lower() in h:
            found.append(name)
        elif len(last) > 4 and last in h and first[0] in h:
            found.append(name)
    return found


def parse_articles(articles, player_names):
    """
    Given articles [{title, url, source}] and a list of player names,
    return [{player_name, event_type, sentiment, impact, headline}].
    """
    results = []
    seen    = set()
    for art in articles:
        title      = art.get("title", "")
        event_type, sentiment = classify(title)
        impact     = 0.9 if abs(sentiment) > 0 else 0.5
        for p in extract_players(title, player_names):
            key = (p, title[:50])
            if key not in seen:
                seen.add(key)
                results.append({
                    "player_name": p,
                    "event_type":  event_type,
                    "sentiment":   sentiment,
                    "impact":      impact,
                    "headline":    title,
                })
    log.debug(f"Parsed {len(results)} player mentions from {len(articles)} articles")
    return results
