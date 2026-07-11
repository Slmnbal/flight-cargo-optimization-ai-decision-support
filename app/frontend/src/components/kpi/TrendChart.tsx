import { useId } from 'react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface TrendChartProps {
  title: string
  data: { period: string; value: number }[]
  color: string
  valueFormatter?: (value: number) => string
}

// Tek seri -> dataviz skill kuralı: legend kutusu gerekmiyor, başlık zaten
// neyin çizildiğini söylüyor. Çizgi 2px, alan dolgusu seri renginin ~%10
// opaklıkta washı, gridline tek adım soluk/hairline.
export function TrendChart({ title, data, color, valueFormatter = String }: TrendChartProps) {
  // useId(): title'dan türetilen bir string (parantez, % gibi karakterler
  // içerebilir) SVG id/url() referansı olarak geçersiz olurdu ve gradyanın
  // sessizce düz griye düşmesine yol açardı -- React'ın garanti geçerli,
  // benzersiz id üretimi bu sınıf hatayı tamamen ortadan kaldırıyor.
  const gradientId = `trend-fill-${useId()}`

  return (
    <div className="card p-4">
      <p className="text-sm font-medium text-ink">{title}</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.12} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--color-grid)" strokeWidth={1} />
            <XAxis
              dataKey="period"
              tick={{ fontSize: 11, fill: 'var(--color-ink-muted)' }}
              axisLine={{ stroke: 'var(--color-grid)' }}
              tickLine={false}
              minTickGap={24}
            />
            <YAxis
              tick={{ fontSize: 11, fill: 'var(--color-ink-muted)' }}
              axisLine={false}
              tickLine={false}
              width={48}
              tickFormatter={valueFormatter}
            />
            <Tooltip
              formatter={(value) => valueFormatter(Number(value))}
              contentStyle={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: 'var(--color-ink-secondary)' }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              dot={false}
              activeDot={{ r: 4, stroke: 'var(--color-surface)', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
