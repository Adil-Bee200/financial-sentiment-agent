import { describe, expect, it } from 'vitest'
import type { SentimentDaily } from '../api/types'
import { historyBySymbol, latestDailyBySymbol } from './chart'

function daily(
  symbol: string,
  analysis_date: string,
  avg_sentiment: number,
): SentimentDaily {
  return {
    symbol,
    analysis_date,
    analysis_date_label: analysis_date,
    chart_axis_label: analysis_date,
    timezone: 'America/New_York',
    avg_sentiment,
    article_count: 1,
    momentum: null,
    rolling_7d_sentiment: null,
    std_div: null,
    last_run_at: null,
    is_current_analysis_day: false,
  }
}

describe('chart helpers', () => {
  it('picks the latest analysis day per symbol', () => {
    const rows = [
      daily('NVDA', '2026-06-15', 0.1),
      daily('NVDA', '2026-06-17', 0.3),
      daily('AAPL', '2026-06-16', -0.2),
    ]

    expect(latestDailyBySymbol(rows).NVDA?.avg_sentiment).toBe(0.3)
    expect(latestDailyBySymbol(rows).AAPL?.avg_sentiment).toBe(-0.2)
  })

  it('groups history by symbol in ascending date order', () => {
    const rows = [
      daily('NVDA', '2026-06-17', 0.3),
      daily('NVDA', '2026-06-15', 0.1),
      daily('NVDA', '2026-06-16', 0.2),
    ]

    const history = historyBySymbol(rows).NVDA ?? []
    expect(history.map((row) => row.analysis_date)).toEqual([
      '2026-06-15',
      '2026-06-16',
      '2026-06-17',
    ])
  })
})
