import { useState } from 'react'
import { useCargoRequests } from '@/hooks/useCargoRequests'
import { DataTable, type DataTableColumn } from '@/components/tables/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { PredictionBadge } from '@/components/ml/PredictionBadge'
import { formatCurrency } from '@/lib/format'
import type { CargoRequestOut } from '@/types/api'

const PAGE_SIZE = 25

const CARGO_TYPES = ['general', 'perishable', 'dangerous_goods', 'valuable', 'live_animal', 'oversized']

export function CargoRequestsPage() {
  const [cargoType, setCargoType] = useState('')
  const [priorityClass, setPriorityClass] = useState('')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)

  const { data, isLoading } = useCargoRequests({
    cargo_type: cargoType || undefined,
    priority_class: priorityClass || undefined,
    status: status || undefined,
    limit: PAGE_SIZE,
    offset,
  })

  const columns: DataTableColumn<CargoRequestOut>[] = [
    { key: 'id', header: 'Talep ID', render: (r) => `#${r.request_id}` },
    { key: 'flight', header: 'Uçuş ID', render: (r) => `#${r.flight_id}` },
    { key: 'cargo_type', header: 'Kargo Tipi', render: (r) => r.cargo_type },
    { key: 'priority', header: 'Öncelik', render: (r) => (r.priority_class === 'contract' ? 'Sözleşmeli' : 'Spot') },
    { key: 'weight', header: 'Ağırlık (kg)', render: (r) => r.weight_kg.toLocaleString('en-US'), align: 'right' },
    { key: 'revenue', header: 'Gelir', render: (r) => formatCurrency(r.revenue), align: 'right' },
    { key: 'status', header: 'Durum', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'prediction', header: 'ML Tahmini', render: (r) => <PredictionBadge requestId={r.request_id} /> },
  ]

  const total = data?.total ?? 0
  const hasNext = offset + PAGE_SIZE < total
  const hasPrev = offset > 0

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Kargo Tipi
          <select
            value={cargoType}
            onChange={(e) => {
              setCargoType(e.target.value)
              setOffset(0)
            }}
            className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          >
            <option value="">Tümü</option>
            {CARGO_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Öncelik
          <select
            value={priorityClass}
            onChange={(e) => {
              setPriorityClass(e.target.value)
              setOffset(0)
            }}
            className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          >
            <option value="">Tümü</option>
            <option value="contract">Sözleşmeli</option>
            <option value="spot">Spot</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Durum
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setOffset(0)
            }}
            className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          >
            <option value="">Tümü</option>
            <option value="pending">Bekliyor</option>
            <option value="accepted">Kabul edildi</option>
            <option value="rejected">Reddedildi</option>
          </select>
        </label>
      </div>

      <DataTable columns={columns} rows={data?.items ?? []} rowKey={(r) => r.request_id} isLoading={isLoading} />

      <div className="flex items-center justify-between text-sm text-ink-secondary">
        <span>Toplam {total.toLocaleString('en-US')} talep</span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!hasPrev}
            onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
            className="rounded-md border border-border px-3 py-1 disabled:opacity-40"
          >
            Önceki
          </button>
          <button
            type="button"
            disabled={!hasNext}
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            className="rounded-md border border-border px-3 py-1 disabled:opacity-40"
          >
            Sonraki
          </button>
        </div>
      </div>
    </div>
  )
}
