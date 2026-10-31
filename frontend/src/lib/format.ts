const UK_TZ = 'Europe/London'

export function formatMw(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)
}

export function formatPct(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)}%`
}

export function formatSignedMw(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  const formatted = formatMw(Math.abs(value), digits)
  if (value > 0) return `+${formatted}`
  if (value < 0) return `−${formatted}`
  return formatted
}

export function formatUkDateTime(value: string | Date | null | undefined): string {
  if (!value) return '—'
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: UK_TZ,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

export function formatUkDate(value: string | Date | null | undefined): string {
  if (!value) return '—'
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: UK_TZ,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function formatUkTime(value: string | Date | null | undefined): string {
  if (!value) return '—'
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: UK_TZ,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

export function errorTone(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'text-muted'
  if (Math.abs(value) >= 1500) return 'text-danger'
  if (Math.abs(value) >= 800) return 'text-warn'
  return 'text-ink'
}
