import './StatsBar.css'

export default function StatsBar({ results }) {
  const leads = results?.leads || []

  const high = leads.filter(l => l['Potential Category'] === 'High').length
  const noWebsite = leads.filter(l => l['Website Status'] === 'No Website').length
  const scores = leads.map(l => parseInt(l['Digital Presence Score'] || 0))
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
  const hasSocial = leads.filter(l => l['Social Channels'] && l['Social Channels'].trim()).length

  const stats = [
    { label: 'Total Leads', value: leads.length },
    { label: 'High Priority', value: high },
    { label: 'No Website', value: noWebsite },
    { label: 'Avg. Presence Score', value: avgScore, suffix: '/100' },
  ]

  const sheetId = results?.exported_to_sheet
  const sheetUrl = sheetId ? `https://docs.google.com/spreadsheets/d/${sheetId}` : null

  return (
    <div className="stats-bar fade-in">
      <div className="stats-grid">
        {stats.map((s, i) => (
          <div key={i} className="stat-card" style={{ animationDelay: `${i * 0.08}s` }}>
            <div className="stat-value">
              {s.value}
              {s.suffix && <span className="stat-suffix">{s.suffix}</span>}
            </div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {hasSocial > 0 && (
        <div className="social-summary-banner">
          <span>
            <strong>{hasSocial}</strong> of {leads.length} businesses have social media presence.
            {' '}<strong>{leads.length - hasSocial}</strong> have none listed.
          </span>
        </div>
      )}

      {results?.status === 'success' && (
        <div className="export-banner">
          <div className="export-info">
            <span className="export-check material-symbols-outlined">check_circle</span>
            <div>
              <div className="export-title">Exported to Google Sheets</div>
              <div className="export-msg">{results.message}</div>
            </div>
          </div>
          {sheetUrl && (
            <a href={sheetUrl} target="_blank" rel="noopener noreferrer" className="sheet-btn">
              Open Sheet
            </a>
          )}
        </div>
      )}
    </div>
  )
}
