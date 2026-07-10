import { useMemo, useState } from 'react'
import { useKpiTrend } from '@/hooks/useKpiTrend'
import { KpiCard } from '@/components/kpi/KpiCard'
import { TrendChart } from '@/components/kpi/TrendChart'
import { formatCompactNumber, formatCurrency, formatCurrencyCompact, formatPercent } from '@/lib/format'
import type { KpiTrendGroupBy } from '@/types/api'

const GROUP_BY_OPTIONS: { value: KpiTrendGroupBy; label: string }[] = [
  { value: 'day', label: 'Gün' },
  { value: 'week', label: 'Hafta' },
  { value: 'month', label: 'Ay' },
]

export function OverviewPage() {
  const [groupBy, setGroupBy] = useState<KpiTrendGroupBy>('week')
  const { data, isLoading, isError } = useKpiTrend(undefined, undefined, groupBy)

  const summary = useMemo(() => {
    const points = data?.points ?? []
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
  }, [data])

  const revenueSeries = (data?.points ?? []).map((p) => ({ period: p.period, value: p.total_revenue }))
  const acceptanceSeries = (data?.points ?? []).map((p) => ({ period: p.period, value: p.acceptance_rate * 100 }))
  const utilizationSeries = (data?.points ?? []).map((p) => ({ period: p.period, value: p.avg_weight_utilization_pct }))

  if (isError) {
    return <p className="text-critical">Trend verisi yüklenemedi. Backend'in çalıştığından emin ol.</p>
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Toplam Gelir" value={isLoading ? '—' : formatCurrency(summary.totalRevenue)} hint="Optimize edilmiş tüm günler" />
        <KpiCard label="Kabul Oranı" value={isLoading ? '—' : formatPercent(summary.acceptanceRate)} />
        <KpiCard label="Ort. Ağırlık Kullanımı" value={isLoading ? '—' : formatPercent(summary.avgWeightUtilization / 100)} />
        <KpiCard label="Toplam Talep" value={isLoading ? '—' : formatCompactNumber(summary.totalRequests)} />
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-ink-secondary">Grupla:</span>
        {GROUP_BY_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setGroupBy(opt.value)}
            className={`rounded-md px-3 py-1 text-sm font-medium ${
              groupBy === opt.value ? 'bg-brand text-white' : 'border border-border text-ink-secondary hover:bg-surface'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

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
