import { useState, useEffect, useCallback } from "react";
import { usePlayerList, useNews, usePredict } from "./hooks/usePredict";
import { PlayerDetail, PredictResult } from "./components/ResultPanel";
import Field from "./components/Field";

// ─── Constants ────────────────────────────────────────────────────────────────
const PAGE_SIZE = 24;
const POSITIONS = ["ALL", "QB", "WR", "RB", "TE", "DB", "LB", "DL", "OL"];

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

function posColor(pos)   { return POS_COLORS[pos]   || "#666"; }
function teamColor(team) { return TEAM_COLORS[team]  || "#444"; }
function initials(name)  { return name.split(" ").slice(0,2).map(w=>w[0]).join("").toUpperCase(); }

function fmtNIL(v) {
  if (!v) return "N/A";
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  return `$${(v/1000).toFixed(0)}K`;
}
function fmtFollowers(n) {
  if (!n) return "0";
  if (n >= 1e6) return `${(n/1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n/1e3).toFixed(1)}K`;
  return n.toLocaleString();
}

// ─── Predict form default state ───────────────────────────────────────────────
const PREDICT_DEFAULTS = {
  name: "", team: "", position: "WR", class: "JR",
  height_in: "", weight_lb: "", games_played: "",
  follower_count: "", instagram_user: "", engagement_rate: "",
  team_FPI: "", team_RK: "", program_tier: "3",
  season_pass_yards: "0", career_pass_yards: "0",
  season_rec_yards: "0", career_rec_yards: "0",
  season_rush_yards: "0", career_rush_yards: "0",
  season_scoring_td: "0", career_scoring_td: "0",
  season_def_tackles: "0", career_def_tackles: "0",
  season_def_sacks: "0", career_def_sacks: "0",
};

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [searchInput, setSearchInput] = useState("");
  const [query,       setQuery]       = useState("");
  const [position,    setPosition]    = useState("ALL");
  const [detailName,  setDetailName]  = useState(null);
  const [predictOpen, setPredictOpen] = useState(false);
  const [predictForm, setPredictForm] = useState(PREDICT_DEFAULTS);

  const { players, total, loading, error, page, setPage } =
    usePlayerList({ query, position, pageSize: PAGE_SIZE });

  const { predict, result: predictResult, loading: predictLoading, error: predictError } = usePredict();

  const { articles } = useNews(10);

  // Escape closes any open overlay
  useEffect(() => {
    const handler = (e) => {
      if (e.key !== "Escape") return;
      if (detailName) setDetailName(null);
      else if (predictOpen) setPredictOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [detailName, predictOpen]);

  const handleSearch = useCallback(() => {
    setQuery(searchInput.trim());
  }, [searchInput]);

  const handlePredictField = useCallback((name, value) => {
    setPredictForm((prev) => ({ ...prev, [name]: value }));
  }, []);

  const handlePredictSubmit = (e) => {
    e.preventDefault();
    // coerce numeric strings to numbers
    const payload = {};
    for (const [k, v] of Object.entries(predictForm)) {
      const n = parseFloat(v);
      payload[k] = isNaN(n) ? v : n;
    }
    predict(payload);
  };

  // Stats
  const withNil = players.filter((p) => p.nil_value);
  const avgNIL  = withNil.length
    ? withNil.reduce((s, p) => s + p.nil_value, 0) / withNil.length
    : 0;
  const topNIL  = withNil.reduce((m, p) => Math.max(m, p.nil_value), 0);
  const igCount = players.filter((p) => p.instagram_user).length;

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <>
      {/* ── Breaking Ticker ── */}
      <BreakingTicker articles={articles} />

      {/* ── Header ── */}
      <header className="header">
        <div className="logo">
          SEC<span className="logo-accent">NIL</span>
          <span className="logo-badge">INTELLIGENCE</span>
        </div>

        <div className="search-wrapper">
          <input
            className="search-input"
            type="text"
            placeholder="Search athletes, schools, positions…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            autoComplete="off"
          />
          <button className="btn" onClick={handleSearch}>SEARCH</button>
        </div>

        <button
          className="btn"
          style={{ background: "var(--surface2)", border: "1px solid var(--border2)", color: "var(--text2)", fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 600, letterSpacing: ".5px" }}
          onClick={() => setPredictOpen(true)}
        >
          ⚡ Predict NIL
        </button>
      </header>

      {/* ── Filter Bar ── */}
      <div className="filter-bar">
        <span className="filter-label">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          POSITION:
        </span>
        {POSITIONS.map((pos) => (
          <button
            key={pos}
            className={`filter-btn${position === pos ? " active" : ""}`}
            onClick={() => setPosition(pos)}
          >
            {pos}
          </button>
        ))}
      </div>

      {/* ── Main ── */}
      <main className="main">

        {/* Stats bar */}
        <div className="stats-bar">
          <div className="stat-pill"><span className="stat-pill-label">Total Athletes</span><span className="stat-pill-value">{total}</span></div>
          <div className="stat-pill"><span className="stat-pill-label">Avg NIL Value</span><span className="stat-pill-value">{fmtNIL(avgNIL)}</span></div>
          <div className="stat-pill"><span className="stat-pill-label">Top Valuation</span><span className="stat-pill-value">{fmtNIL(topNIL)}</span></div>
          <div className="stat-pill"><span className="stat-pill-label">Live IG Profiles</span><span className="stat-pill-value">{igCount}</span></div>
        </div>

        {/* Grid header */}
        <div className="grid-header">
          <span className="grid-title">ATHLETE VALUATIONS</span>
          <span className="grid-count">{total} athlete{total !== 1 ? "s" : ""}</span>
        </div>

        {/* Error banner */}
        {error && (
          <div style={{ gridColumn: "1/-1", background: "rgba(239,68,68,.1)", border: "1px solid rgba(239,68,68,.3)", borderRadius: "var(--r)", padding: "14px 18px", marginBottom: 16, color: "var(--red)", fontSize: 13 }}>
            Could not reach the API. Make sure Flask is running on port 8000.
          </div>
        )}

        {/* Player grid */}
        <div className="player-grid">
          {loading
            ? Array(PAGE_SIZE).fill(0).map((_, i) => <SkeletonCard key={i} />)
            : players.length
              ? players.map((p) => (
                  <PlayerCard key={`${p.name}-${p.team}`} player={p} onClick={() => setDetailName(p.name)} />
                ))
              : (
                <div className="empty-state">
                  <h3>NO ATHLETES FOUND</h3>
                  <p>Try adjusting your search or filter</p>
                </div>
              )
          }
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <Pagination page={page} totalPages={totalPages} onPage={setPage} />
        )}
      </main>

      {/* ── Player Detail Modal ── */}
      {detailName && (
        <PlayerDetail name={detailName} onClose={() => setDetailName(null)} />
      )}

      {/* ── Predict Drawer ── */}
      {predictOpen && (
        <PredictDrawer
          form={predictForm}
          onChange={handlePredictField}
          onSubmit={handlePredictSubmit}
          onClose={() => setPredictOpen(false)}
          loading={predictLoading}
          result={predictResult}
          error={predictError}
        />
      )}
    </>
  );
}

// ─── BreakingTicker ───────────────────────────────────────────────────────────
function BreakingTicker({ articles }) {
  if (!articles.length) return null;
  const doubled = [...articles, ...articles]; // seamless loop
  return (
    <div className="ticker-bar">
      <div className="ticker-label">BREAKING</div>
      <div className="ticker-scroll">
        <div className="ticker-track">
          {doubled.map((a, i) => (
            <span key={i} className="ticker-item">
              <a href={a.url} target="_blank" rel="noopener noreferrer">{a.title}</a>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── PlayerCard ───────────────────────────────────────────────────────────────
function PlayerCard({ player: p, onClick }) {
  const tc    = teamColor(p.team);
  const pc    = posColor(p.position);
  const nil   = fmtNIL(p.nil_value);
  const hasIG = !!p.instagram_user;

  // Deterministic pseudo-trend from name hash
  const hash  = p.name.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const trends = ["up", "down", "flat"];
  const trend  = trends[hash % 3];
  const tIcon  = trend === "up" ? "▲" : trend === "down" ? "▼" : "→";
  const tPct   = ((hash % 180) / 10 + 1).toFixed(1);

  return (
    <div className="player-card" onClick={onClick}>
      <div className="card-top">
        <div
          className="avatar"
          style={{ background: `${tc}20`, border: `2px solid ${tc}40`, color: tc }}
        >
          {initials(p.name)}
        </div>
        <span
          className="pos-badge"
          style={{ background: `${pc}22`, color: pc }}
        >
          {p.position}
        </span>
      </div>

      <div className="player-name">{p.name}</div>
      <div className="player-team">{p.team}</div>

      {p.follower_count > 0 && (
        <div className="ig-row">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ opacity: .5 }}>
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
          </svg>
          <span className="ig-count">{fmtFollowers(p.follower_count)}</span>
          {hasIG && <div className="ig-live-dot" />}
        </div>
      )}

      <div className="card-valuation">
        <div className="val-label">VALUATION</div>
        <div>
          <span className="val-amount">{nil}</span>
          {nil !== "N/A" && (
            <span className={`val-trend ${trend}`}>{tIcon} {tPct}%</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── SkeletonCard ─────────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton" style={{ width: 44, height: 44, borderRadius: "50%" }} />
      <div className="skeleton" style={{ width: "70%", height: 14 }} />
      <div className="skeleton" style={{ width: "45%", height: 11 }} />
      <div style={{ marginTop: "auto" }}>
        <div className="skeleton" style={{ width: "55%", height: 20 }} />
      </div>
    </div>
  );
}

// ─── Pagination ───────────────────────────────────────────────────────────────
function Pagination({ page, totalPages, onPage }) {
  const pages = [];
  for (let i = 0; i < totalPages; i++) {
    const dist = Math.abs(i - page);
    if (i < 2 || i >= totalPages - 2 || dist <= 1) {
      pages.push(i);
    } else if (dist === 2) {
      pages.push("…");
    }
  }
  // Deduplicate consecutive ellipses
  const deduped = pages.filter((p, i) => !(p === "…" && pages[i - 1] === "…"));

  return (
    <div className="pagination">
      <button className="page-btn" disabled={page === 0} onClick={() => onPage(page - 1)}>← Prev</button>
      {deduped.map((p, i) =>
        p === "…"
          ? <span key={`e${i}`} className="page-ellipsis">…</span>
          : <button key={p} className={`page-btn${p === page ? " active" : ""}`} onClick={() => onPage(p)}>{p + 1}</button>
      )}
      <button className="page-btn" disabled={page >= totalPages - 1} onClick={() => onPage(page + 1)}>Next →</button>
    </div>
  );
}

// ─── PredictDrawer ────────────────────────────────────────────────────────────
function PredictDrawer({ form, onChange, onSubmit, onClose, loading, result, error }) {
  const posOptions   = ["QB","WR","RB","TE","DB","LB","DL","OL","CB","DE","EDGE"].map(p=>({value:p,label:p}));
  const classOptions = ["FR","SO","JR","SR","GR"].map(c=>({value:c,label:c}));
  const tierOptions  = [1,2,3,4,5].map(n=>({value:String(n),label:`Tier ${n}`}));

  return (
    <div className="detail-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="detail-panel" style={{ width: 620 }}>
        {/* Header */}
        <div className="detail-header" style={{ borderBottom: "1px solid var(--border)", paddingBottom: 18, marginBottom: 0 }}>
          <div>
            <div className="detail-name" style={{ fontSize: 22 }}>⚡ NIL Predictor</div>
            <div className="detail-meta">Enter player details to generate a valuation estimate</div>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="detail-body" style={{ maxHeight: "70vh", overflowY: "auto" }}>
          <form onSubmit={onSubmit}>
            {/* Identity */}
            <SectionLabel>Identity</SectionLabel>
            <div style={formGrid(3)}>
              <Field label="Name"     name="name"     value={form.name}     onChange={onChange} placeholder="e.g. Ryan Williams" />
              <Field label="Team"     name="team"     value={form.team}     onChange={onChange} placeholder="e.g. Alabama Crimson Tide" />
              <Field label="Position" name="position" value={form.position} onChange={onChange} type="select" options={posOptions} />
            </div>
            <div style={{ ...formGrid(3), marginTop: 10 }}>
              <Field label="Class"        name="class"        value={form.class}        onChange={onChange} type="select" options={classOptions} />
              <Field label="Program Tier" name="program_tier" value={form.program_tier} onChange={onChange} type="select" options={tierOptions} hint="1=elite, 5=lower" />
              <Field label="Games Played" name="games_played" value={form.games_played} onChange={onChange} type="number" placeholder="0" />
            </div>

            {/* Physical */}
            <SectionLabel>Physical</SectionLabel>
            <div style={formGrid(3)}>
              <Field label="Height (in)"  name="height_in"  value={form.height_in}  onChange={onChange} type="number" placeholder="72" />
              <Field label="Weight (lbs)" name="weight_lb"  value={form.weight_lb}  onChange={onChange} type="number" placeholder="190" />
              <Field label="Team FPI"     name="team_FPI"   value={form.team_FPI}   onChange={onChange} type="number" placeholder="15.0" />
            </div>

            {/* Social */}
            <SectionLabel>Social</SectionLabel>
            <div style={formGrid(3)}>
              <Field label="Instagram User"   name="instagram_user"  value={form.instagram_user}  onChange={onChange} placeholder="username" />
              <Field label="Follower Count"   name="follower_count"  value={form.follower_count}  onChange={onChange} type="number" placeholder="50000" />
              <Field label="Engagement Rate"  name="engagement_rate" value={form.engagement_rate} onChange={onChange} type="number" placeholder="0.05" hint="e.g. 0.05 = 5%" />
            </div>

            {/* Performance */}
            <SectionLabel>Season Stats</SectionLabel>
            <div style={formGrid(3)}>
              <Field label="Pass Yds (season)"  name="season_pass_yards"  value={form.season_pass_yards}  onChange={onChange} type="number" />
              <Field label="Rec Yds (season)"   name="season_rec_yards"   value={form.season_rec_yards}   onChange={onChange} type="number" />
              <Field label="Rush Yds (season)"  name="season_rush_yards"  value={form.season_rush_yards}  onChange={onChange} type="number" />
              <Field label="TDs (season)"       name="season_scoring_td"  value={form.season_scoring_td}  onChange={onChange} type="number" />
              <Field label="Tackles (season)"   name="season_def_tackles" value={form.season_def_tackles} onChange={onChange} type="number" />
              <Field label="Sacks (season)"     name="season_def_sacks"   value={form.season_def_sacks}   onChange={onChange} type="number" />
            </div>

            <SectionLabel>Career Stats</SectionLabel>
            <div style={formGrid(3)}>
              <Field label="Pass Yds (career)"  name="career_pass_yards"  value={form.career_pass_yards}  onChange={onChange} type="number" />
              <Field label="Rec Yds (career)"   name="career_rec_yards"   value={form.career_rec_yards}   onChange={onChange} type="number" />
              <Field label="Rush Yds (career)"  name="career_rush_yards"  value={form.career_rush_yards}  onChange={onChange} type="number" />
              <Field label="TDs (career)"       name="career_scoring_td"  value={form.career_scoring_td}  onChange={onChange} type="number" />
              <Field label="Tackles (career)"   name="career_def_tackles" value={form.career_def_tackles} onChange={onChange} type="number" />
              <Field label="Sacks (career)"     name="career_def_sacks"   value={form.career_def_sacks}   onChange={onChange} type="number" />
            </div>

            <button
              type="submit"
              className="btn"
              disabled={loading}
              style={{ width: "100%", marginTop: 20, fontSize: 16, letterSpacing: 2 }}
            >
              {loading ? "RUNNING MODEL…" : "⚡ PREDICT NIL VALUE"}
            </button>
          </form>

          {/* Result */}
          {(predictResult => predictResult || loading || error)(result) && (
            <div style={{ marginTop: 20 }}>
              <PredictResult result={result} loading={loading} error={error} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontSize: 10, fontWeight: 700, letterSpacing: "1.2px",
      textTransform: "uppercase", color: "var(--text3)",
      margin: "18px 0 10px", borderBottom: "1px solid var(--border)",
      paddingBottom: 6,
    }}>
      {children}
    </div>
  );
}

function formGrid(cols) {
  return { display: "grid", gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 10 };
}
