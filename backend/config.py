"""
config.py — Central configuration for the NIL platform backend.

Directory layout expected:
  SENIOR_MENTORSHIP_DEMO/
  ├── backend/
  │   ├── app.py               ← entry point (run from here)
  │   ├── config.py            ← this file
  │   ├── model_artifacts/
  │   ├── routes/
  │   └── utils/
  ├── frontend/
  └── sec_final_training_data.csv
"""
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
# __file__ = backend/config.py  →  BACKEND_DIR = backend/  →  ROOT = project root
BACKEND_DIR   = os.path.dirname(__file__)
ROOT_DIR      = os.path.dirname(BACKEND_DIR)

ARTIFACTS_DIR    = os.path.join(BACKEND_DIR, "model_artifacts")
CSV_PATH         = os.path.join(ROOT_DIR,    "sec_final_training_data.csv")
HISTORY_CSV_PATH = os.path.join(ROOT_DIR,    "sec_history.csv")

# ─── Server ───────────────────────────────────────────────────────────────────
HOST  = "0.0.0.0"
PORT  = int(os.environ.get("PORT", 8000))
DEBUG = False

# ─── Scraping ─────────────────────────────────────────────────────────────────
INSTAGRAM_CACHE_TTL = 3600   # seconds — 1 hour
NEWS_CACHE_TTL      = 900    # seconds — 15 minutes
REQUEST_TIMEOUT     = 8      # seconds

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ─── NIL Model ────────────────────────────────────────────────────────────────
PREDICTION_SIGMA = 0.55   # log-space uncertainty used for CI bands
