import React from 'react'

export function Card({ children, style = {} }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0',
      boxShadow: '0 1px 3px rgba(0,0,0,.06)', padding: 20, ...style,
    }}>
      {children}
    </div>
  )
}

export function CardTitle({ children }) {
  return (
    <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 16 }}>
      {children}
    </h2>
  )
}

export function Stat({ label, value, color = '#4f46e5' }) {
  return (
    <div style={{
      background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10,
      padding: '16px 20px', textAlign: 'center',
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value ?? '—'}</div>
      <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{label}</div>
    </div>
  )
}

export function Btn({ children, onClick, variant = 'primary', disabled = false, style = {}, type = 'button' }) {
  const base = {
    padding: '8px 18px', borderRadius: 8, fontWeight: 600,
    fontSize: 13, cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1, border: 'none', ...style,
  }
  const variants = {
    primary: { background: '#4f46e5', color: '#fff' },
    secondary: { background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' },
    danger: { background: '#fee2e2', color: '#dc2626' },
    success: { background: '#d1fae5', color: '#065f46' },
  }
  return (
    <button type={type} style={{ ...base, ...variants[variant] }} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

export function Badge({ children, color = '#4f46e5' }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 20,
      fontSize: 11, fontWeight: 600, background: color + '22', color,
    }}>
      {children}
    </span>
  )
}

export function Input({ label, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 }}>{label}</label>}
      <input style={{
        width: '100%', padding: '8px 12px', border: '1px solid #e2e8f0',
        borderRadius: 8, fontSize: 14, outline: 'none', background: '#fff',
        color: '#1e293b',
      }} {...props} />
    </div>
  )
}

export function Textarea({ label, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 }}>{label}</label>}
      <textarea style={{
        width: '100%', padding: '8px 12px', border: '1px solid #e2e8f0',
        borderRadius: 8, fontSize: 14, outline: 'none', background: '#fff',
        color: '#1e293b', resize: 'vertical', minHeight: 90,
      }} {...props} />
    </div>
  )
}

export function Spinner() {
  return (
    <div style={{ display: 'inline-block', width: 20, height: 20 }}>
      <svg viewBox="0 0 24 24" style={{ animation: 'spin 1s linear infinite', width: 20, height: 20 }}>
        <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
        <circle cx="12" cy="12" r="10" stroke="#4f46e5" strokeWidth="3" fill="none" strokeDasharray="31 62" />
      </svg>
    </div>
  )
}

export function Alert({ children, type = 'info' }) {
  const colors = {
    info: { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af' },
    success: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534' },
    error: { bg: '#fef2f2', border: '#fecaca', text: '#991b1b' },
    warning: { bg: '#fffbeb', border: '#fde68a', text: '#92400e' },
  }
  const c = colors[type] || colors.info
  return (
    <div style={{
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
      borderRadius: 8, padding: '10px 14px', fontSize: 13, marginBottom: 12,
    }}>
      {children}
    </div>
  )
}

export function PageHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1e293b' }}>{title}</h1>
      {subtitle && <p style={{ color: '#64748b', marginTop: 4, fontSize: 14 }}>{subtitle}</p>}
    </div>
  )
}
