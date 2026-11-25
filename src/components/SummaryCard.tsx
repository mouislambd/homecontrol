import type { ReactNode } from 'react'

interface SummaryCardProps {
  label: string
  value: number
  icon: ReactNode
  tint: string
  caption: string
}

export function SummaryCard({ label, value, icon, tint, caption }: SummaryCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/[0.07] bg-slate-900/40 p-5 backdrop-blur-xl transition-colors hover:border-white/15">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
            {label}
          </p>
          <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
        </div>
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ring-1 ${tint}`}
        >
          {icon}
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-500">{caption}</p>
    </div>
  )
}
