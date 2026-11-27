const configuredUrl = import.meta.env.VITE_API_BASE_URL

if (typeof configuredUrl !== 'string' || configuredUrl.trim() === '') {
  throw new Error('VITE_API_BASE_URL is not set. Add it to .env.local or your hosting environment.')
}

export const API_BASE_URL = configuredUrl.trim().replace(/\/+$/, '')

const resource = (path: string): string => `${API_BASE_URL}${path}`

export const API_ENDPOINTS = {
  health: resource('/'),
  devices: resource('/devices'),
  devicePower: (deviceId: string, on: boolean): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}/${on ? 'on' : 'off'}`),
  deviceStatus: (deviceId: string): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}/status`),
  deviceConnectivity: (deviceId: string, online: boolean): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}/${online ? 'online' : 'offline'}`),
  deviceRoom: (deviceId: string): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}/room`),
  deviceTemperature: (deviceId: string): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}/temperature`),
  device: (deviceId: string): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}`),
  deviceActivity: (deviceId: string, limit = 100): string =>
    resource(`/devices/${encodeURIComponent(deviceId)}/activity?limit=${limit}`),

  rooms: resource('/rooms'),
  room: (roomId: string): string => resource(`/rooms/${encodeURIComponent(roomId)}`),
  roomDevices: (roomId: string): string =>
    resource(`/rooms/${encodeURIComponent(roomId)}/devices`),

  schedules: resource('/schedules'),
  schedule: (scheduleId: string): string =>
    resource(`/schedules/${encodeURIComponent(scheduleId)}`),
  scheduleToggle: (scheduleId: string): string =>
    resource(`/schedules/${encodeURIComponent(scheduleId)}/toggle`),
  schedulesRunNow: resource('/schedules/run-now'),

  rules: resource('/rules'),
  rule: (ruleId: string): string => resource(`/rules/${encodeURIComponent(ruleId)}`),

  energy: resource('/energy'),
  energyStats: resource('/energy/stats'),
  energyLogs: (deviceId: string | null, limit = 100): string => {
    const query = new URLSearchParams({ limit: String(limit) })
    if (deviceId) query.set('device_id', deviceId)
    return resource(`/energy/logs?${query.toString()}`)
  },
  energyDevice: (deviceId: string): string =>
    resource(`/energy/${encodeURIComponent(deviceId)}`),

  activity: (
    deviceId: string | null,
    limit = 100,
    source: string | null = null,
  ): string => {
    const query = new URLSearchParams({ limit: String(limit) })
    if (deviceId) query.set('device_id', deviceId)
    if (source) query.set('source', source)
    return resource(`/activity?${query.toString()}`)
  },

  notifications: resource('/notifications'),
  notificationRead: (notificationId: string): string =>
    resource(`/notifications/${encodeURIComponent(notificationId)}/read`),
  notification: (notificationId: string): string =>
    resource(`/notifications/${encodeURIComponent(notificationId)}`),
}

export const WS_URL = `${API_BASE_URL.replace(/^http/, 'ws')}/ws`
