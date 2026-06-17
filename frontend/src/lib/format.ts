const ET = 'America/New_York'

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-US', {
    timeZone: ET,
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(new Date(iso))
}

export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const hours = Math.floor(diff / 3_600_000)
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  return `${days}d ago`
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(amount)
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function formatCalendarDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const d = new Date(`${dateStr}T12:00:00`)
  return new Intl.DateTimeFormat('en-US', {
    timeZone: ET,
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  }).format(d)
}
