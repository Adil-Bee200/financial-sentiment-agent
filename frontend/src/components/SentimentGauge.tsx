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
  const cx = 120
  const cy = 110
  const needleLen = 72
  const nx = cx + needleLen * Math.cos(rad)
  const ny = cy - needleLen * Math.sin(rad)

  return (
    <Card className="flex flex-col items-center px-6 py-5">
      <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500">
        Daily Sentiment Gauge
      </p>

      <div className="relative w-full max-w-[240px]">
        <svg viewBox="0 0 240 140" className="w-full" aria-hidden>
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
          </defs>

          {/* Background track */}
          <path
            d="M 30 110 A 90 90 0 0 1 210 110"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="14"
            strokeLinecap="round"
          />

          {/* Colored arc */}
          <path
            d="M 30 110 A 90 90 0 0 1 210 110"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="14"
            strokeLinecap="round"
            opacity="0.85"
          />

          {/* Needle */}
          <line
            x1={cx}
            y1={cy}
            x2={nx}
            y2={ny}
            stroke="#e4e4e7"
            strokeWidth="2.5"
            strokeLinecap="round"
            style={{ transition: 'all 0.6s ease' }}
          />
          <circle cx={cx} cy={cy} r="5" fill="#e4e4e7" />
        </svg>

        {/* Zone labels */}
        <div className="absolute bottom-8 left-2 text-[10px] font-medium text-red-400/80">
          red
        </div>
        <div className="absolute bottom-14 left-1/2 -translate-x-1/2 text-[10px] font-medium text-amber-400/80">
          yellow
        </div>
        <div className="absolute bottom-8 right-2 text-[10px] font-medium text-emerald-400/80">
          green
        </div>
      </div>

      <div className="mt-1 text-center">
        <p
          className={`font-mono text-4xl font-bold tracking-tight ${getSentimentColor(score)}`}
        >
          {formatScore(score)}
        </p>
        <p className="mt-1 text-base font-medium text-zinc-300">
          {getSentimentLabel(score)}
        </p>
        <p className="mt-2 text-sm text-zinc-500">
          Based on {articleCount} article{articleCount !== 1 ? 's' : ''}
        </p>
      </div>
    </Card>
  )
}
