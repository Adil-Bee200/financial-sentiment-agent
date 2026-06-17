import type { ReactNode } from 'react'
import { ResponsiveContainer } from 'recharts'

interface ChartContainerProps {
  children: ReactNode
}

export function ChartContainer({ children }: ChartContainerProps) {
  return (
    <div className="h-full min-h-[140px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  )
}
