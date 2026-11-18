import React, { useState } from 'react'
import { generateRoadmap } from '../api/client'
import { Card, CardTitle, Btn, Input, Textarea, Spinner, Alert, Badge, PageHeader } from '../components/Card'

const typeIcon = { youtube: '▶️', docs: '📄', article: '📰', course: '🎓' }
const typeColor = { youtube: '#ef4444', docs: '#3b82f6', article: '#8b5cf6', course: '#10b981' }

export default function Roadmap() {
  const studentId = localStorage.getItem('student_id')
  const [form, setForm] = useState({ target_role: '', duration_weeks: 8, jd_text: '' })
  const [roadmap, setRoadmap] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [openWeek, setOpenWeek] = useState(1)

  const set = k => e => setForm({ ...form, [k]: e.target.value })

  const handleGenerate = async () => {
    if (!form.target_role.trim()) { setError('Please enter a target role.'); return }
    setError(''); setLoading(true); setRoadmap(null)
    try {
      const res = await generateRoadmap({
        student_id: studentId,
        target_role: form.target_role,
        duration_weeks: parseInt(form.duration_weeks),
        jd_text: form.jd_text || undefined,
      })
      setRoadmap(res.data)
      setOpenWeek(1)
    } catch (e) { setError(e.response?.data?.detail || 'Generation failed.') }
    finally { setLoading(false) }
  }

  return (
    <div>
      <PageHeader title="🗺️ Learning Roadmap" subtitle="Personalized week-by-week career plan with YouTube & documentation links" />
      {error && <Alert type="error">{error}</Alert>}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Config */}
        <div>
          <Card>
            <CardTitle>Generate Roadmap</CardTitle>
            <Input label="Target Role *" placeholder="e.g. Full Stack Developer, Data Scientist, DevOps Engineer" value={form.target_role} onChange={set('target_role')} />
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Duration: {form.duration_weeks} Weeks</label>
              <input type="range" min={4} max={16} step={4} value={form.duration_weeks} onChange={set('duration_weeks')} style={{ width: '100%' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                {[4,8,12,16].map(w => <span key={w}>{w}w</span>)}
              </div>
            </div>
            <Textarea label="Job Description (optional)" placeholder="Paste a JD for a more targeted roadmap…" value={form.jd_text} onChange={set('jd_text')} />
            <Btn onClick={handleGenerate} disabled={loading} style={{ width: '100%' }}>
              {loading ? <><Spinner />&nbsp;Generating…</> : '🗺️ Generate Roadmap →'}
            </Btn>
          </Card>

          {roadmap && (
            <Card style={{ marginTop: 16 }}>
              <CardTitle>📌 Skill Gaps</CardTitle>
              {roadmap.skill_gaps?.length ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {roadmap.skill_gaps.slice(0, 12).map((g, i) => <Badge key={i} color="#f59e0b">{g}</Badge>)}
                </div>
              ) : <div style={{ color: '#94a3b8', fontSize: 13 }}>No significant gaps identified.</div>}
            </Card>
          )}
        </div>

        {/* Roadmap */}
        <div>
          {loading && (
            <Card style={{ textAlign: 'center', padding: 60 }}>
              <Spinner />
              <div style={{ marginTop: 16, color: '#64748b', fontSize: 15 }}>Building your personalized roadmap with resources…</div>
            </Card>
          )}

          {roadmap && !loading && (
            <>
              <Card style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, flexWrap: 'wrap' }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>{roadmap.target_role}</div>
                  <Badge color="#4f46e5">{roadmap.duration_weeks} Weeks</Badge>
                </div>
                {roadmap.overview && <div style={{ color: '#64748b', fontSize: 14, lineHeight: 1.6 }}>{roadmap.overview}</div>}
                {roadmap.final_milestone && (
                  <div style={{ marginTop: 12, padding: '8px 14px', background: '#eef2ff', borderRadius: 8, fontSize: 13, color: '#3730a3', fontWeight: 500 }}>
                    🏆 Final Goal: {roadmap.final_milestone}
                  </div>
                )}
              </Card>

              {roadmap.weeks?.map(week => (
                <div key={week.week} style={{ marginBottom: 10 }}>
                  <div
                    onClick={() => setOpenWeek(openWeek === week.week ? null : week.week)}
                    style={{ background: openWeek === week.week ? '#4f46e5' : '#fff', color: openWeek === week.week ? '#fff' : '#1e293b', padding: '14px 18px', borderRadius: openWeek === week.week ? '10px 10px 0 0' : 10, border: '1px solid #e2e8f0', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontWeight: 600, fontSize: 14 }}>
                    <span>Week {week.week}: {week.focus}</span>
                    <span style={{ opacity: 0.7 }}>{openWeek === week.week ? '▲' : '▼'}</span>
                  </div>

                  {openWeek === week.week && (
                    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderTop: 'none', borderRadius: '0 0 10px 10px', padding: 20 }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 8 }}>📚 Topics to Study</div>
                          <ul style={{ paddingLeft: 18, fontSize: 13, color: '#475569', margin: 0 }}>
                            {(week.topics || []).map((t, i) => <li key={i} style={{ marginBottom: 4 }}>{t}</li>)}
                          </ul>
                        </div>
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 8 }}>🛠️ Mini Projects</div>
                          <ul style={{ paddingLeft: 18, fontSize: 13, color: '#475569', margin: 0 }}>
                            {(week.projects || []).map((p, i) => <li key={i} style={{ marginBottom: 4 }}>{p}</li>)}
                          </ul>
                        </div>
                      </div>

                      {/* Resources with links */}
                      {week.resources?.length > 0 && (
                        <div style={{ marginBottom: 14 }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 10 }}>🔗 Resources & Links</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {week.resources.map((r, i) => {
                              const res = typeof r === 'string' ? { title: r, type: 'article', url: '', description: r } : r
                              const color = typeColor[res.type] || '#64748b'
                              const icon = typeIcon[res.type] || '🔗'
                              return (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#f8f9fb', borderRadius: 8, border: `1px solid ${color}22` }}>
                                  <span style={{ fontSize: 18 }}>{icon}</span>
                                  <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginBottom: 2 }}>{res.title}</div>
                                    {res.description && <div style={{ fontSize: 11, color: '#64748b' }}>{res.description}</div>}
                                  </div>
                                  {res.url ? (
                                    <a href={res.url} target="_blank" rel="noopener noreferrer"
                                      style={{ background: color, color: '#fff', padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap', textDecoration: 'none' }}>
                                      Open →
                                    </a>
                                  ) : (
                                    <Badge color={color}>{res.type}</Badge>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#166534' }}>
                        🎯 <strong>Week Milestone:</strong> {week.milestone}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </>
          )}

          {!roadmap && !loading && (
            <Card style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>🗺️</div>
              <div style={{ fontSize: 15, fontWeight: 600, color: '#64748b' }}>Fill the form to generate your personalized roadmap</div>
              <div style={{ fontSize: 13, marginTop: 8 }}>Includes YouTube playlists, official docs, and project ideas for each week</div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
