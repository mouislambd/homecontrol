import {
  AirConditionerIcon,
  FanIcon,
  GenericDeviceIcon,
  LightIcon,
} from '../components/icons'
import type { IconComponent } from '../components/icons'
import type { AccentTheme, DeviceAccent, DeviceTypeKey } from '../types'

export interface DeviceTypeConfig {
  type: DeviceTypeKey
  label: string
  description: string
  icon: IconComponent
  theme: AccentTheme
  defaultWattage: number
  supportsTemperature: boolean
  capabilityHint: string
}

const neutralTheme: AccentTheme = {
  iconWrapper: 'bg-slate-400/10 text-slate-300 ring-slate-300/20',
  dot: 'bg-slate-300',
  dotGlow: 'shadow-[0_0_10px_2px_rgba(148,163,184,0.4)]',
  statusText: 'text-slate-200',
  toggleTrack: 'from-slate-400 to-slate-500',
  cardGlow: 'bg-slate-500/10',
}

export const deviceTypes: Record<DeviceTypeKey, DeviceTypeConfig> = {
  light: {
    type: 'light',
    label: 'Light',
    description: 'Lighting device',
    icon: LightIcon,
    theme: {
      iconWrapper: 'bg-amber-400/10 text-amber-300 ring-amber-300/20',
      dot: 'bg-amber-300',
      dotGlow: 'shadow-[0_0_10px_2px_rgba(252,211,77,0.55)]',
      statusText: 'text-amber-200',
      toggleTrack: 'from-amber-400 to-orange-400',
      cardGlow: 'bg-amber-500/20',
    },
    defaultWattage: 60,
    supportsTemperature: false,
    capabilityHint: 'On/off control · rated power',
  },
  fan: {
    type: 'fan',
    label: 'Fan',
    description: 'Ceiling fan',
    icon: FanIcon,
    theme: {
      iconWrapper: 'bg-cyan-400/10 text-cyan-300 ring-cyan-300/20',
      dot: 'bg-cyan-300',
      dotGlow: 'shadow-[0_0_10px_2px_rgba(103,232,249,0.55)]',
      statusText: 'text-cyan-200',
      toggleTrack: 'from-cyan-400 to-sky-500',
      cardGlow: 'bg-cyan-500/20',
    },
    defaultWattage: 75,
    supportsTemperature: false,
    capabilityHint: 'On/off control · rated power',
  },
  ac: {
    type: 'ac',
    label: 'Air Conditioner',
    description: 'Climate control',
    icon: AirConditionerIcon,
    theme: {
      iconWrapper: 'bg-violet-400/10 text-violet-300 ring-violet-300/20',
      dot: 'bg-violet-300',
      dotGlow: 'shadow-[0_0_10px_2px_rgba(196,181,253,0.55)]',
      statusText: 'text-violet-200',
      toggleTrack: 'from-violet-400 to-fuchsia-500',
      cardGlow: 'bg-violet-500/20',
    },
    defaultWattage: 1200,
    supportsTemperature: true,
    capabilityHint: 'On/off control · simulated temperature input',
  },
  generic: {
    type: 'generic',
    label: 'Unknown device',
    description: 'Unsupported device type',
    icon: GenericDeviceIcon,
    theme: neutralTheme,
    defaultWattage: 0,
    supportsTemperature: false,
    capabilityHint: 'On/off control',
  },
}

export const deviceTypeOptions: readonly DeviceAccent[] = ['light', 'fan', 'ac']

export function getDeviceType(value: string | null | undefined): DeviceTypeConfig {
  if (value === 'light' || value === 'fan' || value === 'ac') return deviceTypes[value]
  return deviceTypes.generic
}
