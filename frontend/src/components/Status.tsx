import type { ReactNode } from 'react'

import type { HealthStatus } from '@/types/api'

export function LoadingBlock({ label = 'Loading data' }: { label?: string }) {
  return (
    <div className="flex h-48 items-center justify-center text-sm text-muted" role="status">
      {label}…
    </div>
  )
}

export function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-danger" role="alert">
      {message}
    </div>
  )
}

export function EmptyBlock({ children }: { children: ReactNode }) {
  return <div className="flex h-40 items-center justify-center text-sm text-muted">{children}</div>
}

export function ImportRequiredBlock({ health }: { health?: HealthStatus }) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-warn" role="status">
      <div className="font-medium text-navy">No historical data imported</div>
      <p className="mt-1 text-ink">
        Dashboards read cached Elexon records from PostgreSQL. They do not call Elexon on each page load.
        Load January 2026 FUELHH and WINDFOR data, then refresh.
      </p>
      <pre className="mt-2 overflow-x-auto rounded bg-white px-3 py-2 text-xs text-navy">
        {health?.import_hint ?? 'cd backend && python -m app.cli import-historical'}
      </pre>
    </div>
  )
}
