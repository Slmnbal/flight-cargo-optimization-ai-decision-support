import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Icon, type IconName } from '@/components/icons/Icon'

const NAV_ITEMS: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: '/', label: 'Genel Bakış', icon: 'overview', end: true },
  { to: '/dataset', label: 'Veri Seti', icon: 'database' },
  { to: '/routes', label: 'Rotalar', icon: 'route' },
  { to: '/flights', label: 'Uçuşlar', icon: 'flight' },
  { to: '/cargo-requests', label: 'Kargo Talepleri', icon: 'cargo' },
  { to: '/optimize', label: 'Optimizasyon', icon: 'gauge' },
  { to: '/agent', label: 'AI Asistan', icon: 'chat' },
]

// Gerçek THY logosu buradan KAYNAKLANMAZ (bkz. proje notu) -- halka açık bir
// GitHub reposuna marka hakkı riski taşıyan bir varlık gömülmüyor. Bunun
// yerine: kullanıcı isterse kendi `public/logo-thy.svg` (ya da .png)
// dosyasını koyabilir (bu dosya .gitignore'da, asla commit'lenmez); yoksa
// aşağıdaki özgün/telif-riski-olmayan simgeye düşülür. Kırmızı daire zemin,
// THY'nin kendi logosundaki "kırmızı daire rozet" konvansiyonundan esinlenildi.
function BrandMark() {
  const [imgFailed, setImgFailed] = useState(false)

  if (!imgFailed) {
    return (
      <img
        src="/logo-thy.svg"
        alt=""
        className="h-10 w-10 rounded-full bg-brand object-contain p-1.5"
        onError={() => setImgFailed(true)}
      />
    )
  }

  return (
    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand text-white">
      <Icon name="cargo" size={20} />
    </span>
  )
}

export function Sidebar() {
  return (
    <aside className="chrome-shell flex w-60 shrink-0 flex-col text-white">
      <div className="flex items-center gap-3 border-b border-white/10 px-5 py-6">
        <BrandMark />
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-white/60">THY Cargo Ops</p>
          <p className="text-lg font-semibold leading-tight">Karar Destek Paneli</p>
        </div>
      </div>
      <nav className="flex flex-col gap-1 px-3 pt-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                isActive ? 'bg-brand text-white' : 'text-white/70 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon name={item.icon} size={17} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto px-5 py-4 text-xs text-white/50">
        Flight Cargo Optimization & AI Decision Support System
      </div>
    </aside>
  )
}
