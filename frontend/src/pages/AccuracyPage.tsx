import { useQuery } from '@tanstack/react-query'

import { BarMetricChart } from '@/components/charts/BarMetricChart'
import { ErrorBlock } from '@/components/Status'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useFilters } from '@/hooks/useFilters'
import { fetchAccuracy, fetchDistribution, queryErrorMessage } from '@/lib/api'
import { formatMw, formatPct, formatSignedMw, formatUkDateTime } from '@/lib/format'

export function AccuracyPage() {
  const filters = useFilters()
  const metrics = useQuery({
    queryKey: ['accuracy', filters.query],
    queryFn: () => fetchAccuracy(filters.query),
  })
  const distribution = useQuery({
    queryKey: ['distribution', filters.query],
    queryFn: () => fetchDistribution(filters.query),
  })

  if (metrics.isError) {
    return <ErrorBlock message={queryErrorMessage(metrics.error, 'Accuracy metrics could not be loaded.')} />
  }

  const data = metrics.data

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="MAE" value={`${formatMw(data?.mae_mw)} MW`} note="mean |Forecast − Actual|" />
        <Metric label="RMSE" value={`${formatMw(data?.rmse_mw)} MW`} note="sqrt mean squared error" />
        <Metric label="Bias" value={`${formatSignedMw(data?.bias_mw)} MW`} note="mean Forecast − Actual" />
        <Metric
          label="MAPE"
          value={formatPct(data?.mape_pct)}
          note={`${data?.mape_sample_count ?? 0} valid samples, ${data?.mape_excluded_count ?? 0} excluded`}
        />
      </div>
      <p className="text-xs text-muted">{data?.mape_notes}</p>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Error distribution</CardTitle>
              <CardDescription>Histogram of Forecast − Actual on matched periods.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {distribution.isLoading ? (
              <Skeleton className="h-[260px]" />
            ) : (
              <BarMetricChart
                color="#ea580c"
                items={(distribution.data?.histogram.bins ?? []).map((bin, index) => ({
                  label: `${Math.round(bin.from)}`,
                  value: distribution.data?.histogram.counts[index] ?? 0,
                }))}
                unit="periods"
              />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Daily MAE trend</CardTitle>
              <CardDescription>Mean absolute error by UK calendar day.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {metrics.isLoading ? (
              <Skeleton className="h-[260px]" />
            ) : (
              <BarMetricChart
                color="#dc2626"
                items={(data?.daily ?? []).map((row) => ({ label: row.date.slice(8), value: row.mae_mw }))}
              />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Under-forecast vs over-forecast</CardTitle>
              <CardDescription>Counts of signed error on matched hours.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <Metric label="Over-forecast" value={String(data?.overforecast_count ?? '—')} note="Forecast > actual" />
            <Metric label="Under-forecast" value={String(data?.underforecast_count ?? '—')} note="Forecast < actual" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Accuracy by hour of day</CardTitle>
              <CardDescription>UK local hour. January 2026 is GMT.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {metrics.isLoading ? (
              <Skeleton className="h-[260px]" />
            ) : (
              <BarMetricChart
                items={(data?.by_hour ?? []).map((row) => ({
                  label: `${String(row.hour).padStart(2, '0')}:00`,
                  value: row.mae_mw,
                }))}
              />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Worst forecast periods</CardTitle>
            <CardDescription>Largest absolute errors. Percentiles: P90 {formatMw(data?.p90_abs_error_mw)} MW, P95 {formatMw(data?.p95_abs_error_mw)} MW.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted">
                <tr>
                  <th className="py-2 font-medium">Delivery</th>
                  <th className="py-2 font-medium">Actual</th>
                  <th className="py-2 font-medium">Forecast</th>
                  <th className="py-2 font-medium">Error</th>
                  <th className="py-2 font-medium">|Error|</th>
                </tr>
              </thead>
              <tbody>
                {(distribution.data?.worst_periods ?? data?.worst_periods ?? []).map((row) => (
                  <tr key={row.start_time} className="border-t border-line">
                    <td className="py-2">{formatUkDateTime(row.start_time)}</td>
                    <td className="py-2 font-mono">{formatMw(row.actual_mw)}</td>
                    <td className="py-2 font-mono">{formatMw(row.forecast_mw)}</td>
                    <td className="py-2 font-mono">{formatSignedMw(row.error_mw)}</td>
                    <td className="py-2 font-mono">{formatMw(row.abs_error_mw)}</td>
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

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="text-xs text-muted">{label}</div>
        <div className="mt-1 font-mono text-2xl whitespace-nowrap text-navy">{value}</div>
        <div className="mt-2 text-[11px] text-muted">{note}</div>
      </CardContent>
    </Card>
  )
}
