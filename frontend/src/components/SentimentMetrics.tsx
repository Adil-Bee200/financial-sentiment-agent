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
    <div className="mt-6 flex w-full flex-col gap-4">
      <div className="mx-auto w-full max-w-sm">
        <MomentumIndicator momentum={momentum} />
      </div>

      <div className="grid w-full grid-cols-1 items-stretch gap-4 md:grid-cols-2">
        <SentimentTrendChart data={history} />
        <ArticleVolumeChart data={history} />
      </div>
    </div>
  )
}
