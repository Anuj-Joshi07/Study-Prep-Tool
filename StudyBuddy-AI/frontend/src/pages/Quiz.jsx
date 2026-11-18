import React, { useState } from 'react'
import { generateQuiz, submitQuiz } from '../api/client'
import { Card, CardTitle, Btn, Input, Spinner, Alert, Badge, PageHeader } from '../components/Card'

export default function Quiz() {
  const studentId = localStorage.getItem('student_id')
  const [form, setForm] = useState({ topic: '', difficulty: 'medium', num_questions: 5, domain: '' })
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState('setup')

  const set = k => e => setForm({ ...form, [k]: e.target.value })

  const handleGenerate = async () => {
    if (!form.topic.trim()) { setError('Please enter a topic.'); return }
    setError(''); setLoading(true); setResult(null); setAnswers({})
    try {
      const res = await generateQuiz({
        student_id: studentId,
        topic: form.topic,
        difficulty: form.difficulty,
        num_questions: parseInt(form.num_questions),
        domain: form.domain || undefined,
      })
      const q = res.data
      if (!q.questions || q.questions.length === 0) {
        setError('Quiz generated but had no valid questions. Please try a different topic.')
        setLoading(false); return
      }
      setQuiz(q)
      setStep('taking')
    } catch (e) { setError(e.response?.data?.detail || 'Failed to generate quiz. Check your connection.') }
    finally { setLoading(false) }
  }

  const handleSubmit = async () => {
    if (!quiz) return
    setLoading(true); setError('')
    try {
      const res = await submitQuiz({ quiz_id: quiz.quiz_id, student_id: studentId, answers })
      setResult(res.data); setStep('result')
    } catch (e) { setError(e.response?.data?.detail || 'Submission failed.') }
    finally { setLoading(false) }
  }

  const scoreColor = s => s >= 80 ? '#10b981' : s >= 60 ? '#f59e0b' : '#ef4444'

  return (
    <div>
      <PageHeader title="📝 Adaptive Quiz" subtitle="AI-generated quizzes tailored to your level and weak areas" />
      {error && <Alert type="error">{error}</Alert>}

      {step === 'setup' && (
        <Card style={{ maxWidth: 520 }}>
          <CardTitle>Generate a Quiz</CardTitle>
          <Input label="Topic *" placeholder="e.g. Binary Trees, React Hooks, SQL JOINs, Machine Learning" value={form.topic} onChange={set('topic')} />
          <Input label="Domain (optional)" placeholder="e.g. DSA, Web Dev, Python, System Design" value={form.domain} onChange={set('domain')} />
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Difficulty</label>
            <div style={{ display: 'flex', gap: 10 }}>
              {['easy', 'medium', 'hard'].map(d => (
                <div key={d} onClick={() => setForm({ ...form, difficulty: d })}
                  style={{ flex: 1, padding: '8px 0', textAlign: 'center', border: `2px solid ${form.difficulty === d ? '#4f46e5' : '#e2e8f0'}`, borderRadius: 8, cursor: 'pointer', background: form.difficulty === d ? '#eef2ff' : '#fff', color: form.difficulty === d ? '#4f46e5' : '#64748b', fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>
                  {d}
                </div>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Number of Questions: {form.num_questions}</label>
            <input type="range" min={3} max={15} value={form.num_questions} onChange={set('num_questions')} style={{ width: '100%' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#94a3b8' }}><span>3</span><span>15</span></div>
          </div>
          <Btn onClick={handleGenerate} disabled={loading} style={{ width: '100%' }}>
            {loading ? <><Spinner /> &nbsp;Generating Quiz…</> : '🎯 Generate Quiz →'}
          </Btn>
        </Card>
      )}

      {step === 'taking' && quiz && (
        <div style={{ maxWidth: 720 }}>
          <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <Badge color="#4f46e5">{quiz.topic}</Badge>
            <Badge color="#f59e0b">{quiz.difficulty}</Badge>
            <span style={{ color: '#64748b', fontSize: 13 }}>{quiz.questions.length} questions</span>
            <Btn variant="secondary" onClick={() => setStep('setup')} style={{ marginLeft: 'auto' }}>← New Quiz</Btn>
          </div>

          {quiz.questions.map((q, i) => (
            <Card key={q.id} style={{ marginBottom: 16, borderLeft: answers[q.id] ? '3px solid #4f46e5' : '3px solid #e2e8f0' }}>
              <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                <div style={{ background: '#eef2ff', color: '#4f46e5', borderRadius: 20, width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13, flexShrink: 0 }}>{i + 1}</div>
                <div style={{ fontWeight: 600, color: '#1e293b', fontSize: 14, lineHeight: 1.5 }}>{q.question}</div>
              </div>

              {q.type === 'short_answer' ? (
                <textarea
                  style={{ width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 14, minHeight: 80, resize: 'vertical', outline: 'none', fontFamily: 'inherit' }}
                  placeholder="Type your answer here…"
                  value={answers[q.id] || ''}
                  onChange={e => setAnswers({ ...answers, [q.id]: e.target.value })}
                />
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(q.options || []).map((opt, j) => {
                    const letter = opt.charAt(0)
                    const selected = answers[q.id] === letter || answers[q.id] === opt
                    return (
                      <div key={j} onClick={() => setAnswers({ ...answers, [q.id]: letter })}
                        style={{ padding: '10px 14px', border: `2px solid ${selected ? '#4f46e5' : '#e2e8f0'}`, borderRadius: 8, cursor: 'pointer', background: selected ? '#eef2ff' : '#fafafa', color: selected ? '#3730a3' : '#475569', fontWeight: selected ? 600 : 400, fontSize: 14, transition: 'all .15s' }}>
                        {opt}
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>
          ))}

          <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
            <Btn onClick={handleSubmit} disabled={loading}>
              {loading ? <><Spinner /> &nbsp;Submitting…</> : '✅ Submit Quiz →'}
            </Btn>
            <span style={{ fontSize: 12, color: '#94a3b8', alignSelf: 'center' }}>
              {Object.keys(answers).length}/{quiz.questions.length} answered
            </span>
          </div>
        </div>
      )}

      {step === 'result' && result && (
        <div style={{ maxWidth: 720 }}>
          <Card style={{ marginBottom: 20, textAlign: 'center', padding: 32 }}>
            <div style={{ fontSize: 64, fontWeight: 800, color: scoreColor(result.score), lineHeight: 1 }}>{result.score}%</div>
            <div style={{ fontSize: 18, color: '#64748b', marginTop: 8 }}>{result.correct} of {result.total} correct</div>
            <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center', gap: 12 }}>
              <Btn onClick={() => { setStep('setup'); setQuiz(null) }}>🎯 New Quiz</Btn>
              <Btn variant="secondary" onClick={() => setStep('taking')}>👁️ Review Answers</Btn>
            </div>
          </Card>

          {result.weak_concepts?.length > 0 && (
            <Card style={{ marginBottom: 16 }}>
              <CardTitle>⚠️ Concepts to Review</CardTitle>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {result.weak_concepts.map((c, i) => <Badge key={i} color="#ef4444">{c.slice(0, 60)}</Badge>)}
              </div>
            </Card>
          )}

          <Card style={{ marginBottom: 16 }}>
            <CardTitle>📋 Answer Review</CardTitle>
            {Object.values(result.feedback || {}).map((fb, i) => (
              <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Q{i+1}. {fb.question}</div>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                  Your answer: <strong>{fb.student_answer || '(no answer)'}</strong>
                  {!fb.is_correct && <span style={{ color: '#10b981', marginLeft: 8 }}>Correct: <strong>{fb.correct_answer}</strong></span>}
                </div>
                <div style={{ fontSize: 13, color: fb.is_correct ? '#065f46' : '#991b1b', background: fb.is_correct ? '#f0fdf4' : '#fef2f2', padding: '6px 10px', borderRadius: 6 }}>
                  {fb.feedback}
                </div>
              </div>
            ))}
          </Card>

          <Card>
            <CardTitle>💡 Recommendations</CardTitle>
            <ul style={{ paddingLeft: 18, color: '#475569', fontSize: 14 }}>
              {result.recommendations?.map((r, i) => <li key={i} style={{ marginBottom: 6 }}>{r}</li>)}
            </ul>
          </Card>
        </div>
      )}
    </div>
  )
}
