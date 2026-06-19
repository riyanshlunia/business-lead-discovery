import { useState, useRef } from 'react'
import Header from './components/Header'
import Hero from './components/Hero'
import SearchForm from './components/SearchForm'
import ResultsTable from './components/ResultsTable'
import StatsBar from './components/StatsBar'
import Footer from './components/Footer'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_API_URL || ''

const INITIAL_STEPS = [
  { icon: 'travel_explore', label: 'Searching OpenStreetMap for businesses', done: false },
  { icon: 'cleaning_services', label: 'Cleaning and de-duplicating data', done: false },
  { icon: 'language', label: 'Checking website quality', done: false },
  { icon: 'bar_chart', label: 'Scoring online presence', done: false },
  { icon: 'psychology', label: 'Generating lead insights', done: false },
  { icon: 'table_view', label: 'Exporting to Google Sheets', done: false },
]

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastQuery, setLastQuery] = useState(null)
  const [progressSteps, setProgressSteps] = useState([])
  const [progressPct, setProgressPct] = useState(0)
  const abortRef = useRef(null)

  const handleSearch = async ({ industry, location }) => {
    if (abortRef.current) abortRef.current.abort()

    setLoading(true)
    setError(null)
    setResults(null)
    setLastQuery({ industry, location })
    setProgressPct(0)
    setProgressSteps(INITIAL_STEPS.map(s => ({ ...s })))

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const formData = new FormData()
      formData.append('industry', industry)
      formData.append('location', location)
      formData.append('max_results', '20')

      const res = await fetch(`${BACKEND_URL}/run/stream`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      if (!res.ok) throw new Error(`Server responded with ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try { handleSSEEvent(JSON.parse(line.slice(6))) } catch { /* skip */ }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      await runFallback(industry, location)
    }
  }

  const handleSSEEvent = (event) => {
    if (event.type === 'progress') {
      setProgressPct(event.pct || 0)
      if (event.step) {
        setProgressSteps(prev =>
          prev.map((s, i) =>
            i === event.step - 1 ? { ...s, label: event.label, done: !!event.done } : s
          )
        )
      }
    } else if (event.type === 'done') {
      setProgressPct(100)
      setProgressSteps(prev => prev.map(s => ({ ...s, done: true })))
      setTimeout(() => { setResults(event); setLoading(false) }, 500)
    } else if (event.type === 'error') {
      setError(event.message)
      setLoading(false)
    }
  }

  const runFallback = async (industry, location) => {
    try {
      const formData = new FormData()
      formData.append('industry', industry)
      formData.append('location', location)
      formData.append('max_results', '20')
      const res = await fetch(`${BACKEND_URL}/run`, { method: 'POST', body: formData })
      const data = await res.json()
      if (data.status === 'error') setError(data.message)
      else setResults(data)
    } catch {
      setError('Could not connect to the backend. Ensure the API server is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <Hero />
        <SearchForm onSearch={handleSearch} loading={loading} />
        {(results || error || loading) && (
          <section className="results-section">
            {loading && <LoadingState query={lastQuery} steps={progressSteps} pct={progressPct} />}
            {error && !loading && <ErrorState message={error} />}
            {results && !loading && (
              <>
                <StatsBar results={results} />
                <ResultsTable results={results} query={lastQuery} />
              </>
            )}
          </section>
        )}
        <Footer />
      </main>
    </div>
  )
}

function LoadingState({ query, steps, pct }) {
  return (
    <div className="loading-state fade-in">
      <div className="loading-header">
        <div className="loading-spinner">
          <div className="spinner-ring" />
        </div>
        <div className="loading-title-group">
          <p className="loading-eyebrow">Processing</p>
          <h3 className="loading-title">
            {query?.industry}
            <span className="loading-sep">·</span>
            {query?.location}
          </h3>
        </div>
      </div>

      <div className="loading-progress-row">
        <div className="loading-progress-bar">
          <div className="loading-progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="loading-pct">{pct}%</span>
      </div>

      <div className="loading-steps">
        {steps.map((s, i) => {
          const state = s.done ? 'done' : (pct > (i / steps.length) * 100 ? 'active' : 'pending')
          return (
            <div key={i} className={`loading-step step-${state}`} style={{ animationDelay: `${i * 0.08}s` }}>
              <div className="step-indicator">
                {s.done
                  ? <span className="material-symbols-outlined step-icon-done">check</span>
                  : <span className="material-symbols-outlined step-icon">{s.icon}</span>
                }
              </div>
              <span className="step-label">{s.label}</span>
              {state === 'active' && <div className="step-pulse" />}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div className="error-state fade-in">
      <div className="error-state-header">
        <div className="error-icon-wrap">
          <span className="material-symbols-outlined">error_outline</span>
        </div>
        <h3>Request failed</h3>
      </div>
      <p>{message}</p>
    </div>
  )
}
