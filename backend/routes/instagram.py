"""
routes/instagram.py

GET /instagram/<username>   Live follower count for any public IG profile.
"""

from flask import Blueprint, jsonify
from utils.scraper import scrape_instagram_followers

instagram_bp = Blueprint("instagram", __name__)


@instagram_bp.get("/instagram/<username>")
def get_followers(username: str):
    count = scrape_instagram_followers(username)
    if count is None:
        return jsonify({
            "error":    "Could not fetch — profile may be private or rate-limited",
            "username": username,
        }), 404
    return jsonify({"username": username, "followers": count})
