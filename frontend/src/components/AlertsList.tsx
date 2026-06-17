import type { Alert } from '../api/types'
import { formatRelativeTime } from '../lib/format'
import { formatScore, getSentimentColor } from '../lib/sentiment'
import { Card, SectionTitle } from './ui'

interface AlertsListProps {
  alerts: Alert[]
}

export function AlertsList({ alerts }: AlertsListProps) {
  return (
    <div className="mt-4">
      <SectionTitle>Recent Alerts</SectionTitle>
      {alerts.length === 0 ? (
        <Card className="mt-3 p-3">
          <p className="text-xs text-zinc-600">No alerts yet.</p>
        </Card>
      ) : (
        <ul className="mt-3 space-y-2">
          {alerts.map((alert) => (
            <li key={alert.alert_id}>
              <Card className="p-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-mono text-xs font-semibold text-zinc-300">
                    {alert.symbol}
                  </span>
                  <span
                    className={`font-mono text-xs ${getSentimentColor(alert.sentiment_value)}`}
                  >
                    {formatScore(alert.sentiment_value)}
                  </span>
                </div>
                <p className="mt-1.5 text-xs leading-snug text-zinc-400">
                  {alert.trigger_reason}
                </p>
                <p className="mt-1.5 text-[10px] text-zinc-600">
                  {formatRelativeTime(alert.created_at)}
                </p>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
