

import numpy as np
from flask import Blueprint, request, jsonify
from utils.features import engineer_features
from config import PREDICTION_SIGMA

predict_bp = Blueprint("predict", __name__)

_model  = None
_scaler = None
_meta   = {}


def init_predict(model, scaler, meta: dict):
    """Injected from app.py after model artifacts are loaded."""
    global _model, _scaler, _meta
    _model  = model
    _scaler = scaler
    _meta   = meta


@predict_bp.post("/predict")
def predict():
    if _model is None:
        return jsonify({"error": "Model not loaded — check backend/model_artifacts/"}), 503

    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON payload"}), 400

    try:
        X     = engineer_features(data, _meta)
        log_y = _model.predict(_scaler.transform(X))[0]
        pred  = float(np.exp(log_y))

        return jsonify({
            "predicted_nil": round(pred),
            "ci_low":        round(float(np.exp(log_y - PREDICTION_SIGMA))),
            "ci_high":       round(float(np.exp(log_y + PREDICTION_SIGMA))),
            "cv_r2":         _meta.get("best_cv_r2"),
            "pos_group":     _meta["pos_map"].get(data.get("position", "WR"), "SKILL"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
