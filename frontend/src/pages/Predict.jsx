import { useState } from 'react'
import { Field, Input, Select, FieldRow, SectionLabel, Divider } from '../components/Field'
import ResultPanel from '../components/ResultPanel'
import { useModelStatus, runPredict, computeBreakdown } from '../hooks/usePredict'

const DEFAULTS = {
  position: 'WR', class: 'JR',
  height_in: 73, weight_lb: 195,
  games_played: 30, follower_count: 125000,
  team_FPI: 15, program_tier: 3,
  season_pass_yards: 0,  career_pass_yards: 0,
  season_rec_yards: 850, career_rec_yards: 1400,
  season_rush_yards: 30, career_rush_yards: 60,
  season_scoring_td: 7,  career_scoring_td: 14,
  season_def_tackles: 0, career_def_tackles: 0,
  season_def_sacks: 0,   career_def_sacks: 0,
}

export default function Predict() {
  const modelStatus             = useModelStatus()
  const [form, setForm]         = useState(DEFAULTS)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const set    = (key, value) => setForm(f => ({ ...f, [key]: value }))
  const numSet = (key) => (e) => set(key, e.target.value === '' ? '' : Number(e.target.value))

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const data      = await runPredict(form)
      const breakdown = computeBreakdown(form)
      setResult({ ...data, breakdown })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const panelStyle = {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    padding: '2rem',
  }

  const panelTitleStyle = {
    fontFamily: 'var(--mono)', fontSize: '.65rem', fontWeight: 700,
    letterSpacing: '.2em', textTransform: 'uppercase', color: 'var(--muted)',
    paddingBottom: '.7rem', marginBottom: '1.6rem',
    borderBottom: '1px solid var(--border)',
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '3rem 6vw 6rem' }}>

      {/* Header */}
      <div style={{ marginBottom: '3rem', paddingBottom: '2rem', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '.62rem', letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '.7rem' }}>
          NIL Valuation Engine
        </div>
        <h1 style={{ fontFamily: 'var(--cond)', fontSize: 'clamp(2.2rem, 5vw, 3.5rem)', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.03em', color: '#fff', marginBottom: '.5rem' }}>
          Player Predictor
        </h1>
        <p style={{ fontSize: '.88rem', color: 'var(--text-dim)' }}>
          Fill in the athlete's metrics and click Generate Valuation.
        </p>
      </div>

      {/* Two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2.5rem', alignItems: 'start' }}>

        {/* Form */}
        <form onSubmit={handleSubmit} style={panelStyle}>
          <div style={panelTitleStyle}>Athlete Metrics</div>

          <FieldRow>
            <Field label="Position">
              <Select value={form.position} onChange={e => set('position', e.target.value)}>
                <optgroup label="Offense">
                  <option value="QB">QB</option>
                  <option value="WR">WR</option>
                  <option value="RB">RB</option>
                  <option value="TE">TE</option>
                  <option value="OL">OL</option>
                  <option value="OT">OT</option>
                </optgroup>
                <optgroup label="Defense">
                  <option value="DB">DB</option>
                  <option value="CB">CB</option>
                  <option value="S">S</option>
                  <option value="LB">LB</option>
                  <option value="DE">DE</option>
                  <option value="DT">DT</option>
                  <option value="EDGE">EDGE</option>
                </optgroup>
              </Select>
            </Field>
            <Field label="Class Year">
              <Select value={form.class} onChange={e => set('class', e.target.value)}>
                <option value="FR">Freshman</option>
                <option value="SO">Sophomore</option>
                <option value="JR">Junior</option>
                <option value="SR">Senior</option>
                <option value="GR">Grad</option>
              </Select>
            </Field>
          </FieldRow>

          <SectionLabel>Physical</SectionLabel>
          <FieldRow>
            <Field label="Height (inches)">
              <Input type="number" value={form.height_in} onChange={numSet('height_in')} min={60} max={84} />
            </Field>
            <Field label="Weight (lbs)">
              <Input type="number" value={form.weight_lb} onChange={numSet('weight_lb')} min={140} max={380} />
            </Field>
          </FieldRow>

          <SectionLabel>Program</SectionLabel>
          <FieldRow>
            <Field label="Team FPI">
              <Input type="number" value={form.team_FPI} onChange={numSet('team_FPI')} step={0.1} />
            </Field>
            <Field label="Program Tier (1–5)">
              <Input type="number" value={form.program_tier} onChange={numSet('program_tier')} min={1} max={5} />
            </Field>
          </FieldRow>

          <SectionLabel>Experience</SectionLabel>
          <Field label="Games Played (career)">
            <Input type="number" value={form.games_played} onChange={numSet('games_played')} min={0} max={60} />
          </Field>

          <SectionLabel>Social Media</SectionLabel>
          <Field label="Instagram Followers">
            <Input type="number" value={form.follower_count} onChange={numSet('follower_count')} min={0} />
          </Field>

          <Divider />

          <SectionLabel>Offensive Stats (0 if N/A)</SectionLabel>
          <FieldRow>
            <Field label="Season Pass Yards"><Input type="number" value={form.season_pass_yards} onChange={numSet('season_pass_yards')} min={0} /></Field>
            <Field label="Career Pass Yards"><Input type="number" value={form.career_pass_yards} onChange={numSet('career_pass_yards')} min={0} /></Field>
          </FieldRow>
          <FieldRow>
            <Field label="Season Rec Yards"><Input type="number" value={form.season_rec_yards} onChange={numSet('season_rec_yards')} min={0} /></Field>
            <Field label="Career Rec Yards"><Input type="number" value={form.career_rec_yards} onChange={numSet('career_rec_yards')} min={0} /></Field>
          </FieldRow>
          <FieldRow>
            <Field label="Season Rush Yards"><Input type="number" value={form.season_rush_yards} onChange={numSet('season_rush_yards')} min={0} /></Field>
            <Field label="Career Rush Yards"><Input type="number" value={form.career_rush_yards} onChange={numSet('career_rush_yards')} min={0} /></Field>
          </FieldRow>
          <FieldRow>
            <Field label="Season TDs"><Input type="number" value={form.season_scoring_td} onChange={numSet('season_scoring_td')} min={0} /></Field>
            <Field label="Career TDs"><Input type="number" value={form.career_scoring_td} onChange={numSet('career_scoring_td')} min={0} /></Field>
          </FieldRow>

          <SectionLabel>Defensive Stats (0 if N/A)</SectionLabel>
          <FieldRow>
            <Field label="Season Tackles"><Input type="number" value={form.season_def_tackles} onChange={numSet('season_def_tackles')} min={0} /></Field>
            <Field label="Career Tackles"><Input type="number" value={form.career_def_tackles} onChange={numSet('career_def_tackles')} min={0} /></Field>
          </FieldRow>
          <FieldRow>
            <Field label="Season Sacks"><Input type="number" value={form.season_def_sacks} onChange={numSet('season_def_sacks')} step={0.5} min={0} /></Field>
            <Field label="Career Sacks"><Input type="number" value={form.career_def_sacks} onChange={numSet('career_def_sacks')} step={0.5} min={0} /></Field>
          </FieldRow>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', marginTop: '1.5rem', padding: '1rem',
              background: loading ? '#2a1010' : 'var(--accent)',
              border: 'none', color: loading ? 'var(--dim)' : '#fff',
              fontFamily: 'var(--cond)', fontSize: '1rem', fontWeight: 800,
              letterSpacing: '.18em', textTransform: 'uppercase',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background .15s',
            }}
          >
            {loading ? 'Calculating…' : 'Generate Valuation'}
          </button>
        </form>

        {/* Results */}
        <ResultPanel result={result} loading={loading} error={error} modelStatus={modelStatus} />

      </div>
    </div>
  )
}
