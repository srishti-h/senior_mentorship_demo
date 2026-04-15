function Bar({ label, pct }) {
  return (
    <div className="bar-row">
      <div className="bar-meta">
        <span>{label}</span>
        <span>{pct != null ? `${pct}%` : '—'}</span>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: pct != null ? `${pct}%` : '0%' }} />
      </div>
    </div>
  )
}

export default function ResultPanel({ result, loading, error, modelStatus }) {
  const { online, cvR2, message } = modelStatus

  return (
    <div className="result-panel">


      <div className="result-box">
        <div className="result-eyebrow">Estimated Market Value</div>
        <div className={`result-value ${loading ? 'loading' : !result ? 'empty' : ''}`}>
          {loading ? 'Calculating…' : result ? `$${result.predicted_nil.toLocaleString()}` : '—'}
        </div>
        {result && (
          <div className="result-ci">
            Confidence interval: ${result.ci_low.toLocaleString()} – ${result.ci_high.toLocaleString()}
          </div>
        )}
      </div>

      {error && <div className="error-box">{error}</div>}
    </div>
  )
}
