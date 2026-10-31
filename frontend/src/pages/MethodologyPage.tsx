import { useQuery } from '@tanstack/react-query'

import { ErrorBlock } from '@/components/Status'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useFilters } from '@/hooks/useFilters'
import { fetchQuality, queryErrorMessage } from '@/lib/api'
import { formatPct, formatUkDateTime } from '@/lib/format'

export function MethodologyPage() {
  const filters = useFilters()
  const quality = useQuery({
    queryKey: ['quality', filters.query],
    queryFn: () => fetchQuality(filters.query),
  })

  if (quality.isError) {
    return <ErrorBlock message={queryErrorMessage(quality.error, 'Data quality details could not be loaded.')} />
  }

  const data = quality.data

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Stat label="Actual records" value={data?.total_actual_records} />
        <Stat label="Forecast records" value={data?.total_forecast_records} />
        <Stat label="Matched periods" value={data?.matched_delivery_periods} />
        <Stat label="Coverage" value={formatPct(data?.data_coverage_pct)} />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Observed coverage</CardTitle>
              <CardDescription>
                Warehouse totals are all imported rows. Coverage uses the same delivery-date window as Overview.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Row label="Missing actual periods" value={data?.missing_actual_periods} />
            <Row label="Missing eligible forecasts" value={data?.missing_eligible_forecast_periods} />
            <Row label="Expected hours" value={data?.expected_periods} />
            <Row
              label="Coverage window"
              value={
                data?.coverage_range
                  ? `Delivery ${data.coverage_range.from} to ${data.coverage_range.to} (decisions ${data.coverage_range.decision_from} to ${data.coverage_range.decision_to})`
                  : '—'
              }
            />
            <Row label="Actuals from" value={formatUkDateTime(data?.actual_timestamp_range.min)} />
            <Row label="Actuals to" value={formatUkDateTime(data?.actual_timestamp_range.max)} />
            <Row label="Forecasts from" value={formatUkDateTime(data?.forecast_timestamp_range.min)} />
            <Row label="Forecasts to" value={formatUkDateTime(data?.forecast_timestamp_range.max)} />
            <Row
              label="Last successful import"
              value={
                data?.last_successful_import
                  ? `${data.last_successful_import.dataset} · ${formatUkDateTime(data.last_successful_import.completed_at)} · ${data.last_successful_import.records_processed} rows`
                  : 'None recorded'
              }
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Recent import runs</CardTitle>
              <CardDescription>Idempotent loads. Revisions are kept, not overwritten.</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {quality.isLoading ? (
              <Skeleton className="h-40" />
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted">
                  <tr>
                    <th className="py-2 font-medium">Dataset</th>
                    <th className="py-2 font-medium">Status</th>
                    <th className="py-2 font-medium">Rows</th>
                    <th className="py-2 font-medium">Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.recent_imports ?? []).map((run) => (
                    <tr key={`${run.dataset}-${run.started_at}`} className="border-t border-line">
                      <td className="py-2">{run.dataset}</td>
                      <td className="py-2">{run.status}</td>
                      <td className="py-2 font-mono">{run.records_processed}</td>
                      <td className="py-2">{formatUkDateTime(run.completed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Data sources</CardTitle>
            <CardDescription>Official Elexon BMRS datasets only. No prices, demand, or weather feeds.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-6">
          <p>{data?.methodology.sources.actuals}</p>
          <p>{data?.methodology.sources.forecasts}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CardTitle>Decision cutoff assumption</CardTitle>
            <Badge className="border-amber-200 bg-amber-50 text-warn">Assumption</Badge>
          </div>
        </CardHeader>
        <CardContent className="text-sm leading-6">
          {data?.methodology.decision_cutoff_assumption.rationale}
          <div className="mt-2 font-mono text-xs text-muted">
            Default {String(data?.methodology.decision_cutoff_assumption.hour).padStart(2, '0')}:
            {String(data?.methodology.decision_cutoff_assumption.minute).padStart(2, '0')} {data?.methodology.decision_cutoff_assumption.timezone}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Forecast selection</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-6">{data?.methodology.forecast_selection}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Matching and missing data</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-6">{data?.methodology.matching}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Formulas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          {Object.entries(data?.methodology.formulas ?? {}).map(([name, formula]) => (
            <div key={name} className="flex gap-3">
              <span className="w-16 font-medium uppercase text-muted">{name}</span>
              <span className="font-mono text-navy">{formula}</span>
            </div>
          ))}
          <p className="pt-3 text-muted">{data?.methodology.aggregation}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Limitations</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1 pl-5 text-sm leading-6">
            {(data?.methodology.limitations ?? []).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="text-xs text-muted">{label}</div>
        <div className="mt-1 font-mono text-2xl whitespace-nowrap text-navy">{value ?? '—'}</div>
      </CardContent>
    </Card>
  )
}

function Row({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-line py-1.5 last:border-0">
      <span className="text-muted">{label}</span>
      <span className="text-right text-navy">{value ?? '—'}</span>
    </div>
  )
}
