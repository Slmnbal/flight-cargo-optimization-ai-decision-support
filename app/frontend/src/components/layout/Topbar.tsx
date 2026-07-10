import { useLocation } from 'react-router-dom'

const TITLES: Record<string, string> = {
  '/': 'Genel Bakış',
  '/routes': 'Rotalar',
  '/flights': 'Uçuşlar',
  '/cargo-requests': 'Kargo Talepleri',
  '/optimize': 'Optimizasyon',
  '/agent': 'AI Asistan',
}

export function Topbar() {
  const location = useLocation()
  const title = TITLES[location.pathname] ?? 'THY Cargo Ops'

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-surface px-6">
      <h1 className="text-lg font-semibold text-ink">{title}</h1>
      <span className="text-xs text-ink-muted">Faz 4 · Karar Destek Dashboard'u</span>
    </header>
  )
}
