import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { EmptyBlock, ErrorBlock } from '@/components/Status'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NativeSelect } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useFilters } from '@/hooks/useFilters'
import { fetchRevisions, fetchTargets, queryErrorMessage } from '@/lib/api'
import { formatMw, formatUkDateTime } from '@/lib/format'

export function ExplorerPage() {
  const filters = useFilters()
  const [target, setTarget] = useState<string>('')
  const targets = useQuery({
    queryKey: ['targets', filters.query],
    queryFn: () => fetchTargets(filters.query),
  })

  const selectedTarget = target || targets.data?.items[0] || ''
  const revisions = useQuery({
    queryKey: ['revisions', selectedTarget, filters.selection],
    queryFn: () => fetchRevisions(selectedTarget, filters.selection),
    enabled: Boolean(selectedTarget),
  })

  const chartData = useMemo(
    () =>
      (revisions.data?.revisions ?? []).map((row) => ({
        ...row,
        label: formatUkDateTime(row.publish_time),
      })),
    [revisions.data],
  )

  if (targets.isError) {
    return <ErrorBlock message={queryErrorMessage(targets.error, 'Could not load forecast target timestamps.')} />
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Target delivery hour</CardTitle>
            <CardDescription>
              WINDFOR is hourly. The highlighted point is the latest revision published at or before the configured decision cutoff.
            </CardDescription>
          </div>
          {targets.isLoading ? (
            <Skeleton className="h-9 w-64" />
          ) : !(targets.data?.items ?? []).length ? (
            <EmptyBlock>No forecast targets in this delivery range. Import historical WINDFOR data if the warehouse is empty.</EmptyBlock>
          ) : (
            <NativeSelect
              aria-label="Target delivery time"
              value={selectedTarget}
              onChange={(event) => setTarget(event.target.value)}
              className="min-w-[260px]"
            >
              {(targets.data?.items ?? []).map((item) => (
                <option key={item} value={item}>
                  {formatUkDateTime(item)} UK
                </option>
              ))}
            </NativeSelect>
          )}
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <Fact label="Target" value={formatUkDateTime(revisions.data?.target_start_time)} />
          <Fact label="Decision cutoff" value={formatUkDateTime(revisions.data?.decision_cutoff)} />
          <Fact label="Selected forecast" value={`${formatMw(revisions.data?.selected?.generation_mw)} MW`} />
          <Fact label="Actual (hour mean)" value={`${formatMw(revisions.data?.actual_mw)} MW`} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Forecast revisions over time</CardTitle>
            <CardDescription>Each point is a published WINDFOR value for the same delivery hour. Grey points were not available at decision time.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {revisions.isLoading ? (
            <Skeleton className="h-[320px]" />
          ) : !chartData.length ? (
            <EmptyBlock>No revisions for this timestamp.</EmptyBlock>
          ) : (
            <div className="h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#e6eaef" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5b6b7c' }} minTickGap={20} />
                  <YAxis tick={{ fontSize: 11, fill: '#5b6b7c' }} tickFormatter={(value: number) => formatMw(value)} />
                  <Tooltip
                    formatter={(value, name) => [typeof value === 'number' ? `${formatMw(value)} MW` : '—', String(name)]}
                    contentStyle={{ borderRadius: 8, borderColor: '#e6eaef', fontSize: 12 }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="generation_mw" name="Forecast revision" stroke="#2563eb" strokeWidth={2} />
                  {revisions.data?.actual_mw != null ? (
                    <ReferenceLine y={revisions.data.actual_mw} stroke="#059669" strokeDasharray="4 4" label="Actual" />
                  ) : null}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>All available versions</CardTitle>
            <CardDescription>Eligibility is publish time ≤ cutoff. Later revisions exist in history but were not known at decision time.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted">
                <tr>
                  <th className="py-2 font-medium">Published</th>
                  <th className="py-2 font-medium">Forecast MW</th>
                  <th className="py-2 font-medium">Eligible</th>
                  <th className="py-2 font-medium">Selected</th>
                </tr>
              </thead>
              <tbody>
                {(revisions.data?.revisions ?? []).map((row) => (
                  <tr key={row.publish_time} className={`border-t border-line ${row.selected ? 'bg-blue-50' : !row.eligible_at_decision ? 'text-muted' : ''}`}>
                    <td className="py-2">{formatUkDateTime(row.publish_time)}</td>
                    <td className="py-2 font-mono">{formatMw(row.generation_mw)}</td>
                    <td className="py-2">{row.eligible_at_decision ? 'Yes' : 'No — after cutoff'}</td>
                    <td className="py-2">{row.selected ? 'Decision forecast' : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-canvas/60 px-3 py-2">
      <div className="text-[11px] text-muted">{label}</div>
      <div className="mt-1 text-sm font-medium text-navy">{value}</div>
    </div>
  )
}
