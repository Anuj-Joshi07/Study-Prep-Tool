import React, { useState, useEffect, useRef } from 'react'
import { uploadDocument, listDocuments, deleteDocument, queryDocuments } from '../api/client'
import { Card, CardTitle, Btn, Textarea, Spinner, Alert, Badge, PageHeader } from '../components/Card'
import ReactMarkdown from 'react-markdown'

export default function Documents() {
  const studentId = localStorage.getItem('student_id')
  const fileRef = useRef()
  const [docs, setDocs] = useState([])
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState(null)
  const [querying, setQuerying] = useState(false)

  const load = async () => {
    try {
      const r = await listDocuments(studentId)
      setDocs(Array.isArray(r.data) ? r.data : [])
    } catch { setDocs([]) }
  }

  useEffect(() => { if (studentId) load() }, [studentId])

  const handleUpload = async () => {
    if (!file) { setError('Please select a file first.'); return }
    setError(''); setSuccess(''); setUploading(true)
    const fd = new FormData()
    fd.append('student_id', studentId)
    fd.append('file', file)
    try {
      const r = await uploadDocument(fd)
      setSuccess(`✅ "${r.data.filename}" uploaded and indexed into ${r.data.chunk_count} chunks!`)
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      await load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Check the file format and size.')
    } finally { setUploading(false) }
  }

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return
    try {
      await deleteDocument(id)
      setDocs(docs.filter(d => d.document_id !== id))
      setSuccess(`Deleted "${name}"`)
    } catch { setError('Delete failed.') }
  }

  const handleQuery = async () => {
    if (!query.trim()) return
    if (docs.length === 0) { setError('Upload at least one document first.'); return }
    setError(''); setQuerying(true); setQueryResult(null)
    try {
      const res = await queryDocuments({ student_id: studentId, query: query.trim(), top_k: 4 })
      setQueryResult(res.data)
    } catch (e) { setError(e.response?.data?.detail || 'Query failed.') }
    finally { setQuerying(false) }
  }

  const fileTypeColor = t => ({ pdf: '#ef4444', docx: '#3b82f6', txt: '#10b981', md: '#8b5cf6' })[t] || '#64748b'

  return (
    <div>
      <PageHeader title="📚 Documents" subtitle="Upload your notes — AI answers questions based on your own materials" />

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Left: upload + list */}
        <div>
          <Card style={{ marginBottom: 16 }}>
            <CardTitle>Upload Document</CardTitle>
            <div
              onClick={() => fileRef.current?.click()}
              style={{ border: `2px dashed ${file ? '#4f46e5' : '#c7d2fe'}`, borderRadius: 10, padding: 24, textAlign: 'center', cursor: 'pointer', background: file ? '#eef2ff' : '#fafbff', marginBottom: 14, transition: 'all .2s' }}>
              <div style={{ fontSize: 32, marginBottom: 6 }}>{file ? '📎' : '📤'}</div>
              <div style={{ fontSize: 13, color: '#4f46e5', fontWeight: 600 }}>
                {file ? file.name : 'Click to select file'}
              </div>
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>PDF, DOCX, TXT, MD — max 10 MB</div>
            </div>
            <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" style={{ display: 'none' }}
              onChange={e => { setFile(e.target.files[0]); setSuccess('') }} />
            <Btn onClick={handleUpload} disabled={uploading || !file} style={{ width: '100%' }}>
              {uploading ? <><Spinner />&nbsp;Uploading & Indexing…</> : '⬆️ Upload & Index →'}
            </Btn>
          </Card>

          <Card>
            <CardTitle>Your Documents ({docs.length})</CardTitle>
            {docs.length === 0 ? (
              <div style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', padding: '12px 0' }}>
                No documents yet. Upload a PDF, DOCX, or TXT file to get started.
              </div>
            ) : docs.map(d => (
              <div key={d.document_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.filename}</div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
                    <Badge color={fileTypeColor(d.file_type)}>{(d.file_type || '?').toUpperCase()}</Badge>
                    <Badge color="#64748b">{d.chunk_count} chunks</Badge>
                    {d.indexed && <Badge color="#10b981">✓ Indexed</Badge>}
                  </div>
                </div>
                <button onClick={() => handleDelete(d.document_id, d.filename)}
                  style={{ background: '#fee2e2', color: '#dc2626', border: 'none', borderRadius: 6, padding: '4px 10px', cursor: 'pointer', fontSize: 13, marginLeft: 8, flexShrink: 0 }}>✕</button>
              </div>
            ))}
          </Card>
        </div>

        {/* Right: query */}
        <div>
          <Card style={{ marginBottom: 16 }}>
            <CardTitle>🔍 Ask Your Documents</CardTitle>
            <Textarea
              placeholder="Ask anything about your uploaded notes…&#10;e.g. 'Explain the main concepts from my notes' or 'What did I study about sorting algorithms?'"
              value={query}
              onChange={e => setQuery(e.target.value)}
              style={{ minHeight: 100 }}
            />
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <Btn onClick={handleQuery} disabled={querying || !query.trim()}>
                {querying ? <><Spinner />&nbsp;Searching…</> : '🔍 Search & Answer →'}
              </Btn>
              {docs.length === 0 && (
                <span style={{ fontSize: 12, color: '#f59e0b' }}>⚠️ Upload documents first</span>
              )}
            </div>
          </Card>

          {queryResult && (
            <Card>
              <CardTitle>💡 Answer</CardTitle>
              <div style={{ fontSize: 14, color: '#1e293b', lineHeight: 1.8, marginBottom: 16 }}>
                <ReactMarkdown>{queryResult.answer}</ReactMarkdown>
              </div>

              {queryResult.sources?.length > 0 && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Source Excerpts Used
                  </div>
                  {queryResult.sources.map((src, i) => (
                    <div key={i} style={{ background: '#f8f9fb', border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 14px', fontSize: 12, color: '#475569', marginBottom: 8, lineHeight: 1.6 }}>
                      <span style={{ color: '#94a3b8', fontWeight: 600, marginRight: 6 }}>#{i+1}</span>
                      {src.length > 300 ? src.slice(0, 300) + '…' : src}
                    </div>
                  ))}
                </div>
              )}

              {(!queryResult.sources || queryResult.sources.length === 0) && (
                <Alert type="warning">No matching content found in your documents. The answer is from general AI knowledge.</Alert>
              )}
            </Card>
          )}

          {!queryResult && !querying && (
            <Card style={{ textAlign: 'center', padding: 50 }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>🔍</div>
              <div style={{ fontSize: 15, fontWeight: 600, color: '#64748b' }}>Upload documents and ask questions</div>
              <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 8, lineHeight: 1.6 }}>
                The AI will search your notes and provide answers<br />grounded in your own study materials
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
