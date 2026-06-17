export type SentimentLabel =
  | 'Strong Positive'
  | 'Positive'
  | 'Neutral'
  | 'Negative'
  | 'Strong Negative'

export function getSentimentLabel(score: number | null | undefined): SentimentLabel {
  if (score == null) return 'Neutral'
  if (score >= 0.5) return 'Strong Positive'
  if (score >= 0.15) return 'Positive'
  if (score > -0.15) return 'Neutral'
  if (score > -0.5) return 'Negative'
  return 'Strong Negative'
}

export function getSentimentColor(score: number | null | undefined): string {
  if (score == null) return 'text-zinc-400'
  if (score >= 0.15) return 'text-emerald-400'
  if (score > -0.15) return 'text-amber-400'
  return 'text-red-400'
}

export function getSentimentBg(score: number | null | undefined): string {
  if (score == null) return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
  if (score >= 0.15) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  if (score > -0.15) return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  return 'bg-red-500/10 text-red-400 border-red-500/20'
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return '—'
  const sign = score > 0 ? '+' : ''
  return `${sign}${score.toFixed(2)}`
}

/** Map -1..1 to 0..1 for gauge needle position */
export function scoreToGaugePosition(score: number): number {
  return Math.max(0, Math.min(1, (score + 1) / 2))
}
