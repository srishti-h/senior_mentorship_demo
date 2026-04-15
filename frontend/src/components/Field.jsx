const labelStyle = {
  display: 'block',
  fontFamily: 'var(--mono)',
  fontSize: '.62rem',
  letterSpacing: '.18em',
  textTransform: 'uppercase',
  color: 'var(--muted)',
  marginBottom: '.4rem',
}

const inputStyle = {
  width: '100%',
  background: 'var(--bg)',
  border: '1px solid var(--border)',
  color: 'var(--text)',
  fontFamily: 'var(--mono)',
  fontSize: '.88rem',
  padding: '.6rem .85rem',
  outline: 'none',
  borderRadius: 0,
}

const selectStyle = {
  ...inputStyle,
  appearance: 'none',
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23777' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right .85rem center',
  cursor: 'pointer',
}

export function Field({ label, children }) {
  return (
    <div style={{ marginBottom: '1.2rem' }}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  )
}

export function Input(props) {
  return <input style={inputStyle} {...props} />
}

export function Select({ children, ...props }) {
  return <select style={selectStyle} {...props}>{children}</select>
}

export function FieldRow({ children }) {
  return <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem' }}>{children}</div>
}

export function SectionLabel({ children }) {
  return (
    <p style={{
      fontFamily: 'var(--mono)', fontSize: '.58rem', fontWeight: 700,
      letterSpacing: '.2em', textTransform: 'uppercase',
      color: 'var(--dim)', margin: '1.4rem 0 .7rem',
    }}>
      {children}
    </p>
  )
}

export function Divider() {
  return <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1.4rem 0' }} />
}
