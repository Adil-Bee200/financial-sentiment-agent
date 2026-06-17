import type { SentimentDaily } from '../api/types'

export function sortByDateAsc(data: SentimentDaily[]): SentimentDaily[] {
  return [...data].sort((a, b) =>
    a.analysis_date.localeCompare(b.analysis_date),
  )
}

/** Latest analysis-day rollup per symbol. */
export function latestDailyBySymbol(
  data: SentimentDaily[],
): Record<string, SentimentDaily> {
  const bySymbol: Record<string, SentimentDaily> = {}
  for (const row of data) {
    const existing = bySymbol[row.symbol]
    if (!existing || row.analysis_date > existing.analysis_date) {
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

/** Group analysis-day rows by symbol, sorted ascending. */
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

export interface ChartPoint extends SentimentDaily {
  day: string
  dateLabel: string
}

export function toChartPoints(data: SentimentDaily[]): ChartPoint[] {
  return data.map((row) => ({
    ...row,
    day: row.chart_axis_label,
    dateLabel: row.analysis_date_label,
  }))
}
