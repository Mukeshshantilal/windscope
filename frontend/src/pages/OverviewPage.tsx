import { useQuery } from '@tanstack/react-query'

import { BarMetricChart } from '@/components/charts/BarMetricChart'
import { GenerationChart } from '@/components/charts/GenerationChart'
import { ErrorBlock } from '@/components/Status'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NativeSelect } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useFilters } from '@/hooks/useFilters'
import { emptyStateMessage, fetchDashboard, fetchSeries, queryErrorMessage } from '@/lib/api'
import { formatMw, formatPct, formatSignedMw, formatUkDate } from '@/lib/format'
import type { Granularity } from '@/types/api'

export function OverviewPage() {
  const filters = useFilters()
  const summary = useQuery({
    queryKey: ['dashboard', filters.query],
    queryFn: () => fetchDashboard(filters.query),
  })
  const series = useQuery({
    queryKey: ['series', filters.query, filters.granularity],
    queryFn: () => fetchSeries({ ...filters.query, granularity: filters.granularity }),
  })

  if (summary.isError) {
    return <ErrorBlock message={queryErrorMessage(summary.error, 'Could not load the dashboard.')} />
  }

  const kpis = summary.data?.kpis
  const cards = [
    { label: 'Average actual', value: formatMw(kpis?.average_actual_mw), unit: 'MW', note: 'Mean FUELHH WIND outturn' },
    { label: 'Average forecast', value: formatMw(kpis?.average_forecast_mw), unit: 'MW', note: 'Mean selected WINDFOR' },
    { label: 'MAE', value: formatMw(kpis?.mae_mw), unit: 'MW', note: 'Mean absolute error' },
    { label: 'RMSE', value: formatMw(kpis?.rmse_mw), unit: 'MW', note: 'Root mean squared error' },
    { label: 'Forecast bias', value: formatSignedMw(kpis?.bias_mw), unit: 'MW', note: 'Positive = over-forecast' },
    { label: 'Data coverage', value: formatPct(kpis?.data_coverage_pct), unit: '', note: `${kpis?.matched_periods ?? 0} matched of ${kpis?.expected_periods ?? 0} expected hours` },
  ]

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {summary.isLoading
          ? cards.map((card) => <Skeleton key={card.label} className="h-28" />)
          : cards.map((card) => (
              <Card key={card.label}>
                <CardContent className="pt-4">
                  <div className="text-xs font-medium text-muted">{card.label}</div>
                  <div className="mt-1 font-mono text-2xl font-medium whitespace-nowrap text-navy">
                    {card.value}
                    {card.unit ? <span className="ml-1 text-xs text-muted">{card.unit}</span> : null}
                  </div>
                  <div className="mt-2 text-[11px] text-muted">{card.note}</div>
                </CardContent>
              </Card>
            ))}
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Wind Generation — Forecast vs Actual</CardTitle>
            <CardDescription>
              Daily and hourly views use hourly mean actual MW versus the selected forecast. Half-hourly is display-only. Missing forecasts are gaps, not zeros.
            </CardDescription>
          </div>
          <NativeSelect
            aria-label="Chart granularity"
            value={filters.granularity}
            onChange={(event) => filters.update({ granularity: event.target.value as Granularity })}
          >
            <option value="daily">Daily mean MW</option>
            <option value="hourly">Hourly</option>
            <option value="half_hourly">Half-hourly</option>
          </NativeSelect>
        </CardHeader>
        <CardContent>
          {series.isLoading ? (
            <Skeleton className="h-[340px]" />
          ) : (
            <GenerationChart
              points={series.data?.points ?? []}
              emptyMessage={emptyStateMessage(summary.data?.empty_reason ?? series.data?.empty_reason)}
            />
          )}
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Daily forecast error</CardTitle>
              <CardDescription>Daily MAE from matched hourly periods, UK calendar days.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {summary.isLoading ? (
              <Skeleton className="h-[260px]" />
            ) : (
              <BarMetricChart
                color="#dc2626"
                items={(summary.data?.daily_error ?? []).map((row) => ({
                  label: formatUkDate(`${row.date}T00:00:00Z`),
                  value: row.mae_mw,
                }))}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Forecast accuracy summary</CardTitle>
              <CardDescription>Matched timestamps only. MAPE excludes near-zero actuals.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <Stat label="MAPE" value={formatPct(summary.data?.accuracy_summary.mape_pct)} />
            <Stat label="MAPE sample" value={String(summary.data?.accuracy_summary.mape_sample_count ?? '—')} />
            <Stat label="Over-forecast periods" value={String(summary.data?.accuracy_summary.overforecast_count ?? '—')} />
            <Stat label="Under-forecast periods" value={String(summary.data?.accuracy_summary.underforecast_count ?? '—')} />
            <Stat label="P50 |error|" value={`${formatMw(summary.data?.accuracy_summary.p50_abs_error_mw)} MW`} />
            <Stat label="P90 |error|" value={`${formatMw(summary.data?.accuracy_summary.p90_abs_error_mw)} MW`} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Days with the largest errors</CardTitle>
              <CardDescription>Ranked by daily MAE.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted">
                  <tr>
                    <th className="py-2 font-medium">Date</th>
                    <th className="py-2 font-medium">MAE</th>
                    <th className="py-2 font-medium">Bias</th>
                    <th className="py-2 font-medium">Actual</th>
                    <th className="py-2 font-medium">Forecast</th>
                  </tr>
                </thead>
                <tbody>
                  {(summary.data?.worst_days ?? []).map((row) => (
                    <tr key={row.date} className="border-t border-line">
                      <td className="py-2">{row.date}</td>
                      <td className="py-2 font-mono">{formatMw(row.mae_mw)} MW</td>
                      <td className="py-2 font-mono">{formatSignedMw(row.bias_mw)} MW</td>
                      <td className="py-2 font-mono">{formatMw(row.average_actual_mw)}</td>
                      <td className="py-2 font-mono">{formatMw(row.average_forecast_mw)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Available forecast coverage</CardTitle>
              <CardDescription>Expected hours versus matched decision-time forecasts for the selected delivery dates.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <Stat label="Actual periods" value={String(summary.data?.forecast_coverage.actual_periods ?? '—')} />
            <Stat label="Matched periods" value={String(summary.data?.forecast_coverage.matched_periods ?? '—')} />
            <Stat label="Missing actuals" value={String(summary.data?.forecast_coverage.missing_actual_periods ?? '—')} />
            <Stat label="Missing eligible forecasts" value={String(summary.data?.forecast_coverage.missing_eligible_forecast_periods ?? '—')} />
            <Stat label="Actual coverage" value={formatPct(summary.data?.forecast_coverage.actual_coverage_pct)} />
            <Stat label="Matched coverage" value={formatPct(summary.data?.forecast_coverage.data_coverage_pct)} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-canvas/60 px-3 py-2">
      <div className="text-[11px] text-muted">{label}</div>
      <div className="mt-1 font-mono text-sm text-navy">{value}</div>
    </div>
  )
}
