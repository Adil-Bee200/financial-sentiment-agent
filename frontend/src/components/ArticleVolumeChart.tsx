import {
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SentimentDaily } from '../api/types'
import { toChartPoints, type ChartPoint } from '../lib/chart'
import { formatScore } from '../lib/sentiment'
import { ChartContainer } from './charts/ChartContainer'
import { ChartTooltipBox, ChartTooltipRow } from './charts/ChartTooltip'
import { CHART_AXIS, CHART_CURSOR, CHART_GRID, CHART_MARGIN } from './charts/chartTheme'
import { MetricCard } from './charts/MetricCard'

interface ArticleVolumeChartProps {
  data: SentimentDaily[]
}

function VolumeTooltip({
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
        label="Articles"
        value={String(row.article_count)}
        valueClassName="text-emerald-400"
      />
      <ChartTooltipRow
        label="Avg sentiment"
        value={formatScore(row.avg_sentiment)}
      />
    </ChartTooltipBox>
  )
}

export function ArticleVolumeChart({ data }: ArticleVolumeChartProps) {
  const points = toChartPoints(data)

  if (points.length === 0) {
    return (
      <MetricCard title="Article Volume">
        <p className="py-8 text-center text-xs text-zinc-600">No volume data yet</p>
      </MetricCard>
    )
  }

  return (
    <MetricCard title="Article Volume">
      <ChartContainer>
        <BarChart data={points} margin={CHART_MARGIN}>
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
          />
          <YAxis hide allowDecimals={false} />
          <Tooltip
            content={<VolumeTooltip />}
            cursor={{ fill: CHART_CURSOR }}
          />
          <Bar
            dataKey="article_count"
            fill="#34d399"
            radius={[3, 3, 0, 0]}
            activeBar={{ fill: '#6ee7b7' }}
          />
        </BarChart>
      </ChartContainer>
    </MetricCard>
  )
}
