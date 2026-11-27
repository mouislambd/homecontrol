import type { ReactNode } from 'react'

export const inputClass =
  'w-full rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-indigo-400/50 focus:ring-2 focus:ring-indigo-400/20'

export const labelClass =
  'mb-1.5 block text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500'

interface FieldProps {
  label: string
  children: ReactNode
}

export function Field({ label, children }: FieldProps) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      {children}
    </label>
  )
}
