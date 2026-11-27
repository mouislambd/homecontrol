import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type { AppNotification } from '../types'

export interface NotificationInbox {
  notifications: AppNotification[]
  unread_count: number
}

export async function fetchNotifications(): Promise<NotificationInbox> {
  return apiFetch<NotificationInbox>(API_ENDPOINTS.notifications)
}

export async function markNotificationRead(id: string): Promise<AppNotification> {
  return apiFetch<AppNotification>(API_ENDPOINTS.notificationRead(id), {
    method: 'POST',
  })
}

export async function deleteNotification(id: string): Promise<void> {
  await apiFetch<null>(API_ENDPOINTS.notification(id), { method: 'DELETE' })
}

export async function clearNotifications(): Promise<void> {
  await apiFetch<null>(API_ENDPOINTS.notifications, { method: 'DELETE' })
}
