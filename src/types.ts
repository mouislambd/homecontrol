export type DeviceAccent = 'light' | 'fan' | 'ac'

export interface Device {
  id: string
  name: string
  description: string
  isOn: boolean
  accent: DeviceAccent
}

export interface AccentTheme {
  iconWrapper: string
  dot: string
  dotGlow: string
  statusText: string
  toggleTrack: string
  cardGlow: string
}
