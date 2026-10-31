export type SelectionMode = 'decision_time' | 'latest_before_delivery'
export type Granularity = 'daily' | 'hourly' | 'half_hourly'
export type EmptyReason = 'not_imported' | 'no_records_in_range' | 'unmatched' | null

export interface HealthStatus {
  status: string
  database: string
  warehouse: {
    actual_records: number
    forecast_records: number
    imported: boolean
  }
  import_hint: string
  last_successful_import: {
    dataset: string
    completed_at: string | null
    records_processed: number
  } | null
}

export interface DashboardSummary {
  range: { from: string; to: string; timezone: string; decision_from?: string; decision_to?: string; basis?: string; resolution?: string }
  empty_reason?: EmptyReason
  selection_mode: SelectionMode
  decision_cutoff: {
    hour: number
    minute: number
    timezone: string
    is_assumption: boolean
  }
  kpis: {
    average_actual_mw: number | null
    average_forecast_mw: number | null
    mae_mw: number | null
    rmse_mw: number | null
    bias_mw: number | null
    data_coverage_pct: number | null
    matched_periods: number
    expected_periods: number
    period_unit?: string
  }
  accuracy_summary: {
    mape_pct: number | null
    mape_sample_count: number
    mape_excluded_count: number
    overforecast_count: number
    underforecast_count: number
    p50_abs_error_mw: number | null
    p90_abs_error_mw: number | null
    p95_abs_error_mw: number | null
  }
  worst_days: Array<{
    date: string
    mae_mw: number
    bias_mw: number
    average_actual_mw: number
    average_forecast_mw: number
    sample_count: number
  }>
  daily_error: Array<{
    date: string
    mae_mw: number
    rmse_mw: number
    bias_mw: number
    average_actual_mw: number
    average_forecast_mw: number
    actual_mwh: number
    forecast_mwh: number
    sample_count: number
  }>
  forecast_coverage: {
    actual_periods: number
    matched_periods: number
    missing_actual_periods: number
    missing_eligible_forecast_periods: number
    actual_coverage_pct: number | null
    data_coverage_pct: number | null
  }
}

export interface SeriesPoint {
  start_time: string
  actual_mw: number | null
  forecast_mw: number | null
  error_mw: number | null
  abs_error_mw: number | null
  pct_error: number | null
  actual_mwh?: number | null
  forecast_mwh?: number | null
  forecast_publish_time?: string | null
  cutoff?: string | null
  sample_count?: number
}

export interface GenerationTableResponse {
  items: Array<{
    start_time: string
    decision_cutoff: string | null
    forecast_publish_time: string | null
    forecast_mw: number | null
    actual_mw: number | null
    error_mw: number | null
    abs_error_mw: number | null
    pct_error: number | null
  }>
  total: number
  page: number
  page_size: number
}

export interface AccuracyMetrics {
  sample_count: number
  mae_mw: number | null
  rmse_mw: number | null
  bias_mw: number | null
  mape_pct: number | null
  mape_sample_count: number
  mape_excluded_count: number
  average_actual_mw: number | null
  average_forecast_mw: number | null
  overforecast_count: number
  underforecast_count: number
  p50_abs_error_mw: number | null
  p90_abs_error_mw: number | null
  p95_abs_error_mw: number | null
  matched_periods: number
  expected_periods: number
  period_unit?: string
  empty_reason?: EmptyReason
  missing_actual_periods: number
  missing_eligible_forecast_periods: number
  mape_notes: string
  daily: DashboardSummary['daily_error']
  by_hour: Array<{
    hour: number
    mae_mw: number
    bias_mw: number
    sample_count: number
    average_actual_mw: number
    average_forecast_mw: number
  }>
  histogram: { bins: Array<{ from: number; to: number; count: number }>; counts: number[] }
  worst_periods: Array<{
    start_time: string
    actual_mw: number
    forecast_mw: number
    error_mw: number
    abs_error_mw: number
  }>
}

export interface ForecastRevisions {
  target_start_time: string
  actual_mw: number | null
  decision_cutoff: string
  selection_mode: SelectionMode
  selected: { publish_time: string; generation_mw: number } | null
  revisions: Array<{
    publish_time: string
    generation_mw: number
    eligible_at_decision: boolean
    selected: boolean
  }>
  actual_half_hours: Array<{ start_time: string; generation_mw: number }>
}

export interface DataQuality {
  total_actual_records: number
  total_forecast_records: number
  matched_delivery_periods: number
  missing_actual_periods: number
  missing_eligible_forecast_periods: number
  expected_periods: number
  period_unit?: string
  empty_reason?: EmptyReason
  coverage_range?: { from: string; to: string; decision_from?: string; decision_to?: string; basis?: string }
  data_coverage_pct: number | null
  actual_timestamp_range: { min: string | null; max: string | null }
  forecast_timestamp_range: { min: string | null; max: string | null }
  last_successful_import: {
    dataset: string
    completed_at: string | null
    records_processed: number
  } | null
  recent_imports: Array<{
    dataset: string
    started_at: string
    completed_at: string | null
    status: string
    records_processed: number
    error_message: string | null
  }>
  methodology: {
    sources: { actuals: string; forecasts: string }
    decision_cutoff_assumption: {
      hour: number
      minute: number
      timezone: string
      is_assumption: boolean
      rationale: string
    }
    forecast_selection: string
    matching: string
    formulas: Record<string, string>
    aggregation: string
    limitations: string[]
  }
}
