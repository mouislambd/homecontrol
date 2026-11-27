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
import { deviceMeta } from '../data/devices'
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
  device_type: string
  temperature_c: number | null
}

function toDevice(device: ApiDevice, detail: DeviceDetail | undefined): DashboardDevice {
  const meta = deviceMeta[device.id]
  return {
    id: device.id,
    name: device.name,
    description: meta?.description ?? `${device.id} device`,
    accent: meta?.accent ?? 'light',
    isOn: device.status === 'ON',
    online: detail?.online ?? true,
    wattage: detail?.wattage ?? 0,
    room_id: detail?.room_id ?? null,
    device_type: detail?.device_type ?? 'light',
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
  wattage: '25',
  room_id: '',
}

export function DevicesView({ revision }: DevicesViewProps) {
  const { data, loading, error, reload } = useFetch(loadDashboard, revision)
  const roomsState = useFetch(fetchRooms, revision)
  const [pendingIds, setPendingIds] = useState<string[]>([])
  const [actionError, setActionError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [temperatureInputs, setTemperatureInputs] = useState<Record<string, string>>({})
  const devices = data ?? []
  const rooms = roomsState.data ?? []

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
    setEditingId(device.id)
    setForm({
      id: device.id,
      name: device.name,
      device_type: (device.device_type as DeviceAccent) || 'light',
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

  const applyTemperature = (device: DashboardDevice) =>
    runAction(`temp:${device.id}`, async () => {
      const value = Number(temperatureInputs[device.id] ?? '')
      if (!Number.isFinite(value)) throw new Error('Enter a valid temperature')
      await setDeviceTemperature(device.id, value)
      setSuccess('Simulated temperature applied.')
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
        <h3 className="mb-5 text-sm font-semibold text-white">
          {editingId ? 'Edit device' : 'Add a device'}
        </h3>
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
              placeholder="Smart plug"
              required
            />
          </Field>
          <Field label="Type">
            <select
              className={inputClass}
              value={form.device_type}
              onChange={(event) =>
                setForm({ ...form, device_type: event.target.value as DeviceAccent })
              }
            >
              <option value="light">Light</option>
              <option value="fan">Fan</option>
              <option value="ac">Air Conditioner</option>
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
                />
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <span className="mr-auto text-[11px] text-slate-500">
                    Simulated temp: {device.temperature_c === null ? 'none' : `${device.temperature_c} °C`}
                  </span>
                  <input
                    type="number"
                    aria-label={`Simulated temperature for ${device.name}`}
                    className={`${inputClass} w-20 py-1 text-xs`}
                    placeholder="°C"
                    value={temperatureInputs[device.id] ?? ''}
                    onChange={(event) =>
                      setTemperatureInputs({ ...temperatureInputs, [device.id]: event.target.value })
                    }
                  />
                  <button
                    type="button"
                    disabled={pendingIds.includes(`temp:${device.id}`)}
                    onClick={() => void applyTemperature(device)}
                    className="rounded-full border border-cyan-400/20 px-3 py-1 text-xs text-cyan-200 transition hover:bg-cyan-400/10 disabled:opacity-50"
                  >
                    Set
                  </button>
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
