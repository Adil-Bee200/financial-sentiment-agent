import type { SentimentDaily } from '../api/types'
import { ArticleVolumeChart } from './ArticleVolumeChart'
import { MomentumIndicator } from './MomentumIndicator'
import { RollingSentimentIndicator } from './RollingSentimentIndicator'
import { SentimentTrendChart } from './SentimentTrendChart'

interface SentimentMetricsProps {
  history: SentimentDaily[]
  momentum: number | null | undefined
  rolling7d: number | null | undefined
}

export function SentimentMetrics({ history, momentum, rolling7d }: SentimentMetricsProps) {
  return (
    <div className="mt-6 flex w-full flex-col gap-4">
      <div className="mx-auto grid w-full max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2">
        <MomentumIndicator momentum={momentum} />
        <RollingSentimentIndicator rolling={rolling7d} />
      </div>

      <div className="grid w-full grid-cols-1 items-stretch gap-4 md:grid-cols-2">
        <SentimentTrendChart data={history} />
        <ArticleVolumeChart data={history} />
      </div>
    </div>
  )
}
