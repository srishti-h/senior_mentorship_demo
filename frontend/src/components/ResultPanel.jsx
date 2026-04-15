function Bar({ label, pct }) {
  return (
    <div style={{ marginBottom: '.9rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--cond)', fontSize: '.7rem', fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '.3rem' }}>
        <span>{label}</span>
        <span>{pct != null ? `${pct}%` : '—'}</span>
      </div>
      <div style={{ height: '3px', background: 'var(--border)', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: pct != null ? `${pct}%` : '0%', background: 'var(--accent)', transition: 'width .6s cubic-bezier(.4,0,.2,1)' }} />
      </div>
    </div>
  )
}

export default function ResultPanel({ result, loading, error, modelStatus }) {
  const { online, cvR2, message } = modelStatus

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem', position: 'sticky', top: '72px' }}>

      {/* Status badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem', padding: '.65rem 1rem', border: '1px solid var(--border)', background: 'var(--surface)' }}>
        <div style={{ width: 6, height: 6, borderRadius: '50%', background: online ? '#2ecc71' : 'var(--dim)', boxShadow: online ? '0 0 6px #2ecc71' : 'none', flexShrink: 0 }} />
        <span style={{ fontFamily: 'var(--mono)', fontSize: '.68rem', color: 'var(--muted)' }}>{message}</span>
        {cvR2 != null && <span style={{ marginLeft: 'auto', fontFamily: 'var(--mono)', fontSize: '.68rem', color: 'var(--accent)' }}>CV R² {cvR2.toFixed(3)}</span>}
      </div>

      {/* Main value */}
      <div style={{ border: '1px solid var(--border)', padding: '2rem', background: 'var(--surface)', textAlign: 'center' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '.6rem', letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: '.5rem' }}>
          Estimated Market Value
        </div>
        <div style={{
          fontFamily: 'var(--cond)',
          fontSize: 'clamp(2.6rem, 5.5vw, 4.2rem)',
          fontWeight: 900,
          lineHeight: 1,
          color: result ? 'var(--accent)' : 'var(--dim)',
          textShadow: result ? '0 0 40px rgba(230,57,70,.35)' : 'none',
          letterSpacing: '.02em',
          animation: loading ? 'pulse .9s ease infinite' : 'none',
        }}>
          {loading ? 'Calculating…' : result ? `$${result.predicted_nil.toLocaleString()}` : '—'}
        </div>
        {result && (
          <div style={{ marginTop: '.6rem', fontFamily: 'var(--mono)', fontSize: '.7rem', color: 'var(--muted)' }}>
            Confidence interval: ${result.ci_low.toLocaleString()} – ${result.ci_high.toLocaleString()}
          </div>
        )}
      </div>

      {/* Breakdown */}
      <div style={{ padding: '1.4rem', background: 'var(--surface)', border: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '.6rem', fontWeight: 700, letterSpacing: '.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '1.1rem' }}>
          Value Drivers
        </div>
        <Bar label="Social Reach"         pct={result?.breakdown?.social} />
        <Bar label="Program Premium"      pct={result?.breakdown?.prog}   />
        <Bar label="On-Field Performance" pct={result?.breakdown?.perf}   />
        <Bar label="Physical Profile"     pct={result?.breakdown?.phys}   />
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: '.75rem 1rem', border: '1px solid #5a1a1a', background: '#140808', fontFamily: 'var(--mono)', fontSize: '.72rem', color: '#ff6b6b' }}>
          {error}
        </div>
      )}

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }`}</style>
    </div>
  )
}
