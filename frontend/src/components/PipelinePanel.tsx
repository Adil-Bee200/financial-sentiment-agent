import type { PipelineStatus } from '../api/types'
import { formatCurrency, formatDateTime } from '../lib/format'
import { Card, SectionTitle } from './ui'

interface PipelinePanelProps {
  status: PipelineStatus | null
}

function StatRow({
  label,
  value,
  accent,
}: {
  label: string
  value: string
  accent?: 'green' | 'red' | 'neutral'
}) {
  const valueColor =
    accent === 'green'
      ? 'text-emerald-400'
      : accent === 'red'
        ? 'text-red-400'
        : 'text-zinc-200'

  return (
    <div className="flex items-center justify-between py-2.5">
      <span className="text-sm text-zinc-500">{label}</span>
      <span className={`font-mono text-sm font-medium ${valueColor}`}>
        {value}
      </span>
    </div>
  )
}

export function PipelinePanel({ status }: PipelinePanelProps) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-l border-white/[0.08] bg-[#0d1117]">
      <div className="border-b border-white/[0.08] px-4 py-5">
        <SectionTitle>Pipeline Status</SectionTitle>
        <p className="mt-1 text-xs text-zinc-600">Daily cron · 21:00 UTC</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!status ? (
          <Card className="p-4">
            <p className="text-sm text-zinc-500">Loading status…</p>
          </Card>
        ) : (
          <Card className="divide-y divide-white/[0.06] px-4">
            <StatRow
              label="Last run"
              value={formatDateTime(status.lastRun)}
            />
            <StatRow
              label="Articles fetched"
              value={status.articlesFetched.toLocaleString()}
            />
            <StatRow
              label="Articles analyzed"
              value={status.articlesAnalyzed.toLocaleString()}
              accent="green"
            />
            <StatRow
              label="Est. LLM cost"
              value={formatCurrency(status.estimatedLlmCost)}
            />
            <StatRow
              label="Alerts triggered"
              value={String(status.alertsTriggered)}
              accent={status.alertsTriggered > 0 ? 'red' : 'neutral'}
            />
          </Card>
        )}

        <p className="mt-4 px-1 text-[10px] leading-relaxed text-zinc-600">
          Pipeline metrics are estimated from daily sentiment rollups and recent
          alerts. A dedicated status endpoint is not yet available.
        </p>
      </div>
    </aside>
  )
}
