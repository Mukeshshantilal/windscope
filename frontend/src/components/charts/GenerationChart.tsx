import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { EmptyBlock } from '@/components/Status'
import { formatMw, formatUkDateTime } from '@/lib/format'
import type { SeriesPoint } from '@/types/api'

export function GenerationChart({
  points,
  emptyMessage = 'No generation records in this range.',
}: {
  points: SeriesPoint[]
  emptyMessage?: string
}) {
  if (!points.length) {
    return <EmptyBlock>{emptyMessage}</EmptyBlock>
  }

  const data = points.map((point) => ({
    ...point,
    label: formatUkDateTime(point.start_time),
  }))

  return (
    <div className="h-[340px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#e6eaef" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5b6b7c' }} minTickGap={24} />
          <YAxis tick={{ fontSize: 11, fill: '#5b6b7c' }} tickFormatter={(value: number) => formatMw(value)} />
          <Tooltip
            contentStyle={{ borderRadius: 8, borderColor: '#e6eaef', fontSize: 12 }}
            formatter={(value, name) => [typeof value === 'number' ? `${formatMw(value, 0)} MW` : '—', String(name)]}
          />
          <Legend />
          <Line type="monotone" dataKey="actual_mw" name="Actual" stroke="#059669" dot={false} strokeWidth={2} connectNulls={false} />
          <Line type="monotone" dataKey="forecast_mw" name="Selected forecast" stroke="#2563eb" dot={false} strokeWidth={2} connectNulls={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
