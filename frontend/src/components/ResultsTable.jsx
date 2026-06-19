import { useState } from 'react'
import './ResultsTable.css'

const PRIORITY_CONFIG = {
  High: { label: 'High', cls: 'priority-high' },
  Medium: { label: 'Medium', cls: 'priority-medium' },
  Low: { label: 'Low', cls: 'priority-low' },
}

const WEBSITE_CONFIG = {
  'Good Website': { cls: 'ws-good', label: 'Good' },
  'Poor Website': { cls: 'ws-poor', label: 'Poor' },
  'Has Website': { cls: 'ws-has', label: 'Listed' },
  'No Website': { cls: 'ws-none', label: 'None' },
}

const SOCIAL_PLATFORMS = {
  Facebook: { abbr: 'FB', label: 'Facebook' },
  Instagram: { abbr: 'IG', label: 'Instagram' },
  Twitter: { abbr: 'X', label: 'Twitter/X' },
  LinkedIn: { abbr: 'IN', label: 'LinkedIn' },
  YouTube: { abbr: 'YT', label: 'YouTube' },
  Wikipedia: { abbr: 'WK', label: 'Wikipedia' },
  TripAdvisor: { abbr: 'TA', label: 'TripAdvisor' },
}

function ScoreRing({ score, label, size = 52 }) {
  const r = (size - 8) / 2
  const circ = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(score, 100))
  const dash = (pct / 100) * circ
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444'

  return (
    <div className="score-ring-wrap" title={`${label}: ${score}/100`}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="4" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth="4"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
        />
      </svg>
      <span className="score-ring-value" style={{ color }}>{score}</span>
    </div>
  )
}

function SocialLinks({ lead }) {
  const links = []
  Object.entries(SOCIAL_PLATFORMS).forEach(([platform, cfg]) => {
    const val = lead[`${platform} URL`] || ''
    if (val && val.trim() && val !== 'nan' && val !== 'None') {
      links.push({ platform, url: val, ...cfg })
    }
  })
  if (!links.length) return <span className="no-social">—</span>
  return (
    <div className="social-links">
      {links.map(l => (
        <a
          key={l.platform}
          href={l.url.startsWith('http') ? l.url : `https://${l.url}`}
          target="_blank"
          rel="noopener noreferrer"
          className="social-btn"
          title={l.label}
          onClick={e => e.stopPropagation()}
        >
          {l.abbr}
        </a>
      ))}
    </div>
  )
}

export default function ResultsTable({ results, query }) {
  const leads = results?.leads || []
  const [filter, setFilter] = useState('All')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('Lead Opportunity Score')
  const [sortDir, setSortDir] = useState('desc')
  const [expandedRow, setExpandedRow] = useState(null)

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = [...leads]
    .filter(l => filter === 'All' || l['Potential Category'] === filter)
    .filter(l => !search || l['Business Name']?.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      const numA = parseFloat(av)
      const numB = parseFloat(bv)
      const cmp = !isNaN(numA) && !isNaN(numB)
        ? numA - numB
        : String(av).localeCompare(String(bv))
      return sortDir === 'asc' ? cmp : -cmp
    })

  const exportCSV = () => {
    const cols = [
      'Business Name', 'Category', 'Location', 'Website Status', 'Website URL',
      'Digital Presence Score', 'Lead Opportunity Score', 'Potential Category',
      'Social Channels', 'Phone Number', 'Email Address', 'AI Insight',
    ]
    const csv = [
      cols.join(','),
      ...sorted.map(r => cols.map(c => `"${(r[c] || '').toString().replace(/"/g, '""')}"`).join(','))
    ].join('\n')
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    a.download = `leads_${query?.industry}_${query?.location}.csv`
    a.click()
  }

  if (!leads.length) {
    return (
      <div className="no-results">
        <h3>No leads found</h3>
        <p>Try a different industry or location.</p>
      </div>
    )
  }

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <span className="sort-neutral">↕</span>
    return <span className="sort-active">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div className="results-table-wrap fade-in">
      <div className="table-toolbar">
        <div className="toolbar-left">
          <h3 className="results-title">
            <span className="results-count">{sorted.length}</span> Leads
            <span className="results-meta">{query?.industry} · {query?.location}</span>
          </h3>
          <div className="filter-tabs">
            {['All', 'High', 'Medium', 'Low'].map(f => (
              <button
                key={f}
                className={`filter-tab ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="toolbar-right">
          <div className="search-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
              <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <input
              placeholder="Search businesses…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button className="export-csv-btn" onClick={exportCSV}>Export CSV</button>
        </div>
      </div>

      <div className="table-scroll">
        <table className="leads-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('Business Name')} className={sortKey === 'Business Name' ? 'sorted' : ''}>
                Business <SortIcon col="Business Name" />
              </th>
              <th onClick={() => handleSort('Website Status')} className={sortKey === 'Website Status' ? 'sorted' : ''}>
                Website <SortIcon col="Website Status" />
              </th>
              <th
                onClick={() => handleSort('Lead Opportunity Score')}
                className={`score-col ${sortKey === 'Lead Opportunity Score' ? 'sorted' : ''}`}
              >
                Opportunity <SortIcon col="Lead Opportunity Score" />
              </th>
              <th
                onClick={() => handleSort('Digital Presence Score')}
                className={`score-col ${sortKey === 'Digital Presence Score' ? 'sorted' : ''}`}
              >
                Presence <SortIcon col="Digital Presence Score" />
              </th>
              <th>Social</th>
              <th>Contact</th>
              <th>Insight</th>
              <th>Links</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((lead, i) => {
              const priority = PRIORITY_CONFIG[lead['Potential Category']] || PRIORITY_CONFIG.Low
              const ws = WEBSITE_CONFIG[lead['Website Status']] || WEBSITE_CONFIG['No Website']
              const isExpanded = expandedRow === i
              const oppScore = parseInt(lead['Lead Opportunity Score'] || 0)
              const digScore = parseInt(lead['Digital Presence Score'] || 0)
              const websiteUrl = lead['Website URL'] || ''

              return (
                <>
                  <tr
                    key={i}
                    className={`lead-row ${isExpanded ? 'expanded' : ''}`}
                    onClick={() => setExpandedRow(isExpanded ? null : i)}
                  >
                    <td>
                      <div className="business-name">{lead['Business Name'] || '—'}</div>
                      <div className="business-meta">
                        {lead['Category']}
                        {lead['Location'] ? ` · ${lead['Location']}` : ''}
                      </div>
                    </td>

                    <td>
                      <div className="website-cell">
                        <span className={`ws-badge ${ws.cls}`}>{ws.label}</span>
                        {websiteUrl && websiteUrl !== 'nan' && websiteUrl !== 'None' && (
                          <a
                            href={websiteUrl.startsWith('http') ? websiteUrl : `https://${websiteUrl}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="website-link"
                            onClick={e => e.stopPropagation()}
                          >
                            Visit
                          </a>
                        )}
                      </div>
                    </td>

                    <td className="score-cell">
                      <div>
                        <ScoreRing score={oppScore} label="Opportunity" />
                        <span className={`priority-badge ${priority.cls}`}>{priority.label}</span>
                      </div>
                    </td>

                    <td className="score-cell">
                      <ScoreRing score={digScore} label="Presence" />
                    </td>

                    <td><SocialLinks lead={lead} /></td>

                    <td>
                      <div className="contact-info">
                        {lead['Phone Number'] && lead['Phone Number'] !== 'nan' && (
                          <div className="contact-item">{lead['Phone Number']}</div>
                        )}
                        {lead['Email Address'] && lead['Email Address'] !== 'nan' && (
                          <div className="contact-item contact-email">{lead['Email Address']}</div>
                        )}
                        {(!lead['Phone Number'] || lead['Phone Number'] === 'nan') &&
                         (!lead['Email Address'] || lead['Email Address'] === 'nan') && (
                          <span className="no-contact">—</span>
                        )}
                      </div>
                    </td>

                    <td className="insight-cell">
                      <p className={`lead-insight ${isExpanded ? 'expanded' : ''}`}>
                        {lead['AI Insight'] || '—'}
                      </p>
                    </td>

                    <td>
                      <div className="links-cell">
                        {websiteUrl && websiteUrl !== 'nan' && websiteUrl !== 'None' && (
                          <a
                            href={websiteUrl.startsWith('http') ? websiteUrl : `https://${websiteUrl}`}
                            target="_blank" rel="noopener noreferrer"
                            className="link-btn" onClick={e => e.stopPropagation()}
                          >
                            Web
                          </a>
                        )}
                        {lead['Google Maps Profile Link'] && (
                          <a
                            href={lead['Google Maps Profile Link']}
                            target="_blank" rel="noopener noreferrer"
                            className="link-btn maps-btn" onClick={e => e.stopPropagation()}
                          >
                            Map
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr key={`${i}-expand`} className="expand-row">
                      <td colSpan={8}>
                        <div className="expand-content">
                          <div className="expand-section">
                            <div className="expand-label">Presence breakdown</div>
                            <div className="expand-value">{lead['Presence Breakdown'] || '—'}</div>
                          </div>
                          {websiteUrl && websiteUrl !== 'nan' && websiteUrl !== 'None' && (
                            <div className="expand-section">
                              <div className="expand-label">Website</div>
                              <a
                                href={websiteUrl.startsWith('http') ? websiteUrl : `https://${websiteUrl}`}
                                target="_blank" rel="noopener noreferrer"
                                className="expand-link"
                              >
                                {websiteUrl}
                              </a>
                            </div>
                          )}
                          {lead['AI Insight'] && (
                            <div className="expand-section">
                              <div className="expand-label">Full insight</div>
                              <div className="expand-value">{lead['AI Insight']}</div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
