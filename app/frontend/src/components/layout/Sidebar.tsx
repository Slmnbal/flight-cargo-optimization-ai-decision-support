import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Genel Bakış', end: true },
  { to: '/routes', label: 'Rotalar' },
  { to: '/flights', label: 'Uçuşlar' },
  { to: '/cargo-requests', label: 'Kargo Talepleri' },
  { to: '/optimize', label: 'Optimizasyon' },
  { to: '/agent', label: 'AI Asistan' },
]

export function Sidebar() {
  return (
    <aside className="flex w-60 shrink-0 flex-col bg-brand text-white">
      <div className="px-5 py-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-white/70">THY Cargo Ops</p>
        <p className="mt-1 text-lg font-semibold">Karar Destek Paneli</p>
      </div>
      <nav className="flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? 'bg-white/15 text-white' : 'text-white/80 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto px-5 py-4 text-xs text-white/60">
        Flight Cargo Optimization & AI Decision Support System
      </div>
    </aside>
  )
}
