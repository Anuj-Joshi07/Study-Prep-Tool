import React from 'react'
import { useNavigate } from 'react-router-dom'

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div style={s.page}>
      {/* Background blobs */}
      <div style={s.blob1} />
      <div style={s.blob2} />
      <div style={s.blob3} />

      <div style={s.inner}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.logoRow}>
            <span style={s.logoIcon}>🎓</span>
            <span style={s.logoText}>Study Prep Tool</span>
          </div>
          <div style={s.tagline}>One Platform · Every Stage of Your Education</div>
        </div>

        {/* Hero */}
        <div style={s.hero}>
          <h1 style={s.heroTitle}>Choose Your Learning Path</h1>
          <p style={s.heroSub}>
            Powered by advanced AI — select the experience designed for your level
          </p>
        </div>

        {/* Two big cards */}
        <div style={s.cards}>

          {/* Card 1 — Class 1–12 */}
          <div style={s.card} onClick={() => navigate('/jee')}>
            <div style={s.cardGlow1} />
            <div style={s.cardBadge} className="badge-school">Class 1 – 12</div>
            <div style={s.cardIcon}>🏫</div>
            <h2 style={s.cardTitle}>School & JEE / NEET</h2>
            <p style={s.cardDesc}>
              Turn any YouTube lecture into textbook-style notes instantly.
              Get previous year questions, practice tests, and ask AI anything about your subjects.
            </p>
            <div style={s.featureList}>
              {['📹 YouTube → Structured Notes', '📚 Previous Year Questions (JEE/NEET)', '✏️ AI Practice Question Generator', '🤖 Ask Subject Doubts Instantly'].map((f, i) => (
                <div key={i} style={s.featureItem}>
                  <span style={s.featureDot} />
                  {f}
                </div>
              ))}
            </div>
            <div style={s.cardFooter}>
              <div style={{ ...s.cardBtn, background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>
                Enter School Mode →
              </div>
              <div style={s.cardSub}>Physics · Chemistry · Maths · Biology</div>
            </div>
          </div>

          {/* Card 2 — Engineering */}
          <div style={s.card} onClick={() => navigate('/dashboard')}>
            <div style={s.cardGlow2} />
            <div style={s.cardBadge} className="badge-eng">Engineering</div>
            <div style={s.cardIcon}>🎓</div>
            <h2 style={s.cardTitle}>Engineering & Career</h2>
            <p style={s.cardDesc}>
              Full AI-powered learning platform — tutoring, resume analysis, job roadmaps,
              voice mock interviews, adaptive quizzes, and career guidance.
            </p>
            <div style={s.featureList}>
              {['💬 AI Tutor with Memory & RAG', '📄 Resume Analyzer & JD Matcher', '🗺️ Personalized Career Roadmap', '🎤 Voice Mock Interviews (Tech + HR)'].map((f, i) => (
                <div key={i} style={s.featureItem}>
                  <span style={{ ...s.featureDot, background: '#10b981' }} />
                  {f}
                </div>
              ))}
            </div>
            <div style={s.cardFooter}>
              <div style={{ ...s.cardBtn, background: 'linear-gradient(135deg,#059669,#0891b2)' }}>
                Enter Engineering Mode →
              </div>
              <div style={s.cardSub}>B.Tech · MCA · Placement Prep</div>
            </div>
          </div>
        </div>

        {/* Bottom stats */}
        <div style={s.statsRow}>
          {[
            { n: '7', label: 'AI Agents' },
            { n: '2', label: 'Platforms' },
            { n: '∞', label: 'Learning' },
            { n: '1', label: 'App' },
          ].map((stat, i) => (
            <div key={i} style={s.statItem}>
              <div style={s.statNum}>{stat.n}</div>
              <div style={s.statLabel}>{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-18px)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        .badge-school { background:linear-gradient(135deg,#6366f1,#8b5cf6)!important; }
        .badge-eng { background:linear-gradient(135deg,#059669,#0891b2)!important; }
      `}</style>
    </div>
  )
}

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg,#0f0c29 0%,#1a1040 50%,#0d1f3c 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: 24, position: 'relative', overflow: 'hidden',
  },
  blob1: {
    position: 'absolute', top: '-20%', left: '-10%',
    width: 600, height: 600, borderRadius: '50%',
    background: 'radial-gradient(circle,rgba(99,102,241,.18) 0%,transparent 70%)',
    pointerEvents: 'none',
  },
  blob2: {
    position: 'absolute', bottom: '-20%', right: '-10%',
    width: 500, height: 500, borderRadius: '50%',
    background: 'radial-gradient(circle,rgba(16,185,129,.15) 0%,transparent 70%)',
    pointerEvents: 'none',
  },
  blob3: {
    position: 'absolute', top: '40%', left: '50%',
    width: 300, height: 300, borderRadius: '50%',
    background: 'radial-gradient(circle,rgba(139,92,246,.1) 0%,transparent 70%)',
    pointerEvents: 'none',
  },
  inner: {
    maxWidth: 1100, width: '100%', position: 'relative', zIndex: 1,
    animation: 'fadeIn .6s ease both',
  },
  header: { textAlign: 'center', marginBottom: 48 },
  logoRow: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 10 },
  logoIcon: { fontSize: 42 },
  logoText: { fontSize: 32, fontWeight: 800, color: '#fff', letterSpacing: '-1px' },
  tagline: { fontSize: 15, color: 'rgba(255,255,255,.5)', letterSpacing: '0.08em', textTransform: 'uppercase' },
  hero: { textAlign: 'center', marginBottom: 52 },
  heroTitle: { fontSize: 48, fontWeight: 800, color: '#fff', marginBottom: 14, lineHeight: 1.1 },
  heroSub: { fontSize: 18, color: 'rgba(255,255,255,.65)', maxWidth: 520, margin: '0 auto' },
  cards: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 52 },
  card: {
    background: 'rgba(255,255,255,.05)', backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255,255,255,.1)', borderRadius: 24,
    padding: 36, cursor: 'pointer', position: 'relative', overflow: 'hidden',
    transition: 'transform .25s,box-shadow .25s,border-color .25s',
    animation: 'fadeIn .7s ease both',
  },
  cardGlow1: {
    position: 'absolute', top: -60, right: -60, width: 200, height: 200, borderRadius: '50%',
    background: 'radial-gradient(circle,rgba(99,102,241,.25) 0%,transparent 70%)',
    pointerEvents: 'none',
  },
  cardGlow2: {
    position: 'absolute', top: -60, right: -60, width: 200, height: 200, borderRadius: '50%',
    background: 'radial-gradient(circle,rgba(16,185,129,.2) 0%,transparent 70%)',
    pointerEvents: 'none',
  },
  cardBadge: {
    display: 'inline-block', padding: '4px 14px', borderRadius: 20,
    fontSize: 12, fontWeight: 700, color: '#fff', marginBottom: 20, letterSpacing: '0.05em',
  },
  cardIcon: { fontSize: 52, marginBottom: 16 },
  cardTitle: { fontSize: 24, fontWeight: 800, color: '#fff', marginBottom: 12 },
  cardDesc: { fontSize: 14, color: 'rgba(255,255,255,.65)', lineHeight: 1.7, marginBottom: 24 },
  featureList: { display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 28 },
  featureItem: { display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: 'rgba(255,255,255,.8)' },
  featureDot: { width: 7, height: 7, borderRadius: '50%', background: '#6366f1', flexShrink: 0 },
  cardFooter: {},
  cardBtn: {
    padding: '13px 20px', borderRadius: 12, color: '#fff', fontWeight: 700, fontSize: 15,
    textAlign: 'center', marginBottom: 10, transition: 'opacity .2s',
  },
  cardSub: { fontSize: 12, color: 'rgba(255,255,255,.4)', textAlign: 'center' },
  statsRow: {
    display: 'flex', justifyContent: 'center', gap: 48,
    borderTop: '1px solid rgba(255,255,255,.08)', paddingTop: 36,
  },
  statItem: { textAlign: 'center' },
  statNum: { fontSize: 36, fontWeight: 800, color: '#fff', lineHeight: 1 },
  statLabel: { fontSize: 13, color: 'rgba(255,255,255,.45)', marginTop: 4 },
}
