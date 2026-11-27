import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../api/client'
import {
  createDevice,
  deleteDevice,
  fetchDeviceStatus,
  fetchDevices,
  setDeviceConnectivity,
  setDevicePower,
  setDeviceTemperature,
  updateDevice,
} from '../api/devices'
import { fetchRooms } from '../api/rooms'
import { deviceTypeOptions, deviceTypes, getDeviceType } from '../config/devices'
import { Field, inputClass } from '../components/FormFields'
import { DeviceCard } from '../components/DeviceCard'
import { Notice } from '../components/Notice'
import { StatePanel } from '../components/StatePanel'
import { SummarySection } from '../components/SummarySection'
import { useFetch } from '../hooks/useFetch'
import type { ApiDevice, Device, DeviceAccent, DeviceDetail } from '../types'

interface DashboardDevice extends Device {
  online: boolean
  wattage: number
  room_id: string | null
  temperature_c: number | null
}

function toDevice(device: ApiDevice, detail: DeviceDetail | undefined): DashboardDevice {
  const config = getDeviceType(detail?.device_type)
  return {
    id: device.id,
    name: device.name,
    description: config.description,
    device_type: config.type,
    isOn: device.status === 'ON',
    online: detail?.online ?? true,
    wattage: detail?.wattage ?? config.defaultWattage,
    room_id: detail?.room_id ?? null,
    temperature_c: detail?.temperature_c ?? null,
  }
}

async function loadDashboard(): Promise<DashboardDevice[]> {
  const devices = await fetchDevices()
  const details = await Promise.all(devices.map((device) => fetchDeviceStatus(device.id)))
  return devices.map((device, index) => toDevice(device, details[index]))
}

interface DevicesViewProps {
  revision: number
}

const emptyForm = {
  id: '',
  name: '',
  device_type: 'light' as DeviceAccent,
  wattage: String(deviceTypes.light.defaultWattage),
  room_id: '',
}

function withDeviceType(
  current: typeof emptyForm,
  deviceType: DeviceAccent,
): typeof emptyForm {
  const config = deviceTypes[deviceType]
  const previousLabel = deviceTypes[current.device_type].label
  return {
    ...current,
    device_type: deviceType,
    wattage: String(config.defaultWattage),
    name:
      current.name.trim() === '' || current.name === previousLabel
        ? config.label
        : current.name,
  }
}

export function DevicesView({ revision }: DevicesViewProps) {
  const { data, loading, error, reload } = useFetch(loadDashboard, revision)
  const roomsState = useFetch(fetchRooms, revision)
  const [pendingIds, setPendingIds] = useState<string[]>([])
  const [actionError, setActionError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const devices = data ?? []
  const rooms = roomsState.data ?? []
  const selectedConfig = deviceTypes[form.device_type]
  const SelectedIcon = selectedConfig.icon

  const runAction = async (id: string, action: () => Promise<void>) => {
    if (pendingIds.includes(id)) return
    setPendingIds((current) => [...current, id])
    setActionError(null)
    setSuccess(null)
    try {
      await action()
    } catch (err) {
      setActionError(errorMessage(err))
    } finally {
      setPendingIds((current) => current.filter((item) => item !== id))
    }
  }

  const toggleDevice = (device: DashboardDevice) =>
    runAction(device.id, async () => {
      await setDevicePower(device.id, !device.isOn)
      await reload()
    })

  const toggleConnectivity = (device: DashboardDevice) =>
    runAction(device.id, async () => {
      await setDeviceConnectivity(device.id, !device.online)
      await reload()
    })

  const startEdit = (device: DashboardDevice) => {
    const config = getDeviceType(device.device_type)
    const deviceType: DeviceAccent = deviceTypeOptions.includes(
      config.type as DeviceAccent,
    )
      ? (config.type as DeviceAccent)
      : 'light'
    setEditingId(device.id)
    setForm({
      id: device.id,
      name: device.name,
      device_type: deviceType,
      wattage: String(device.wattage),
      room_id: device.room_id ?? '',
    })
  }

  const resetForm = () => {
    setEditingId(null)
    setForm(emptyForm)
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const key = editingId || `form:${form.id || 'new'}`
    void runAction(key, async () => {
      if (editingId) {
        await updateDevice(editingId, {
          name: form.name,
          wattage: Number(form.wattage),
          room_id: form.room_id || null,
        })
        setSuccess('Device updated.')
      } else {
        await createDevice({
          id: form.id,
          name: form.name,
          device_type: form.device_type,
          wattage: Number(form.wattage),
          room_id: form.room_id || null,
          online: true,
          initial_status: 'OFF',
        })
        setSuccess('Device created.')
      }
      resetForm()
      await reload()
    })
  }

  const remove = (device: DashboardDevice) =>
    runAction(device.id, async () => {
      await deleteDevice(device.id)
      if (editingId === device.id) resetForm()
      setSuccess('Device deleted.')
      await reload()
    })

  const activeCount = devices.filter((device) => device.isOn).length

  return (
    <section className="mt-10">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-white">Your devices</h2>
          <p className="mt-1 text-sm text-slate-400">
            Manage and monitor your connected devices
          </p>
        </div>
        <div
          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${
            error
              ? 'border-rose-400/20 bg-rose-400/10 text-rose-200'
              : loading
                ? 'border-amber-400/20 bg-amber-400/10 text-amber-200'
                : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300'
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              error
                ? 'bg-rose-300'
                : loading
                  ? 'animate-pulse-soft bg-amber-300'
                  : 'animate-pulse-soft bg-emerald-300'
            }`}
          />
          {error ? 'Offline' : loading ? 'Connecting…' : 'Live'}
        </div>
      </div>

      <Notice message={actionError} onDismiss={() => setActionError(null)} />
      <Notice message={success} tone="success" onDismiss={() => setSuccess(null)} />

      <form
        onSubmit={submit}
        className="rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl"
      >
        <div className="mb-5 flex items-center gap-3">
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-xl ring-1 ${selectedConfig.theme.iconWrapper}`}
          >
            <SelectedIcon className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              {editingId ? `Edit ${selectedConfig.label}` : `Add ${selectedConfig.label}`}
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">{selectedConfig.capabilityHint}</p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Field label="ID">
            <input
              className={inputClass}
              value={form.id}
              disabled={editingId !== null}
              onChange={(event) => setForm({ ...form, id: event.target.value })}
              placeholder="plug-1"
              required
            />
          </Field>
          <Field label="Name">
            <input
              className={inputClass}
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder={selectedConfig.label}
              required
            />
          </Field>
          <Field label="Type">
            <select
              className={inputClass}
              value={form.device_type}
              disabled={editingId !== null}
              onChange={(event) =>
                setForm(withDeviceType(form, event.target.value as DeviceAccent))
              }
            >
              {deviceTypeOptions.map((type) => (
                <option key={type} value={type}>
                  {deviceTypes[type].label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Rated watts">
            <input
              type="number"
              min="0"
              className={inputClass}
              value={form.wattage}
              onChange={(event) => setForm({ ...form, wattage: event.target.value })}
              required
            />
          </Field>
          <Field label="Room">
            <select
              className={inputClass}
              value={form.room_id}
              onChange={(event) => setForm({ ...form, room_id: event.target.value })}
            >
              <option value="">Unassigned</option>
              {rooms.map((room) => (
                <option key={room.id} value={room.id}>
                  {room.name}
                </option>
              ))}
            </select>
          </Field>
        </div>
        {editingId && (
          <p className="mt-4 text-[11px] text-slate-500">
            Device type is fixed after creation to preserve its identity.
          </p>
        )}
        <div className="mt-5 flex gap-2">
          <button
            type="submit"
            disabled={editingId ? pendingIds.includes(editingId) : pendingIds.some((item) => item.startsWith('form:'))}
            className="rounded-full bg-indigo-500/90 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400 disabled:opacity-50"
          >
            {editingId ? 'Save changes' : 'Add device'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="mt-8">
        <StatePanel
          loading={loading}
          error={error}
          empty={devices.length === 0}
          emptyLabel="No devices found."
          onRetry={() => void reload()}
        >
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {devices.map((device) => (
              <div key={device.id} className="space-y-2">
                <DeviceCard
                  device={device}
                  onToggle={() => void toggleDevice(device)}
                  disabled={pendingIds.includes(device.id)}
                  online={device.online}
                  onConnectivity={() => void toggleConnectivity(device)}
                  temperature={device.temperature_c}
                  temperatureDisabled={pendingIds.includes(`temp:${device.id}`)}
                  onTemperature={(value) =>
                    void runAction(`temp:${device.id}`, async () => {
                      await setDeviceTemperature(device.id, value)
                      setSuccess('Simulated temperature applied.')
                      await reload()
                    })
                  }
                />
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <span className="mr-auto text-[11px] text-slate-500">
                    {getDeviceType(device.device_type).label}
                  </span>
                  <button
                    type="button"
                    onClick={() => startEdit(device)}
                    className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300 transition hover:bg-white/5"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    disabled={pendingIds.includes(device.id)}
                    onClick={() => void remove(device)}
                    className="rounded-full border border-rose-400/20 px-3 py-1 text-xs text-rose-200 transition hover:bg-rose-400/10 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </StatePanel>
      </div>

      <SummarySection
        total={devices.length}
        active={activeCount}
        inactive={devices.length - activeCount}
      />
    </section>
  )
}
