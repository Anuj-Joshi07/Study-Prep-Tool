import React, { useState, useRef } from 'react'
import { uploadResume, matchJD } from '../api/client'
import { Card, CardTitle, Btn, Textarea, Spinner, Alert, Badge, PageHeader } from '../components/Card'

export default function Resume() {
  const studentId = localStorage.getItem('student_id')
  const fileRef = useRef()
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [resumeId, setResumeId] = useState(null)
  const [resumeName, setResumeName] = useState('')
  const [extractedSkills, setExtractedSkills] = useState([])
  const [jdText, setJdText] = useState('')
  const [jdResult, setJdResult] = useState(null)
  const [jdLoading, setJdLoading] = useState(false)

  const handleUpload = async () => {
    if (!file) { setError('Please select a resume file first.'); return }
    setError(''); setLoading(true); setJdResult(null)
    const fd = new FormData()
    fd.append('student_id', studentId)
    fd.append('file', file)
    try {
      const res = await uploadResume(fd)
      setResumeId(res.data.resume_id)
      setResumeName(file.name)
      setExtractedSkills(res.data.parsed?.skills || [])
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Please try again.')
    } finally { setLoading(false) }
  }

  const handleJDMatch = async () => {
    if (!resumeId) { setError('Upload a resume first.'); return }
    if (!jdText.trim()) { setError('Please paste a job description.'); return }
    setError(''); setJdLoading(true); setJdResult(null)
    try {
      const res = await matchJD({ resume_id: resumeId, jd_text: jdText })
      setJdResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'JD match failed. Please retry.')
    } finally { setJdLoading(false) }
  }

  const scoreColor = s => s >= 75 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444'

  return (
    <div>
      <PageHeader
        title="📄 Resume + JD Matcher"
        subtitle="Upload your resume, paste a job description, see how well you match"
      />

      {error && <Alert type="error">{error}</Alert>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        {/* ── LEFT COLUMN: upload + JD input ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Upload card */}
          <Card>
            <CardTitle>Step 1 — Upload Resume</CardTitle>
            <div
              onClick={() => fileRef.current?.click()}
              style={{
                border: `2px dashed ${resumeId ? '#10b981' : file ? '#4f46e5' : '#c7d2fe'}`,
                borderRadius: 10, padding: 36, textAlign: 'center',
                cursor: 'pointer',
                background: resumeId ? '#f0fdf4' : file ? '#eef2ff' : '#fafbff',
                marginBottom: 16, transition: 'all .2s',
              }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>
                {resumeId ? '✅' : '📄'}
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: resumeId ? '#166534' : '#4f46e5' }}>
                {resumeId ? `Uploaded: ${resumeName}` : file ? file.name : 'Click to select resume'}
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
                PDF, DOCX, or TXT — max 10 MB
              </div>
            </div>
            <input
              ref={fileRef} type="file" accept=".pdf,.docx,.txt"
              style={{ display: 'none' }}
              onChange={e => { setFile(e.target.files[0]); setResumeId(null); setJdResult(null) }}
            />
            <Btn
              onClick={handleUpload}
              disabled={loading || !file}
              style={{ width: '100%' }}
            >
              {loading ? <><Spinner />&nbsp;Uploading…</> : resumeId ? '🔄 Re-upload Resume' : '⬆️ Upload Resume →'}
            </Btn>

            {/* Extracted skills preview */}
            {extractedSkills.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 8 }}>
                  Skills found in your resume:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {extractedSkills.slice(0, 20).map((s, i) => (
                    <Badge key={i} color="#4f46e5">{s}</Badge>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* JD input card */}
          <Card>
            <CardTitle>Step 2 — Paste Job Description</CardTitle>
            {!resumeId && (
              <Alert type="warning">Upload your resume first (Step 1).</Alert>
            )}
            <Textarea
              placeholder={`Paste the full job description here…\n\nExample:\nWe are looking for a Full Stack Developer with 2+ years experience in React, Node.js, and PostgreSQL. You will design and build scalable web applications…`}
              value={jdText}
              onChange={e => setJdText(e.target.value)}
              style={{ minHeight: 200 }}
            />
            <Btn
              onClick={handleJDMatch}
              disabled={jdLoading || !resumeId || !jdText.trim()}
              style={{ width: '100%' }}
            >
              {jdLoading ? <><Spinner />&nbsp;Analyzing Match…</> : '🎯 Match Resume to Job →'}
            </Btn>
          </Card>
        </div>

        {/* ── RIGHT COLUMN: results ── */}
        <div>
          {jdResult ? (
            <Card>
              <CardTitle>Match Results</CardTitle>

              {/* Big score */}
              <div style={{
                textAlign: 'center', padding: '24px 0 20px',
                borderBottom: '1px solid #f1f5f9', marginBottom: 20,
              }}>
                <div style={{ fontSize: 72, fontWeight: 800, lineHeight: 1, color: scoreColor(jdResult.match_score) }}>
                  {jdResult.match_score?.toFixed(0)}%
                </div>
                <div style={{ fontSize: 14, color: '#64748b', marginTop: 6 }}>Match Score</div>
                <div style={{
                  display: 'inline-block', marginTop: 10,
                  padding: '4px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600,
                  background: jdResult.match_score >= 75 ? '#d1fae5' : jdResult.match_score >= 50 ? '#fef3c7' : '#fee2e2',
                  color: jdResult.match_score >= 75 ? '#065f46' : jdResult.match_score >= 50 ? '#92400e' : '#991b1b',
                }}>
                  {jdResult.match_score >= 75 ? '🟢 Strong Match' : jdResult.match_score >= 50 ? '🟡 Moderate Match' : '🔴 Weak Match'}
                </div>
              </div>

              {/* Matched skills */}
              {jdResult.matched_skills?.length > 0 && (
                <div style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#10b981', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ✅ Skills You Have ({jdResult.matched_skills.length})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {jdResult.matched_skills.map((s, i) => <Badge key={i} color="#10b981">{s}</Badge>)}
                  </div>
                </div>
              )}

              {/* Missing skills */}
              {jdResult.missing_skills?.length > 0 && (
                <div style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#ef4444', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ❌ Skills to Learn ({jdResult.missing_skills.length})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {jdResult.missing_skills.map((s, i) => <Badge key={i} color="#ef4444">{s}</Badge>)}
                  </div>
                </div>
              )}

              {/* Action items */}
              {jdResult.action_items?.length > 0 && (
                <div style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#475569', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    🎯 Action Items
                  </div>
                  <ul style={{ paddingLeft: 20, fontSize: 14, color: '#475569', margin: 0 }}>
                    {jdResult.action_items.map((a, i) => (
                      <li key={i} style={{ marginBottom: 8, lineHeight: 1.5 }}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendation */}
              {jdResult.recommendation && (
                <div style={{
                  padding: '14px 16px', background: '#eff6ff',
                  border: '1px solid #bfdbfe', borderRadius: 10,
                  fontSize: 14, color: '#1e40af', lineHeight: 1.7,
                }}>
                  💬 {jdResult.recommendation}
                </div>
              )}

              {/* Try another JD */}
              <div style={{ marginTop: 20 }}>
                <Btn variant="secondary" onClick={() => { setJdText(''); setJdResult(null) }}>
                  🔄 Try Another Job Description
                </Btn>
              </div>
            </Card>
          ) : (
            <Card style={{ textAlign: 'center', padding: 60 }}>
              <div style={{ fontSize: 56, marginBottom: 16 }}>🎯</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#475569', marginBottom: 8 }}>
                See how well your resume matches a job
              </div>
              <div style={{ fontSize: 14, color: '#94a3b8', lineHeight: 1.7 }}>
                1. Upload your resume<br />
                2. Paste a job description<br />
                3. Get a match score, skill gaps, and action plan
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
