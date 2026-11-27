export type DeviceAccent = 'light' | 'fan' | 'ac'
export type DeviceTypeKey = DeviceAccent | 'generic'

export type DeviceStatus = 'ON' | 'OFF'

export interface ApiDevice {
  id: string
  name: string
  status: DeviceStatus
}

export interface Device {
  id: string
  name: string
  description: string
  isOn: boolean
  device_type: DeviceTypeKey
  wattage?: number
}

export interface AccentTheme {
  iconWrapper: string
  dot: string
  dotGlow: string
  statusText: string
  toggleTrack: string
  cardGlow: string
}

export interface DeviceDetail extends ApiDevice {
  device_type: string
  online: boolean
  room_id: string | null
  wattage: number
  energy_wh: number
  temperature_c: number | null
  temperature_source: string | null
}

export interface DeviceCreatePayload {
  id: string
  name: string
  device_type: DeviceAccent
  wattage: number
  room_id: string | null
  online: boolean
  initial_status: DeviceStatus
}

export interface DeviceUpdatePayload {
  name?: string
  wattage?: number
  room_id?: string | null
  online?: boolean
}

export interface EnergyLog {
  id: number
  device_id: string
  started_at: string
  ended_at: string
  duration_seconds: number
  wattage: number
  estimated_energy_wh: number
  measurement_source: 'estimated'
}

export interface Room {
  id: string
  name: string
  description: string
  device_count: number
}

export interface RoomPayload {
  name: string
  description: string
}

export type DayNumber = number

export interface Schedule {
  id: string
  device_id: string
  action: DeviceStatus
  time: string
  days: DayNumber[]
  enabled: boolean
  timezone: string
  last_run: string | null
}

export type SchedulePayload = Omit<Schedule, 'id' | 'last_run'>

export interface AutomationRule {
  id: string
  name: string
  trigger_device_id: string
  trigger_status: DeviceStatus
  target_device_id: string
  target_action: DeviceStatus
  enabled: boolean
  trigger_type: 'device_state' | 'temperature_above' | 'temperature_below'
  threshold_c: number | null
}

export type RulePayload = Omit<AutomationRule, 'id'>

export interface ActivityEvent {
  id: string
  device_id: string
  action: string
  previous_status: string
  status: string
  source: string
  occurred_at: string
}

export interface AppNotification {
  id: string
  message: string
  level: string
  read: boolean
  created_at: string
}

export interface EnergyReading {
  device_id: string
  name: string
  wattage: number
  energy_wh: number
}

export interface EnergySummary {
  total_wh: number
  devices: EnergyReading[]
}

export interface EnergyStats {
  total_wh: number
  interval_count: number
  average_interval_wh: number
  peak_device_id: string | null
  note: string
}

export type ViewId =
  | 'devices'
  | 'rooms'
  | 'schedules'
  | 'rules'
  | 'energy'
  | 'activity'
  | 'notifications'
