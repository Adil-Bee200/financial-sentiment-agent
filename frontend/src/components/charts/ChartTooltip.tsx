import type { ReactNode } from 'react'

interface ChartTooltipBoxProps {
  title: string
  children: ReactNode
}

export function ChartTooltipBox({ title, children }: ChartTooltipBoxProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#1a2332] px-3 py-2 text-xs shadow-xl">
      <p className="font-medium text-zinc-300">{title}</p>
      <div className="mt-1 space-y-0.5">{children}</div>
    </div>
  )
}

export function ChartTooltipRow({
  label,
  value,
  valueClassName = 'text-zinc-200',
}: {
  label: string
  value: string
  valueClassName?: string
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-zinc-500">{label}</span>
      <span className={`font-mono font-medium ${valueClassName}`}>{value}</span>
    </div>
  )
}
