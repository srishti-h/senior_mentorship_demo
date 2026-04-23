"""
utils/scraper.py — Live Instagram follower counts + SEC/NIL news scraping.

Instagram:  Hits the public profile page, parses embedded JSON or meta text.
            Results are cached in-memory (TTL = INSTAGRAM_CACHE_TTL seconds).

News:       Tries ESPN and On3 live. Falls back to a curated list of real,
            verified SEC/NIL articles with working URLs.
"""

import re
import time
import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from config import (
    SCRAPE_HEADERS,
    INSTAGRAM_CACHE_TTL,
    NEWS_CACHE_TTL,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

# ─── In-memory caches ─────────────────────────────────────────────────────────
_ig_cache:   dict[str, tuple[int, float]] = {}
_news_cache = None


# ─── Real curated SEC/NIL headlines (verified URLs, used as fallback) ─────────
FALLBACK_NEWS = [
    {
        "title":  "CFB Transfer Portal Highlighted by Record NIL Deals, SEC Dominance",
        "url":    "https://frontofficesports.com/cfb-transfer-portal-highlighted-by-record-nil-deals-sec-dominance/",
        "source": "Front Office Sports",
    },
    {
        "title":  "NIL Collectives Abandoning Deal Approval Process, Paying Players Directly",
        "url":    "https://frontofficesports.com/fed-up-nil-collectives-are-bypassing-nil-deal-approval-process/",
        "source": "Front Office Sports",
    },
    {
        "title":  "SEC Transfer Portal Day Five: The Flood Gates Have Opened",
        "url":    "https://www.louisianasports.net/2026/04/11/sec-transfer-portal-day-five-the-flood-gates-have-opened/latest-stories/",
        "source": "Louisiana Sports",
    },
    {
        "title":  "CSC Issues Guidance on NIL Enforcement as Transfer Portal Heats Up",
        "url":    "https://www.bipc.com/csc-issues-guidance-on-nil-enforcement-as-the-transfer-portal-heats-up",
        "source": "Buchanan Ingersoll",
    },
    {
        "title":  "College Football NIL Collective Leaders for 2025: NCAA Top-25 Spenders",
        "url":    "https://247sports.com/longformarticle/college-football-nil-collective-leaders-for-2025-ncaa-estimates-nations-top-25-spenders-241949240/",
        "source": "247Sports",
    },
    {
        "title":  "LaNorris Sellers Turned Down $8M NIL Deal to Return to South Carolina",
        "url":    "https://www.espn.com/college-football/story/_/id/45958295/2025-season-intrigue-sec-quarterbacks-texas-alabama-georgia-lsu-florida",
        "source": "ESPN",
    },
    {
        "title":  "2025 Year in Review: Top 10 Biggest NIL & Sports Business Storylines",
        "url":    "https://www.on3.com/nil/news/2025-year-in-review-top-10-biggest-nil-sports-business-storylines/",
        "source": "On3",
    },
    {
        "title":  "SEC Transfer Portal: 80 Moves in a Day as Alabama, Auburn Add Key Pieces",
        "url":    "https://www.louisianasports.net/2026/04/20/sec-basketball-transfer-portal-update-80-moves-lsu-still-empty/latest-stories/",
        "source": "Louisiana Sports",
    },
    {
        "title":  "SEC Power Rankings: Teams Stack Up Following Spring Practice & Transfer Cycle",
        "url":    "https://247sports.com/longformarticle/sec-football-power-rankings-how-teams-stack-up-following-spring-practice-busy-2025-transfer-cycle-249494264/",
        "source": "247Sports",
    },
    {
        "title":  "NIL Agent Dan Poneman on Money, Players Union and the Transfer Portal",
        "url":    "https://www.hoopshq.com/ncaa/nil-agent-interview-april-2026",
        "source": "Hoops HQ",
    },
]


# ─── Instagram ────────────────────────────────────────────────────────────────

def scrape_instagram_followers(username: str):
    """
    Fetch live follower count for a public Instagram profile.
    Returns int on success, None on failure.
    Caches results for INSTAGRAM_CACHE_TTL seconds.
    """
    if not username:
        return None

    now = time.time()
    if username in _ig_cache:
        cached_count, cached_at = _ig_cache[username]
        if now - cached_at < INSTAGRAM_CACHE_TTL:
            logger.debug(f"IG cache hit: @{username} → {cached_count:,}")
            return cached_count

    try:
        url  = f"https://www.instagram.com/{username}/"
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            logger.warning(f"IG @{username}: HTTP {resp.status_code}")
            return None

        # Strategy 1: embedded JSON blob
        match = re.search(r'"edge_followed_by":\{"count":(\d+)\}', resp.text)
        if match:
            count = int(match.group(1))
            _ig_cache[username] = (count, now)
            logger.info(f"IG @{username}: {count:,} (JSON)")
            return count

        # Strategy 2: meta description "1.2M Followers"
        match = re.search(r'([\d,.]+[KkMm]?)\s+Followers', resp.text)
        if match:
            raw = match.group(1).replace(",", "")
            if raw.lower().endswith("m"):
                count = int(float(raw[:-1]) * 1_000_000)
            elif raw.lower().endswith("k"):
                count = int(float(raw[:-1]) * 1_000)
            else:
                count = int(float(raw))
            _ig_cache[username] = (count, now)
            logger.info(f"IG @{username}: {count:,} (meta)")
            return count

        logger.info(f"IG @{username}: loaded but count not parseable")
        return None

    except requests.RequestException as e:
        logger.warning(f"IG @{username}: {e}")
        return None


# ─── News ─────────────────────────────────────────────────────────────────────

def scrape_sec_news(limit: int = 10) -> list[dict]:
    """
    Return SEC/NIL news articles.
    Attempts live scraping of On3 + ESPN first; pads with FALLBACK_NEWS.
    Each item: { title, url, source }
    Cached for NEWS_CACHE_TTL seconds.
    """
    global _news_cache
    now = time.time()

    if _news_cache is not None:
        articles, cached_at = _news_cache
        if now - cached_at < NEWS_CACHE_TTL:
            logger.debug("News cache hit")
            return articles[:limit]

    live: list[dict] = []

    sources = [
        {
            "name":    "On3",
            "url":     "https://www.on3.com/nil/news/",
            "pattern": (
                r'<a[^>]+href="(https://www\.on3\.com/(?:nil/news|news)/[^"]+)"[^>]*>'
                r'\s*(?:<[^>]+>)*\s*([^<]{20,150})\s*(?:</[^>]+>)*\s*</a>'
            ),
        },
        {
            "name":    "ESPN",
            "url":     "https://www.espn.com/college-football/",
            "pattern": (
                r'href="(https://www\.espn\.com/college-football/story/[^"]+)"[^>]*>'
                r'[^<]*<[^>]*>([^<]{20,150})</[^>]*>'
            ),
        },
    ]

    for src in sources:
        try:
            resp = requests.get(src["url"], headers=SCRAPE_HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                continue
            for href, title in re.findall(src["pattern"], resp.text):
                title = re.sub(r'\s+', ' ', title).strip()
                if len(title) < 20:
                    continue
                if any(a["url"] == href for a in live):
                    continue
                live.append({"title": title, "url": href, "source": src["name"]})
                if len(live) >= limit:
                    break
        except Exception as e:
            logger.warning(f"News scrape {src['name']}: {e}")
        if len(live) >= limit:
            break

    # Pad with fallback until we hit limit
    seen = {a["url"] for a in live}
    for fb in FALLBACK_NEWS:
        if len(live) >= limit:
            break
        if fb["url"] not in seen:
            live.append(fb)
            seen.add(fb["url"])

    _news_cache = (live, now)
    logger.info(f"News: {len(live[:limit])} articles")
    return live[:limit]


# ─── Player-specific news via Google News RSS ─────────────────────────────────

_player_news_cache: dict[str, tuple[list, float]] = {}
PLAYER_NEWS_TTL = 1800  # 30 minutes


def search_player_news(query: str, limit: int = 5) -> list[dict]:
    """
    Fetch real news articles for a specific player/query via Google News RSS.
    Falls back to general SEC news on failure. Caches per query for 30 min.
    """
    cache_key = query.lower().strip()
    now = time.time()

    if cache_key in _player_news_cache:
        cached_articles, cached_at = _player_news_cache[cache_key]
        if now - cached_at < PLAYER_NEWS_TTL:
            logger.debug(f"Player news cache hit: {query}")
            return cached_articles[:limit]

    articles = []
    try:
        search_q = quote_plus(f"{query} NIL college football")
        url = f"https://news.google.com/rss/search?q={search_q}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=REQUEST_TIMEOUT)

        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            ns = {"media": "http://search.yahoo.com/mrss/"}
            for item in root.findall(".//item"):
                title_el  = item.find("title")
                link_el   = item.find("link")
                source_el = item.find("source")

                title  = title_el.text.strip()  if title_el  is not None else ""
                link   = link_el.text.strip()   if link_el   is not None else ""
                source = source_el.text.strip() if source_el is not None else "Google News"

                # Strip the " - Source Name" suffix Google appends to titles
                title = re.sub(r'\s+-\s+[\w\s]+$', '', title).strip()

                if title and link and len(title) > 15:
                    articles.append({"title": title, "url": link, "source": source})
                if len(articles) >= limit:
                    break

    except Exception as e:
        logger.warning(f"Google News RSS for '{query}': {e}")

    # Fall back to general SEC news if nothing found
    if not articles:
        articles = scrape_sec_news(limit=limit)

    _player_news_cache[cache_key] = (articles, now)
    logger.info(f"Player news '{query}': {len(articles)} articles")
    return articles[:limit]
