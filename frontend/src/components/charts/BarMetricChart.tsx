import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { EmptyBlock } from '@/components/Status'
import { formatMw } from '@/lib/format'

interface Item {
  label: string
  value: number | null
}

export function BarMetricChart({ items, color = '#2563eb', unit = 'MW' }: { items: Item[]; color?: string; unit?: string }) {
  if (!items.length) return <EmptyBlock>No values to chart.</EmptyBlock>
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={items} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#e6eaef" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5b6b7c' }} minTickGap={16} />
          <YAxis tick={{ fontSize: 11, fill: '#5b6b7c' }} tickFormatter={(value: number) => formatMw(value)} />
          <Tooltip
            formatter={(value) => [typeof value === 'number' ? `${formatMw(value, 1)} ${unit}` : '—', '']}
            contentStyle={{ borderRadius: 8, borderColor: '#e6eaef', fontSize: 12 }}
          />
          <Bar dataKey="value" fill={color} radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
