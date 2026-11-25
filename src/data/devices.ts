import type { Device } from '../types'

export const initialDevices: Device[] = [
  {
    id: 'light',
    name: 'Light',
    description: 'Living room lighting',
    isOn: true,
    accent: 'light',
  },
  {
    id: 'fan',
    name: 'Fan',
    description: 'Ceiling fan',
    isOn: false,
    accent: 'fan',
  },
  {
    id: 'ac',
    name: 'Air Conditioner',
    description: 'Climate control',
    isOn: true,
    accent: 'ac',
  },
]
