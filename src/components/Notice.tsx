interface NoticeProps {
  message: string | null
  tone?: 'error' | 'success'
  onDismiss?: () => void
}

export function Notice({ message, tone = 'error', onDismiss }: NoticeProps) {
  if (!message) return null
  const classes =
    tone === 'error'
      ? 'border-rose-400/20 bg-rose-500/10 text-rose-200'
      : 'border-emerald-400/20 bg-emerald-500/10 text-emerald-200'

  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={`mb-5 flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm ${classes}`}
    >
      <span>{message}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss message"
          className="rounded-full px-2 py-0.5 text-xs transition hover:bg-white/10"
        >
          ×
        </button>
      )}
    </div>
  )
}
