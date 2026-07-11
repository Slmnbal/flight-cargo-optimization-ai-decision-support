import { useMemo, useState } from 'react'
import { useKpiTrend } from '@/hooks/useKpiTrend'
import { HeroStatBanner, type HeroStat } from '@/components/kpi/HeroStatBanner'
import { TrendChart } from '@/components/kpi/TrendChart'
import { formatCompactNumber, formatCurrency, formatCurrencyCompact, formatPercent } from '@/lib/format'
import type { KpiTrendGroupBy, KpiTrendPointOut } from '@/types/api'

const GROUP_BY_OPTIONS: { value: KpiTrendGroupBy; label: string }[] = [
  { value: 'day', label: 'Gün' },
  { value: 'week', label: 'Hafta' },
  { value: 'month', label: 'Ay' },
]

const SPARKLINE_WINDOW = 12

function lastN(values: number[], n: number): number[] {
  return values.slice(Math.max(0, values.length - n))
}

/** Son iki nokta arasındaki yüzde değişim -- KpiCard'ın "önceki döneme göre" delta'sı için. */
function deltaBetweenLastTwo(values: number[]): number | undefined {
  if (values.length < 2) return undefined
  const prev = values[values.length - 2]
  const curr = values[values.length - 1]
  if (prev === 0) return undefined
  return ((curr - prev) / Math.abs(prev)) * 100
}

export function OverviewPage() {
  const [groupBy, setGroupBy] = useState<KpiTrendGroupBy>('week')
  const { data, isLoading, isError } = useKpiTrend(undefined, undefined, groupBy)

  // /kpis/trend, 364 günlük pencereyi takvim hafta/ay sınırlarına göre grupluyor
  // -- pencerenin en son "hafta"/"ay" bucket'ı neredeyse her zaman KISMİ (örn.
  // hafta sadece 2-3 gün sürüyor), çünkü backfill_history.py'nin son günü
  // (bugün) kasıtlı olarak dışarıda bırakıyor. Bu kısmi son bucket'ı ham haliyle
  // gösterirsek KPI kartlarındaki "önceki döneme göre" delta'sı ve sparkline'ın
  // sonu yapay bir çöküş gibi görünür -- "gün" grupluğunda her bucket zaten tam
  // bir gün olduğu için bu sorun yok, sadece hafta/ay için son noktayı at.
  const points: KpiTrendPointOut[] = useMemo(() => {
    const raw = data?.points ?? []
    if (groupBy === 'day' || raw.length < 2) return raw
    return raw.slice(0, -1)
  }, [data, groupBy])

  const summary = useMemo(() => {
    const totalRevenue = points.reduce((sum, p) => sum + p.total_revenue, 0)
    const totalAccepted = points.reduce((sum, p) => sum + p.accepted_count, 0)
    const totalRejected = points.reduce((sum, p) => sum + p.rejected_count, 0)
    const totalRequests = totalAccepted + totalRejected
    const avgWeightUtilization = points.length
      ? points.reduce((sum, p) => sum + p.avg_weight_utilization_pct, 0) / points.length
      : 0
    return {
      totalRevenue,
      totalRequests,
      acceptanceRate: totalRequests ? totalAccepted / totalRequests : 0,
      avgWeightUtilization,
    }
  }, [points])

  const revenueValues = points.map((p) => p.total_revenue)
  const acceptanceValues = points.map((p) => p.acceptance_rate * 100)
  const utilizationValues = points.map((p) => p.avg_weight_utilization_pct)
  const requestValues = points.map((p) => p.total_requests)

  const revenueSeries = points.map((p) => ({ period: p.period, value: p.total_revenue }))
  const acceptanceSeries = points.map((p) => ({ period: p.period, value: p.acceptance_rate * 100 }))
  const utilizationSeries = points.map((p) => ({ period: p.period, value: p.avg_weight_utilization_pct }))

  if (isError) {
    return <p className="text-critical">Trend verisi yüklenemedi. Backend'in çalıştığından emin ol.</p>
  }

  const heroStats: HeroStat[] = [
    {
      label: 'Toplam Gelir',
      value: isLoading ? '—' : formatCurrency(summary.totalRevenue),
      hint: 'Optimize edilmiş tüm günler',
      icon: 'trend-up',
      deltaPct: deltaBetweenLastTwo(revenueValues),
      sparkline: lastN(revenueValues, SPARKLINE_WINDOW),
    },
    {
      label: 'Kabul Oranı',
      value: isLoading ? '—' : formatPercent(summary.acceptanceRate),
      icon: 'gauge',
      deltaPct: deltaBetweenLastTwo(acceptanceValues),
      gauge: summary.acceptanceRate * 100,
    },
    {
      label: 'Ort. Ağırlık Kullanımı',
      value: isLoading ? '—' : formatPercent(summary.avgWeightUtilization / 100),
      icon: 'cargo',
      deltaPct: deltaBetweenLastTwo(utilizationValues),
      gauge: summary.avgWeightUtilization,
    },
    {
      label: 'Toplam Talep',
      value: isLoading ? '—' : formatCompactNumber(summary.totalRequests),
      icon: 'route',
      deltaPct: deltaBetweenLastTwo(requestValues),
      sparkline: lastN(requestValues, SPARKLINE_WINDOW),
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <HeroStatBanner stats={heroStats} />

      <div className="flex items-center gap-2">
        <span className="text-sm text-ink-secondary">Grupla:</span>
        {GROUP_BY_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setGroupBy(opt.value)}
            className={`rounded-full px-4 py-1 text-sm font-medium ${
              groupBy === opt.value ? 'bg-brand text-white' : 'border border-border text-ink-secondary hover:bg-surface'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Trend Grafikleri</p>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <TrendChart title="Toplam Gelir" data={revenueSeries} color="var(--color-cat-1)" valueFormatter={formatCurrencyCompact} />
        <TrendChart
          title="Kabul Oranı (%)"
          data={acceptanceSeries}
          color="var(--color-cat-2)"
          valueFormatter={(v) => `%${Math.round(v)}`}
        />
        <TrendChart
          title="Ort. Ağırlık Kullanımı (%)"
          data={utilizationSeries}
          color="var(--color-cat-3)"
          valueFormatter={(v) => `%${Math.round(v)}`}
        />
      </div>
    </div>
  )
}
