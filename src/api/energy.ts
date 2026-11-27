import { apiFetch } from './client'
import { API_ENDPOINTS } from '../config/api'
import type {
  EnergyLog,
  EnergyReading,
  EnergyStats,
  EnergySummary,
} from '../types'

export async function fetchEnergy(): Promise<EnergySummary> {
  return apiFetch<EnergySummary>(API_ENDPOINTS.energy)
}

export async function fetchDeviceEnergy(deviceId: string): Promise<EnergyReading> {
  return apiFetch<EnergyReading>(API_ENDPOINTS.energyDevice(deviceId))
}

export async function fetchEnergyStats(): Promise<EnergyStats> {
  return apiFetch<EnergyStats>(API_ENDPOINTS.energyStats)
}

export async function fetchEnergyLogs(
  deviceId: string | null,
  limit = 50,
): Promise<EnergyLog[]> {
  const payload = await apiFetch<{ logs: EnergyLog[] }>(
    API_ENDPOINTS.energyLogs(deviceId, limit),
  )
  return payload.logs
}
