import { useQuery } from '@tanstack/react-query'
import { Activity, FileText, GitBranch, LayoutDashboard, Target, Wind } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { ErrorBlock, ImportRequiredBlock } from '@/components/Status'
import { Badge } from '@/components/ui/badge'
import { NativeSelect } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { useFilters } from '@/hooks/useFilters'
import { fetchHealth, queryErrorMessage } from '@/lib/api'
import { cn } from '@/lib/utils'

const nav = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/generation', label: 'Generation Analysis', icon: Activity },
  { to: '/accuracy', label: 'Forecast Accuracy', icon: Target },
  { to: '/explorer', label: 'Forecast Explorer', icon: GitBranch },
  { to: '/methodology', label: 'Data Quality & Methodology', icon: FileText },
]

const titles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Overview', subtitle: 'Day-ahead wind generation versus actual outturn' },
  '/generation': { title: 'Generation Analysis', subtitle: 'Hourly actuals, selected forecasts, and errors' },
  '/accuracy': { title: 'Forecast Accuracy', subtitle: 'Error metrics for the selected decision window' },
  '/explorer': { title: 'Forecast Explorer', subtitle: 'Point-in-time forecast revisions for a delivery hour' },
  '/methodology': { title: 'Data Quality & Methodology', subtitle: 'Sources, assumptions, and coverage' },
}

function DataStatusBanner() {
  const health = useQuery({ queryKey: ['health'], queryFn: fetchHealth, retry: 1 })
  if (health.isError) {
    return (
      <div className="mb-4">
        <ErrorBlock message={queryErrorMessage(health.error, 'Backend unavailable.')} />
      </div>
    )
  }
  if (health.data?.warehouse && !health.data.warehouse.imported) {
    return (
      <div className="mb-4">
        <ImportRequiredBlock health={health.data} />
      </div>
    )
  }
  return null
}

export function AppShell() {
  const location = useLocation()
  const page = titles[location.pathname] ?? titles['/']
  const filters = useFilters()

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-line bg-white lg:flex lg:flex-col">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-navy text-white">
            <Wind size={16} />
          </div>
          <div>
            <div className="text-sm font-semibold text-navy">WindScope</div>
            <div className="text-[11px] text-muted">UK wind analytics</div>
          </div>
        </div>
        <nav className="flex-1 px-3">
          {nav.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={`${item.to}?${new URLSearchParams({
                  from: filters.from,
                  to: filters.to,
                  selection: filters.selection,
                  granularity: filters.granularity,
                }).toString()}`}
                className={({ isActive }) =>
                  cn(
                    'mb-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm',
                    isActive ? 'bg-navy text-white' : 'text-ink hover:bg-canvas',
                  )
                }
                end={item.to === '/'}
              >
                <Icon size={16} />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
        <div className="border-t border-line px-5 py-4 text-[11px] text-muted">
          Date filters are UK delivery dates
          <br />
          Decision date is the previous UK day
        </div>
      </aside>

      <div className="lg:pl-60">
        <header className="sticky top-0 z-10 border-b border-line bg-white/95 backdrop-blur">
          <nav className="flex gap-1 overflow-x-auto border-b border-line px-4 py-2 lg:hidden">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={`${item.to}?from=${filters.from}&to=${filters.to}&selection=${filters.selection}`}
                className={({ isActive }) =>
                  cn('whitespace-nowrap rounded-md px-2 py-1 text-xs', isActive ? 'bg-navy text-white' : 'text-ink')
                }
                end={item.to === '/'}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between lg:px-6">
            <div>
              <h1 className="text-lg font-semibold text-navy">{page.title}</h1>
              <p className="text-xs text-muted">{page.subtitle}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>UK time (GMT in January)</Badge>
              <label className="text-[11px] text-muted">
                Delivery from
                <Input
                  type="date"
                  min={filters.minDate}
                  max={filters.maxDate}
                  value={filters.from}
                  onChange={(event) => filters.update({ from: event.target.value })}
                  className="ml-1 w-[140px]"
                />
              </label>
              <label className="text-[11px] text-muted">
                Delivery to
                <Input
                  type="date"
                  min={filters.minDate}
                  max={filters.maxDate}
                  value={filters.to}
                  onChange={(event) => filters.update({ to: event.target.value })}
                  className="ml-1 w-[140px]"
                />
              </label>
              <NativeSelect
                aria-label="Forecast selection mode"
                value={filters.selection}
                onChange={(event) => filters.update({ selection: event.target.value as typeof filters.selection })}
              >
                <option value="decision_time">Decision-time forecast</option>
                <option value="latest_before_delivery">Latest before delivery</option>
              </NativeSelect>
            </div>
          </div>
        </header>
        <main className="px-4 py-5 lg:px-6">
          <DataStatusBanner />
          <Outlet />
        </main>
      </div>
    </div>
  )
}
