import type { SentimentDaily } from '../api/types'

export function sortByDateAsc(data: SentimentDaily[]): SentimentDaily[] {
  return [...data].sort((a, b) => a.date.localeCompare(b.date))
}

/** Latest daily rollup per symbol from any list of daily rows. */
export function latestDailyBySymbol(
  data: SentimentDaily[],
): Record<string, SentimentDaily> {
  const bySymbol: Record<string, SentimentDaily> = {}
  for (const row of data) {
    const existing = bySymbol[row.symbol]
    if (!existing || row.date > existing.date) {
      bySymbol[row.symbol] = row
    }
  }
  return bySymbol
}

export function mergeDailyBySymbol(
  current: Record<string, SentimentDaily | undefined>,
  incoming: SentimentDaily[],
): Record<string, SentimentDaily | undefined> {
  return { ...current, ...latestDailyBySymbol(incoming) }
}

/** Group daily rows by symbol, sorted ascending by date. */
export function historyBySymbol(
  data: SentimentDaily[],
): Record<string, SentimentDaily[]> {
  const grouped: Record<string, SentimentDaily[]> = {}
  for (const row of data) {
    if (!grouped[row.symbol]) grouped[row.symbol] = []
    grouped[row.symbol].push(row)
  }
  for (const symbol of Object.keys(grouped)) {
    grouped[symbol] = sortByDateAsc(grouped[symbol])
  }
  return grouped
}

export function formatChartDay(dateStr: string): string {
  const d = new Date(`${dateStr}T12:00:00`)
  return d.toLocaleDateString('en-US', { weekday: 'short' })
}

export function formatChartDate(dateStr: string): string {
  const d = new Date(`${dateStr}T12:00:00`)
  return d.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

export interface ChartPoint extends SentimentDaily {
  day: string
  dateLabel: string
}

export function toChartPoints(data: SentimentDaily[]): ChartPoint[] {
  return data.map((d) => ({
    ...d,
    day: formatChartDay(d.date),
    dateLabel: formatChartDate(d.date),
  }))
}
