import './Sidebar.css'

const NAV_ITEMS = [
  { icon: 'insights',       label: 'Intelligence' },
  { icon: 'search_check',   label: 'Discovery'    },
  { icon: 'business_center',label: 'Portfolio'    },
  { icon: 'query_stats',    label: 'Analytics'    },
  { icon: 'inventory_2',    label: 'Archive'      },
]

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <>
      {/* Desktop Sidebar */}
      <nav className="sidebar desktop-sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <span className="material-symbols-outlined brand-icon">token</span>
            <h1>ARCHON</h1>
          </div>
        </div>

        <button className="new-discovery-btn" onClick={() => onNavigate('Discovery')}>
          <span className="material-symbols-outlined">add</span>
          New Discovery
        </button>

        <div className="nav-links">
          {NAV_ITEMS.map(({ icon, label }) => (
            <button
              key={label}
              className={`nav-link ${activePage === label ? 'active' : ''}`}
              onClick={() => onNavigate(label)}
            >
              <span className="material-symbols-outlined">{icon}</span>
              {label}
            </button>
          ))}
        </div>

      </nav>

      {/* Mobile Top Header */}
      <header className="mobile-header">
        <h1>ARCHON</h1>
      </header>

      {/* Mobile Bottom Nav */}
      <nav className="mobile-bottom-nav">
        {NAV_ITEMS.map(({ icon, label }) => (
          <button
            key={label}
            className={`bottom-nav-item ${activePage === label ? 'active' : ''}`}
            onClick={() => onNavigate(label)}
          >
            <span className="material-symbols-outlined">{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </>
  )
}
