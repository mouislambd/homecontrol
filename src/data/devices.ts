import { deviceTypes } from '../config/devices'
import type { DeviceAccent } from '../types'

export interface DeviceMeta {
  description: string
  accent: DeviceAccent
}

export const deviceMeta: Record<string, DeviceMeta> = {
  light: { description: deviceTypes.light.description, accent: 'light' },
  fan: { description: deviceTypes.fan.description, accent: 'fan' },
  ac: { description: deviceTypes.ac.description, accent: 'ac' },
}
