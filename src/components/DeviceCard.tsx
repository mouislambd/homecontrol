import { getDeviceType } from '../config/devices'
import type { Device } from '../types'
import { ToggleSwitch } from './ToggleSwitch'

interface DeviceCardProps {
  device: Device
  onToggle: () => void
  disabled?: boolean
  online?: boolean
  onConnectivity?: () => void
  temperature?: number | null
  onTemperature?: (value: number) => void
  temperatureDisabled?: boolean
}

export function DeviceCard({
  device,
  onToggle,
  disabled = false,
  online = true,
  onConnectivity,
  temperature = null,
  onTemperature,
  temperatureDisabled = false,
}: DeviceCardProps) {
  const config = getDeviceType(device.device_type)
  const { icon: Icon, theme } = config
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
          disabled={disabled}
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
        <p className="mt-1 text-xs text-slate-500">
          {config.label} · {device.description}
        </p>
      </div>

      <div className="relative mt-4 space-y-2 text-xs text-slate-500">
        <p>{config.capabilityHint}</p>
        {device.wattage !== undefined && <p>Rated power: {device.wattage} W</p>}
        {config.supportsTemperature && (
          <div className="flex flex-wrap items-center gap-2">
            <span className={temperature === null ? '' : 'text-cyan-200'}>
              Simulated temperature: {temperature === null ? 'not set' : `${temperature} °C`}
            </span>
            {onTemperature && (
              <TemperatureInput
                deviceName={device.name}
                disabled={disabled || temperatureDisabled}
                onSubmit={onTemperature}
              />
            )}
          </div>
        )}
      </div>

      <div className="relative mt-4 flex items-center justify-between text-xs">
        <span className={online ? 'text-emerald-300' : 'text-rose-300'}>
          {online ? 'Online' : 'Offline'}
        </span>
        {onConnectivity && (
          <button
            type="button"
            onClick={onConnectivity}
            disabled={disabled}
            className="rounded-full border border-white/10 px-3 py-1 text-[11px] text-slate-300 transition hover:border-indigo-300/40 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {online ? 'Disconnect' : 'Connect'}
          </button>
        )}
      </div>

      <div className="relative mt-4 flex items-center justify-between border-t border-white/5 pt-4">
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

interface TemperatureInputProps {
  deviceName: string
  disabled: boolean
  onSubmit: (value: number) => void
}

function TemperatureInput({ deviceName, disabled, onSubmit }: TemperatureInputProps) {
  return (
    <form
      className="flex items-center gap-1"
      onSubmit={(event) => {
        event.preventDefault()
        const data = new FormData(event.currentTarget)
        const value = Number(data.get('temperature'))
        if (Number.isFinite(value)) onSubmit(value)
      }}
    >
      <input
        type="number"
        name="temperature"
        step="0.1"
        aria-label={`Simulated temperature for ${deviceName}`}
        placeholder="°C"
        className="w-16 rounded-lg border border-white/10 bg-slate-950/60 px-2 py-1 text-xs text-slate-100 outline-none focus:border-cyan-300/40"
      />
      <button
        type="submit"
        disabled={disabled}
        className="rounded-full border border-cyan-400/20 px-2.5 py-1 text-[11px] text-cyan-200 transition hover:bg-cyan-400/10 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Set
      </button>
    </form>
  )
}
