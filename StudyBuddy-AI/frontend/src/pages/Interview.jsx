import React, { useState, useEffect, useRef } from 'react'
import { startInterview, evaluateInterview } from '../api/client'
import { Card, CardTitle, Btn, Input, Spinner, Alert, Badge, PageHeader } from '../components/Card'

// ---- Web Speech API helpers (browser-native, no DLL needed) ----
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const synth = window.speechSynthesis

function speak(text, onEnd) {
  if (!synth) return
  synth.cancel()
  const utt = new SpeechSynthesisUtterance(text)
  utt.rate = 0.95
  utt.pitch = 1.0
  if (onEnd) utt.onend = onEnd
  synth.speak(utt)
}

export default function Interview() {
  const studentId = localStorage.getItem('student_id')
  const [form, setForm] = useState({ mode: 'technical', target_role: '', num_questions: 5 })
  const [session, setSession] = useState(null)
  const [answers, setAnswers] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState('setup')     // setup | answering | result
  const [current, setCurrent] = useState(0)
  const [voiceMode, setVoiceMode] = useState(false)
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [aiSpeaking, setAiSpeaking] = useState(false)
  const recognizerRef = useRef(null)
  const hasSpeechAPI = !!SpeechRecognition

  const set = k => e => setForm({ ...form, [k]: e.target.value })

  // AI reads the question aloud when in voice mode
  useEffect(() => {
    if (voiceMode && session && step === 'answering') {
      const q = session.questions[current]
      if (q) {
        setAiSpeaking(true)
        speak(`Question ${current + 1}: ${q}`, () => setAiSpeaking(false))
      }
    }
  }, [current, session, voiceMode, step])

  const startListening = () => {
    if (!SpeechRecognition) return
    const rec = new SpeechRecognition()
    rec.continuous = false
    rec.interimResults = true
    rec.lang = 'en-US'
    rec.onresult = (e) => {
      const t = Array.from(e.results).map(r => r[0].transcript).join('')
      setTranscript(t)
    }
    rec.onerror = () => setListening(false)
    rec.onend = () => {
      setListening(false)
      // Save transcript as answer
      setTranscript(prev => {
        if (prev.trim()) {
          setAnswers(a => { const na = [...a]; na[current] = prev.trim(); return na })
        }
        return ''
      })
    }
    recognizerRef.current = rec
    rec.start()
    setListening(true)
  }

  const stopListening = () => {
    if (recognizerRef.current) recognizerRef.current.stop()
    setListening(false)
  }

  const handleStart = async () => {
    setError(''); setLoading(true)
    try {
      const res = await startInterview({
        student_id: studentId,
        mode: form.mode,
        target_role: form.target_role || undefined,
        num_questions: parseInt(form.num_questions),
      })
      setSession(res.data)
      setAnswers(Array(res.data.questions.length).fill(''))
      setCurrent(0); setResult(null); setStep('answering')
    } catch (e) { setError(e.response?.data?.detail || 'Failed to start interview.') }
    finally { setLoading(false) }
  }

  const handleEvaluate = async () => {
    synth?.cancel()
    setLoading(true); setError('')
    try {
      const res = await evaluateInterview({
        session_id: session.session_id,
        student_id: studentId,
        answers,
      })
      setResult(res.data); setStep('result')
    } catch (e) { setError(e.response?.data?.detail || 'Evaluation failed.') }
    finally { setLoading(false) }
  }

  const scoreColor = s => s >= 75 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444'
  const modeLabels = { technical: '💻 Technical', hr: '👔 HR / Behavioral', resume_based: '📄 Resume-Based' }

  return (
    <div>
      <PageHeader title="🎤 Mock Interview" subtitle="Practice with AI — text or voice mode" />
      {error && <Alert type="error">{error}</Alert>}

      {step === 'setup' && (
        <Card style={{ maxWidth: 540 }}>
          <CardTitle>Configure Interview</CardTitle>

          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>Interview Mode</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              {Object.entries(modeLabels).map(([m, label]) => (
                <div key={m} onClick={() => setForm({ ...form, mode: m })}
                  style={{ padding: '10px 6px', textAlign: 'center', border: `2px solid ${form.mode === m ? '#4f46e5' : '#e2e8f0'}`, borderRadius: 8, cursor: 'pointer', background: form.mode === m ? '#eef2ff' : '#fff', color: form.mode === m ? '#4f46e5' : '#64748b', fontWeight: 600, fontSize: 12 }}>
                  {label}
                </div>
              ))}
            </div>
            {form.mode === 'resume_based' && (
              <div style={{ marginTop: 8, padding: '8px 12px', background: '#eff6ff', borderRadius: 8, fontSize: 12, color: '#1e40af' }}>
                💡 Questions will be generated based on your uploaded resume.
              </div>
            )}
          </div>

          <Input label="Target Role" placeholder="e.g. Backend Developer, Data Analyst" value={form.target_role} onChange={set('target_role')} />

          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Questions: {form.num_questions}</label>
            <input type="range" min={3} max={10} value={form.num_questions} onChange={set('num_questions')} style={{ width: '100%' }} />
          </div>

          {hasSpeechAPI && (
            <div style={{ marginBottom: 16, padding: '12px 16px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, fontWeight: 600, color: '#166534' }}>
                <input type="checkbox" checked={voiceMode} onChange={e => setVoiceMode(e.target.checked)} style={{ width: 16, height: 16 }} />
                🎙️ Enable Voice Mode — AI speaks questions, you answer by voice
              </label>
            </div>
          )}

          <Btn onClick={handleStart} disabled={loading} style={{ width: '100%' }}>
            {loading ? <><Spinner />&nbsp;Starting…</> : '🚀 Start Interview →'}
          </Btn>
        </Card>
      )}

      {step === 'answering' && session && (
        <div style={{ maxWidth: 720 }}>
          {/* Progress */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#64748b', marginBottom: 8 }}>
              <span>Question <strong>{current + 1}</strong> of <strong>{session.questions.length}</strong></span>
              <div style={{ display: 'flex', gap: 8 }}>
                <Badge color="#4f46e5">{modeLabels[form.mode] || form.mode}</Badge>
                {voiceMode && <Badge color="#10b981">🎙️ Voice Mode</Badge>}
              </div>
            </div>
            <div style={{ height: 6, background: '#e2e8f0', borderRadius: 3 }}>
              <div style={{ height: '100%', background: '#4f46e5', borderRadius: 3, width: `${((current + 1) / session.questions.length) * 100}%`, transition: 'width .3s' }} />
            </div>
          </div>

          <Card style={{ marginBottom: 20 }}>
            {/* Question */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 20 }}>
              <div style={{ background: '#4f46e5', color: '#fff', borderRadius: '50%', width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, flexShrink: 0 }}>Q</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', lineHeight: 1.6 }}>
                {session.questions[current]}
              </div>
            </div>

            {/* AI speaking indicator */}
            {aiSpeaking && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: '#4f46e5', fontSize: 13 }}>
                <span style={{ animation: 'pulse 1s infinite' }}>🔊</span> AI is reading the question…
              </div>
            )}

            {/* Voice recording UI */}
            {voiceMode ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ marginBottom: 12, minHeight: 60, padding: 12, background: '#f8f9fb', borderRadius: 8, fontSize: 14, color: '#475569', textAlign: 'left' }}>
                  {answers[current] ? <span style={{ color: '#1e293b' }}>{answers[current]}</span> : transcript || <span style={{ color: '#94a3b8' }}>Your answer will appear here…</span>}
                </div>
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                  {!listening ? (
                    <button onClick={startListening} disabled={aiSpeaking}
                      style={{ background: '#ef4444', color: '#fff', border: 'none', borderRadius: '50%', width: 64, height: 64, fontSize: 24, cursor: 'pointer', boxShadow: '0 4px 12px rgba(239,68,68,.4)' }}>
                      🎙️
                    </button>
                  ) : (
                    <button onClick={stopListening}
                      style={{ background: '#ef4444', color: '#fff', border: 'none', borderRadius: '50%', width: 64, height: 64, fontSize: 24, cursor: 'pointer', animation: 'pulse 1s infinite', boxShadow: '0 4px 20px rgba(239,68,68,.6)' }}>
                      ⏹️
                    </button>
                  )}
                </div>
                <div style={{ marginTop: 8, fontSize: 12, color: '#94a3b8' }}>
                  {listening ? '🔴 Recording… click ⏹ to stop' : 'Click 🎙️ to start speaking'}
                </div>
              </div>
            ) : (
              <textarea
                style={{ width: '100%', padding: '12px 14px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 14, minHeight: 120, resize: 'vertical', outline: 'none', fontFamily: 'inherit', lineHeight: 1.6 }}
                placeholder="Type your answer here…"
                value={answers[current] || ''}
                onChange={e => { const a = [...answers]; a[current] = e.target.value; setAnswers(a) }}
              />
            )}
          </Card>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {current > 0 && <Btn variant="secondary" onClick={() => setCurrent(c => c - 1)}>← Prev</Btn>}
            {current < session.questions.length - 1 ? (
              <Btn onClick={() => { setCurrent(c => c + 1); setTranscript('') }}>Next →</Btn>
            ) : (
              <Btn onClick={handleEvaluate} disabled={loading}>
                {loading ? <><Spinner />&nbsp;Evaluating…</> : '📊 Submit & Get Feedback →'}
              </Btn>
            )}
            <Btn variant="secondary" onClick={() => { synth?.cancel(); setStep('setup') }}>Cancel</Btn>
          </div>
        </div>
      )}

      {step === 'result' && result && (
        <div style={{ maxWidth: 720 }}>
          <Card style={{ marginBottom: 20, textAlign: 'center', padding: 32 }}>
            <div style={{ fontSize: 64, fontWeight: 800, color: scoreColor(result.overall_score) }}>
              {result.overall_score?.toFixed(1)}%
            </div>
            <div style={{ color: '#64748b', marginTop: 4, fontSize: 16 }}>Overall Score</div>
            <div style={{ marginTop: 16, fontSize: 14, color: '#475569', maxWidth: 500, margin: '16px auto 0', lineHeight: 1.6 }}>
              {result.summary}
            </div>
            <div style={{ marginTop: 20 }}>
              <Btn onClick={() => setStep('setup')}>🔄 New Interview</Btn>
            </div>
          </Card>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <Card>
              <CardTitle>✅ Strengths</CardTitle>
              <ul style={{ paddingLeft: 18, fontSize: 14, color: '#475569' }}>
                {result.strengths?.map((s, i) => <li key={i} style={{ marginBottom: 6 }}>{s}</li>)}
              </ul>
            </Card>
            <Card>
              <CardTitle>📈 Improve</CardTitle>
              <ul style={{ paddingLeft: 18, fontSize: 14, color: '#475569' }}>
                {result.improvements?.map((s, i) => <li key={i} style={{ marginBottom: 6 }}>{s}</li>)}
              </ul>
            </Card>
          </div>

          <Card>
            <CardTitle>Question-by-Question Breakdown</CardTitle>
            {result.per_question?.map((q, i) => (
              <div key={i} style={{ padding: '14px 0', borderBottom: i < result.per_question.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 8 }}>
                  <div style={{ flex: 1, fontWeight: 600, fontSize: 14 }}>Q{i+1}. {q.question}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: scoreColor(q.score * 10), minWidth: 50, textAlign: 'right' }}>{q.score}/10</div>
                </div>
                <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>
                  <strong>Your answer:</strong> {q.answer || '(no answer)'}
                </div>
                <div style={{ fontSize: 13, color: '#475569', background: '#f8f9fb', padding: '8px 12px', borderRadius: 8 }}>{q.feedback}</div>
                {q.ideal_points?.length > 0 && (
                  <div style={{ marginTop: 6 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', marginBottom: 4 }}>KEY POINTS TO MENTION:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {q.ideal_points.map((p, j) => <span key={j} style={{ background: '#f0fdf4', color: '#166534', padding: '2px 8px', borderRadius: 20, fontSize: 11 }}>{p}</span>)}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </Card>
        </div>
      )}

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
      `}</style>
    </div>
  )
}
