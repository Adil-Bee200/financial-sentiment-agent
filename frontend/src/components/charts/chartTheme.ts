export const CHART_AXIS = { fill: '#71717a', fontSize: 10 }
export const CHART_GRID = 'rgba(255,255,255,0.06)'
export const CHART_CURSOR = 'rgba(255,255,255,0.06)'
export const CHART_MARGIN = { top: 6, right: 4, left: 0, bottom: 0 }
export const SENTIMENT_CHART_MARGIN = { top: 6, right: 4, left: 0, bottom: 0 }

export const SENTIMENT_Y_TICKS = [-1, 0, 1]

export function formatSentimentAxisTick(value: number): string {
  if (value === 0) return '0'
  return value > 0 ? `+${value}` : String(value)
}
