import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type {
  ApiDevice,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceUpdatePayload,
} from '../types'

export async function fetchDevices(): Promise<ApiDevice[]> {
  const payload = await apiFetch<{ devices: ApiDevice[] }>(API_ENDPOINTS.devices)
  return payload.devices
}

export async function fetchDeviceStatus(deviceId: string): Promise<DeviceDetail> {
  return apiFetch<DeviceDetail>(API_ENDPOINTS.deviceStatus(deviceId))
}

export async function setDevicePower(
  id: string,
  on: boolean,
): Promise<ApiDevice> {
  return apiFetch<ApiDevice>(API_ENDPOINTS.devicePower(id, on), { method: 'POST' })
}

export async function setDeviceConnectivity(
  id: string,
  online: boolean,
): Promise<DeviceDetail> {
  return apiFetch<DeviceDetail>(API_ENDPOINTS.deviceConnectivity(id, online), {
    method: 'POST',
  })
}

export async function createDevice(payload: DeviceCreatePayload): Promise<DeviceDetail> {
  return apiFetch<DeviceDetail>(API_ENDPOINTS.devices, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateDevice(
  id: string,
  payload: DeviceUpdatePayload,
): Promise<DeviceDetail> {
  return apiFetch<DeviceDetail>(API_ENDPOINTS.device(id), {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deleteDevice(id: string): Promise<void> {
  await apiFetch<null>(API_ENDPOINTS.device(id), { method: 'DELETE' })
}

export async function setDeviceTemperature(
  id: string,
  value: number,
): Promise<DeviceDetail> {
  return apiFetch<DeviceDetail>(API_ENDPOINTS.deviceTemperature(id), {
    method: 'PUT',
    body: JSON.stringify({ value }),
  })
}

export async function assignDeviceRoom(
  id: string,
  roomId: string | null,
): Promise<DeviceDetail> {
  return apiFetch<DeviceDetail>(API_ENDPOINTS.deviceRoom(id), {
    method: 'PUT',
    body: JSON.stringify({ room_id: roomId }),
  })
}
