"""
utils/features.py — Feature engineering pipeline for the NIL prediction model.
Called by routes/predict.py.
"""

import numpy as np
import pandas as pd


def engineer_features(p: dict, meta: dict) -> pd.DataFrame:
    """
    Build the full feature matrix (single row) from a raw player dict + model meta.
    Returns a pd.DataFrame with exactly the columns the model expects.
    """
    pos_map             = meta["pos_map"]
    class_map           = meta["class_map"]
    class_season_weight = meta["class_season_weight"]
    PERF_WEIGHTS        = meta["PERF_WEIGHTS"]
    PHYSICAL_WEIGHTS    = meta["PHYSICAL_WEIGHTS"]
    stat_pairs          = meta["stat_pairs"]
    pos_cols            = meta["pos_cols"]
    perf_cols           = meta["perf_cols"]
    all_features        = meta["all_features"]
    perf_stats_mean     = meta["perf_stats_mean"]
    perf_stats_std      = meta["perf_stats_std"]
    phys_stats_meta     = meta["phys_stats"]

    row = dict(p)
    pg               = pos_map.get(row.get("position", "WR"), "SKILL")
    row["pos_group"] = pg
    row["class_num"] = class_map.get(row.get("class", "JR"), 2)
    w                = class_season_weight.get(row.get("class", "JR"), 0.4)

    for new_col, s_col, c_col in stat_pairs:
        row[new_col] = (
            w * float(row.get(s_col, 0) or 0)
            + (1 - w) * float(row.get(c_col, 0) or 0)
        )

    mask_qb    = pg == "QB"
    mask_skill = pg == "SKILL"
    mask_ol    = pg == "OL"
    mask_def   = pg in ["DEF_BACK", "LB", "DL"]

    if not mask_qb:                     row["pass_yards"]  = 0
    if not mask_skill and not mask_qb:  row["rec_yards"]   = 0
    if mask_ol or mask_def:             row["rush_yards"]  = 0
    if mask_ol or mask_def:             row["scoring_td"]  = 0
    if not mask_def:                    row["def_tackles"] = 0
    if not mask_def:                    row["def_sacks"]   = 0

    for col in ["height_in", "weight_lb"]:
        mu  = phys_stats_meta[col]["mean"].get(pg, 0)
        sig = phys_stats_meta[col]["std"].get(pg, 1)
        row[f"{col}_zscore"] = (float(row.get(col, 0)) - mu) / sig if sig > 0 else 0

    weights  = PERF_WEIGHTS.get(pg, {})
    perf_raw = sum(w2 * float(row.get(c, 0) or 0) for c, w2 in weights.items())
    row["perf_score_raw"] = perf_raw
    pm = perf_stats_mean.get(pg, 0)
    ps = perf_stats_std.get(pg, 1)
    row["perf_score"] = (perf_raw - pm) / ps if ps > 0 else 0.0

    pw = PHYSICAL_WEIGHTS.get(pg, {"height": 0.5, "weight": 0.5})
    row["phys_score"] = (
        pw["height"] * row["height_in_zscore"]
        + pw["weight"] * row["weight_lb_zscore"]
    )

    fc = float(str(row.get("follower_count", 0)).replace(",", "") or 0)
    gp = max(float(row.get("games_played", 1) or 1), 1)
    row["log_followers"]      = np.log1p(fc)
    row["log_followers_sq"]   = np.log1p(fc) ** 2
    row["followers_per_game"] = np.log1p(fc / gp)
    row["elite_program"]      = float(
        (float(row.get("program_tier", 5) or 5) <= 3)
        and (float(row.get("team_FPI", 0) or 0) >= 10)
    )
    row["brand_signal"]  = (
        row["log_followers"]
        * row["elite_program"]
        * (max(row["perf_score"], 0) + 1)
    )
    row["games_x_QB"]    = gp * float(pg == "QB")
    row["games_x_SKILL"] = gp * float(pg == "SKILL")
    row["games_x_DL"]    = gp * float(pg == "DL")

    team_nil_mean   = meta.get("team_nil_mean", {})
    global_nil_mean = meta.get("global_nil_mean", 12.0)
    row["team_nil_mean"] = team_nil_mean.get(row.get("team", ""), global_nil_mean)

    for pc in pos_cols:
        row[pc] = 1.0 if pc == f"pos_{pg}" else 0.0
        row[f"log_followers_x_{pc}"] = row["log_followers"] * row[pc]

    for stat in perf_cols:
        for pc in pos_cols:
            row[f"{stat}_x_{pc}"] = float(row.get(stat, 0)) * row[pc]

    return pd.DataFrame([row])[all_features].fillna(0)
