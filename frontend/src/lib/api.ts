import axios, { isAxiosError } from 'axios'

import type {
  AccuracyMetrics,
  DashboardSummary,
  DataQuality,
  EmptyReason,
  ForecastRevisions,
  GenerationTableResponse,
  Granularity,
  HealthStatus,
  SelectionMode,
  SeriesPoint,
} from '@/types/api'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

export interface FilterParams {
  from: string
  to: string
  selection: SelectionMode
}

export async function fetchDashboard(params: FilterParams) {
  const { data } = await api.get<DashboardSummary>('/dashboard/summary', { params })
  return data
}

export async function fetchSeries(params: FilterParams & { granularity: Granularity }) {
  const { data } = await api.get<{
    points: SeriesPoint[]
    matched_periods: number
    expected_periods: number
    empty_reason?: EmptyReason
    period_unit?: string
  }>(
    '/generation/series',
    { params },
  )
  return data
}

export async function fetchTable(
  params: FilterParams & { page: number; page_size: number; sort: string; direction: string },
) {
  const { data } = await api.get<GenerationTableResponse>('/generation/table', { params })
  return data
}

export async function fetchAccuracy(params: FilterParams) {
  const { data } = await api.get<AccuracyMetrics>('/accuracy/metrics', { params })
  return data
}

export async function fetchDistribution(params: FilterParams) {
  const { data } = await api.get<Pick<AccuracyMetrics, 'histogram' | 'by_hour' | 'worst_periods' | 'overforecast_count' | 'underforecast_count'>>(
    '/accuracy/distribution',
    { params },
  )
  return data
}

export async function fetchTargets(params: FilterParams) {
  const { data } = await api.get<{ items: string[] }>('/forecasts/targets', { params })
  return data
}

export async function fetchRevisions(startTime: string, selection: SelectionMode) {
  const { data } = await api.get<ForecastRevisions>('/forecasts/revisions', {
    params: { start_time: startTime, selection },
  })
  return data
}

export async function fetchQuality(params?: FilterParams) {
  const { data } = await api.get<DataQuality>('/data/quality', { params })
  return data
}

export async function fetchHealth() {
  const { data } = await api.get<HealthStatus>('/health')
  return data
}

export function queryErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    if (!error.response) {
      return 'Backend unavailable. Start the API with uvicorn on port 8000, then refresh.'
    }
    const detail = error.response.data?.detail
    if (typeof detail === 'string') return detail
    return `${fallback} (HTTP ${error.response.status})`
  }
  return fallback
}

export function emptyStateMessage(reason?: EmptyReason, fallback = 'No generation records in this range.'): string {
  if (reason === 'not_imported') {
    return 'No historical Elexon data has been imported. Run python -m app.cli import-historical from backend/.'
  }
  if (reason === 'no_records_in_range') {
    return 'No imported records fall in the selected delivery dates.'
  }
  if (reason === 'unmatched') {
    return 'Actuals exist in this range, but no eligible decision-time forecasts could be matched.'
  }
  return fallback
}

export function exportCsvUrl(params: FilterParams) {
  const search = new URLSearchParams({
    from: params.from,
    to: params.to,
    selection: params.selection,
  })
  const base = import.meta.env.VITE_API_BASE_URL || '/api'
  return `${base}/generation/export?${search.toString()}`
}
