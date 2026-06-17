import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SentimentDaily } from '../api/types'
import { toChartPoints, type ChartPoint } from '../lib/chart'
import { formatScore, getSentimentLabel } from '../lib/sentiment'
import { ChartContainer } from './charts/ChartContainer'
import { ChartTooltipBox, ChartTooltipRow } from './charts/ChartTooltip'
import {
  CHART_AXIS,
  CHART_CURSOR,
  CHART_GRID,
  formatSentimentAxisTick,
  SENTIMENT_CHART_MARGIN,
  SENTIMENT_Y_TICKS,
} from './charts/chartTheme'
import { MetricCard } from './charts/MetricCard'

interface SentimentTrendChartProps {
  data: SentimentDaily[]
}

function SentimentTrendTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: { payload: ChartPoint }[]
}) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <ChartTooltipBox title={row.dateLabel}>
      <ChartTooltipRow
        label="Sentiment"
        value={formatScore(row.avg_sentiment)}
        valueClassName="text-emerald-400"
      />
      <ChartTooltipRow label="Label" value={getSentimentLabel(row.avg_sentiment)} />
      <ChartTooltipRow label="Articles" value={String(row.article_count)} />
      {row.momentum != null && (
        <ChartTooltipRow label="Momentum" value={formatScore(row.momentum)} />
      )}
    </ChartTooltipBox>
  )
}

export function SentimentTrendChart({ data }: SentimentTrendChartProps) {
  const points = toChartPoints(data)

  if (points.length === 0) {
    return (
      <MetricCard title="7-Day Sentiment Trend">
        <p className="flex h-full items-center justify-center text-xs text-zinc-600">
          No trend data yet
        </p>
      </MetricCard>
    )
  }

  return (
    <MetricCard title="7-Day Sentiment Trend">
      <ChartContainer>
        <AreaChart data={points} margin={SENTIMENT_CHART_MARGIN}>
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#34d399" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={CHART_GRID}
            vertical={false}
          />
          <XAxis
            dataKey="day"
            tick={CHART_AXIS}
            axisLine={false}
            tickLine={false}
            tickMargin={6}
          />
          <YAxis
            domain={[-1, 1]}
            ticks={SENTIMENT_Y_TICKS}
            tick={{ ...CHART_AXIS, textAnchor: 'end' }}
            axisLine={false}
            tickLine={false}
            width={28}
            tickMargin={4}
            tickFormatter={formatSentimentAxisTick}
          />
          <ReferenceLine y={0} stroke={CHART_GRID} strokeDasharray="3 3" />
          <Tooltip
            content={<SentimentTrendTooltip />}
            cursor={{ stroke: CHART_CURSOR, strokeWidth: 1 }}
          />
          <Area
            type="monotone"
            dataKey="avg_sentiment"
            stroke="#34d399"
            strokeWidth={2}
            fill="url(#trendGradient)"
            activeDot={{
              r: 5,
              fill: '#34d399',
              stroke: '#111827',
              strokeWidth: 2,
            }}
          />
        </AreaChart>
      </ChartContainer>
    </MetricCard>
  )
}
