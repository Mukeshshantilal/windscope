import { useSearchParams } from 'react-router-dom'

import type { Granularity, SelectionMode } from '@/types/api'

const MIN_DATE = '2026-01-01'
const MAX_DATE = '2026-02-01'

export function useFilters() {
  const [params, setParams] = useSearchParams()
  const from = params.get('from') ?? '2026-01-01'
  const to = params.get('to') ?? '2026-01-31'
  const selection = (params.get('selection') as SelectionMode) ?? 'decision_time'
  const granularity = (params.get('granularity') as Granularity) ?? 'daily'

  function update(next: Partial<{ from: string; to: string; selection: SelectionMode; granularity: Granularity }>) {
    const copy = new URLSearchParams(params)
    if (next.from) copy.set('from', next.from)
    if (next.to) copy.set('to', next.to)
    if (next.selection) copy.set('selection', next.selection)
    if (next.granularity) copy.set('granularity', next.granularity)
    setParams(copy, { replace: true })
  }

  return {
    from,
    to,
    selection,
    granularity,
    minDate: MIN_DATE,
    maxDate: MAX_DATE,
    update,
    query: { from, to, selection },
  }
}
