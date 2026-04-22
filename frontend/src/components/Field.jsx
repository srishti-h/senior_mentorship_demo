/**
 * components/Field.jsx
 *
 * Reusable form-field building block used in the NIL prediction form.
 *
 * Props:
 *   label       string  — field label
 *   name        string  — key in the form state
 *   value       any     — controlled value
 *   onChange    fn      — (name, value) callback
 *   type        string  — "text" | "number" | "select"  (default "text")
 *   options     array   — [{ value, label }]  required when type="select"
 *   placeholder string
 *   hint        string  — small helper text below the field
 *   required    bool
 */

export default function Field({
  label,
  name,
  value,
  onChange,
  type        = "text",
  options     = [],
  placeholder = "",
  hint,
  required    = false,
}) {
  const handleChange = (e) => onChange(name, e.target.value);

  const baseStyle = {
    width:         "100%",
    background:    "var(--surface2)",
    border:        "1px solid var(--border2)",
    borderRadius:  "var(--r)",
    color:         "var(--text)",
    fontFamily:    "var(--font-body)",
    fontSize:      "13px",
    padding:       "9px 12px",
    outline:       "none",
    transition:    "border-color .2s",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
      <label
        htmlFor={name}
        style={{
          fontSize:      "10px",
          fontWeight:    600,
          color:         "var(--text3)",
          textTransform: "uppercase",
          letterSpacing: "1px",
        }}
      >
        {label}
        {required && <span style={{ color: "var(--accent)", marginLeft: 3 }}>*</span>}
      </label>

      {type === "select" ? (
        <select
          id={name}
          name={name}
          value={value}
          onChange={handleChange}
          style={{ ...baseStyle, cursor: "pointer" }}
          onFocus={(e)  => (e.target.style.borderColor = "var(--accent)")}
          onBlur={(e)   => (e.target.style.borderColor = "var(--border2)")}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} style={{ background: "var(--surface2)" }}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={name}
          name={name}
          type={type}
          value={value}
          placeholder={placeholder}
          onChange={handleChange}
          required={required}
          style={baseStyle}
          onFocus={(e)  => (e.target.style.borderColor = "var(--accent)")}
          onBlur={(e)   => (e.target.style.borderColor = "var(--border2)")}
        />
      )}

      {hint && (
        <span style={{ fontSize: "10px", color: "var(--text3)" }}>{hint}</span>
      )}
    </div>
  );
}
