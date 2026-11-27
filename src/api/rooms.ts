import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type { Room, RoomPayload } from '../types'

export async function fetchRooms(): Promise<Room[]> {
  const payload = await apiFetch<{ rooms: Room[] }>(API_ENDPOINTS.rooms)
  return payload.rooms
}

export async function createRoom(payload: RoomPayload): Promise<Room> {
  return apiFetch<Room>(API_ENDPOINTS.rooms, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateRoom(id: string, payload: Partial<RoomPayload>): Promise<Room> {
  return apiFetch<Room>(API_ENDPOINTS.room(id), {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deleteRoom(id: string): Promise<void> {
  await apiFetch<null>(API_ENDPOINTS.room(id), { method: 'DELETE' })
}
