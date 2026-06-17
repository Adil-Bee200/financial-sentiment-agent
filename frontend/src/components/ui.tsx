import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-white/[0.08] bg-[#111827]/80 backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  )
}

interface SectionTitleProps {
  children: ReactNode
}

export function SectionTitle({ children }: SectionTitleProps) {
  return (
    <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
      {children}
    </h2>
  )
}
