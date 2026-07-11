import { useLocation } from 'react-router-dom'
import { Icon, type IconName } from '@/components/icons/Icon'

const PAGE_META: Record<string, { title: string; subtitle: string; icon: IconName }> = {
  '/': {
    title: 'Genel Bakış',
    subtitle: '12 aylık gelir, kabul oranı ve kapasite kullanım trendi',
    icon: 'overview',
  },
  '/dataset': {
    title: 'Veri Seti',
    subtitle: 'Havalimanları, uçak tipleri ve veri kapsamı özeti',
    icon: 'database',
  },
  '/routes': {
    title: 'Rotalar',
    subtitle: 'IST merkezli rota ağı, embargo ve tehlikeli madde kısıtları',
    icon: 'route',
  },
  '/flights': {
    title: 'Uçuşlar',
    subtitle: 'Planlanmış ve tamamlanmış uçuşlar, uçuş bazlı kapasite kullanımı',
    icon: 'flight',
  },
  '/cargo-requests': {
    title: 'Kargo Talepleri',
    subtitle: 'Tüm kargo talepleri ve ML tabanlı kabul olasılığı tahmini',
    icon: 'cargo',
  },
  '/optimize': {
    title: 'Optimizasyon',
    subtitle: 'Geçmiş senaryo sonuçları ve yeni optimizasyon çalıştırma',
    icon: 'gauge',
  },
  '/agent': {
    title: 'AI Asistan',
    subtitle: 'Gerçek veri ve proje dokümantasyonuna dayanan RAG destekli sohbet',
    icon: 'chat',
  },
}

export function Topbar() {
  const location = useLocation()
  const meta = PAGE_META[location.pathname] ?? { title: 'THY Cargo Ops', subtitle: '', icon: 'overview' as IconName }

  return (
    <header className="flex h-[4.5rem] shrink-0 items-center justify-between border-b-2 border-brand/20 bg-surface px-6">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-chrome-soft text-chrome">
          <Icon name={meta.icon} size={18} />
        </span>
        <div>
          <h1 className="text-xl font-semibold text-ink">{meta.title}</h1>
          <p className="text-xs text-ink-secondary">{meta.subtitle}</p>
        </div>
      </div>
      <span className="text-xs text-ink-muted">Faz 4 · Karar Destek Dashboard'u</span>
    </header>
  )
}
