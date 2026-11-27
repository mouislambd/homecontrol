import { deviceTypes } from './config/devices'
import type { AccentTheme, DeviceAccent } from './types'

export const accentThemes: Record<DeviceAccent, AccentTheme> = {
  light: deviceTypes.light.theme,
  fan: deviceTypes.fan.theme,
  ac: deviceTypes.ac.theme,
}
