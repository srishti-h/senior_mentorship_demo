import { Link } from 'react-router-dom'
import { useModelStatus } from '../hooks/usePredict'

const STATS = [
  { value: '220+', label: 'SEC Players Analyzed' },
  { value: '0.53', label: 'CV R² Accuracy' },
  { value: '6',    label: 'Position Groups' },
  { value: '40+',  label: 'Model Features' },
]

const STEPS = [
  { num: '01', title: 'Enter Athlete Metrics', body: 'Input position, class year, physical attributes, program info, social following, and on-field stats.' },
  { num: '02', title: 'Model Runs Inference', body: 'A linear regression model trained on SEC comparables applies 40+ engineered features to generate a valuation.' },
  { num: '03', title: 'Get Fair Market Value', body: 'Receive a dollar estimate with confidence interval and a breakdown of which factors drive the number.' },
]

const FEATURES = [
  { title: 'Social Reach',        desc: 'Instagram follower count with diminishing-returns curve and per-game efficiency weighting.' },
  { title: 'Program Premium',     desc: 'Team FPI, program tier, and a team NIL mean feature that captures brand floor beyond raw rankings.' },
  { title: 'On-Field Performance',desc: 'Position-specific weighted stats — pass yards for QBs, tackles for DBs — blended across season and career.' },
  { title: 'Physical Profile',    desc: 'Height and weight z-scored within position group, so a 6\'5" OL and a 6\'5" WR are evaluated differently.' },
  { title: 'Experience',          desc: 'Games played and class year, including position-interacted versions that weight experience differently by role.' },
  { title: 'Brand Signal',        desc: 'A composite of elite program × followers × performance that identifies the rare $2M+ NIL tier.' },
]

export default function Home() {
  const modelStatus = useModelStatus()

  return (
    <div style={{ overflowX: 'hidden' }}>

      {/* Hero */}
      <section style={{
        minHeight: 'calc(100vh - 56px)',
        display: 'grid', gridTemplateColumns: '1fr 1fr', alignItems: 'center',
        gap: '4rem', padding: '5rem 6vw',
        borderBottom: '1px solid var(--border)',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 50% at 80% 50%, rgba(230,57,70,.06) 0%, transparent 70%)', pointerEvents: 'none' }} />

        <div style={{ position: 'relative' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '.65rem', letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '1.5rem' }}>
            SEC Analytics · NIL Valuation Engine
          </div>
          <h1 style={{ fontFamily: 'var(--cond)', fontSize: 'clamp(3.5rem, 7vw, 6.5rem)', fontWeight: 900, lineHeight: .95, letterSpacing: '.02em', textTransform: 'uppercase', color: '#fff', marginBottom: '1.8rem' }}>
            What is an<br />
            <span style={{ color: 'var(--accent)' }}>SEC athlete</span><br />
            worth?
          </h1>
          <p style={{ fontSize: '.95rem', color: 'var(--text-dim)', maxWidth: '440px', lineHeight: 1.7, marginBottom: '2.5rem' }}>
            A machine-learning model trained on real SEC NIL comparables. Input athlete metrics and get an instant fair-market valuation with position-specific performance weighting.
          </p>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '2rem' }}>
            <Link to="/predict" style={{ display: 'inline-block', padding: '.8rem 2rem', background: 'var(--accent)', color: '#fff', fontFamily: 'var(--cond)', fontSize: '.9rem', fontWeight: 800, letterSpacing: '.15em', textTransform: 'uppercase' }}>
              Run a Prediction
            </Link>
            <a href="#how" style={{ fontFamily: 'var(--mono)', fontSize: '.7rem', letterSpacing: '.15em', textTransform: 'uppercase', color: 'var(--muted)', borderBottom: '1px solid var(--border2)', paddingBottom: '2px' }}>
              How it works
            </a>
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '.5rem', padding: '.4rem .8rem', border: `1px solid ${modelStatus.online ? 'rgba(46,204,113,.3)' : 'var(--border2)'}`, background: 'var(--surface)', fontFamily: 'var(--mono)', fontSize: '.65rem', color: 'var(--muted)' }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: modelStatus.online ? '#2ecc71' : 'var(--dim)', boxShadow: modelStatus.online ? '0 0 5px #2ecc71' : 'none' }} />
            {modelStatus.message}
            {modelStatus.cvR2 != null && <span style={{ color: 'var(--accent)', marginLeft: '.25rem' }}>· CV R² {modelStatus.cvR2.toFixed(3)}</span>}
          </div>
        </div>

        {/* Graphic */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px' }}>
          <div style={{ position: 'absolute', width: 320, height: 320, borderRadius: '50%', border: '1px solid rgba(230,57,70,.2)', animation: 'spin 20s linear infinite' }} />
          <div style={{ position: 'absolute', width: 220, height: 220, borderRadius: '50%', border: '1px solid rgba(230,57,70,.12)', animation: 'spin 14s linear infinite reverse' }} />
          <div style={{ fontFamily: 'var(--cond)', fontSize: '9rem', fontWeight: 900, color: 'transparent', WebkitTextStroke: '1px rgba(230,57,70,.25)', letterSpacing: '-.02em', userSelect: 'none' }}>$</div>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </section>

      {/* Stats bar */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', borderBottom: '1px solid var(--border)' }}>
        {STATS.map((s, i) => (
          <div key={s.label} style={{ padding: '2rem 1.5rem', borderRight: i < STATS.length - 1 ? '1px solid var(--border)' : 'none' }}>
            <div style={{ fontFamily: 'var(--cond)', fontSize: '2.2rem', fontWeight: 900, color: 'var(--accent)', lineHeight: 1 }}>{s.value}</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '.62rem', letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--muted)', marginTop: '.3rem' }}>{s.label}</div>
          </div>
        ))}
      </section>

      {/* How it works */}
      <section id="how" style={{ padding: '6rem 6vw', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '.62rem', letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '1rem' }}>Methodology</div>
          <h2 style={{ fontFamily: 'var(--cond)', fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 900, textTransform: 'uppercase', color: '#fff', marginBottom: '3rem', letterSpacing: '.03em' }}>How It Works</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
            {STEPS.map(s => (
              <div key={s.num} style={{ padding: '2rem', background: 'var(--surface)', border: '1px solid var(--border)', borderTop: '2px solid var(--accent)' }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '.65rem', letterSpacing: '.15em', color: 'var(--accent)', marginBottom: '1rem' }}>{s.num}</div>
                <h3 style={{ fontFamily: 'var(--cond)', fontSize: '1.1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: '#fff', marginBottom: '.65rem' }}>{s.title}</h3>
                <p style={{ fontSize: '.85rem', color: 'var(--text-dim)', lineHeight: 1.65 }}>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '6rem 6vw', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '.62rem', letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '1rem' }}>Model Details</div>
          <h2 style={{ fontFamily: 'var(--cond)', fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 900, textTransform: 'uppercase', color: '#fff', marginBottom: '3rem', letterSpacing: '.03em' }}>What drives the valuation</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
            {FEATURES.map(f => (
              <div key={f.title} style={{ padding: '1.5rem', border: '1px solid var(--border)', background: 'var(--bg)' }}>
                <div style={{ width: 24, height: 2, background: 'var(--accent)', marginBottom: '1rem' }} />
                <h4 style={{ fontFamily: 'var(--cond)', fontSize: '.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: '#fff', marginBottom: '.5rem' }}>{f.title}</h4>
                <p style={{ fontSize: '.82rem', color: 'var(--text-dim)', lineHeight: 1.65 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '6rem 6vw' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '2rem' }}>
          <h2 style={{ fontFamily: 'var(--cond)', fontSize: 'clamp(1.8rem, 3.5vw, 2.6rem)', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.03em', color: '#fff' }}>
            Ready to run a valuation?
          </h2>
          <Link to="/predict" style={{ display: 'inline-block', padding: '.9rem 2.5rem', background: 'var(--accent)', color: '#fff', fontFamily: 'var(--cond)', fontSize: '.95rem', fontWeight: 800, letterSpacing: '.15em', textTransform: 'uppercase' }}>
            Open Predictor →
          </Link>
        </div>
      </section>

    </div>
  )
}
