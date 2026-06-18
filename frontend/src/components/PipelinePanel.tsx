import type { Alert, HealthStatus, PipelineStatus } from '../api/types'
import { formatCurrency, formatDateTime } from '../lib/format'
import { AlertsList } from './AlertsList'
import { Card, SectionTitle } from './ui'

interface PipelinePanelProps {
  status: PipelineStatus | null
  health: HealthStatus | null
  alerts: Alert[]
  loading?: boolean
}

function StatRow({
  label,
  value,
  accent,
}: {
  label: string
  value: string
  accent?: 'green' | 'red' | 'amber' | 'neutral'
}) {
  const valueColor =
    accent === 'green'
      ? 'text-emerald-400'
      : accent === 'red'
        ? 'text-red-400'
        : accent === 'amber'
          ? 'text-amber-400'
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

function formatRunStatus(status: PipelineStatus['status']): string {
  switch (status) {
    case 'completed':
      return 'Completed'
    case 'running':
      return 'Running'
    case 'error':
      return 'Error'
    case 'no_runs':
      return 'No runs yet'
    default:
      return status
  }
}

function statusAccent(
  status: PipelineStatus['status'],
): 'green' | 'red' | 'amber' | 'neutral' {
  switch (status) {
    case 'completed':
      return 'green'
    case 'running':
      return 'amber'
    case 'error':
      return 'red'
    default:
      return 'neutral'
  }
}

function HealthIndicator({ health }: { health: HealthStatus | null }) {
  const ok = health?.status === 'ok' && health?.database === 'connected'
  return (
    <div className="mt-2 flex items-center gap-2">
      <span
        className={`h-2 w-2 rounded-full ${ok ? 'bg-emerald-400' : 'bg-red-400'}`}
      />
      <span className="text-[10px] text-zinc-600">
        API {ok ? 'connected' : 'unavailable'}
        {health?.database ? ` · DB ${health.database}` : ''}
      </span>
    </div>
  )
}

export function PipelinePanel({
  status,
  health,
  alerts,
  loading = false,
}: PipelinePanelProps) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-l border-white/[0.08] bg-[#0d1117]">
      <div className="border-b border-white/[0.08] px-4 py-5">
        <SectionTitle>Pipeline Status</SectionTitle>
        <p className="mt-1 text-xs text-zinc-600">Daily cron · 21:00 UTC</p>
        <HealthIndicator health={health} />
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!status ? (
          <Card className="p-4">
            <p className="text-sm text-zinc-500">
              {loading ? 'Waiting for API…' : 'Loading status…'}
            </p>
          </Card>
        ) : (
          <Card className="divide-y divide-white/[0.06] px-4">
            <StatRow
              label="Run status"
              value={formatRunStatus(status.status)}
              accent={statusAccent(status.status)}
            />
            <StatRow
              label="Last run"
              value={formatDateTime(status.last_run_at)}
            />
            <StatRow
              label="Articles fetched"
              value={status.articles_fetched.toLocaleString()}
            />
            <StatRow
              label="Articles analyzed"
              value={status.articles_analyzed.toLocaleString()}
              accent="green"
            />
            <StatRow
              label="LLM cost (obs.)"
              value={formatCurrency(status.estimated_llm_cost)}
            />
            <StatRow
              label="Alerts triggered"
              value={String(status.alerts_triggered)}
              accent={status.alerts_triggered > 0 ? 'red' : 'neutral'}
            />
          </Card>
        )}

        {status?.status === 'no_runs' && (
          <p className="mt-4 px-1 text-[10px] leading-relaxed text-zinc-600">
            No pipeline runs recorded yet. Metrics will appear after the first
            cron execution.
          </p>
        )}

        <AlertsList alerts={alerts} />
      </div>
    </aside>
  )
}
