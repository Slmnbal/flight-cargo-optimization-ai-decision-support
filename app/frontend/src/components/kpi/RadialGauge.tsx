// dataviz skill'in "Meter" spec'i: dolgu değeri renkte, boş track aynı
// rengin daha açık (opaklık düşürülmüş) tonu -- state tüm halka boyunca
// okunabilir kalıyor. Yüzde bazlı KPI'lar için (Kabul Oranı, Ort. Ağırlık
// Kullanımı) sparkline yerine kullanılıyor -- "ne kadar dolu" sorusu bir
// trend çizgisinden çok bir halka ile daha sezgisel okunuyor.
interface RadialGaugeProps {
  value: number // 0-100
  color: string
  size?: number
}

export function RadialGauge({ value, color, size = 44 }: RadialGaugeProps) {
  const strokeWidth = 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(100, value))
  const dash = (clamped / 100) * circumference

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90 shrink-0">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeOpacity={0.15} strokeWidth={strokeWidth} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={`${dash} ${circumference - dash}`}
        strokeLinecap="round"
      />
    </svg>
  )
}
