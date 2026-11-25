interface ToggleSwitchProps {
  checked: boolean
  onChange: () => void
  label: string
  activeTrack: string
}

export function ToggleSwitch({ checked, onChange, label, activeTrack }: ToggleSwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={onChange}
      className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full p-1 transition-colors duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ${
        checked ? `bg-gradient-to-r ${activeTrack}` : 'bg-slate-700'
      }`}
    >
      <span
        className={`h-5 w-5 rounded-full bg-white shadow-md transition-transform duration-300 ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  )
}
