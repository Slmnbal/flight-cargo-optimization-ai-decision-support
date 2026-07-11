import { Link } from 'react-router-dom'
import { useAirports } from '@/hooks/useAirports'
import { useAircraftTypes } from '@/hooks/useAircraftTypes'
import { useDatasetSummary } from '@/hooks/useDatasetSummary'
import { KpiCard } from '@/components/kpi/KpiCard'
import { DataTable, type DataTableColumn } from '@/components/tables/DataTable'
import { Icon, type IconName } from '@/components/icons/Icon'
import { formatCompactNumber } from '@/lib/format'
import type { AirportOut, AircraftTypeOut } from '@/types/api'

const airportColumns: DataTableColumn<AirportOut>[] = [
  { key: 'code', header: 'Kod', render: (a) => a.airport_code },
  { key: 'name', header: 'Ad', render: (a) => a.airport_name },
  { key: 'country', header: 'Ülke', render: (a) => a.country },
  { key: 'timezone', header: 'Saat Dilimi', render: (a) => a.timezone },
  { key: 'customs', header: 'Gümrük', render: (a) => (a.customs_available ? 'Var' : '—') },
]

const aircraftColumns: DataTableColumn<AircraftTypeOut>[] = [
  { key: 'type', header: 'Uçak Tipi', render: (a) => a.aircraft_type },
  { key: 'weight', header: 'Max Ağırlık (kg)', render: (a) => a.max_cargo_weight_kg.toLocaleString('en-US'), align: 'right' },
  { key: 'volume', header: 'Max Hacim (m³)', render: (a) => a.max_cargo_volume_m3.toLocaleString('en-US'), align: 'right' },
  {
    key: 'cold',
    header: 'Soğuk Zincir (kg)',
    render: (a) => a.temperature_controlled_capacity_kg.toLocaleString('en-US'),
    align: 'right',
  },
  { key: 'freighter', header: 'Freighter', render: (a) => (a.is_freighter ? 'Evet' : 'Hayır') },
  { key: 'dg', header: 'Tehlikeli Madde', render: (a) => (a.dangerous_goods_allowed ? 'İzinli' : 'Yasak') },
]

const RELATED_PAGES: { to: string; label: string; description: string; icon: IconName }[] = [
  { to: '/routes', label: 'Rotalar', description: 'IST merkezli rota ağı, embargo ve kısıtlar', icon: 'route' },
  { to: '/flights', label: 'Uçuşlar', description: '12 aylık uçuş takvimi, kapasite kullanımı', icon: 'flight' },
  { to: '/cargo-requests', label: 'Kargo Talepleri', description: 'Tüm kargo talepleri ve ML tahmini', icon: 'cargo' },
  { to: '/optimize', label: 'Optimizasyon', description: 'Senaryo geçmişi ve yeni çalıştırma', icon: 'gauge' },
]

function formatDate(value: string | null): string {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
}

export function DatasetPage() {
  const { data: summary, isLoading: summaryLoading } = useDatasetSummary()
  const { data: airports, isLoading: airportsLoading } = useAirports()
  const { data: aircraftTypes, isLoading: aircraftLoading } = useAircraftTypes()

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard label="Havalimanı" value={summaryLoading ? '—' : String(summary?.airports_count)} icon="route" />
        <KpiCard label="Uçak Tipi" value={summaryLoading ? '—' : String(summary?.aircraft_types_count)} icon="flight" />
        <KpiCard label="Rota" value={summaryLoading ? '—' : String(summary?.routes_count)} icon="route" />
        <KpiCard
          label="Uçuş"
          value={summaryLoading ? '—' : formatCompactNumber(summary?.flights_count ?? 0)}
          icon="flight"
        />
        <KpiCard
          label="Kargo Talebi"
          value={summaryLoading ? '—' : formatCompactNumber(summary?.cargo_requests_count ?? 0)}
          icon="cargo"
        />
        <KpiCard
          label="Optimizasyon Sonucu"
          value={summaryLoading ? '—' : formatCompactNumber(summary?.optimization_results_count ?? 0)}
          icon="gauge"
        />
      </div>

      {summary && (
        <p className="text-sm text-ink-secondary">
          Veri aralığı: <span className="font-medium text-ink">{formatDate(summary.data_start)}</span> —{' '}
          <span className="font-medium text-ink">{formatDate(summary.data_end)}</span>
        </p>
      )}

      <div>
        <p className="mb-3 text-sm font-medium text-ink">Havalimanları</p>
        <DataTable columns={airportColumns} rows={airports ?? []} rowKey={(a) => a.airport_code} isLoading={airportsLoading} />
      </div>

      <div>
        <p className="mb-3 text-sm font-medium text-ink">Uçak Tipleri</p>
        <DataTable
          columns={aircraftColumns}
          rows={aircraftTypes ?? []}
          rowKey={(a) => a.aircraft_type}
          isLoading={aircraftLoading}
        />
      </div>

      <div>
        <p className="mb-3 text-sm font-medium text-ink">Detaylı veri için</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {RELATED_PAGES.map((page) => (
            <Link key={page.to} to={page.to} className="card flex items-start gap-3 p-4 transition-colors hover:bg-surface-alt">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-chrome-soft text-chrome">
                <Icon name={page.icon} size={16} />
              </span>
              <div>
                <p className="text-sm font-medium text-ink">{page.label}</p>
                <p className="mt-0.5 text-xs text-ink-secondary">{page.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
