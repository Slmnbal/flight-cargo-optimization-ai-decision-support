// warning tonu açık yüzeyde düşük kontrastlı (dataviz skill'inin status
// paleti notu) -- metni ham warning rengiyle değil, ink ile yazıp rengi
// sadece arka plan ipucu (secondary encoding) olarak kullanıyoruz; birincil
// anlam zaten metin etiketinde (LABELS).
const STATUS_STYLES: Record<string, string> = {
  accepted: 'bg-good/15 text-good',
  completed: 'bg-good/15 text-good',
  rejected: 'bg-critical/15 text-critical',
  pending: 'bg-warning/25 text-ink',
  scheduled: 'bg-warning/25 text-ink',
}

const DEFAULT_STYLE = 'bg-ink-muted/15 text-ink-secondary'

const LABELS: Record<string, string> = {
  accepted: 'Kabul edildi',
  rejected: 'Reddedildi',
  pending: 'Bekliyor',
  scheduled: 'Planlandı',
  completed: 'Tamamlandı',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        STATUS_STYLES[status] ?? DEFAULT_STYLE
      }`}
    >
      {LABELS[status] ?? status}
    </span>
  )
}
