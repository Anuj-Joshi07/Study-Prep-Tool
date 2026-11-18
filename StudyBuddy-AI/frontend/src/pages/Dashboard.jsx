import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard } from '../api/client'
import { Card, CardTitle, Stat, Badge, Spinner, PageHeader, Alert } from '../components/Card'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function Dashboard() {
  const navigate = useNavigate()
  const studentId = localStorage.getItem('student_id')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!studentId) { navigate('/login'); return }
    getDashboard(studentId)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load dashboard'))
      .finally(() => setLoading(false))
  }, [studentId])

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}><Spinner /></div>
  if (error) return <Alert type="error">{error}</Alert>
  if (!data) return null

  const { student, progress, quiz_trend, memory_facts, recommendations, latest_resume, latest_interview } = data

  return (
    <div>
      <PageHeader title={`Welcome back, ${student.name} 👋`} subtitle={`Target Role: ${student.target_role || 'Not set'}`} />

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 16, marginBottom: 24 }}>
        <Stat label="Avg Quiz Score" value={`${progress.avg_quiz_score}%`} color="#4f46e5" />
        <Stat label="Quizzes Taken" value={progress.total_quizzes} color="#10b981" />
        <Stat label="Topics Studied" value={progress.topics_studied} color="#f59e0b" />
        <Stat label="ATS Score" value={progress.ats_score ? `${progress.ats_score}%` : '—'} color="#6366f1" />
        <Stat label="Readiness" value={progress.readiness_score ? `${progress.readiness_score}%` : '—'} color="#ec4899" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Quiz trend */}
        <Card>
          <CardTitle>Quiz Score Trend</CardTitle>
          {quiz_trend.length > 1 ? (
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={quiz_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" hide />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Line type="monotone" dataKey="score" stroke="#4f46e5" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ color: '#94a3b8', fontSize: 13, padding: '20px 0' }}>Take quizzes to see your trend.</div>
          )}
        </Card>

        {/* Recommendations */}
        <Card>
          <CardTitle>🎯 Recommended Topics</CardTitle>
          {recommendations.length ? (
            <ul style={{ paddingLeft: 18, color: '#475569', fontSize: 14 }}>
              {recommendations.map((r, i) => <li key={i} style={{ marginBottom: 6 }}>{r}</li>)}
            </ul>
          ) : <div style={{ color: '#94a3b8', fontSize: 13 }}>Chat with the AI tutor to get personalized recommendations.</div>}
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Weak concepts */}
        <Card>
          <CardTitle>⚠️ Weak Areas</CardTitle>
          {progress.weak_concepts.length ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {progress.weak_concepts.map((c, i) => <Badge key={i} color="#ef4444">{c.slice(0, 40)}</Badge>)}
            </div>
          ) : <div style={{ color: '#94a3b8', fontSize: 13 }}>No weak areas identified yet.</div>}
        </Card>

        {/* Memory facts */}
        <Card>
          <CardTitle>🧠 Memory Facts</CardTitle>
          {memory_facts.length ? (
            <ul style={{ paddingLeft: 18, color: '#475569', fontSize: 13 }}>
              {memory_facts.slice(0, 5).map((f, i) => <li key={i} style={{ marginBottom: 4 }}>{f}</li>)}
            </ul>
          ) : <div style={{ color: '#94a3b8', fontSize: 13 }}>Facts extracted from your conversations appear here.</div>}
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Latest resume */}
        <Card>
          <CardTitle>📄 Latest Resume</CardTitle>
          {latest_resume ? (
            <>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{latest_resume.filename}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#64748b', fontSize: 13 }}>ATS Score:</span>
                <Badge color="#10b981">{latest_resume.ats_score?.toFixed(1)}%</Badge>
              </div>
            </>
          ) : <div style={{ color: '#94a3b8', fontSize: 13 }}>Upload a resume to get your ATS score.</div>}
        </Card>

        {/* Latest interview */}
        <Card>
          <CardTitle>🎤 Latest Interview</CardTitle>
          {latest_interview ? (
            <>
              <div style={{ fontWeight: 600, marginBottom: 4, textTransform: 'capitalize' }}>{latest_interview.mode} Interview</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#64748b', fontSize: 13 }}>Score:</span>
                <Badge color="#6366f1">{latest_interview.overall_score?.toFixed(1)}%</Badge>
              </div>
            </>
          ) : <div style={{ color: '#94a3b8', fontSize: 13 }}>Practice mock interviews to build confidence.</div>}
        </Card>
      </div>
    </div>
  )
}
