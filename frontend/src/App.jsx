import { useEffect, useRef, useState } from 'react'
import { authConfigured, getAccessToken, getSignedInUser, signIn, signOutUser } from './auth'

const COUNTS = [
  { value: 'auto', label: 'AI Recommended', detail: 'Automatically choose up to 20 flashcards' },
  { value: '5', label: '5 cards' },
  { value: '10', label: '10 cards' },
  { value: '20', label: '20 cards' },
]

export default function App() {
  const [apiStatus, setApiStatus] = useState('Checking…')
  const [authUser, setAuthUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authError, setAuthError] = useState('')
  const [mode, setMode] = useState('pdf')
  const [count, setCount] = useState('auto')
  const [topic, setTopic] = useState('')
  const [notes, setNotes] = useState('')
  const [pdf, setPdf] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [deck, setDeck] = useState(null)
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [known, setKnown] = useState([])
  const fileInput = useRef(null)

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) throw new Error('Health check failed')
        return response.json()
      })
      .then((data) => setApiStatus(data.status === 'ok' ? 'Connected' : 'Unavailable'))
      .catch(() => setApiStatus('Unavailable'))
  }, [])

  useEffect(() => {
    let active = true
    getSignedInUser()
      .then((user) => {
        if (active) setAuthUser(user)
      })
      .catch(() => {
        if (active) setAuthError('Could not restore your sign-in. Please sign in again.')
      })
      .finally(() => {
        if (active) setAuthLoading(false)
      })
    return () => { active = false }
  }, [])

  async function handleSignIn() {
    setAuthError('')
    try {
      await signIn()
    } catch (err) {
      setAuthError(err.message || 'Could not open Cognito sign-in.')
    }
  }

  async function handleSignOut() {
    setAuthError('')
    try {
      await signOutUser()
      setAuthUser(null)
      setDeck(null)
    } catch (err) {
      setAuthError(err.message || 'Could not sign out.')
    }
  }

  async function generate(event) {
    event.preventDefault()
    setError('')
    if (mode === 'pdf' && !pdf) return setError('Choose a lecture PDF first.')
    if (mode === 'topic' && topic.trim().length < 12) return setError('Enter a more specific topic.')
    if (mode === 'notes' && notes.trim().length < 12) return setError('Paste a little more study material.')
    if (!authUser) return setError('Sign in before generating flashcards.')

    const data = new FormData()
    data.append('mode', mode)
    data.append('count', count)
    if (mode === 'pdf') data.append('file', pdf)
    if (mode === 'topic') data.append('topic', topic)
    if (mode === 'notes') data.append('notes', notes)

    setBusy(true)
    try {
      const accessToken = await getAccessToken()
      if (!accessToken) throw new Error('Your sign-in expired. Please sign in again.')
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken}` },
        body: data,
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Could not generate cards. Please try again.')
      setDeck(result)
      setIndex(0)
      setFlipped(false)
      setKnown([])
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  function next() {
    setIndex((old) => Math.min(old + 1, deck.cards.length - 1))
    setFlipped(false)
  }

  function previous() {
    setIndex((old) => Math.max(old - 1, 0))
    setFlipped(false)
  }

  function mark(learned) {
    setKnown((old) => learned ? [...new Set([...old, index])] : old.filter((item) => item !== index))
    if (index < deck.cards.length - 1) next()
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand"><span className="brand-icon">✦</span><span>study<span className="brand-accent">buddy</span></span></div>
        <span className="header-note">Your smarter study space</span>
        <div className="account-controls">
          {authLoading ? <span className="account-name">Checking sign-in…</span> : authUser ? (
            <>
              <span className="account-name">Signed in as {authUser.email || authUser.userId}</span>
              <button type="button" className="auth-button" onClick={handleSignOut}>Sign out</button>
            </>
          ) : authConfigured ? (
            <button type="button" className="auth-button" onClick={handleSignIn}>Sign in / Sign up</button>
          ) : (
            <span className="auth-warning">Set up Cognito in .env to sign in</span>
          )}
          {authError && <span role="alert" className="auth-error">{authError}</span>}
        </div>
        <span className={`connection ${apiStatus === 'Connected' ? 'online' : ''}`}><span className="status-dot" /> API {apiStatus}</span>
      </header>

      {!deck ? (
        <main className="workspace">
          <div className="hero">
            <span className="eyebrow">FLASHCARDS, MADE SIMPLE</span>
            <h1>Less prep. <span>More progress.</span></h1>
            <p>Turn lecture slides, notes, or any topic into cards you'll actually want to study.</p>
          </div>
          <form className="creator" onSubmit={generate}>
            <div className="form-heading"><div><h2>Create your next deck</h2><p>Pick your study material to get started.</p></div><span className="step-pill">01 / Create</span></div>
            <div className="mode-tabs" aria-label="Study material type">
              {[['pdf', '▤', 'Upload PDF'], ['notes', '≡', 'Paste notes'], ['topic', '✧', 'Enter topic']].map(([value, icon, label]) => (
                <button type="button" key={value} className={mode === value ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode(value); setError('') }} aria-pressed={mode === value}>
                  <span aria-hidden="true">{icon}</span> {label}
                </button>
              ))}
            </div>
            {mode === 'pdf' && (
              <div className="upload-zone">
                <div className="upload-symbol">⇧</div>
                <strong>{pdf ? pdf.name : 'Your lecture notes go here'}</strong>
                <p>{pdf ? `${(pdf.size / (1024 * 1024)).toFixed(2)} MB · ready to generate` : 'Use a PDF of your slides or study guide'}</p>
                <button type="button" className="secondary-action" onClick={() => fileInput.current?.click()}>{pdf ? 'Change PDF' : 'Choose a PDF'}</button>
                <input ref={fileInput} type="file" accept=".pdf,application/pdf" className="visually-hidden" onChange={(event) => { setPdf(event.target.files?.[0] || null); setError('') }} />
                <span className="file-hint">PDF only · Up to 8 MB · 30 pages</span>
              </div>
            )}
            {mode === 'notes' && (
              <label className="text-field">Your notes
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={7} maxLength={15000} placeholder="Paste your class notes here…" />
              </label>
            )}
            {mode === 'topic' && (
              <label className="text-field">What are you studying?
                <input value={topic} onChange={(event) => setTopic(event.target.value)} maxLength={300} placeholder="e.g. Docker Compose, ECS and Fargate" />
                <span className="field-note">Try a specific topic for better questions.</span>
              </label>
            )}
            <div className="settings-header"><div><h3>How many flashcards?</h3><p>{count === 'auto' ? 'Automatically choose up to 20 flashcards.' : `Aim for ${count} flashcards.`}</p></div></div>
            <div className="count-options" role="radiogroup" aria-label="Number of flashcards">
              {COUNTS.map((option) => (
                <label className={`count-option ${count === option.value ? 'chosen' : ''}`} key={option.value}>
                  <input type="radio" name="count" checked={count === option.value} onChange={() => setCount(option.value)} value={option.value} />
                  <span className="radio-dot" />
                  <span className="option-copy"><strong>{option.value === 'auto' ? '✦ ' : ''}{option.label}</strong>{option.detail && <small>{option.detail}</small>}</span>
                  {option.value === 'auto' && <span className="recommend-pill">Recommended</span>}
                </label>
              ))}
            </div>
            {error && <div role="alert" className="error">{error}</div>}
            <button className="primary-action" disabled={busy} type="submit">{busy ? 'Creating your flashcards…' : '✦ Generate flashcards'} <span aria-hidden="true">→</span></button>
            <p className="privacy-note">{busy ? 'Qwen is generating your cards locally. This can take a few minutes.' : authUser ? 'Powered by a locally hosted AI model.' : 'Sign in with Cognito to generate flashcards.'}</p>
          </form>
          <footer className="footer-copy">Made for better study sessions. One card at a time.</footer>
        </main>
      ) : (
        <main className="study-workspace">
          <div className="study-header">
            <button type="button" className="back-link" onClick={() => { setDeck(null); setError('') }}>← Create another deck</button>
            <span className="step-pill">02 / Study</span>
          </div>
          <div className="study-title"><span className="eyebrow">READY TO STUDY</span><h1>{deck.title || 'Your flashcards'}</h1><p>{deck.count} flashcards generated {deck.recommended ? '· AI-selected count' : ''}</p>{deck.message && <p className="privacy-note" role="status">{deck.message}</p>}</div>
          <div className="progress-heading"><span>Card {index + 1} of {deck.cards.length}</span><span>{known.length} marked learned</span></div>
          <div className="progress-track"><div style={{ width: `${((index + 1) / deck.cards.length) * 100}%` }} /></div>
          <button type="button" className={`study-card ${flipped ? 'flipped' : ''}`} onClick={() => setFlipped((old) => !old)} aria-label="Flip flashcard">
            <span className="card-label">{flipped ? 'THE ANSWER' : 'THE QUESTION'}</span>
            <strong>{flipped ? deck.cards[index].answer : deck.cards[index].question}</strong>
            <span className="flip-hint">⟳ Tap to flip</span>
          </button>
          <div className="study-controls">
            <button className="study-secondary" type="button" disabled={index === 0} onClick={previous}>← Previous</button>
            <div className="answer-actions">
              <button type="button" className="again-btn" onClick={() => mark(false)}>↻ Study again</button>
              <button type="button" className="got-btn" onClick={() => mark(true)}>✓ Got it</button>
            </div>
            <button className="study-secondary" type="button" disabled={index === deck.cards.length - 1} onClick={next}>Next →</button>
          </div>
          <div className="study-bottom"><span>{known.length} / {deck.count} learned this session</span><button type="button" onClick={() => { setIndex(0); setFlipped(false); setKnown([]) }}>Restart session ↻</button></div>
          <p className="privacy-note">Flashcards are temporary until saved decks arrive in a later milestone. Check AI-generated facts against your notes.</p>
        </main>
      )}
    </div>
  )
}
