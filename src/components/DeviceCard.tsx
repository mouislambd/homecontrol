import type { Device } from '../types'
import { accentThemes } from '../theme'
import { ToggleSwitch } from './ToggleSwitch'
import { AirConditionerIcon, FanIcon, LightIcon } from './icons'

const deviceIcons = {
  light: LightIcon,
  fan: FanIcon,
  ac: AirConditionerIcon,
}

interface DeviceCardProps {
  device: Device
  onToggle: () => void
}

export function DeviceCard({ device, onToggle }: DeviceCardProps) {
  const theme = accentThemes[device.accent]
  const Icon = deviceIcons[device.accent]
  const { isOn } = device

  return (
    <article
      className={`group relative overflow-hidden rounded-3xl border p-6 shadow-[0_20px_45px_-25px_rgba(0,0,0,0.9)] transition-all duration-300 hover:-translate-y-1 ${
        isOn ? 'border-white/15 bg-slate-800/50' : 'border-white/[0.07] bg-slate-900/40'
      }`}
    >
      <div
        aria-hidden="true"
        className={`pointer-events-none absolute -right-12 -top-16 h-48 w-48 rounded-full blur-3xl transition-opacity duration-500 ${theme.cardGlow} ${
          isOn ? 'opacity-100' : 'opacity-0'
        }`}
      />

      <div className="relative flex items-start justify-between gap-4">
        <div
          className={`flex h-14 w-14 items-center justify-center rounded-2xl ring-1 transition-all duration-300 ${
            isOn ? theme.iconWrapper : 'bg-white/5 text-slate-500 ring-white/5'
          }`}
        >
          <Icon className="h-7 w-7" />
        </div>
        <ToggleSwitch
          checked={isOn}
          onChange={onToggle}
          label={`Toggle ${device.name}`}
          activeTrack={theme.toggleTrack}
        />
      </div>

      <div className="relative mt-7">
        <h3
          className={`text-lg font-semibold transition-colors duration-300 ${
            isOn ? 'text-white' : 'text-slate-400'
          }`}
        >
          {device.name}
        </h3>
        <p className="mt-1 text-xs text-slate-500">{device.description}</p>
      </div>

      <div className="relative mt-6 flex items-center justify-between border-t border-white/5 pt-4">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full transition-all duration-300 ${
              isOn ? `${theme.dot} ${theme.dotGlow}` : 'bg-slate-600'
            }`}
          />
          <span
            className={`text-sm font-semibold tracking-wide transition-colors duration-300 ${
              isOn ? theme.statusText : 'text-slate-500'
            }`}
          >
            {isOn ? 'ON' : 'OFF'}
          </span>
        </div>
        <span className="text-xs text-slate-500">{isOn ? 'Active' : 'Inactive'}</span>
      </div>
    </article>
  )
}
