"""
routes/news.py

GET /news   SEC/NIL news headlines for the breaking ticker.
"""

from flask import Blueprint, request, jsonify
from utils.scraper import scrape_sec_news

news_bp = Blueprint("news", __name__)


@news_bp.get("/news")
def get_news():
    limit    = min(int(request.args.get("limit", 10)), 20)
    articles = scrape_sec_news(limit=limit)
    return jsonify({"count": len(articles), "articles": articles})
