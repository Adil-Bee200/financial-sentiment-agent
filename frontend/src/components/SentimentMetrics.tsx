import type { SentimentDaily } from '../api/types'
import { ArticleVolumeChart } from './ArticleVolumeChart'
import { MomentumIndicator } from './MomentumIndicator'
import { SentimentTrendChart } from './SentimentTrendChart'

interface SentimentMetricsProps {
  history: SentimentDaily[]
  momentum: number | null | undefined
}

export function SentimentMetrics({ history, momentum }: SentimentMetricsProps) {
  return (
    <div className="mt-6 grid w-full grid-cols-1 gap-4 sm:grid-cols-3">
      <SentimentTrendChart data={history} />
      <ArticleVolumeChart data={history} />
      <MomentumIndicator momentum={momentum} />
    </div>
  )
}
