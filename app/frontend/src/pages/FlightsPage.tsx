import { useState } from 'react'
import { useFlights } from '@/hooks/useFlights'
import { useRoutes } from '@/hooks/useRoutes'
import { useCapacityUtilization } from '@/hooks/useCapacityUtilization'
import { DataTable, type DataTableColumn } from '@/components/tables/DataTable'
import { StatusBadge } from '@/components/common/StatusBadge'
import { Icon } from '@/components/icons/Icon'
import type { FlightOut } from '@/types/api'

const PAGE_SIZE = 25

export function FlightsPage() {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [routeId, setRouteId] = useState('')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)
  const [selectedFlightId, setSelectedFlightId] = useState<number | undefined>(undefined)

  const { data: routes } = useRoutes()
  const { data, isLoading } = useFlights({
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    route_id: routeId ? Number(routeId) : undefined,
    status: status || undefined,
    limit: PAGE_SIZE,
    offset,
  })
  const { data: capacity, isFetching: isCapacityLoading } = useCapacityUtilization(selectedFlightId)

  const routeLabel = (routeIdValue: number) => {
    const route = routes?.find((r) => r.route_id === routeIdValue)
    return route ? `${route.origin_airport} → ${route.destination_airport}` : `#${routeIdValue}`
  }

  const columns: DataTableColumn<FlightOut>[] = [
    { key: 'flight_number', header: 'Uçuş No', render: (f) => f.flight_number },
    { key: 'route', header: 'Rota', render: (f) => routeLabel(f.route_id) },
    { key: 'aircraft', header: 'Uçak Tipi', render: (f) => f.aircraft_type },
    {
      key: 'departure',
      header: 'Kalkış',
      render: (f) => new Date(f.departure_scheduled).toLocaleString('tr-TR', { dateStyle: 'medium', timeStyle: 'short' }),
    },
    { key: 'status', header: 'Durum', render: (f) => <StatusBadge status={f.status} /> },
    {
      key: 'action',
      header: 'Kapasite',
      render: (f) => (
        <button
          type="button"
          onClick={() => setSelectedFlightId(f.flight_id)}
          className="text-xs font-medium text-brand hover:underline"
        >
          Görüntüle
        </button>
      ),
    },
  ]

  const total = data?.total ?? 0
  const hasNext = offset + PAGE_SIZE < total
  const hasPrev = offset > 0

  return (
    <div className="flex flex-col gap-4">
      <div className="card flex flex-wrap items-end gap-3 p-4">
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Başlangıç
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value)
              setOffset(0)
            }}
            className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Bitiş
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value)
              setOffset(0)
            }}
            className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Rota
          <select
            value={routeId}
            onChange={(e) => {
              setRouteId(e.target.value)
              setOffset(0)
            }}
            className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink"
          >
            <option value="">Tümü</option>
            {routes?.map((r) => (
              <option key={r.route_id} value={r.route_id}>
                {r.origin_airport} → {r.destination_airport}
              </option>
            ))}
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
            <option value="scheduled">Planlandı</option>
            <option value="completed">Tamamlandı</option>
          </select>
        </label>
      </div>

      {selectedFlightId && (
        <div className="card flex items-center gap-3 p-4 text-sm">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-chrome-soft text-chrome">
            <Icon name="cargo" size={16} />
          </span>
          {isCapacityLoading && <p className="text-ink-muted">Yükleniyor...</p>}
          {capacity && (
            <div className="flex flex-wrap gap-6">
              <p className="text-ink">
                <span className="text-ink-muted">Uçuş:</span> {capacity.flight_number}
              </p>
              <p className="text-ink">
                <span className="text-ink-muted">Ağırlık kullanımı:</span> %{capacity.weight_utilization_pct}
              </p>
              <p className="text-ink">
                <span className="text-ink-muted">Hacim kullanımı:</span> %{capacity.volume_utilization_pct}
              </p>
            </div>
          )}
        </div>
      )}

      <DataTable columns={columns} rows={data?.items ?? []} rowKey={(f) => f.flight_id} isLoading={isLoading} />

      <div className="flex items-center justify-between text-sm text-ink-secondary">
        <span>Toplam {total.toLocaleString('en-US')} uçuş</span>
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
  )
}
