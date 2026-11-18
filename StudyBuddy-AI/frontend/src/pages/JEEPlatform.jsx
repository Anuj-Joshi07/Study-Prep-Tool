import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { analyzeVideo, generatePYQs, askQuestion } from '../api/jeeClient'

const SUBJECTS = ['Physics', 'Chemistry', 'Mathematics', 'Biology']

export default function JEEPlatform() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('video')       // video | pyq | ask
  const [videoUrl, setVideoUrl] = useState('')
  const [subject, setSubject] = useState('Physics')
  const [chapter, setChapter] = useState('')
  const [mode, setMode] = useState('full')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [pyqs, setPyqs] = useState([])
  const [pyqLoading, setPyqLoading] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [askLoading, setAskLoading] = useState(false)
  const [openPyq, setOpenPyq] = useState(null)

  const handleAnalyze = async () => {
    if (!videoUrl.trim()) { setError('Please enter a YouTube URL.'); return }
    setError(''); setLoading(true); setResult(null)
    try {
      const res = await analyzeVideo({ url: videoUrl, subject, chapter: chapter || null, mode })
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to analyze video.')
    } finally { setLoading(false) }
  }

  const handlePYQs = async () => {
    setPyqLoading(true); setPyqs([])
    try {
      const res = await generatePYQs(subject, chapter || 'General', 8)
      setPyqs(res.data.pyqs || [])
    } catch (e) { setError(e.response?.data?.detail || 'Failed to generate PYQs.') }
    finally { setPyqLoading(false) }
  }

  const handleAsk = async () => {
    if (!question.trim()) return
    setAskLoading(true); setAnswer('')
    try {
      const res = await askQuestion(question, subject)
      setAnswer(res.data.answer)
    } catch (e) { setError(e.response?.data?.detail || 'Failed to get answer.') }
    finally { setAskLoading(false) }
  }

  return (
    <div style={s.page}>
      {/* Top bar */}
      <div style={s.topbar}>
        <div style={s.topLeft}>
          <button onClick={() => navigate('/')} style={s.backBtn}>← Back</button>
          <div style={s.brand}>
            <span style={s.brandIcon}>🏫</span>
            <span style={s.brandText}>JEE / NEET Study Hub</span>
          </div>
        </div>
        <div style={s.subjectTabs}>
          {SUBJECTS.map(sub => (
            <button key={sub} onClick={() => setSubject(sub)}
              style={{ ...s.subBtn, ...(subject === sub ? s.subBtnActive : {}) }}>
              {sub}
            </button>
          ))}
        </div>
      </div>

      <div style={s.body}>
        {/* Nav tabs */}
        <div style={s.navTabs}>
          {[['video', '📹 Video Notes'], ['pyq', '📚 Previous Year Qs'], ['ask', '🤖 Ask AI Tutor']].map(([t, label]) => (
            <button key={t} onClick={() => { setTab(t); setError('') }}
              style={{ ...s.navTab, ...(tab === t ? s.navTabActive : {}) }}>
              {label}
            </button>
          ))}
        </div>

        {error && (
          <div style={s.errorBox}>⚠️ {error}</div>
        )}

        {/* ───── VIDEO TAB ───── */}
        {tab === 'video' && (
          <div style={s.tabContent}>
            <div style={s.sectionTitle}>Convert YouTube Lecture → Textbook Notes</div>
            <div style={s.inputGroup}>
              <label style={s.label}>YouTube URL *</label>
              <input style={s.input}
                placeholder="https://www.youtube.com/watch?v=..."
                value={videoUrl} onChange={e => setVideoUrl(e.target.value)} />
            </div>
            <div style={s.row}>
              <div style={{ flex: 1 }}>
                <label style={s.label}>Chapter / Topic</label>
                <input style={s.input} placeholder="e.g. Newton's Laws, Electrostatics…"
                  value={chapter} onChange={e => setChapter(e.target.value)} />
              </div>
              <div>
                <label style={s.label}>Mode</label>
                <div style={s.modeRow}>
                  {['fast', 'full'].map(m => (
                    <button key={m} onClick={() => setMode(m)}
                      style={{ ...s.modeBtn, ...(mode === m ? s.modeBtnActive : {}) }}>
                      {m === 'fast' ? '⚡ Fast' : '🔬 Full'}
                    </button>
                  ))}
                </div>
                <div style={s.modeHint}>{mode === 'fast' ? 'Notes only' : 'Notes + Practice Qs'}</div>
              </div>
            </div>
            <button style={s.primaryBtn} onClick={handleAnalyze} disabled={loading}>
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center' }}>
                  <Loader /> Analyzing video… (may take 1–2 min)
                </span>
              ) : '🚀 Analyze Video →'}
            </button>

            {loading && (
              <div style={s.progressBox}>
                <div style={s.progressBar}><div style={s.progressFill} /></div>
                <div style={s.progressText}>Extracting transcript → Generating notes with AI…</div>
              </div>
            )}

            {result && (
              <div style={{ marginTop: 32 }}>
                {/* Notes */}
                <div style={s.resultCard}>
                  <div style={s.resultHeader}>
                    <span style={s.resultIcon}>📖</span>
                    <span style={s.resultTitle}>AI-Generated Study Notes</span>
                    <span style={s.resultChip}>{subject} · {chapter || 'General'}</span>
                  </div>
                  <div style={s.noteContent}>
                    <ReactMarkdown>{result.summary}</ReactMarkdown>
                  </div>
                </div>

                {/* Practice questions */}
                {result.practice_questions && (
                  <div style={{ ...s.resultCard, marginTop: 20 }}>
                    <div style={s.resultHeader}>
                      <span style={s.resultIcon}>✏️</span>
                      <span style={s.resultTitle}>Practice Questions</span>
                    </div>
                    <div style={s.noteContent}>
                      <ReactMarkdown>{result.practice_questions}</ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* PYQs */}
                {result.pyqs?.length > 0 && (
                  <div style={{ ...s.resultCard, marginTop: 20 }}>
                    <div style={s.resultHeader}>
                      <span style={s.resultIcon}>📚</span>
                      <span style={s.resultTitle}>Previous Year Questions</span>
                      <span style={s.resultChip}>{result.pyqs.length} questions</span>
                    </div>
                    <PYQList pyqs={result.pyqs} openPyq={openPyq} setOpenPyq={setOpenPyq} />
                  </div>
                )}
              </div>
            )}

            {!result && !loading && (
              <div style={s.emptyState}>
                <div style={{ fontSize: 64, marginBottom: 16 }}>📹</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: '#fff' }}>
                  Paste any JEE/NEET lecture URL
                </div>
                <div style={{ color: 'rgba(255,255,255,.5)', fontSize: 14 }}>
                  Works with Physics Wallah, Vedantu, Unacademy, Khan Academy and more
                </div>
              </div>
            )}
          </div>
        )}

        {/* ───── PYQ TAB ───── */}
        {tab === 'pyq' && (
          <div style={s.tabContent}>
            <div style={s.sectionTitle}>Previous Year Questions — {subject}</div>
            <div style={s.row}>
              <div style={{ flex: 1 }}>
                <label style={s.label}>Chapter / Topic</label>
                <input style={s.input} placeholder="e.g. Electrostatics, Organic Chemistry…"
                  value={chapter} onChange={e => setChapter(e.target.value)} />
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button style={s.primaryBtn} onClick={handlePYQs} disabled={pyqLoading}>
                  {pyqLoading ? <><Loader /> Generating…</> : '🔍 Get PYQs →'}
                </button>
              </div>
            </div>

            {pyqs.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <PYQList pyqs={pyqs} openPyq={openPyq} setOpenPyq={setOpenPyq} />
              </div>
            )}

            {!pyqs.length && !pyqLoading && (
              <div style={s.emptyState}>
                <div style={{ fontSize: 56, marginBottom: 12 }}>📚</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 8 }}>AI-Generated JEE/NEET Pattern Questions</div>
                <div style={{ color: 'rgba(255,255,255,.5)', fontSize: 14 }}>Select a subject and chapter, then click Get PYQs</div>
              </div>
            )}
          </div>
        )}

        {/* ───── ASK AI TAB ───── */}
        {tab === 'ask' && (
          <div style={s.tabContent}>
            <div style={s.sectionTitle}>Ask Your AI {subject} Tutor</div>
            <div style={s.askBox}>
              <textarea style={s.askInput}
                placeholder={`Ask any ${subject} question…\ne.g. "Explain the work-energy theorem with a numerical example"\n"What is the difference between NaOH and KOH?"`}
                value={question} onChange={e => setQuestion(e.target.value)}
                rows={4}
              />
              <button style={s.askBtn} onClick={handleAsk} disabled={askLoading || !question.trim()}>
                {askLoading ? <><Loader /> Thinking…</> : '💡 Get Answer →'}
              </button>
            </div>

            {answer && (
              <div style={{ ...s.resultCard, marginTop: 20 }}>
                <div style={s.resultHeader}>
                  <span style={s.resultIcon}>🤖</span>
                  <span style={s.resultTitle}>AI Answer — {subject}</span>
                </div>
                <div style={s.noteContent}>
                  <ReactMarkdown>{answer}</ReactMarkdown>
                </div>
              </div>
            )}

            {!answer && !askLoading && (
              <div style={s.emptyState}>
                <div style={{ fontSize: 56, marginBottom: 12 }}>🤖</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 8 }}>Your AI Teacher is Ready</div>
                <div style={{ color: 'rgba(255,255,255,.5)', fontSize: 14 }}>Ask numerical problems, conceptual doubts, formula derivations — anything!</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function PYQList({ pyqs, openPyq, setOpenPyq }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {pyqs.map((q, i) => (
        <div key={i} style={s.pyqCard}>
          <div style={s.pyqHeader} onClick={() => setOpenPyq(openPyq === i ? null : i)}>
            <div style={s.pyqMeta}>
              <span style={s.pyqYear}>{q.year || q.exam || `Q${i+1}`}</span>
              {q.subject && <span style={s.pyqSubject}>{q.subject}</span>}
            </div>
            <div style={s.pyqQ}>{q.question}</div>
            <span style={s.pyqToggle}>{openPyq === i ? '▲' : '▼'}</span>
          </div>
          {openPyq === i && (
            <div style={s.pyqBody}>
              {q.options && (
                <div style={s.optionsGrid}>
                  {Object.entries(q.options).map(([k, v]) => (
                    <div key={k} style={{ ...s.option, ...(k === q.correct ? s.optionCorrect : {}) }}>
                      <strong>{k})</strong> {v}
                      {k === q.correct && <span style={s.correctBadge}>✓ Correct</span>}
                    </div>
                  ))}
                </div>
              )}
              {q.explanation && (
                <div style={s.explanation}>
                  <strong style={{ color: '#10b981' }}>Explanation:</strong>
                  <div style={{ marginTop: 6, lineHeight: 1.7 }}>{q.explanation}</div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function Loader() {
  return (
    <svg viewBox="0 0 24 24" style={{ width: 18, height: 18, animation: 'spin 1s linear infinite', display: 'inline' }}>
      <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
      <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,.4)" strokeWidth="3" fill="none" />
      <path d="M12 2 A10 10 0 0 1 22 12" stroke="#fff" strokeWidth="3" fill="none" strokeLinecap="round"/>
    </svg>
  )
}

const s = {
  page: { minHeight: '100vh', background: 'linear-gradient(135deg,#0f0c29 0%,#1a1040 60%,#0d1f3c 100%)', color: '#e2e8f0' },
  topbar: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 28px', background: 'rgba(0,0,0,.4)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,.08)', flexWrap: 'wrap', gap: 12 },
  topLeft: { display: 'flex', alignItems: 'center', gap: 16 },
  backBtn: { background: 'rgba(255,255,255,.08)', border: '1px solid rgba(255,255,255,.12)', color: '#c4b5fd', padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600 },
  brand: { display: 'flex', alignItems: 'center', gap: 8 },
  brandIcon: { fontSize: 24 },
  brandText: { fontSize: 18, fontWeight: 800, color: '#fff' },
  subjectTabs: { display: 'flex', gap: 6 },
  subBtn: { padding: '6px 14px', borderRadius: 20, border: '1px solid rgba(255,255,255,.12)', background: 'transparent', color: 'rgba(255,255,255,.6)', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  subBtnActive: { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', border: '1px solid transparent' },
  body: { maxWidth: 900, margin: '0 auto', padding: 32 },
  navTabs: { display: 'flex', gap: 4, marginBottom: 28, background: 'rgba(255,255,255,.04)', borderRadius: 12, padding: 4 },
  navTab: { flex: 1, padding: '10px 0', borderRadius: 9, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 600, background: 'transparent', color: 'rgba(255,255,255,.5)', transition: 'all .15s' },
  navTabActive: { background: 'rgba(255,255,255,.12)', color: '#fff' },
  errorBox: { background: 'rgba(239,68,68,.15)', border: '1px solid rgba(239,68,68,.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 20, fontSize: 14, color: '#fca5a5' },
  tabContent: {},
  sectionTitle: { fontSize: 22, fontWeight: 800, color: '#fff', marginBottom: 24 },
  label: { display: 'block', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,.5)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' },
  inputGroup: { marginBottom: 16 },
  input: { width: '100%', padding: '11px 14px', background: 'rgba(255,255,255,.07)', border: '1px solid rgba(255,255,255,.12)', borderRadius: 10, color: '#fff', fontSize: 14, outline: 'none', fontFamily: 'inherit' },
  row: { display: 'flex', gap: 16, marginBottom: 20, alignItems: 'flex-start' },
  modeRow: { display: 'flex', gap: 8 },
  modeBtn: { padding: '8px 16px', border: '1px solid rgba(255,255,255,.12)', borderRadius: 8, background: 'transparent', color: 'rgba(255,255,255,.5)', cursor: 'pointer', fontSize: 13, fontWeight: 600 },
  modeBtnActive: { background: 'rgba(99,102,241,.3)', borderColor: '#6366f1', color: '#a5b4fc' },
  modeHint: { fontSize: 11, color: 'rgba(255,255,255,.35)', marginTop: 4 },
  primaryBtn: { padding: '12px 28px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', borderRadius: 10, color: '#fff', fontWeight: 700, fontSize: 15, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' },
  progressBox: { marginTop: 24, padding: 20, background: 'rgba(255,255,255,.05)', borderRadius: 12, border: '1px solid rgba(255,255,255,.08)' },
  progressBar: { height: 4, background: 'rgba(255,255,255,.1)', borderRadius: 2, overflow: 'hidden', marginBottom: 12 },
  progressFill: { height: '100%', width: '60%', background: 'linear-gradient(90deg,#6366f1,#22d3ee)', borderRadius: 2, animation: 'progress 2s ease infinite alternate' },
  progressText: { fontSize: 13, color: 'rgba(255,255,255,.6)', textAlign: 'center' },
  emptyState: { textAlign: 'center', padding: '64px 20px', color: 'rgba(255,255,255,.5)' },
  resultCard: { background: 'rgba(255,255,255,.05)', border: '1px solid rgba(255,255,255,.1)', borderRadius: 16, overflow: 'hidden' },
  resultHeader: { display: 'flex', alignItems: 'center', gap: 10, padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,.08)', background: 'rgba(255,255,255,.03)' },
  resultIcon: { fontSize: 20 },
  resultTitle: { fontSize: 15, fontWeight: 700, color: '#fff', flex: 1 },
  resultChip: { background: 'rgba(99,102,241,.25)', color: '#a5b4fc', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 },
  noteContent: { padding: 24, fontSize: 14, lineHeight: 1.8, color: 'rgba(255,255,255,.85)', overflowX: 'auto' },
  pyqCard: { background: 'rgba(255,255,255,.05)', border: '1px solid rgba(255,255,255,.08)', borderRadius: 12, overflow: 'hidden' },
  pyqHeader: { display: 'flex', alignItems: 'flex-start', gap: 12, padding: '14px 16px', cursor: 'pointer' },
  pyqMeta: { display: 'flex', flexDirection: 'column', gap: 4, minWidth: 90 },
  pyqYear: { fontSize: 11, fontWeight: 700, color: '#a5b4fc', background: 'rgba(99,102,241,.2)', padding: '2px 8px', borderRadius: 20, textAlign: 'center' },
  pyqSubject: { fontSize: 10, color: 'rgba(255,255,255,.4)', textAlign: 'center' },
  pyqQ: { flex: 1, fontSize: 14, color: '#e2e8f0', lineHeight: 1.6 },
  pyqToggle: { color: 'rgba(255,255,255,.4)', fontSize: 12, flexShrink: 0, marginTop: 2 },
  pyqBody: { padding: '0 16px 16px', borderTop: '1px solid rgba(255,255,255,.06)' },
  optionsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 14, marginBottom: 14 },
  option: { padding: '8px 12px', background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.08)', borderRadius: 8, fontSize: 13, color: 'rgba(255,255,255,.75)', position: 'relative' },
  optionCorrect: { background: 'rgba(16,185,129,.12)', borderColor: 'rgba(16,185,129,.3)', color: '#6ee7b7' },
  correctBadge: { position: 'absolute', top: 4, right: 8, fontSize: 10, color: '#10b981', fontWeight: 700 },
  explanation: { background: 'rgba(16,185,129,.06)', border: '1px solid rgba(16,185,129,.15)', borderRadius: 8, padding: '12px 14px', fontSize: 13, color: 'rgba(255,255,255,.75)' },
  askBox: { display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 8 },
  askInput: { width: '100%', padding: '14px', background: 'rgba(255,255,255,.07)', border: '1px solid rgba(255,255,255,.12)', borderRadius: 10, color: '#fff', fontSize: 14, resize: 'vertical', outline: 'none', fontFamily: 'inherit', lineHeight: 1.6 },
  askBtn: { padding: '12px 24px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', border: 'none', borderRadius: 10, color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer', alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 8 },
}
