import { formatScore, getSentimentColor, getSentimentLabel } from '../lib/sentiment'
import { Card, SectionTitle } from './ui'

interface RollingSentimentIndicatorProps {
  rolling: number | null | undefined
}

export function RollingSentimentIndicator({ rolling }: RollingSentimentIndicatorProps) {
  return (
    <Card className="flex h-full flex-1 flex-col p-4">
      <SectionTitle>7-day rolling</SectionTitle>
      <div className="mt-3 flex flex-1 flex-col items-center justify-center py-2 text-center">
        <p
          className={`font-mono text-2xl font-bold ${getSentimentColor(rolling)}`}
        >
          {formatScore(rolling)}
        </p>
        <p className="mt-1 text-sm font-medium text-zinc-300">
          {getSentimentLabel(rolling)}
        </p>
        <p className="mt-2 text-xs leading-relaxed text-zinc-500">
          Article-weighted average over the last 7 analysis days. Used for alerts.
        </p>
      </div>
    </Card>
  )
}
