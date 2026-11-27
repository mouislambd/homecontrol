import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type { ActivityEvent } from '../types'

export async function fetchActivity(
  deviceId: string | null,
  limit = 100,
  source: string | null = null,
): Promise<ActivityEvent[]> {
  const payload = await apiFetch<{ activity: ActivityEvent[] }>(
    API_ENDPOINTS.activity(deviceId, limit, source),
  )
  return payload.activity
}

export async function fetchDeviceActivity(
  deviceId: string,
  limit = 100,
): Promise<ActivityEvent[]> {
  const payload = await apiFetch<{ activity: ActivityEvent[] }>(
    API_ENDPOINTS.deviceActivity(deviceId, limit),
  )
  return payload.activity
}
