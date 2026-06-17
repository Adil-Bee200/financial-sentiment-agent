import type { ReactNode } from 'react'
import { Card, SectionTitle } from '../ui'

interface MetricCardProps {
  title: string
  children: ReactNode
}

export function MetricCard({ title, children }: MetricCardProps) {
  return (
    <Card className="flex h-full min-h-[220px] flex-1 flex-col p-4">
      <SectionTitle>{title}</SectionTitle>
      <div className="mt-3 min-h-0 flex-1">{children}</div>
    </Card>
  )
}
