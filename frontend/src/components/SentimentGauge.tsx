import { formatCalendarDate } from '../lib/format'
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
  asOfDate: string | null | undefined
}

const CX = 160
const CY = 138
const R = 120
const STROKE = 18
const GAP = 4

const ZONES = [
  { color: '#ef4444' },
  { color: '#eab308' },
  { color: '#22c55e' },
] as const

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = (deg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) }
}

const OUTER_R = R + STROKE / 2
const INNER_R = R - STROKE / 2

/** Filled annular arc — flat radial ends match the bar segment shape exactly. */
function barPath(
  cx: number,
  cy: number,
  startDeg: number,
  endDeg: number,
) {
  const outerStart = polar(cx, cy, OUTER_R, startDeg)
  const outerEnd = polar(cx, cy, OUTER_R, endDeg)
  const innerEnd = polar(cx, cy, INNER_R, endDeg)
  const innerStart = polar(cx, cy, INNER_R, startDeg)
  const sweep = startDeg > endDeg ? 1 : 0
  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${OUTER_R} ${OUTER_R} 0 0 ${sweep} ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${INNER_R} ${INNER_R} 0 0 ${1 - sweep} ${innerStart.x} ${innerStart.y}`,
    'Z',
  ].join(' ')
}

/** Three equal semicircle segments with small gaps between them. */
function zoneAngles(index: number): { start: number; end: number } {
  const segment = 180 / 3
  const start = 180 - index * segment - (index > 0 ? GAP / 2 : 0)
  const end = 180 - (index + 1) * segment + (index < 2 ? GAP / 2 : 0)
  return { start, end }
}

/** How much of a zone (0–1) is filled based on overall gauge position (0–1). */
function zoneFillFraction(zoneIndex: number, position: number): number {
  const zoneStart = zoneIndex / 3
  const zoneEnd = (zoneIndex + 1) / 3
  if (position <= zoneStart) return 0
  if (position >= zoneEnd) return 1
  return (position - zoneStart) / (zoneEnd - zoneStart)
}

export function SentimentGauge({ score, articleCount, asOfDate }: SentimentGaugeProps) {
  const position = score != null ? scoreToGaugePosition(score) : 0

  return (
    <Card className="flex w-full flex-col items-center px-6 py-7">
      <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500">
        Daily Sentiment Gauge
      </p>

      <div className="w-full max-w-[380px]">
        <svg viewBox="0 0 320 175" className="w-full" aria-hidden>
          {ZONES.map((zone, i) => {
            const { start, end } = zoneAngles(i)
            const fraction = score != null ? zoneFillFraction(i, position) : 0
            const fillEnd = start - fraction * (start - end)

            return (
              <g key={i}>
                <path
                  d={barPath(CX, CY, start, end)}
                  fill={zone.color}
                  opacity={0.22}
                />
                {fraction > 0 && (
                  <path
                    d={barPath(CX, CY, start, fillEnd)}
                    fill={zone.color}
                    opacity={0.95}
                    style={{ transition: 'd 0.6s ease' }}
                  />
                )}
              </g>
            )
          })}
        </svg>
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
          {asOfDate && (
            <span className="block text-xs text-zinc-600">
              As of {formatCalendarDate(asOfDate)} ET
            </span>
          )}
        </p>
      </div>
    </Card>
  )
}
