/**
 * hooks/usePredict.js
 *
 * Custom hooks that talk to the Flask backend.
 *
 * usePlayerList  — paginated player list with search + position filter
 * usePlayerDetail — single player detail with optional live IG refresh
 * usePredict     — POST /predict NIL valuation
 * useNews        — GET /news breaking ticker headlines
 */

import { useState, useEffect, useCallback, useRef } from "react";

// Vite proxies /api → http://localhost:8000  (see vite.config.js)
const BASE = "/api";

// ─── Generic fetcher ─────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ─── usePlayerList ────────────────────────────────────────────────────────────
/**
 * Fetches the paginated player list.
 * Returns { players, total, loading, error, page, setPage }
 */
export function usePlayerList({ query = "", position = "ALL", pageSize = 24 } = {}) {
  const [players, setPlayers] = useState([]);
  const [total,   setTotal]   = useState(0);
  const [page,    setPage]    = useState(0);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  // Reset to page 0 whenever filters change
  const prevFilters = useRef({ query, position });
  useEffect(() => {
    if (
      prevFilters.current.query    !== query ||
      prevFilters.current.position !== position
    ) {
      prevFilters.current = { query, position };
      setPage(0);
    }
  }, [query, position]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams({
      limit:  pageSize,
      offset: page * pageSize,
    });
    if (query)              params.set("q", query);
    if (position !== "ALL") params.set("position", position);

    apiFetch(`/players?${params}`)
      .then((data) => {
        if (cancelled) return;
        setPlayers(data.players);
        setTotal(data.total);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [query, position, page, pageSize]);

  return { players, total, loading, error, page, setPage };
}

// ─── usePlayerDetail ──────────────────────────────────────────────────────────
/**
 * Fetches a single player by name.
 * Optionally refreshes the live Instagram follower count.
 * Returns { player, loading, error, refreshIG, igLoading }
 */
export function usePlayerDetail(name) {
  const [player,    setPlayer]    = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);
  const [igLoading, setIgLoading] = useState(false);

  useEffect(() => {
    if (!name) { setPlayer(null); return; }

    let cancelled = false;
    setLoading(true);
    setError(null);

    apiFetch(`/players/${encodeURIComponent(name)}?refresh_ig=true`)
      .then((data) => { if (!cancelled) setPlayer(data); })
      .catch((err)  => { if (!cancelled) setError(err.message); })
      .finally(()   => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [name]);

  const refreshIG = useCallback(async () => {
    if (!player?.instagram_user) return;
    setIgLoading(true);
    try {
      const data = await apiFetch(`/instagram/${player.instagram_user}`);
      setPlayer((prev) => ({ ...prev, follower_count: data.followers, follower_count_live: true }));
    } catch {
      // silently fail — stale count stays displayed
    } finally {
      setIgLoading(false);
    }
  }, [player]);

  return { player, loading, error, refreshIG, igLoading };
}

// ─── usePredict ───────────────────────────────────────────────────────────────
/**
 * Sends a player dict to POST /predict.
 * Returns { predict, result, loading, error }
 * Call predict(playerData) to trigger a prediction.
 */
export function usePredict() {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const predict = useCallback(async (playerData) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiFetch("/predict", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(playerData),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { predict, result, loading, error };
}

// ─── useNews ──────────────────────────────────────────────────────────────────
/**
 * Fetches SEC/NIL news for the breaking ticker.
 * Returns { articles, loading }
 */
export function useNews(limit = 10) {
  const [articles, setArticles] = useState([]);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    apiFetch(`/news?limit=${limit}`)
      .then((data) => setArticles(data.articles || []))
      .catch(() => setArticles([]))
      .finally(() => setLoading(false));
  }, [limit]);

  return { articles, loading };
}
