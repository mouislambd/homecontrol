import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../api/client'
import {
  assignDeviceRoom,
  fetchDeviceStatus,
  fetchDevices,
} from '../api/devices'
import { createRoom, deleteRoom, fetchRooms, updateRoom } from '../api/rooms'
import { getDeviceType } from '../config/devices'
import { Field, inputClass } from '../components/FormFields'
import { Notice } from '../components/Notice'
import { StatePanel } from '../components/StatePanel'
import { useFetch } from '../hooks/useFetch'
import type { Room } from '../types'

interface RoomsViewProps {
  revision: number
}

export function RoomsView({ revision }: RoomsViewProps) {
  const roomsState = useFetch(fetchRooms, revision)
  const devicesState = useFetch(fetchDevices, revision)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [notice, setNotice] = useState<string | null>(null)
  const [tone, setTone] = useState<'error' | 'success'>('error')
  const [busy, setBusy] = useState(false)

  const rooms = roomsState.data ?? []
  const devices = devicesState.data ?? []

  const resetForm = () => {
    setEditingId(null)
    setName('')
    setDescription('')
  }

  const startEdit = (room: Room) => {
    setEditingId(room.id)
    setName(room.name)
    setDescription(room.description)
  }

  const runAction = async (action: () => Promise<void>) => {
    setBusy(true)
    setNotice(null)
    try {
      await action()
      await roomsState.reload()
      await devicesState.reload()
    } catch (err) {
      setTone('error')
      setNotice(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void runAction(async () => {
      if (editingId) {
        await updateRoom(editingId, { name, description })
        setTone('success')
        setNotice('Room updated.')
      } else {
        await createRoom({ name, description })
        setTone('success')
        setNotice('Room created.')
      }
      resetForm()
    })
  }

  const remove = (room: Room) =>
    void runAction(async () => {
      await deleteRoom(room.id)
      if (editingId === room.id) resetForm()
      setTone('success')
      setNotice('Room deleted.')
    })

  const assign = (deviceId: string, roomId: string) =>
    void runAction(async () => {
      await assignDeviceRoom(deviceId, roomId || null)
      setTone('success')
      setNotice('Device room updated.')
    })

  return (
    <section className="mt-10">
      <h2 className="text-2xl font-semibold tracking-tight text-white">Rooms</h2>
      <p className="mt-1 text-sm text-slate-400">
        Organize devices by room and reassign them at any time.
      </p>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <form
          onSubmit={submit}
          className="rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl"
        >
          <h3 className="mb-5 text-sm font-semibold text-white">
            {editingId ? 'Edit room' : 'Add a room'}
          </h3>
          <div className="space-y-4">
            <Field label="Name">
              <input
                className={inputClass}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. Kitchen"
                required
              />
            </Field>
            <Field label="Description">
              <input
                className={inputClass}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Optional details"
              />
            </Field>
          </div>
          <div className="mt-5 flex gap-2">
            <button
              type="submit"
              disabled={busy}
              className="rounded-full bg-indigo-500/90 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400 disabled:opacity-50"
            >
              {editingId ? 'Save changes' : 'Create room'}
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

        <div className="rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl">
          <h3 className="mb-5 text-sm font-semibold text-white">Device assignment</h3>
          <div className="space-y-3">
            {devicesState.error ? (
              <p className="text-sm text-rose-300">{devicesState.error}</p>
            ) : devicesState.loading ? (
              <p className="text-sm text-slate-400">Loading devices…</p>
            ) : devices.length === 0 ? (
              <p className="text-sm text-slate-400">No devices available.</p>
            ) : (
              devices.map((device) => (
                <DeviceRoomRow
                  key={device.id}
                  deviceId={device.id}
                  deviceName={device.name}
                  rooms={rooms}
                  disabled={busy}
                  revision={revision}
                  onAssign={assign}
                />
              ))
            )}
          </div>
        </div>
      </div>

      <Notice message={notice} tone={tone} onDismiss={() => setNotice(null)} />

      <div className="mt-6">
        <StatePanel
          loading={roomsState.loading}
          error={roomsState.error}
          empty={rooms.length === 0}
          emptyLabel="No rooms yet. Create one above."
          onRetry={() => void roomsState.reload()}
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {rooms.map((room) => (
              <div
                key={room.id}
                className="rounded-2xl border border-white/[0.07] bg-slate-900/40 p-5 backdrop-blur-xl"
              >
                <h3 className="text-lg font-semibold text-white">{room.name}</h3>
                <p className="mt-1 text-xs text-slate-500">
                  {room.description || 'No description'}
                </p>
                <p className="mt-4 text-xs text-slate-400">
                  {room.device_count} device{room.device_count === 1 ? '' : 's'}
                </p>
                <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => startEdit(room)}
                    className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/5"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(room)}
                    disabled={busy}
                    className="rounded-full border border-rose-400/20 px-3 py-1.5 text-xs text-rose-200 transition hover:bg-rose-400/10 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </StatePanel>
      </div>
    </section>
  )
}

interface DeviceRoomRowProps {
  deviceId: string
  deviceName: string
  rooms: Room[]
  disabled: boolean
  revision: number
  onAssign: (deviceId: string, roomId: string) => void
}

function DeviceRoomRow({
  deviceId,
  deviceName,
  rooms,
  disabled,
  revision,
  onAssign,
}: DeviceRoomRowProps) {
  const { data, loading } = useFetch(
    () => fetchDeviceStatus(deviceId),
    `${deviceId}:${revision}`,
  )
  const currentRoom = data?.room_id ?? ''
  const config = getDeviceType(data?.device_type)
  const Icon = config.icon

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-slate-950/40 px-3 py-2">
      <span className="flex items-center gap-2 text-sm text-slate-300">
        <Icon className="h-4 w-4 text-slate-400" />
        <span>{deviceName}</span>
        <span className="text-[11px] text-slate-500">{config.label}</span>
      </span>
      <select
        aria-label={`Room for ${deviceName}`}
        className={`${inputClass} w-40 py-1.5`}
        value={currentRoom}
        disabled={disabled || loading}
        onChange={(event) => onAssign(deviceId, event.target.value)}
      >
        <option value="">Unassigned</option>
        {rooms.map((room) => (
          <option key={room.id} value={room.id}>
            {room.name}
          </option>
        ))}
      </select>
    </div>
  )
}
