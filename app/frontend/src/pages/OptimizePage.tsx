import { useState } from 'react'
import { useOptimize } from '@/hooks/useOptimize'
import { useTrainModel } from '@/hooks/useTrainModel'
import { useGenerateDemand } from '@/hooks/useGenerateDemand'
import { useScenarios } from '@/hooks/useScenarios'
import { useKpis } from '@/hooks/useKpis'
import { KpiCard } from '@/components/kpi/KpiCard'
import { DataTable, type DataTableColumn } from '@/components/tables/DataTable'
import { Icon } from '@/components/icons/Icon'
import { formatCurrency } from '@/lib/format'
import type { ScenarioSummaryOut } from '@/types/api'

const PAGE_SIZE = 20

export function OptimizePage() {
  const [scenarioName, setScenarioName] = useState('live')
  const [selectedScenario, setSelectedScenario] = useState<string | undefined>(undefined)
  const [offset, setOffset] = useState(0)

  const optimize = useOptimize()
  const train = useTrainModel()
  const generateDemand = useGenerateDemand()
  const { data: scenariosData, isLoading: scenariosLoading } = useScenarios({ limit: PAGE_SIZE, offset })
  const { data: kpis, isLoading: kpisLoading, isError: kpisError } = useKpis(selectedScenario)

  const handleRunOptimize = () => {
    optimize.mutate(scenarioName, {
      onSuccess: () => setSelectedScenario(scenarioName),
    })
  }

  const columns: DataTableColumn<ScenarioSummaryOut>[] = [
    {
      key: 'name',
      header: 'Senaryo',
      render: (s) => (
        <button type="button" onClick={() => setSelectedScenario(s.scenario_name)} className="font-medium text-brand hover:underline">
          {s.scenario_name}
        </button>
      ),
    },
    {
      key: 'last_run',
      header: 'Son Çalışma',
      render: (s) => new Date(s.last_run_at).toLocaleString('tr-TR', { dateStyle: 'medium', timeStyle: 'short' }),
    },
    { key: 'total', header: 'Talep', render: (s) => s.total_requests.toLocaleString('en-US'), align: 'right' },
    { key: 'accepted', header: 'Kabul', render: (s) => s.accepted_count.toLocaleString('en-US'), align: 'right' },
    { key: 'rejected', header: 'Red', render: (s) => s.rejected_count.toLocaleString('en-US'), align: 'right' },
    { key: 'revenue', header: 'Gelir', render: (s) => formatCurrency(s.total_revenue), align: 'right' },
  ]

  const total = scenariosData?.total ?? 0
  const hasNext = offset + PAGE_SIZE < total
  const hasPrev = offset > 0

  return (
    <div className="flex flex-col gap-6">
      <div className="card flex flex-wrap items-end gap-3 p-4">
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Senaryo Adı
          <input
            type="text"
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            className="w-48 rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          />
        </label>
        <button
          type="button"
          onClick={() => generateDemand.mutate()}
          disabled={generateDemand.isPending}
          className="flex items-center gap-1.5 rounded-full border border-border px-5 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-alt disabled:opacity-50"
        >
          <Icon name="cargo" size={15} />
          {generateDemand.isPending ? 'Üretiliyor...' : 'Yeni Talep Üret'}
        </button>
        <button
          type="button"
          onClick={handleRunOptimize}
          disabled={optimize.isPending || !scenarioName.trim()}
          className="flex items-center gap-1.5 rounded-full bg-brand px-5 py-2 text-sm font-medium text-white hover:bg-brand-hover disabled:opacity-50"
        >
          <Icon name="gauge" size={15} />
          {optimize.isPending ? 'Çalışıyor...' : 'Optimizasyonu Çalıştır'}
        </button>
        <button
          type="button"
          onClick={() => train.mutate()}
          disabled={train.isPending}
          className="rounded-full border border-border px-5 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-alt disabled:opacity-50"
        >
          {train.isPending ? 'Eğitiliyor...' : 'ML Modelini Eğit'}
        </button>
        {generateDemand.isError && <p className="w-full text-sm text-critical">{generateDemand.error.message}</p>}
        {generateDemand.data && (
          <p className="w-full text-sm text-ink-secondary">
            {generateDemand.data.flights_count} uçuşa {generateDemand.data.generated_count} yeni bekleyen talep eklendi
            (toplam {generateDemand.data.pending_count} bekleyen talep var).
          </p>
        )}
        {optimize.isError && <p className="w-full text-sm text-critical">{optimize.error.message}</p>}
        {train.data && (
          <p className="w-full text-sm text-ink-secondary">
            {train.data.detail}
            {train.data.trained && train.data.accuracy !== null && (
              <> — doğruluk: %{Math.round((train.data.accuracy ?? 0) * 100)} ({train.data.n_samples} örnek)</>
            )}
          </p>
        )}
      </div>

      {selectedScenario && (
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium text-ink">Senaryo Detayı — {selectedScenario}</p>
          {kpisLoading && <p className="text-sm text-ink-muted">Yükleniyor...</p>}
          {kpisError && <p className="text-sm text-critical">Bu senaryo için sonuç bulunamadı.</p>}
          {kpis && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KpiCard label="Toplam Talep" value={String(kpis.total_requests)} icon="route" />
              <KpiCard label="Kabul Edilen" value={String(kpis.accepted_count)} icon="cargo" />
              <KpiCard label="Reddedilen" value={String(kpis.rejected_count)} icon="gauge" />
              <KpiCard label="Toplam Gelir" value={formatCurrency(kpis.total_revenue)} icon="trend-up" />
            </div>
          )}
        </div>
      )}

      <div className="flex flex-col gap-3">
        <p className="text-sm font-medium text-ink">Senaryo Geçmişi</p>
        <DataTable
          columns={columns}
          rows={scenariosData?.items ?? []}
          rowKey={(s) => s.scenario_name}
          isLoading={scenariosLoading}
        />
        <div className="flex items-center justify-between text-sm text-ink-secondary">
          <span>Toplam {total.toLocaleString('en-US')} senaryo</span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={!hasPrev}
              onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
              className="rounded-full border border-border px-3.5 py-1 disabled:opacity-40"
            >
              Önceki
            </button>
            <button
              type="button"
              disabled={!hasNext}
              onClick={() => setOffset((o) => o + PAGE_SIZE)}
              className="rounded-full border border-border px-3.5 py-1 disabled:opacity-40"
            >
              Sonraki
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
