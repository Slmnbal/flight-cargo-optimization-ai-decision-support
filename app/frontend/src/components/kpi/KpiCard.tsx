import { Icon, type IconName } from '@/components/icons/Icon'
import { RadialGauge } from './RadialGauge'

interface KpiCardProps {
  label: string
  value: string
  hint?: string
  icon?: IconName
  /** Önceki döneme göre işaretli değişim, örn. +12.4 ya da -3.1 (yüzde puanı ya da % -- caller formatlar) */
  deltaPct?: number
  /** Yükselişin "iyi" mi "kötü" mü olduğu -- delta rengini belirler. Varsayılan: yukarı iyi. */
  deltaGoodDirection?: 'up' | 'down'
  /** dataviz skill stat-tile spec'i: 12 noktalık sparkline, de-emphasis tonda + son nokta accent */
  sparkline?: number[]
  /** Yüzde bazlı KPI'lar için sparkline yerine kullanılan radial gauge (0-100) */
  gauge?: number
  /** Sol kenar aksan çubuğu + gauge dolgu rengi. Varsayılan: marka rengi. */
  accentColor?: string
  /** Kartın büyük/öne çıkan (hero) sürümü -- Overview'daki başlıca KPI için */
  featured?: boolean
}

function Sparkline({ points }: { points: number[] }) {
  if (points.length < 2) return null
  const width = 64
  const height = 22
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
      <path d={path} fill="none" stroke="var(--color-ink-muted)" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r={2.5} fill="var(--color-brand)" />
    </svg>
  )
}

export function KpiCard({
  label,
  value,
  hint,
  icon,
  deltaPct,
  deltaGoodDirection = 'up',
  sparkline,
  gauge,
  accentColor = 'var(--color-brand)',
  featured = false,
}: KpiCardProps) {
  const isPositive = (deltaPct ?? 0) >= 0
  const isGood = deltaGoodDirection === 'up' ? isPositive : !isPositive
  const deltaColor = deltaPct === undefined ? '' : isGood ? 'text-good' : 'text-critical'

  return (
    <div className="card relative flex flex-col gap-2 overflow-hidden p-4">
      <span className="absolute inset-y-0 left-0 w-1" style={{ backgroundColor: accentColor }} />
      <div className="flex items-center justify-between pl-2">
        <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{label}</p>
        {icon && (
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-chrome-soft text-chrome">
            <Icon name={icon} size={15} />
          </span>
        )}
      </div>
      <div className="flex items-end justify-between gap-3 pl-2">
        <div>
          <p className={`font-semibold tabular-nums text-ink ${featured ? 'text-4xl' : 'text-3xl'}`}>{value}</p>
          {hint && <p className="mt-1 text-xs text-ink-secondary">{hint}</p>}
          {deltaPct !== undefined && (
            <p className={`mt-1 text-xs font-medium ${deltaColor}`}>
              {isPositive ? '+' : ''}
              {deltaPct.toFixed(1)}% önceki döneme göre
            </p>
          )}
        </div>
        {gauge !== undefined ? (
          <RadialGauge value={gauge} color={accentColor} size={featured ? 56 : 44} />
        ) : (
          sparkline && sparkline.length >= 2 && <Sparkline points={sparkline} />
        )}
      </div>
    </div>
  )
}
