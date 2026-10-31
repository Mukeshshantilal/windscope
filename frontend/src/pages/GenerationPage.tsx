import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { useState } from 'react'

import { GenerationChart } from '@/components/charts/GenerationChart'
import { ErrorBlock } from '@/components/Status'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NativeSelect } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useFilters } from '@/hooks/useFilters'
import { emptyStateMessage, exportCsvUrl, fetchSeries, fetchTable, queryErrorMessage } from '@/lib/api'
import { errorTone, formatMw, formatPct, formatSignedMw, formatUkDateTime } from '@/lib/format'
import type { Granularity } from '@/types/api'

export function GenerationPage() {
  const filters = useFilters()
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState('start_time')
  const [direction, setDirection] = useState('asc')
  const series = useQuery({
    queryKey: ['series', filters.query, filters.granularity],
    queryFn: () => fetchSeries({ ...filters.query, granularity: filters.granularity }),
  })
  const table = useQuery({
    queryKey: ['table', filters.query, page, sort, direction],
    queryFn: () => fetchTable({ ...filters.query, page, page_size: 25, sort, direction }),
  })

  if (series.isError) {
    return <ErrorBlock message={queryErrorMessage(series.error, 'Generation data could not be loaded from the API.')} />
  }

  const points = series.data?.points ?? []
  const withBoth = points.filter((point) => point.actual_mw != null && point.forecast_mw != null)
  const meanPct =
    withBoth.length > 0
      ? withBoth.reduce((sum, point) => sum + Math.abs(point.pct_error ?? 0), 0) / withBoth.length
      : null

  function toggleSort(column: string) {
    if (sort === column) {
      setDirection(direction === 'asc' ? 'desc' : 'asc')
    } else {
      setSort(column)
      setDirection('asc')
    }
    setPage(1)
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Actual vs selected forecast</CardTitle>
            <CardDescription>
              Percentage deviation uses matched hourly periods only. Daily energy is sum of hourly MW × 1 h. Half-hourly is a display overlay.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <NativeSelect
              aria-label="Granularity"
              value={filters.granularity}
              onChange={(event) => filters.update({ granularity: event.target.value as Granularity })}
            >
              <option value="daily">Daily</option>
              <option value="hourly">Hourly</option>
              <option value="half_hourly">Half-hourly</option>
            </NativeSelect>
            <Button asChild variant="outline" size="sm">
              <a href={exportCsvUrl(filters.query)}>
                <Download size={14} />
                Export CSV
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {series.isLoading ? (
            <Skeleton className="h-[340px]" />
          ) : (
            <GenerationChart points={points} emptyMessage={emptyStateMessage(series.data?.empty_reason)} />
          )}
          <div className="mt-3 text-xs text-muted">
            Mean absolute percentage deviation on matched points: {formatPct(meanPct)}. Matched {series.data?.matched_periods ?? 0} of {series.data?.expected_periods ?? 0} expected hours.
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Period table</CardTitle>
              <CardDescription>Hourly mean actual MW joined to the forecast available at the decision cutoff.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {table.isLoading ? (
            <Skeleton className="h-64" />
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[860px] text-left text-sm">
                  <thead className="text-xs text-muted">
                    <tr>
                      {[
                        ['start_time', 'Delivery'],
                        ['forecast_publish_time', 'Forecast published'],
                        ['forecast_mw', 'Forecast MW'],
                        ['actual_mw', 'Actual MW'],
                        ['error_mw', 'Error MW'],
                        ['abs_error_mw', '|Error| MW'],
                        ['pct_error', '% error'],
                      ].map(([key, label]) => (
                        <th key={key} className="py-2 font-medium">
                          <button type="button" className="hover:text-navy" onClick={() => toggleSort(key)}>
                            {label}
                          </button>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(table.data?.items ?? []).map((row) => (
                      <tr key={row.start_time} className="border-t border-line">
                        <td className="py-2">
                          {formatUkDateTime(row.start_time)}
                          <div className="text-[11px] text-muted">Cutoff {formatUkDateTime(row.decision_cutoff)}</div>
                        </td>
                        <td className="py-2">{formatUkDateTime(row.forecast_publish_time)}</td>
                        <td className="py-2 font-mono">{formatMw(row.forecast_mw)}</td>
                        <td className="py-2 font-mono">{formatMw(row.actual_mw)}</td>
                        <td className={`py-2 font-mono ${errorTone(row.error_mw)}`}>{formatSignedMw(row.error_mw)}</td>
                        <td className="py-2 font-mono">{formatMw(row.abs_error_mw)}</td>
                        <td className="py-2 font-mono">{formatPct(row.pct_error)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 flex items-center justify-between text-xs text-muted">
                <span>
                  {table.data?.total ?? 0} rows
                </span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page * 25 >= (table.data?.total ?? 0)}
                    onClick={() => setPage((value) => value + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
