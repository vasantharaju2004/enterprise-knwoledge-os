import { useState, useEffect } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'

interface AuthResponse {
  token: string
  user_id: string
  org_id: string
}

interface UploadResult {
  document_id: string
  filename: string
  status: string
}

interface FileUploadState {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  result?: UploadResult
  error?: string
}

interface DocumentSummary {
  id: string
  filename: string
  status: string
}

interface QuerySource {
  document_id: string
  chunk_index: number
  rerank_score?: number
}

interface QueryResult {
  answer: string
  sources: QuerySource[]
  provider_used: string | null
}

interface ChatTurn {
  question: string
  answer: string
  provider_used: string | null
}

// Single shared helper: every authenticated request goes through
// this, so the Authorization header is attached exactly once,
// consistently — not retyped at five separate call sites where
// one could silently be missed or misspelled.
function authFetch(token: string, path: string, options: RequestInit = {}) {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  })
}

// Small mark used on the auth screen and in the header — a stack of
// three index cards, echoing the document/ledger metaphor used
// throughout the product.
function BrandGlyph() {
  return (
    <svg className="glyph" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="4" width="18" height="20" rx="1.5" fill="#262d3a" stroke="#4a9587" strokeWidth="1.2" />
      <rect x="3" y="8" width="18" height="20" rx="1.5" fill="#1f2530" stroke="#343d4c" strokeWidth="1.2" />
      <line x1="7" y1="13" x2="17" y2="13" stroke="#8b94a3" strokeWidth="1" />
      <line x1="7" y1="17" x2="14" y2="17" stroke="#8b94a3" strokeWidth="1" />
      <line x1="7" y1="21" x2="16" y2="21" stroke="#8b94a3" strokeWidth="1" />
    </svg>
  )
}

function BrandMark() {
  return (
    <div className="brand-mark">
      <BrandGlyph />
      <div className="wordmark">
        Enterprise Knowledge OS
        <small>Document intelligence</small>
      </div>
    </div>
  )
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: (auth: AuthResponse) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setError(null)
    setLoading(true)
    try {
      const endpoint = mode === 'login' ? '/login' : '/register'
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!response.ok) {
        const errBody = await response.json()
        throw new Error(errBody.detail || `${mode} failed`)
      }
      const data: AuthResponse = await response.json()
      localStorage.setItem('auth', JSON.stringify(data))
      onAuthenticated(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <BrandMark />
        <p className="auth-eyebrow">{mode === 'login' ? 'Welcome back' : 'Create an account'}</p>
        <h1 className="auth-title">{mode === 'login' ? 'Log in' : 'Register'}</h1>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
        </div>

        <button className="btn btn-primary" onClick={handleSubmit} disabled={loading || !email || !password}>
          {loading ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Register'}
        </button>

        {error && <p className="form-error">{error}</p>}

        <p className="auth-switch">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              setMode(mode === 'login' ? 'register' : 'login')
            }}
          >
            {mode === 'login' ? 'Register' : 'Log in'}
          </a>
        </p>
      </div>
    </div>
  )
}

function MainApp({ auth, onLogout }: { auth: AuthResponse; onLogout: () => void }) {
  const [uploads, setUploads] = useState<FileUploadState[]>([])
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [selectedDocId, setSelectedDocId] = useState<string>('')
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [thread, setThread] = useState<ChatTurn[]>([])

  const loadDocuments = async () => {
    try {
      const response = await authFetch(auth.token, '/documents')
      const data: DocumentSummary[] = await response.json()
      setDocuments(data)
    } catch {
      // Non-critical.
    }
  }

  const loadHistory = async () => {
    try {
      const response = await authFetch(auth.token, '/history')
      const data: ChatTurn[] = await response.json()
      setThread(data.reverse())
    } catch {
      // Non-critical.
    }
  }

  useEffect(() => {
    loadDocuments()
    loadHistory()
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    setUploads(files.map((file) => ({ file, status: 'pending' })))
  }

  const uploadOne = async (index: number, file: File) => {
    setUploads((prev) => prev.map((u, i) => (i === index ? { ...u, status: 'uploading' } : u)))
    const formData = new FormData()
    formData.append('file', file)
    try {
      const response = await authFetch(auth.token, '/upload', { method: 'POST', body: formData })
      if (!response.ok) {
        const errBody = await response.json()
        throw new Error(errBody.detail || `Upload failed (${response.status})`)
      }
      const data: UploadResult = await response.json()
      setUploads((prev) => prev.map((u, i) => (i === index ? { ...u, status: 'success', result: data } : u)))

      // The API returned instantly with "processing" — the real
      // work is happening in the background worker. Poll the
      // document list until THIS specific document's status
      // changes, rather than trusting the immediate response.
      pollForCompletion(index, data.document_id)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong'
      setUploads((prev) => prev.map((u, i) => (i === index ? { ...u, status: 'error', error: message } : u)))
    }
  }

  const pollForCompletion = (index: number, documentId: string) => {
    const intervalId = setInterval(async () => {
      try {
        const response = await authFetch(auth.token, '/documents')
        const docs: DocumentSummary[] = await response.json()
        const match = docs.find((d) => d.id === documentId)

        if (match && (match.status === 'embedded' || match.status === 'failed')) {
          clearInterval(intervalId)
          setUploads((prev) =>
            prev.map((u, i) =>
              i === index
                ? { ...u, status: match.status === 'embedded' ? 'success' : 'error',
                    result: { document_id: documentId, filename: u.file.name, status: match.status },
                    error: match.status === 'failed' ? 'Processing failed on the server.' : undefined }
                : u
            )
          )
          loadDocuments()
        }
      } catch {
        // A transient poll failure isn't fatal — just try again
        // on the next interval tick.
      }
    }, 2000)
  }

  const handleUploadAll = () => {
    uploads.forEach((u, i) => {
      if (u.status === 'pending') uploadOne(i, u.file)
    })
  }

  const handleAsk = async () => {
    if (!question.trim()) return
    const askedQuestion = question
    setAsking(true)
    setQueryError(null)
    setQuestion('')
    try {
      const response = await authFetch(auth.token, '/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: askedQuestion, document_id: selectedDocId || null }),
      })
      if (!response.ok) {
        const errBody = await response.json()
        throw new Error(errBody.detail || `Query failed (${response.status})`)
      }
      const data: QueryResult = await response.json()
      setThread((prev) => [...prev, { question: askedQuestion, answer: data.answer, provider_used: data.provider_used }])
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setAsking(false)
    }
  }

  const pendingCount = uploads.filter((u) => u.status === 'pending').length

  return (
    <div className="app-shell">
      <header className="app-header">
        <BrandMark />
        <button className="btn btn-ghost" onClick={onLogout}>Log out</button>
      </header>

      <div className="app-body">
        {/* ---------------- Ledger: upload + document registry ---------------- */}
        <aside className="panel panel-ledger">
          <p className="section-eyebrow">Intake</p>
          <h2 className="section-title">Upload documents</h2>

          <div className="dropzone">
            <input type="file" multiple onChange={handleFileSelect} />
          </div>

          <div className="upload-all-row">
            <button className="btn" onClick={handleUploadAll} disabled={uploads.length === 0 || pendingCount === 0}>
              Upload all ({pendingCount})
            </button>
          </div>

          {uploads.length > 0 && (
            <div className="upload-list">
              {uploads.map((u, i) => (
                <div className="upload-card" data-status={u.status} key={i}>
                  <p className="upload-card-name">
                    <span>{u.file.name}</span>
                    <span className="upload-status-tag">{u.status}</span>
                  </p>
                  {u.status === 'success' && u.result && (
                    <p style={{ fontSize: 12, color: '#444', margin: '4px 0 0' }}>
                      Status: {u.result.status}
                    </p>
                  )}
                  {u.status === 'uploading' && (
                    <p style={{ fontSize: 12, color: '#888', margin: '4px 0 0' }}>
                      Processing in background...
                    </p>
                  )}
                  {u.status === 'error' && <p className="upload-card-error">{u.error}</p>}
                </div>
              ))}
            </div>
          )}

          <div className="doc-registry">
            <p className="section-eyebrow">Registry</p>
            <h2 className="section-title">Documents</h2>
            {documents.length === 0 ? (
              <p className="doc-registry-empty">Nothing indexed yet.</p>
            ) : (
              <div className="doc-registry-list">
                {documents.map((doc) => (
                  <div className="doc-row" key={doc.id}>
                    <span className="doc-row-name" title={doc.filename}>{doc.filename}</span>
                    <span className="doc-row-status mono">{doc.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* ---------------- Reading room: scoped chat ---------------- */}
        <section className="panel panel-reading">
          <p className="section-eyebrow">Consult</p>
          <h2 className="section-title">Ask the archive</h2>

          <div className="scope-row">
            <label htmlFor="scope">Search scope</label>
            <select id="scope" value={selectedDocId} onChange={(e) => setSelectedDocId(e.target.value)}>
              <option value="">All documents</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>{doc.filename} ({doc.status})</option>
              ))}
            </select>
          </div>

          <div className="thread">
            {thread.length === 0 && (
              <p className="thread-empty">No questions yet — ask something below.</p>
            )}
            {thread.map((turn, i) => (
              <div className="turn" key={i}>
                <p className="turn-index">Entry {String(i + 1).padStart(3, '0')}</p>
                <div className="bubble bubble-user">
                  <span className="who">You</span>
                  <p>{turn.question}</p>
                </div>
                <div className="bubble bubble-assistant">
                  <span className="who">Assistant{turn.provider_used ? ` · ${turn.provider_used}` : ''}</span>
                  <p>{turn.answer}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="ask-row">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              placeholder="Ask a question…"
            />
            <button className="btn btn-primary" onClick={handleAsk} disabled={asking || !question.trim()}>
              {asking ? 'Thinking…' : 'Ask'}
            </button>
          </div>

          {queryError && <p className="query-error">Error: {queryError}</p>}
        </section>
      </div>
    </div>
  )
}

function App() {
  const [auth, setAuth] = useState<AuthResponse | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem('auth')
    if (stored) setAuth(JSON.parse(stored))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('auth')
    setAuth(null)
  }

  if (!auth) {
    return <AuthScreen onAuthenticated={setAuth} />
  }

  return <MainApp auth={auth} onLogout={handleLogout} />
}

export default App