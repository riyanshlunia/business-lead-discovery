import { useState } from 'react'
import './SearchForm.css'

export default function SearchForm({ onSearch, loading }) {
  const [industry, setIndustry] = useState('')
  const [location, setLocation] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (industry.trim() && location.trim()) {
      onSearch({ industry: industry.trim(), location: location.trim() })
    }
  }

  return (
    <section className="search-section">
      <form className="search-form" onSubmit={handleSubmit} id="search-form">
        <div className="search-inputs-group">
          <div className="field-premium relative">
            <span className="material-symbols-outlined input-icon">domain</span>
            <input
              id="industry-input"
              type="text"
              className="input-premium"
              value={industry}
              onChange={e => setIndustry(e.target.value)}
              placeholder="Industry (e.g., Renewable Energy)"
              required
              disabled={loading}
              autoComplete="off"
            />
          </div>
          
          <div className="field-premium relative">
            <span className="material-symbols-outlined input-icon">location_on</span>
            <input
              id="location-input"
              type="text"
              className="input-premium"
              value={location}
              onChange={e => setLocation(e.target.value)}
              placeholder="Location (e.g., Scandinavia)"
              required
              disabled={loading}
              autoComplete="off"
            />
          </div>
          
          <button type="submit" className="submit-premium" disabled={loading || !industry.trim() || !location.trim()}>
            {loading ? (
              <div className="btn-spinner-premium" />
            ) : (
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>search</span>
            )}
            {loading ? 'Searching' : 'Search'}
          </button>
        </div>
      </form>
    </section>
  )
}
