/**
 * components/ResultPanel.jsx
 *
 * Two exported components:
 *
 * <PredictResult result={} loading={} error={} />
 *   Shows the NIL prediction output (value, CI band, R², position group).
 *
 * <PlayerDetail name={} onClose={} />
 *   Modal overlay showing full player profile including stats, IG count,
 *   performance bars, and a live-refresh button.
 */

import { usePlayerDetail } from "../hooks/usePredict";

// ─── Helpers ─────────────────────────────────────────────────────────────────
const POS_COLORS = {
  QB: "#e8353b", WR: "#3b82f6", RB: "#f59e0b", TE: "#8b5cf6",
  DB: "#06b6d4", LB: "#10b981", DL: "#f97316", OL: "#6b7280",
  CB: "#06b6d4", DE: "#f97316", EDGE: "#f97316",
};
const TEAM_COLORS = {
  "Alabama Crimson Tide":      "#9e1b32",
  "Auburn Tigers":             "#e87722",
  "Georgia Bulldogs":          "#ba0c2f",
  "LSU Tigers":                "#461d7c",
  "Texas Longhorns":           "#bf5700",
  "Florida Gators":            "#0021a5",
  "Tennessee Volunteers":      "#ff8200",
  "Oklahoma Sooners":          "#841617",
  "Texas A&M Aggies":          "#500000",
  "Ole Miss Rebels":           "#ce1126",
  "Mississippi State Bulldogs":"#660000",
  "Kentucky Wildcats":         "#0033a0",
  "Missouri Tigers":           "#f1b82d",
  "Arkansas Razorbacks":       "#9d2235",
  "South Carolina Gamecocks":  "#73000a",
  "Vanderbilt Commodores":     "#866d4b",
};

function posColor(pos)  { return POS_COLORS[pos]  || "#666"; }
function teamColor(team){ return TEAM_COLORS[team] || "#444"; }

function initials(name) {
  return name.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase();
}
function fmtNIL(v) {
  if (!v && v !== 0) return "N/A";
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${(v / 1000).toFixed(0)}K`;
}
function fmtFollowers(n) {
  if (!n) return "0";
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toLocaleString();
}
function fmtHeight(inches) {
  if (!inches) return "—";
  return `${Math.floor(inches / 12)}'${inches % 12}"`;
}


// ─── PredictResult ────────────────────────────────────────────────────────────
export function PredictResult({ result, loading, error }) {
  if (loading) {
    return (
      <div style={panelStyle}>
        <div style={{ textAlign: "center", padding: "32px", color: "var(--text3)" }}>
          <div style={{ fontSize: 13 }}>Running model…</div>
          <div className="skeleton" style={{ width: "60%", height: 36, margin: "16px auto 8px" }} />
          <div className="skeleton" style={{ width: "40%", height: 13, margin: "0 auto" }} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={panelStyle}>
        <div style={{ padding: "24px", textAlign: "center" }}>
          <div style={{ color: "var(--red)", fontWeight: 600, marginBottom: 6 }}>Prediction failed</div>
          <div style={{ fontSize: 12, color: "var(--text3)" }}>{error}</div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const { predicted_nil, ci_low, ci_high, cv_r2, pos_group } = result;

  return (
    <div style={panelStyle}>
      {/* NIL value */}
      <div style={{
        background:    "linear-gradient(135deg,rgba(232,53,59,.12),rgba(232,53,59,.04))",
        border:        "1px solid rgba(232,53,59,.2)",
        borderRadius:  "var(--r2)",
        padding:       "18px 20px",
        marginBottom:  16,
      }}>
        <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "1.2px", color: "var(--accent)", fontWeight: 600, marginBottom: 6 }}>
          Predicted NIL Value
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 38, fontWeight: 600 }}>
          {fmtNIL(predicted_nil)}
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text3)", marginTop: 4 }}>
          Range: {fmtNIL(ci_low)} – {fmtNIL(ci_high)}
        </div>
      </div>

      {/* Meta row */}
      <div style={{ display: "flex", gap: 10 }}>
        <div style={metaBox}>
          <span style={metaLabel}>Position Group</span>
          <span style={metaVal}>{pos_group}</span>
        </div>
        {cv_r2 != null && (
          <div style={metaBox}>
            <span style={metaLabel}>Model CV R²</span>
            <span style={metaVal}>{cv_r2.toFixed(3)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

const panelStyle = {
  background:   "var(--surface)",
  border:       "1px solid var(--border)",
  borderRadius: "var(--r2)",
  overflow:     "hidden",
};
const metaBox   = { flex: 1, background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: "var(--r)", padding: "10px 14px", display: "flex", flexDirection: "column", gap: 3 };
const metaLabel = { fontSize: 10, color: "var(--text3)", textTransform: "uppercase", letterSpacing: "1px", fontWeight: 600 };
const metaVal   = { fontFamily: "var(--font-mono)", fontSize: 15, fontWeight: 600 };


// ─── PlayerDetail ─────────────────────────────────────────────────────────────
export function PlayerDetail({ name, onClose }) {
  const { player, loading, error, refreshIG, igLoading } = usePlayerDetail(name);

  // Close on Escape
  // (handled in App.jsx via keydown listener so we don't duplicate)

  const tc = player ? teamColor(player.team) : "#444";
  const pc = player ? posColor(player.position) : "#666";

  return (
    <div className="detail-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="detail-panel">

        {/* ── Loading state ── */}
        {loading && (
          <div style={{ padding: "40px", textAlign: "center" }}>
            <div className="skeleton" style={{ width: 64, height: 64, borderRadius: "50%", margin: "0 auto 16px" }} />
            <div className="skeleton" style={{ width: "60%", height: 24, margin: "0 auto 8px" }} />
            <div className="skeleton" style={{ width: "40%", height: 13, margin: "0 auto" }} />
          </div>
        )}

        {/* ── Error state ── */}
        {error && !loading && (
          <div style={{ padding: "40px", textAlign: "center" }}>
            <div style={{ color: "var(--red)", fontWeight: 600 }}>{error}</div>
            <button className="btn-sm" onClick={onClose} style={{ margin: "16px auto 0", display: "flex" }}>Close</button>
          </div>
        )}

        {/* ── Player data ── */}
        {player && !loading && (
          <>
            {/* Header */}
            <div className="detail-header">
              <div className="detail-header-left">
                <div
                  className="detail-avatar"
                  style={{ background: `${tc}25`, border: `2px solid ${tc}60`, color: tc }}
                >
                  {initials(player.name)}
                </div>
                <div>
                  <div className="detail-name">{player.name}</div>
                  <div className="detail-meta">
                    <span style={{ color: pc, fontWeight: 700 }}>{player.position}</span>
                    &nbsp;·&nbsp;{player.team}
                    &nbsp;·&nbsp;{player.class || "—"}
                  </div>
                </div>
              </div>
              <button className="close-btn" onClick={onClose}>✕</button>
            </div>

            <div className="detail-body">
              {/* NIL valuation */}
              {player.nil_value && (
                <div className="detail-nil">
                  <div className="detail-nil-label">NIL Valuation</div>
                  <div className="detail-nil-value">{fmtNIL(player.nil_value)}</div>
                  <div className="detail-nil-range">
                    Est. range: {fmtNIL(Math.round(player.nil_value * 0.6))} – {fmtNIL(Math.round(player.nil_value * 1.7))}
                  </div>
                </div>
              )}

              {/* Instagram */}
              {player.instagram_user && (
                <div className="ig-section">
                  <div className="ig-left">
                    <span className="ig-section-label">Instagram</span>
                    <span className="ig-section-user">@{player.instagram_user}</span>
                    <span className="ig-section-count">{fmtFollowers(player.follower_count)}</span>
                    {player.follower_count_live && (
                      <span className="ig-live-label">● Live data</span>
                    )}
                  </div>
                  <button
                    className={`btn-sm${igLoading ? " loading" : ""}`}
                    onClick={refreshIG}
                    disabled={igLoading}
                  >
                    {igLoading ? "Loading…" : "↻ Refresh"}
                  </button>
                </div>
              )}

              {/* Stats grid */}
              <div className="stats-grid">
                <StatBox label="Team FPI"    value={player.team_FPI  || "—"} />
                <StatBox label="Team Rank"   value={player.team_RK   || "—"} />
                <StatBox label="Height"      value={fmtHeight(player.height_in)} />
                <StatBox label="Weight"      value={player.weight_lb ? `${player.weight_lb} lbs` : "—"} />
                <StatBox label="Games"       value={player.games_played || "—"} />
                <StatBox label="Engagement"  value={player.engagement_rate ? `${(player.engagement_rate * 100).toFixed(1)}%` : "—"} />
              </div>

              {/* Performance bars */}
              <PerfBars player={player} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatBox({ label, value }) {
  return (
    <div className="stat-box">
      <div className="stat-box-label">{label}</div>
      <div className="stat-box-value">{value}</div>
    </div>
  );
}

function PerfBars({ player }) {
  const bars = [
    player.season_pass_yards  && { label: "Pass Yds",  val: player.season_pass_yards,  max: 5000, color: "#e8353b" },
    player.season_rec_yards   && { label: "Rec Yds",   val: player.season_rec_yards,   max: 2000, color: "#3b82f6" },
    player.season_rush_yards  && { label: "Rush Yds",  val: player.season_rush_yards,  max: 2000, color: "#f59e0b" },
    player.season_scoring_td  && { label: "TDs",       val: player.season_scoring_td,  max: 50,   color: "#22c55e" },
    player.season_def_tackles && { label: "Tackles",   val: player.season_def_tackles, max: 150,  color: "#06b6d4" },
    player.season_def_sacks   && { label: "Sacks",     val: player.season_def_sacks,   max: 20,   color: "#a855f7" },
  ].filter(Boolean);

  if (!bars.length) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <div className="perf-section-label">Performance</div>
      {bars.map(({ label, val, max, color }) => (
        <div key={label} className="perf-bar-row">
          <span className="perf-bar-label">{label}</span>
          <div className="perf-bar-track">
            <div
              className="perf-bar-fill"
              style={{ width: `${Math.min(100, (val / max) * 100)}%`, background: color }}
            />
          </div>
          <span className="perf-bar-val">{val}</span>
        </div>
      ))}
    </div>
  );
}
