import type { SentimentDaily, TrackedAsset } from '../api/types'
import {
  formatScore,
  getSentimentColor,
  getSentimentLabel,
} from '../lib/sentiment'
import { SectionTitle } from './ui'

interface SidebarProps {
  assets: TrackedAsset[]
  dailyBySymbol: Record<string, SentimentDaily | undefined>
  selectedSymbol: string | null
  onSelect: (symbol: string) => void
}

export function Sidebar({
  assets,
  dailyBySymbol,
  selectedSymbol,
  onSelect,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-56 shrink-0 flex-col border-r border-white/[0.08] bg-[#0d1117]">
      <div className="border-b border-white/[0.08] px-4 py-5">
        <p className="text-sm font-semibold text-zinc-100">Sentiment Agent</p>
        <p className="mt-0.5 text-xs text-zinc-500">Financial dashboard</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <SectionTitle>Tracked Assets</SectionTitle>
        <ul className="mt-3 space-y-1">
          {assets.map((asset) => {
            const daily = dailyBySymbol[asset.symbol]
            const score = daily?.avg_sentiment ?? null
            const isSelected = asset.symbol === selectedSymbol

            return (
              <li key={asset.ticker_id}>
                <button
                  type="button"
                  onClick={() => onSelect(asset.symbol)}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left transition-colors ${
                    isSelected
                      ? 'bg-white/[0.08] ring-1 ring-white/[0.12]'
                      : 'hover:bg-white/[0.04]'
                  }`}
                >
                  <span className="font-mono text-sm font-semibold text-zinc-100">
                    {asset.symbol}
                  </span>
                  <div className="text-right">
                    <p
                      className={`font-mono text-xs font-medium ${getSentimentColor(score)}`}
                    >
                      {formatScore(score)}
                    </p>
                    <p className="text-[10px] text-zinc-500">
                      {getSentimentLabel(score)}
                    </p>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </aside>
  )
}
