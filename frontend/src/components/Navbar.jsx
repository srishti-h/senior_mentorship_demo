import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()

  const linkStyle = (path) => ({
    fontFamily: 'var(--mono)',
    fontSize: '.7rem',
    letterSpacing: '.15em',
    textTransform: 'uppercase',
    color: pathname === path ? 'var(--text)' : 'var(--muted)',
    paddingBottom: '2px',
    borderBottom: pathname === path ? '1px solid var(--accent)' : '1px solid transparent',
    transition: 'color .15s, border-color .15s',
  })

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2.5rem',
      height: '56px',
      borderBottom: '1px solid var(--border)',
      background: 'rgba(10,10,10,0.96)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <Link to="/" style={{ fontFamily: 'var(--cond)', fontSize: '1.25rem', fontWeight: 900, letterSpacing: '.08em', textTransform: 'uppercase' }}>
        <span style={{ color: 'var(--accent)' }}>SEC</span>
        <span style={{ color: 'var(--text)' }}> NIL</span>
      </Link>
      <div style={{ display: 'flex', gap: '2rem' }}>
        <Link to="/" style={linkStyle('/')}>Home</Link>
        <Link to="/predict" style={linkStyle('/predict')}>Predictor</Link>
      </div>
    </nav>
  )
}
