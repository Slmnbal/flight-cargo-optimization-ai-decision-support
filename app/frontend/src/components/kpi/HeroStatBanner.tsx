import { Icon, type IconName } from '@/components/icons/Icon'

export interface HeroStat {
  label: string
  value: string
  icon: IconName
  hint?: string
  deltaPct?: number
  deltaGoodDirection?: 'up' | 'down'
  sparkline?: number[]
  gauge?: number
}

// Havayolu kurumsal sitelerinde tipik olan "hero banner" deseni -- Genel
// Bakış'ın en önemli 4 metriği artık ayrı beyaz kartlar yerine tek, koyu
// lacivert (chrome) panelde; kırmızı burada SADECE aksan (sparkline son
// nokta, gauge dolgusu) -- gerçek THY sitesindeki "lacivert zemin + kırmızı
// nokta vurgu" dağılımıyla tutarlı. "Dikkat" delta'sı kırmızıyla
// karışmaması için altın/amber (--color-warning) kalıyor.
export function HeroStatBanner({ stats }: { stats: HeroStat[] }) {
  return (
    <div className="chrome-shell rounded-2xl p-6 text-white shadow-sm">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 lg:divide-x lg:divide-white/15">
        {stats.map((stat, i) => (
          <div key={stat.label} className={`flex flex-col gap-2 ${i > 0 ? 'lg:pl-6' : ''}`}>
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-white/70">{stat.label}</p>
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/10">
                <Icon name={stat.icon} size={14} />
              </span>
            </div>
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="text-3xl font-bold tabular-nums">{stat.value}</p>
                {stat.hint && <p className="mt-1 text-xs text-white/60">{stat.hint}</p>}
                {stat.deltaPct !== undefined && <HeroDelta stat={stat} />}
              </div>
              {stat.gauge !== undefined ? (
                <HeroGauge value={stat.gauge} />
              ) : (
                stat.sparkline && stat.sparkline.length >= 2 && <HeroSparkline points={stat.sparkline} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function HeroDelta({ stat }: { stat: HeroStat }) {
  const isPositive = (stat.deltaPct ?? 0) >= 0
  const isGood = (stat.deltaGoodDirection ?? 'up') === 'up' ? isPositive : !isPositive
  return (
    <p className={`mt-1 text-xs font-medium ${isGood ? 'text-white/85' : 'text-warning'}`}>
      {isPositive ? '▲' : '▼'} {Math.abs(stat.deltaPct ?? 0).toFixed(1)}% önceki döneme göre
    </p>
  )
}

function HeroSparkline({ points }: { points: number[] }) {
  const width = 64
  const height = 24
  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min || 1
  const coords = points.map((v, i) => {
    const x = (i / (points.length - 1)) * width
    const y = height - ((v - min) / range) * height
    return [x, y] as const
  })
  const path = coords.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const [lastX, lastY] = coords[coords.length - 1]

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="shrink-0">
      <path d={path} fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r={2.5} fill="var(--color-brand)" />
    </svg>
  )
}

function HeroGauge({ value }: { value: number }) {
  const size = 44
  const strokeWidth = 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(100, value))
  const dash = (clamped / 100) * circumference

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90 shrink-0">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth={strokeWidth} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--color-brand)"
        strokeWidth={strokeWidth}
        strokeDasharray={`${dash} ${circumference - dash}`}
        strokeLinecap="round"
      />
    </svg>
  )
}
