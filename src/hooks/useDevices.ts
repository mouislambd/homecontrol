import { fetchDevices } from '../api/devices'
import { useFetch } from './useFetch'

export function useDevices(reloadKey?: unknown) {
  return useFetch(fetchDevices, reloadKey)
}
