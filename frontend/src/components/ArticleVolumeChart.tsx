import type { SentimentDaily } from '../api/types'
import { formatChartDay } from '../lib/chart'
import { Card, SectionTitle } from './ui'

interface ArticleVolumeChartProps {
  data: SentimentDaily[]
}

const W = 260
const H = 100
const PAD = { top: 8, right: 8, bottom: 20, left: 8 }
const PLOT_W = W - PAD.left - PAD.right
const PLOT_H = H - PAD.top - PAD.bottom

export function ArticleVolumeChart({ data }: ArticleVolumeChartProps) {
  if (data.length === 0) {
    return (
      <Card className="flex flex-1 flex-col p-4">
        <SectionTitle>Article Volume</SectionTitle>
        <p className="mt-3 py-8 text-center text-xs text-zinc-600">No volume data yet</p>
      </Card>
    )
  }

  const maxCount = Math.max(...data.map((d) => d.article_count), 1)
  const barGap = 6
  const barWidth = (PLOT_W - barGap * (data.length - 1)) / data.length

  return (
    <Card className="flex flex-1 flex-col p-4">
      <SectionTitle>Article Volume</SectionTitle>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full" aria-hidden>
        {data.map((d, i) => {
          const barH = (d.article_count / maxCount) * PLOT_H
          const x = PAD.left + i * (barWidth + barGap)
          const y = PAD.top + PLOT_H - barH
          return (
            <g key={d.date}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barH}
                rx="2"
                fill="#34d399"
                opacity={0.55 + (d.article_count / maxCount) * 0.45}
              />
              <text
                x={x + barWidth / 2}
                y={H - 4}
                textAnchor="middle"
                fill="#71717a"
                fontSize="8"
              >
                {formatChartDay(d.date)}
              </text>
            </g>
          )
        })}
      </svg>
    </Card>
  )
}
