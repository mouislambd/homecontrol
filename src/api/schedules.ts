import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type { Schedule, SchedulePayload } from '../types'

export async function fetchSchedules(): Promise<Schedule[]> {
  const payload = await apiFetch<{ schedules: Schedule[] }>(API_ENDPOINTS.schedules)
  return payload.schedules
}

export async function createSchedule(payload: SchedulePayload): Promise<Schedule> {
  return apiFetch<Schedule>(API_ENDPOINTS.schedules, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateSchedule(
  id: string,
  payload: Partial<SchedulePayload>,
): Promise<Schedule> {
  return apiFetch<Schedule>(API_ENDPOINTS.schedule(id), {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function toggleSchedule(id: string): Promise<Schedule> {
  return apiFetch<Schedule>(API_ENDPOINTS.scheduleToggle(id), { method: 'POST' })
}

export async function deleteSchedule(id: string): Promise<void> {
  await apiFetch<null>(API_ENDPOINTS.schedule(id), { method: 'DELETE' })
}

export async function runSchedulesNow(): Promise<number> {
  const payload = await apiFetch<{ fired: number }>(API_ENDPOINTS.schedulesRunNow, {
    method: 'POST',
  })
  return payload.fired
}
