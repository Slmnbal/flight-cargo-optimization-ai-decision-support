import { useMemo, useState } from 'react'
import { useRoutes } from '@/hooks/useRoutes'
import { DataTable, type DataTableColumn } from '@/components/tables/DataTable'
import type { RouteOut } from '@/types/api'

const columns: DataTableColumn<RouteOut>[] = [
  { key: 'route', header: 'Rota', render: (r) => `${r.origin_airport} → ${r.destination_airport}` },
  { key: 'region', header: 'Bölge', render: (r) => r.region },
  { key: 'type', header: 'Tip', render: (r) => r.route_type },
  { key: 'distance', header: 'Mesafe (km)', render: (r) => r.distance_km.toLocaleString('en-US'), align: 'right' },
  { key: 'customs', header: 'Gümrük', render: (r) => (r.customs_required ? 'Gerekli' : '—') },
  {
    key: 'embargo',
    header: 'Embargo',
    render: (r) =>
      r.embargo_active ? (
        <span className="text-critical">{r.embargoed_cargo_types ?? 'Tüm kargo tipleri'}</span>
      ) : (
        <span className="text-ink-muted">—</span>
      ),
  },
  {
    key: 'restricted',
    header: 'Tehlikeli Madde',
    render: (r) => (r.restricted_cargo_allowed ? <span className="text-ink-muted">İzinli</span> : <span className="text-critical">Kısıtlı</span>),
  },
]

export function RoutesPage() {
  const { data, isLoading } = useRoutes()
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!data) return []
    const q = search.trim().toUpperCase()
    if (!q) return data
    return data.filter(
      (r) => r.origin_airport.includes(q) || r.destination_airport.includes(q) || r.region.toUpperCase().includes(q),
    )
  }, [data, search])

  return (
    <div className="flex flex-col gap-4">
      <input
        type="text"
        placeholder="Havalimanı kodu veya bölge ara (örn. IST, Asia)"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-brand"
      />
      <DataTable columns={columns} rows={filtered} rowKey={(r) => r.route_id} isLoading={isLoading} />
    </div>
  )
}
