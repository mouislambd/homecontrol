import type { ViewId } from '../types'

export interface TabItem {
  id: ViewId
  label: string
}

interface TabsProps {
  tabs: TabItem[]
  active: ViewId
  onChange: (id: ViewId) => void
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Dashboard sections"
      className="mt-8 flex gap-2 overflow-x-auto rounded-2xl border border-white/[0.07] bg-slate-900/40 p-2 backdrop-blur-xl"
    >
      {tabs.map((tab) => {
        const selected = tab.id === active
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(tab.id)}
            className={`shrink-0 rounded-xl px-4 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300 ${
              selected
                ? 'bg-indigo-500/20 text-white ring-1 ring-indigo-300/30'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
