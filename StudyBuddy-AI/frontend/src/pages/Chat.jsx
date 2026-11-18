import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendChat, getConversations } from '../api/client'
import { Spinner, Btn, Badge } from '../components/Card'

const s = {
  page: { display: 'flex', height: 'calc(100vh - 48px)', gap: 0 },
  sidebar: { width: 220, background: '#fff', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', flexShrink: 0 },
  sideHead: { padding: '14px 16px', borderBottom: '1px solid #e2e8f0', fontWeight: 700, fontSize: 13, color: '#1e293b' },
  convItem: (active) => ({ padding: '10px 16px', cursor: 'pointer', fontSize: 12, borderBottom: '1px solid #f1f5f9', background: active ? '#eef2ff' : 'transparent', color: active ? '#4f46e5' : '#475569' }),
  chat: { flex: 1, display: 'flex', flexDirection: 'column', background: '#f8f9fb' },
  messages: { flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 },
  bubble: (role) => ({
    maxWidth: '72%', padding: '10px 14px', borderRadius: role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
    background: role === 'user' ? '#4f46e5' : '#fff', color: role === 'user' ? '#fff' : '#1e293b',
    alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    boxShadow: '0 1px 3px rgba(0,0,0,.08)', fontSize: 14, lineHeight: 1.6,
    border: role === 'assistant' ? '1px solid #e2e8f0' : 'none',
  }),
  inputBar: { padding: '12px 20px', background: '#fff', borderTop: '1px solid #e2e8f0', display: 'flex', gap: 10 },
  input: { flex: 1, padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: 10, fontSize: 14, outline: 'none', resize: 'none' },
  sendBtn: { padding: '10px 20px', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 600, cursor: 'pointer', fontSize: 14 },
}

export default function Chat() {
  const studentId = localStorage.getItem('student_id')
  const [convId, setConvId] = useState(null)
  const [convs, setConvs] = useState([])
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [useRag, setUseRag] = useState(true)
  const bottomRef = useRef()

  useEffect(() => {
    if (studentId) {
      getConversations(studentId).then(r => setConvs(r.data)).catch(() => {})
    }
  }, [studentId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input.trim() }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await sendChat({
        student_id: studentId,
        message: userMsg.content,
        conversation_id: convId || undefined,
        use_rag: useRag,
      })
      const d = res.data
      if (!convId) {
        setConvId(d.conversation_id)
        getConversations(studentId).then(r => setConvs(r.data)).catch(() => {})
      }
      setMessages(m => [...m, { role: 'assistant', content: d.reply, intent: d.intent, suggestions: d.suggested_topics }])
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', content: '⚠️ Error: ' + (err.response?.data?.detail || err.message) }])
    } finally {
      setLoading(false)
    }
  }

  const newConv = () => { setConvId(null); setMessages([]) }

  return (
    <div style={s.page}>
      {/* Sidebar */}
      <div style={s.sidebar}>
        <div style={s.sideHead}>
          Conversations
          <button onClick={newConv} style={{ float: 'right', background: '#eef2ff', color: '#4f46e5', border: 'none', borderRadius: 6, padding: '2px 8px', cursor: 'pointer', fontSize: 11, fontWeight: 600 }}>+ New</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {convs.map(c => (
            <div key={c.id} style={s.convItem(c.id === convId)} onClick={() => { setConvId(c.id); setMessages([]) }}>
              {c.title || 'Untitled'}
            </div>
          ))}
          {!convs.length && <div style={{ padding: 16, color: '#94a3b8', fontSize: 12 }}>No conversations yet.</div>}
        </div>
        <div style={{ padding: '12px 16px', borderTop: '1px solid #f1f5f9' }}>
          <label style={{ fontSize: 12, color: '#475569', display: 'flex', gap: 6, alignItems: 'center', cursor: 'pointer' }}>
            <input type="checkbox" checked={useRag} onChange={e => setUseRag(e.target.checked)} />
            Use my documents (RAG)
          </label>
        </div>
      </div>

      {/* Chat area */}
      <div style={s.chat}>
        {!messages.length && (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 10, color: '#94a3b8' }}>
            <div style={{ fontSize: 48 }}>💬</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#64748b' }}>Ask anything or say "Teach me about..."</div>
            <div style={{ fontSize: 13 }}>Your AI tutor is ready</div>
          </div>
        )}

        <div style={s.messages}>
          {messages.map((m, i) => (
            <div key={i} style={s.bubble(m.role)}>
              {m.role === 'assistant'
                ? <ReactMarkdown>{m.content}</ReactMarkdown>
                : m.content
              }
              {m.intent && m.intent !== 'general' && (
                <div style={{ marginTop: 6 }}>
                  <Badge color="#4f46e5">{m.intent}</Badge>
                </div>
              )}
              {m.suggestions?.length > 0 && (
                <div style={{ marginTop: 10, borderTop: '1px solid #e2e8f0', paddingTop: 8 }}>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6 }}>📌 Suggested topics:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {m.suggestions.map((s, j) => (
                      <span key={j} onClick={() => setInput(`Teach me about ${s}`)}
                        style={{ background: '#eef2ff', color: '#4f46e5', padding: '2px 8px', borderRadius: 20, fontSize: 11, cursor: 'pointer' }}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ ...s.bubble('assistant'), display: 'flex', alignItems: 'center', gap: 8 }}>
              <Spinner /> Thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div style={s.inputBar}>
          <textarea
            style={s.input}
            rows={1}
            placeholder="Ask a question or say 'Teach me about Python…'"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          />
          <button style={s.sendBtn} onClick={send} disabled={loading}>Send →</button>
        </div>
      </div>
    </div>
  )
}
