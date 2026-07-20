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

function authFetch(token: string, path: string, options: RequestInit = {}) {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  })
}

function BrandGlyph() {
  return (
    <svg className="glyph" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="4" width="18" height="20" rx="3" fill="#0f172a" stroke="#0ea5e9" strokeWidth="1.5" />
      <rect x="3" y="8" width="18" height="20" rx="3" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
      <line x1="7" y1="14" x2="17" y2="14" stroke="#64748b" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="7" y1="18" x2="14" y2="18" stroke="#64748b" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="7" y1="22" x2="16" y2="22" stroke="#64748b" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function BrandMark() {
  return (
    <div className="brand-mark">
      <BrandGlyph />
      <div className="wordmark">
        Knowledge OS
        <small>RAG Intelligence Engine</small>
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
        <h1 className="auth-title">{mode === 'login' ? 'Sign In' : 'Create Account'}</h1>
        <p className="auth-eyebrow">{mode === 'login' ? 'Access your localized archive' : 'Get started with Knowledge OS'}</p>

        <div className="field">
          <label htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            placeholder="name@organization.com"
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

        <button className="btn btn-primary btn-block" onClick={handleSubmit} disabled={loading || !email || !password}>
          {loading ? 'Authenticating...' : mode === 'login' ? 'Sign In' : 'Register'}
        </button>

        {error && <p className="form-error">{error}</p>}

        <p className="auth-switch">
          {mode === 'login' ? "New to the platform? " : 'Already registered? '}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              setMode(mode === 'login' ? 'register' : 'login')
            }}
          >
            {mode === 'login' ? 'Create an account' : 'Sign in here'}
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
        // Transient poll failure safely caught
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
        <div className="header-meta">
          <span className="org-badge">Org: {auth.org_id.substring(0, 8)}</span>
          <button className="btn btn-secondary btn-sm" onClick={onLogout}>Log out</button>
        </div>
      </header>

      <div className="app-body">
        {/* Left Side: Document Registry & Processing Engine */}
        <aside className="panel panel-ledger">
          <div className="panel-header-block">
            <p className="section-eyebrow">Data Intake</p>
            <h2 className="section-title">Knowledge Base</h2>
          </div>

          <div className="dropzone-container">
            <label className="dropzone-label">
              <span className="dropzone-action">Choose files</span> or drag them here
              <input type="file" multiple onChange={handleFileSelect} className="hidden-file-input" />
            </label>
          </div>

          {uploads.length > 0 && (
            <div className="upload-section">
              <button className="btn btn-primary btn-sm btn-block" onClick={handleUploadAll} disabled={pendingCount === 0}>
                Process Queue ({pendingCount})
              </button>
              
              <div className="upload-list">
                {uploads.map((u, i) => (
                  <div className="upload-card" data-status={u.status} key={i}>
                    <div className="upload-card-header">
                      <span className="upload-card-name" title={u.file.name}>{u.file.name}</span>
                      <span className={`status-pill pill-${u.status}`}>{u.status}</span>
                    </div>
                    {u.status === 'success' && u.result && (
                      <p className="status-subtext">Indexing status: {u.result.status}</p>
                    )}
                    {u.status === 'uploading' && (
                      <div className="progress-bar-container"><div className="progress-bar infinite"></div></div>
                    )}
                    {u.status === 'error' && <p className="upload-card-error">{u.error}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="doc-registry">
            <div className="registry-header">
              <p className="section-eyebrow">Indexed System</p>
              <h3 className="registry-title">Active Corpus ({documents.length})</h3>
            </div>
            
            {documents.length === 0 ? (
              <div className="empty-state-card">
                <p>No vectors detected in database. Upload documents to construct your knowledge tree.</p>
              </div>
            ) : (
              <div className="doc-registry-list">
                {documents.map((doc) => (
                  <div className="doc-row" key={doc.id}>
                    <div className="doc-info">
                      <svg className="doc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                      </svg>
                      <span className="doc-row-name" title={doc.filename}>{doc.filename}</span>
                    </div>
                    <span className={`status-badge badge-${doc.status}`}>{doc.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Right Side: RAG Consultation Room */}
        <section className="panel panel-reading">
          <div className="panel-header-block layout-split">
            <div>
              <p className="section-eyebrow">Contextual Engine</p>
              <h2 className="section-title">Archive Query Console</h2>
            </div>
            <div className="scope-box">
              <label htmlFor="scope">Context Scope</label>
              <select id="scope" value={selectedDocId} onChange={(e) => setSelectedDocId(e.target.value)}>
                <option value="">Global Archive (All docs)</option>
                {documents.filter(d => d.status === 'embedded').map((doc) => (
                  <option key={doc.id} value={doc.id}>{doc.filename}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="thread">
            {thread.length === 0 && (
              <div className="thread-empty">
                <div className="empty-icon">⚡</div>
                <h3>System Ready</h3>
                <p>Submit questions scoped to your verified knowledge indexes. Sources will be extracted instantly.</p>
              </div>
            )}
            {thread.map((turn, i) => (
              <div className="turn" key={i}>
                <div className="turn-meta">
                  <span className="turn-index">VECTOR_QUERY_{String(i + 1).padStart(3, '0')}</span>
                </div>
                
                <div className="bubble bubble-user">
                  <div className="bubble-header">Prompt</div>
                  <p>{turn.question}</p>
                </div>
                
                <div className="bubble bubble-assistant">
                  <div className="bubble-header">
                    <span>Synthesis Output</span>
                    {turn.provider_used && <span className="provider-tag">{turn.provider_used}</span>}
                  </div>
                  <p>{turn.answer}</p>
                </div>
              </div>
            ))}
            {asking && (
              <div className="turn systematic-loading">
                <span className="spinner-text">Retrieving chunks and synthesizing response...</span>
              </div>
            )}
          </div>

          <div className="input-panel">
            <div className="ask-row">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                placeholder="Query workspace using semantic context..."
                disabled={asking}
              />
              <button className="btn btn-primary" onClick={handleAsk} disabled={asking || !question.trim()}>
                {asking ? 'Searching...' : 'Run Query'}
              </button>
            </div>
            {queryError && <p className="query-error">Execution Error: {queryError}</p>}
          </div>
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