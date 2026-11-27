import type { ReactNode } from 'react'

interface StatePanelProps {
  loading: boolean
  error: string | null
  empty: boolean
  emptyLabel?: string
  onRetry?: () => void
  children: ReactNode
}

const panelClass =
  'rounded-3xl border border-white/[0.07] bg-slate-900/40 p-10 text-center text-sm text-slate-400'

export function StatePanel({
  loading,
  error,
  empty,
  emptyLabel = 'Nothing here yet.',
  onRetry,
  children,
}: StatePanelProps) {
  if (error) {
    return (
      <div role="alert" className="rounded-3xl border border-rose-400/20 bg-rose-500/10 p-6 text-sm text-rose-200">
        <p>{error}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-full border border-rose-300/30 px-4 py-1.5 text-xs font-medium transition hover:bg-rose-400/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-300"
          >
            Retry
          </button>
        )}
      </div>
    )
  }

  if (loading) {
    return <div className={panelClass}>Loading…</div>
  }

  if (empty) {
    return <div className={panelClass}>{emptyLabel}</div>
  }

  return <>{children}</>
}
