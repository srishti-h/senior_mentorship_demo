"""
routes/news.py

GET /news         SEC/NIL general headlines for the breaking ticker.
GET /news?q=name  Player-specific news via Google News RSS.
"""

from flask import Blueprint, request, jsonify
from utils.scraper import scrape_sec_news, search_player_news

news_bp = Blueprint("news", __name__)


@news_bp.get("/news")
def get_news():
    limit = min(int(request.args.get("limit", 10)), 20)
    q     = request.args.get("q", "").strip()
    if q:
        articles = search_player_news(q, limit=limit)
    else:
        articles = scrape_sec_news(limit=limit)
    return jsonify({"count": len(articles), "articles": articles})
