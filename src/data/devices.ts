import type { DeviceAccent } from '../types'

export interface DeviceMeta {
  description: string
  accent: DeviceAccent
}

export const deviceMeta: Record<string, DeviceMeta> = {
  light: { description: 'Living room lighting', accent: 'light' },
  fan: { description: 'Ceiling fan', accent: 'fan' },
  ac: { description: 'Climate control', accent: 'ac' },
}
