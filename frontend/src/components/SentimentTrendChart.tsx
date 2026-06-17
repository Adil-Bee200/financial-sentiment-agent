import type { ReactNode } from 'react'
import type { SentimentDaily } from '../api/types'
import { formatChartDay } from '../lib/chart'
import { Card, SectionTitle } from './ui'

interface SentimentTrendChartProps {
  data: SentimentDaily[]
}

const W = 260
const H = 100
const PAD = { top: 8, right: 8, bottom: 20, left: 28 }
const PLOT_W = W - PAD.left - PAD.right
const PLOT_H = H - PAD.top - PAD.bottom

export function SentimentTrendChart({ data }: SentimentTrendChartProps) {
  if (data.length === 0) {
    return (
      <MetricCard title="7-Day Sentiment Trend">
        <p className="py-8 text-center text-xs text-zinc-600">No trend data yet</p>
      </MetricCard>
    )
  }

  const points = data.map((d, i) => {
    const x = PAD.left + (data.length === 1 ? PLOT_W / 2 : (i / (data.length - 1)) * PLOT_W)
    const y = PAD.top + PLOT_H - ((d.avg_sentiment + 1) / 2) * PLOT_H
    return { x, y, ...d }
  })

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${PAD.top + PLOT_H} L ${points[0].x} ${PAD.top + PLOT_H} Z`
  const zeroY = PAD.top + PLOT_H / 2

  return (
    <MetricCard title="7-Day Sentiment Trend">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" aria-hidden>
        <line
          x1={PAD.left}
          y1={zeroY}
          x2={PAD.left + PLOT_W}
          y2={zeroY}
          stroke="rgba(255,255,255,0.08)"
          strokeDasharray="3 3"
        />
        <path d={areaPath} fill="url(#trendFill)" opacity="0.4" />
        <path
          d={linePath}
          fill="none"
          stroke="#34d399"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {points.map((p) => (
          <circle key={p.date} cx={p.x} cy={p.y} r="3" fill="#34d399" />
        ))}
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="0" />
          </linearGradient>
        </defs>
        {points.map((p) => (
          <text
            key={`label-${p.date}`}
            x={p.x}
            y={H - 4}
            textAnchor="middle"
            fill="#71717a"
            fontSize="8"
          >
            {formatChartDay(p.date)}
          </text>
        ))}
      </svg>
    </MetricCard>
  )
}

function MetricCard({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <Card className="flex flex-1 flex-col p-4">
      <SectionTitle>{title}</SectionTitle>
      <div className="mt-3 flex-1">{children}</div>
    </Card>
  )
}
