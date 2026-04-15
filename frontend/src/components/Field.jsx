export function Field({ label, children }) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
    </div>
  )
}

export function Input(props) {
  return <input {...props} />
}

export function Select({ children, ...props }) {
  return <select {...props}>{children}</select>
}

export function FieldRow({ children }) {
  return <div className="field-row">{children}</div>
}

export function SectionLabel({ children }) {
  return <p className="section-label">{children}</p>
}

export function Divider() {
  return <hr className="divider" />
}
