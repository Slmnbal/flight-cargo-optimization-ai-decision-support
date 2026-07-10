import { useState } from 'react'
import { useOptimize } from '@/hooks/useOptimize'
import { useTrainModel } from '@/hooks/useTrainModel'
import { KpiCard } from '@/components/kpi/KpiCard'
import { formatCurrency } from '@/lib/format'

export function OptimizePage() {
  const [scenarioName, setScenarioName] = useState('live')
  const optimize = useOptimize()
  const train = useTrainModel()

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-lg border border-border bg-surface p-4">
        <p className="text-sm font-medium text-ink">Optimizasyonu Çalıştır</p>
        <p className="mt-1 text-xs text-ink-secondary">
          Bekleyen ("pending") kargo taleplerini, uçuş kapasitesi ve iş kuralları (embargo, tehlikeli madde, soğuk
          zincir, öncelik sınıfı) kısıtları altında geliri maksimize edecek şekilde kabul/red kararına bağlar.
        </p>
        <div className="mt-4 flex flex-wrap items-end gap-3">
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
            onClick={() => optimize.mutate(scenarioName)}
            disabled={optimize.isPending || !scenarioName.trim()}
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-hover disabled:opacity-50"
          >
            {optimize.isPending ? 'Çalışıyor...' : 'Optimizasyonu Çalıştır'}
          </button>
        </div>
        {optimize.isError && <p className="mt-3 text-sm text-critical">{optimize.error.message}</p>}
      </div>

      {optimize.data && (
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium text-ink">Sonuç — {scenarioName}</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Solver Durumu" value={optimize.data.status} />
            <KpiCard label="Kabul Edilen" value={String(optimize.data.accepted.length)} />
            <KpiCard label="Reddedilen" value={String(optimize.data.rejected.length)} />
            <KpiCard label="Toplam Gelir" value={formatCurrency(optimize.data.total_revenue)} />
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border bg-surface p-4">
        <p className="text-sm font-medium text-ink">ML Modelini Eğit</p>
        <p className="mt-1 text-xs text-ink-secondary">
          Geçmiş optimizasyon sonuçlarından (bkz. backfill) bir kabul-olasılığı modeli eğitir — kargo talepleri
          tablosundaki "Tahmin Et" aksiyonu bu modeli kullanır.
        </p>
        <button
          type="button"
          onClick={() => train.mutate()}
          disabled={train.isPending}
          className="mt-4 rounded-md border border-border px-4 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-alt disabled:opacity-50"
        >
          {train.isPending ? 'Eğitiliyor...' : 'Modeli Eğit'}
        </button>
        {train.data && (
          <p className="mt-3 text-sm text-ink-secondary">
            {train.data.detail}
            {train.data.trained && train.data.accuracy !== null && (
              <> — doğruluk: %{Math.round((train.data.accuracy ?? 0) * 100)} ({train.data.n_samples} örnek)</>
            )}
          </p>
        )}
      </div>
    </div>
  )
}
