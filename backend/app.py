

import json
import logging
import os
import sys

# Allow  `python app.py`  from inside backend/  AND
#        `python backend/app.py`  from project root
# by ensuring the backend directory is on sys.path.
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

import joblib
from flask import Flask, jsonify, render_template
from flask_cors import CORS

from config import ARTIFACTS_DIR, HOST, PORT, DEBUG
from routes.players   import players_bp
from routes.instagram import instagram_bp
from routes.news      import news_bp
from routes.predict   import predict_bp, init_predict
from routes.history   import history_bp
from utils.data_loader    import load_players
from utils.history_loader import load_history

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── App ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

# ─── Register blueprints ──────────────────────────────────────────────────────
app.register_blueprint(players_bp)
app.register_blueprint(instagram_bp)
app.register_blueprint(news_bp)
app.register_blueprint(predict_bp)
app.register_blueprint(history_bp)

# ─── Load model artifacts ─────────────────────────────────────────────────────
def _load_model():
    try:
        model  = joblib.load(os.path.join(ARTIFACTS_DIR, "nil_model.pkl"))
        scaler = joblib.load(os.path.join(ARTIFACTS_DIR, "scaler.pkl"))
        with open(os.path.join(ARTIFACTS_DIR, "meta.json")) as f:
            meta = json.load(f)
        init_predict(model, scaler, meta)
        logger.info(f"Model loaded — CV R² = {meta.get('best_cv_r2', 'n/a'):.4f}")
    except Exception as e:
        logger.warning(f"Model not loaded: {e}  →  /predict will return 503")

# ─── Frontend ─────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    return render_template("index.html")

# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    from routes.predict import _model, _meta
    return jsonify({
        "status":         "ok",
        "model_loaded":   _model is not None,
        "cv_r2":          _meta.get("best_cv_r2") if _model else None,
        "players_loaded": len(load_players()),
    })

# ─── Startup (runs for both gunicorn and direct python app.py) ───────────────
load_players()
_load_model()
load_history()   # no-op if sec_history.csv not yet generated

# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"Server → http://localhost:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
