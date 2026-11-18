import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createStudent, listStudents } from '../api/client'

export default function Login() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')   // 'login' | 'register'
  const [form, setForm] = useState({ name: '', email: '', target_role: '', cgpa: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const handleLogin = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await listStudents()
      const found = res.data.find(s => s.email === form.email)
      if (!found) { setError('No account found. Please register first.'); setLoading(false); return }
      localStorage.setItem('student_id', found.id)
      localStorage.setItem('student_name', found.name)
      navigate('/dashboard')
    } catch {
      setError('Failed to connect to server. Is the backend running?')
    } finally { setLoading(false) }
  }

  const handleRegister = async () => {
    setError('')
    if (!form.name || !form.email) { setError('Name and email are required.'); return }
    setLoading(true)
    try {
      const res = await createStudent({
        name: form.name,
        email: form.email,
        target_role: form.target_role,
        cgpa: form.cgpa ? parseFloat(form.cgpa) : null,
      })
      localStorage.setItem('student_id', res.data.id)
      localStorage.setItem('student_name', res.data.name)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally { setLoading(false) }
  }

  const s = {
    page: { minHeight: '100vh', background: 'linear-gradient(135deg,#1e1b4b 0%,#312e81 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' },
    box: { background: '#fff', borderRadius: 16, padding: 40, width: '100%', maxWidth: 420, boxShadow: '0 25px 50px rgba(0,0,0,.3)' },
    title: { fontSize: 26, fontWeight: 800, color: '#1e293b', textAlign: 'center', marginBottom: 6 },
    sub: { textAlign: 'center', color: '#64748b', marginBottom: 28, fontSize: 14 },
    tabs: { display: 'flex', gap: 8, marginBottom: 24 },
    tab: (active) => ({ flex: 1, padding: '8px 0', borderRadius: 8, fontWeight: 600, fontSize: 13, border: 'none', cursor: 'pointer', background: active ? '#4f46e5' : '#f1f5f9', color: active ? '#fff' : '#64748b' }),
    input: { width: '100%', padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 14, marginBottom: 14, outline: 'none', boxSizing: 'border-box' },
    btn: { width: '100%', padding: '11px 0', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 },
    err: { background: '#fef2f2', color: '#991b1b', borderRadius: 8, padding: '8px 12px', fontSize: 13, marginBottom: 16 },
  }

  return (
    <div style={s.page}>
      <div style={s.box}>
        <div style={{ textAlign: 'center', fontSize: 42, marginBottom: 8 }}>🎓</div>
        <div style={s.title}>Study Prep Tool</div>
        <div style={s.sub}>Engineering · Career · Placement Prep</div>

        <div style={s.tabs}>
          <button style={s.tab(mode === 'login')} onClick={() => setMode('login')}>Sign In</button>
          <button style={s.tab(mode === 'register')} onClick={() => setMode('register')}>Register</button>
        </div>

        {error && <div style={s.err}>⚠️ {error}</div>}

        {mode === 'register' && (
          <input style={s.input} placeholder="Full Name" value={form.name} onChange={set('name')} />
        )}
        <input style={s.input} placeholder="Email address" type="email" value={form.email} onChange={set('email')} />
        {mode === 'register' && (
          <>
            <input style={s.input} placeholder="Target Role (e.g. Full Stack Developer)" value={form.target_role} onChange={set('target_role')} />
            <input style={s.input} placeholder="CGPA (optional)" type="number" step="0.1" value={form.cgpa} onChange={set('cgpa')} />
          </>
        )}

        <button style={s.btn} disabled={loading} onClick={mode === 'login' ? handleLogin : handleRegister}>
          {loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
        </button>

        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: '#94a3b8' }}>
          No password required — email is your identity
        </p>
        <p style={{ textAlign: 'center', marginTop: 10, fontSize: 12 }}>
          <a href="/" style={{ color: '#6366f1' }}>← Back to Home</a>
        </p>
      </div>
    </div>
  )
}
