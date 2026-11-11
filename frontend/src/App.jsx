import { useEffect, useState } from 'react'

export default function App() {
  const [apiStatus, setApiStatus] = useState('Checking...')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) throw new Error('Health check failed')
        return response.json()
      })
      .then((data) => setApiStatus(data.status === 'ok' ? 'Connected' : 'Unavailable'))
      .catch(() => setApiStatus('Unavailable'))
  }, [])

  return (
    <main className="shell">
      <div className="eyebrow">CS 1660 / 2060 | Cloud Computing</div>
      <h1>Study Buddy</h1>
      <p>An AI-powered flashcard study application, currently under development.</p>
      <section className="status" aria-live="polite">
        <span>Backend API:</span>
        <strong>{apiStatus}</strong>
      </section>
      <p className="note">
        This is the starting application shell. Flashcard generation, accounts, and saved decks
        will be added later.
      </p>
    </main>
  )
}
