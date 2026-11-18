import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { to: '/chat', label: 'AI Tutor', icon: '💬' },
  { to: '/quiz', label: 'Quiz', icon: '📝' },
  { to: '/resume', label: 'Resume & JD', icon: '📄' },
  { to: '/roadmap', label: 'Roadmap', icon: '🗺️' },
  { to: '/interview', label: 'Interview', icon: '🎤' },
  { to: '/documents', label: 'Documents', icon: '📚' },
]

export default function Layout({ children }) {
  const navigate = useNavigate()
  const studentName = localStorage.getItem('student_name') || 'Student'
  const studentId = localStorage.getItem('student_id')

  const handleLogout = () => {
    localStorage.removeItem('student_id')
    localStorage.removeItem('student_name')
    navigate('/login')
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8f9fb' }}>
      {/* Sidebar */}
      <aside style={s.sidebar}>
        {/* Brand */}
        <div style={s.brand}>
          <div style={s.brandRow}>
            <span style={s.brandIcon}>🎓</span>
            <div>
              <div style={s.brandName}>Study Prep Tool</div>
              <div style={s.brandMode}>Engineering Mode</div>
            </div>
          </div>
        </div>

        {/* Switch mode button */}
        <button onClick={() => navigate('/')} style={s.switchBtn}>
          🏫 Switch to School Mode
        </button>

        {/* Nav */}
        <nav style={s.nav}>
          {NAV.map(({ to, label, icon }) => (
            <NavLink key={to} to={to}
              style={({ isActive }) => ({
                ...s.navLink,
                ...(isActive ? s.navLinkActive : {}),
              })}>
              <span style={s.navIcon}>{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User card */}
        <div style={s.userCard}>
          <div style={s.avatar}>{studentName.charAt(0).toUpperCase()}</div>
          <div style={s.userInfo}>
            <div style={s.userName}>{studentName}</div>
            <div style={s.userId}>{studentId?.slice(0, 8)}…</div>
          </div>
          <button onClick={handleLogout} style={s.logoutBtn} title="Sign out">↩</button>
        </div>
      </aside>

      {/* Main */}
      <main style={s.main}>{children}</main>
    </div>
  )
}

const s = {
  sidebar: {
    width: 230, flexShrink: 0,
    background: 'linear-gradient(180deg,#1e1b4b 0%,#1a1040 100%)',
    display: 'flex', flexDirection: 'column',
    position: 'sticky', top: 0, height: '100vh', overflowY: 'auto',
  },
  brand: { padding: '20px 16px 16px', borderBottom: '1px solid rgba(255,255,255,.08)' },
  brandRow: { display: 'flex', alignItems: 'center', gap: 10 },
  brandIcon: { fontSize: 28 },
  brandName: { color: '#fff', fontSize: 16, fontWeight: 800, letterSpacing: '-0.3px' },
  brandMode: { color: '#818cf8', fontSize: 11, fontWeight: 500 },
  switchBtn: {
    margin: '12px 12px 4px',
    padding: '8px 12px', width: 'calc(100% - 24px)',
    background: 'rgba(99,102,241,.15)', border: '1px solid rgba(99,102,241,.3)',
    color: '#a5b4fc', borderRadius: 10, cursor: 'pointer', fontSize: 12, fontWeight: 600,
    textAlign: 'left',
  },
  nav: { flex: 1, padding: '8px 8px' },
  navLink: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '9px 12px', fontSize: 13, fontWeight: 500,
    color: 'rgba(255,255,255,.55)', textDecoration: 'none',
    borderRadius: 10, transition: 'all .15s', marginBottom: 2,
  },
  navLinkActive: { background: 'rgba(99,102,241,.25)', color: '#a5b4fc' },
  navIcon: { fontSize: 16, width: 20, textAlign: 'center' },
  userCard: {
    margin: '8px', padding: '10px 12px',
    background: 'rgba(255,255,255,.06)', borderRadius: 12,
    display: 'flex', alignItems: 'center', gap: 10,
    border: '1px solid rgba(255,255,255,.08)',
  },
  avatar: {
    width: 32, height: 32, borderRadius: '50%',
    background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#fff', fontWeight: 700, fontSize: 14, flexShrink: 0,
  },
  userInfo: { flex: 1, minWidth: 0 },
  userName: { color: '#e2e8f0', fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  userId: { color: '#6366f1', fontSize: 11, marginTop: 1 },
  logoutBtn: { background: 'none', border: 'none', color: 'rgba(255,255,255,.4)', cursor: 'pointer', fontSize: 18, padding: '2px 4px' },
  main: { flex: 1, padding: 28, overflowY: 'auto', maxWidth: '100%' },
}
