import { formatScore } from '../lib/sentiment'
import { Card, SectionTitle } from './ui'

interface MomentumIndicatorProps {
  momentum: number | null | undefined
}

function getMomentumMeta(momentum: number | null | undefined) {
  if (momentum == null) {
    return {
      label: 'No data',
      description: 'Day-over-day change unavailable',
      color: 'text-zinc-400',
      bg: 'bg-zinc-500/10',
      border: 'border-zinc-500/20',
      arrow: '→',
    }
  }
  if (momentum > 0.05) {
    return {
      label: 'Improving',
      description: 'Sentiment trending up vs yesterday',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      arrow: '↑',
    }
  }
  if (momentum < -0.05) {
    return {
      label: 'Declining',
      description: 'Sentiment trending down vs yesterday',
      color: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/20',
      arrow: '↓',
    }
  }
  return {
    label: 'Stable',
    description: 'Little change vs yesterday',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    arrow: '→',
  }
}

export function MomentumIndicator({ momentum }: MomentumIndicatorProps) {
  const meta = getMomentumMeta(momentum)

  return (
    <Card className="flex flex-1 flex-col p-4">
      <SectionTitle>Momentum</SectionTitle>
      <div className="mt-3 flex flex-1 flex-col items-center justify-center py-2 text-center">
        <div
          className={`flex h-16 w-16 items-center justify-center rounded-full border text-3xl font-bold ${meta.bg} ${meta.border} ${meta.color}`}
        >
          {meta.arrow}
        </div>
        <p className={`mt-4 font-mono text-2xl font-bold ${meta.color}`}>
          {formatScore(momentum)}
        </p>
        <p className="mt-1 text-sm font-medium text-zinc-300">{meta.label}</p>
        <p className="mt-2 text-xs leading-relaxed text-zinc-500">{meta.description}</p>
      </div>
    </Card>
  )
}
