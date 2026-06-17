import {
  formatScore,
  getSentimentColor,
  getSentimentLabel,
  scoreToGaugePosition,
} from '../lib/sentiment'
import { Card } from './ui'

interface SentimentGaugeProps {
  score: number | null
  articleCount: number
}

export function SentimentGauge({ score, articleCount }: SentimentGaugeProps) {
  const position = score != null ? scoreToGaugePosition(score) : 0.5
  const angle = 180 - position * 180
  const rad = (angle * Math.PI) / 180
  const cx = 160
  const cy = 138
  const needleLen = 95
  const nx = cx + needleLen * Math.cos(rad)
  const ny = cy - needleLen * Math.sin(rad)

  return (
    <Card className="flex w-full flex-col items-center px-6 py-7">
      <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500">
        Daily Sentiment Gauge
      </p>

      <div className="relative w-full max-w-[380px]">
        <svg viewBox="0 0 320 175" className="w-full" aria-hidden>
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
          </defs>

          <path
            d="M 40 138 A 120 120 0 0 1 280 138"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="18"
            strokeLinecap="round"
          />

          <path
            d="M 40 138 A 120 120 0 0 1 280 138"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="18"
            strokeLinecap="round"
            opacity="0.85"
          />

          <line
            x1={cx}
            y1={cy}
            x2={nx}
            y2={ny}
            stroke="#e4e4e7"
            strokeWidth="3"
            strokeLinecap="round"
            style={{ transition: 'all 0.6s ease' }}
          />
          <circle cx={cx} cy={cy} r="6" fill="#e4e4e7" />
        </svg>

        <div className="pointer-events-none absolute bottom-8 left-3 text-[10px] font-medium text-red-400/80">
          red
        </div>
        <div className="pointer-events-none absolute bottom-14 left-1/2 -translate-x-1/2 text-[10px] font-medium text-amber-400/80">
          yellow
        </div>
        <div className="pointer-events-none absolute bottom-8 right-3 text-[10px] font-medium text-emerald-400/80">
          green
        </div>
      </div>

      <div className="mt-2 text-center">
        <p
          className={`font-mono text-5xl font-bold tracking-tight ${getSentimentColor(score)}`}
        >
          {formatScore(score)}
        </p>
        <p className="mt-1 text-lg font-medium text-zinc-300">
          {getSentimentLabel(score)}
        </p>
        <p className="mt-2 text-sm text-zinc-500">
          Based on {articleCount} article{articleCount !== 1 ? 's' : ''}
        </p>
      </div>
    </Card>
  )
}
