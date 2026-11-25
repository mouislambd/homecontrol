import { CheckCircleIcon, LayersIcon, PowerIcon } from './icons'
import { SummaryCard } from './SummaryCard'

interface SummarySectionProps {
  total: number
  active: number
  inactive: number
}

export function SummarySection({ total, active, inactive }: SummarySectionProps) {
  const activePercent = total === 0 ? 0 : Math.round((active / total) * 100)

  return (
    <section className="mt-12 sm:mt-14">
      <div className="mb-5 flex items-center gap-4">
        <h2 className="text-xl font-semibold tracking-tight text-white">Overview</h2>
        <div className="h-px flex-1 bg-gradient-to-r from-white/10 to-transparent" />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <SummaryCard
          label="Total Devices"
          value={total}
          icon={<LayersIcon className="h-5 w-5" />}
          tint="bg-indigo-400/10 text-indigo-300 ring-indigo-300/20"
          caption="Connected to your home"
        />
        <SummaryCard
          label="Active Devices"
          value={active}
          icon={<CheckCircleIcon className="h-5 w-5" />}
          tint="bg-emerald-400/10 text-emerald-300 ring-emerald-300/20"
          caption="Currently switched on"
        />
        <SummaryCard
          label="Inactive Devices"
          value={inactive}
          icon={<PowerIcon className="h-5 w-5" />}
          tint="bg-slate-400/10 text-slate-300 ring-slate-300/20"
          caption="Currently switched off"
        />
      </div>

      <div className="mt-4 rounded-2xl border border-white/[0.07] bg-slate-900/40 p-5 backdrop-blur-xl">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Home activity</span>
          <span className="font-semibold text-white">{activePercent}% active</span>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/5">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 transition-all duration-500"
            style={{ width: `${activePercent}%` }}
          />
        </div>
      </div>
    </section>
  )
}
