import { usePredict } from '@/hooks/usePredict'
import { ApiError } from '@/lib/apiClient'

function probabilityStyle(pct: number): string {
  if (pct >= 66) return 'bg-good/15 text-good'
  if (pct >= 33) return 'bg-warning/25 text-ink'
  return 'bg-critical/15 text-critical'
}

export function PredictionBadge({ requestId }: { requestId: number }) {
  const { data, isFetching, error, refetch } = usePredict(requestId)

  if (data) {
    const pct = Math.round(data.acceptance_probability * 100)
    return (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${probabilityStyle(pct)}`}>
        %{pct} kabul olasılığı
      </span>
    )
  }

  if (error) {
    const message = error instanceof ApiError && error.status === 400 ? 'Model eğitilmedi' : 'Tahmin başarısız'
    return <span className="text-xs text-ink-muted">{message}</span>
  }

  return (
    <button
      type="button"
      onClick={() => refetch()}
      disabled={isFetching}
      className="rounded-md border border-border px-2.5 py-1 text-xs font-medium text-ink-secondary hover:bg-surface-alt disabled:opacity-50"
    >
      {isFetching ? 'Tahmin ediliyor...' : 'Tahmin Et'}
    </button>
  )
}
