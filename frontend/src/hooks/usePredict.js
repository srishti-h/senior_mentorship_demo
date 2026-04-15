import { useState, useEffect } from 'react'

const API = '/api'

export function useModelStatus() {
  const [status, setStatus] = useState({ online: false, cvR2: null, message: 'Checking model…' })

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(d => {
        if (d.model_loaded) {
          setStatus({ online: true, cvR2: d.cv_r2, message: 'Model ready' })
        } else {
          setStatus({ online: false, cvR2: null, message: 'Model not loaded' })
        }
      })
      .catch(err => {
        console.error('Health check failed:', err)
        setStatus({ online: false, cvR2: null, message: 'Backend offline' })
      })
  }, [])

  return status
}

export async function runPredict(payload) {
  const r = await fetch(`${API}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const d = await r.json()
  if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`)
  return d
}

export function computeBreakdown(payload) {
  const social = Math.log1p(payload.follower_count)
  const prog   = (payload.team_FPI / 30) * (6 - payload.program_tier) / 5
  const perf   = (
    payload.season_rec_yards   / 1000 + payload.career_rec_yards   / 2000 +
    payload.season_pass_yards  / 3000 + payload.career_pass_yards  / 6000 +
    payload.season_scoring_td  / 15   + payload.career_scoring_td  / 30   +
    payload.season_def_tackles / 50   + payload.career_def_tackles / 100  +
    payload.season_def_sacks   / 10   + payload.career_def_sacks   / 20
  )
  const phys  = Math.abs((payload.height_in - 72) / 6 + (payload.weight_lb - 220) / 80)
  const total = social + prog + perf + phys + 0.0001
  return {
    social: Math.round(social / total * 100),
    prog:   Math.round(prog   / total * 100),
    perf:   Math.round(perf   / total * 100),
    phys:   Math.round(phys   / total * 100),
  }
}
