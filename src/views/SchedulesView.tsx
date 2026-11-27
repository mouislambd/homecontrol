import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../api/client'
import { Field, inputClass } from '../components/FormFields'
import { Notice } from '../components/Notice'
import { StatePanel } from '../components/StatePanel'
import { useDevices } from '../hooks/useDevices'
import { useFetch } from '../hooks/useFetch'
import {
  createSchedule,
  deleteSchedule,
  fetchSchedules,
  runSchedulesNow,
  toggleSchedule,
  updateSchedule,
} from '../api/schedules'
import type { DeviceStatus, Schedule } from '../types'

const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

interface SchedulesViewProps {
  revision: number
}

export function SchedulesView({ revision }: SchedulesViewProps) {
  const schedulesState = useFetch(fetchSchedules, revision)
  const devicesState = useDevices(revision)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [deviceId, setDeviceId] = useState('')
  const [action, setAction] = useState<DeviceStatus>('ON')
  const [time, setTime] = useState('08:00')
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4, 5, 6])
  const [enabled, setEnabled] = useState(true)
  const [timezone, setTimezone] = useState('UTC')
  const [notice, setNotice] = useState<string | null>(null)
  const [tone, setTone] = useState<'error' | 'success'>('error')
  const [busy, setBusy] = useState(false)

  const schedules = schedulesState.data ?? []
  const devices = devicesState.data ?? []

  const selectedDeviceId = deviceId || devices[0]?.id || ''

  const resetForm = () => {
    setEditingId(null)
    setDeviceId('')
    setAction('ON')
    setTime('08:00')
    setDays([0, 1, 2, 3, 4, 5, 6])
    setEnabled(true)
    setTimezone('UTC')
  }

  const startEdit = (schedule: Schedule) => {
    setEditingId(schedule.id)
    setDeviceId(schedule.device_id)
    setAction(schedule.action)
    setTime(schedule.time)
    setDays(schedule.days)
    setEnabled(schedule.enabled)
    setTimezone(schedule.timezone)
  }

  const runAction = async (operation: () => Promise<void>) => {
    setBusy(true)
    setNotice(null)
    try {
      await operation()
      await schedulesState.reload()
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
      const payload = { device_id: selectedDeviceId, action, time, days, enabled, timezone }
      if (editingId) {
        await updateSchedule(editingId, payload)
        setTone('success')
        setNotice('Schedule updated.')
      } else {
        await createSchedule(payload)
        setTone('success')
        setNotice('Schedule created.')
      }
      resetForm()
    })
  }

  const toggleDay = (day: number) =>
    setDays((current) =>
      current.includes(day)
        ? current.filter((item) => item !== day)
        : [...current, day].sort((a, b) => a - b),
    )

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-white">Schedules</h2>
          <p className="mt-1 text-sm text-slate-400">
            Turn devices on or off automatically at a set time.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            void runAction(async () => {
              const fired = await runSchedulesNow()
              setTone('success')
              setNotice(`${fired} due schedule${fired === 1 ? '' : 's'} applied.`)
            })
          }
          className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
        >
          Run due now
        </button>
      </div>

      <Notice message={notice} tone={tone} onDismiss={() => setNotice(null)} />

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <form
          onSubmit={submit}
          className="rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl"
        >
          <h3 className="mb-5 text-sm font-semibold text-white">
            {editingId ? 'Edit schedule' : 'New schedule'}
          </h3>
          <div className="space-y-4">
            <Field label="Device">
              <select
                className={inputClass}
                value={selectedDeviceId}
                onChange={(event) => setDeviceId(event.target.value)}
                required
              >
                <option value="">Select a device</option>
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.name}
                  </option>
                ))}
              </select>
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Action">
                <select
                  className={inputClass}
                  value={action}
                  onChange={(event) => setAction(event.target.value as DeviceStatus)}
                >
                  <option value="ON">Turn ON</option>
                  <option value="OFF">Turn OFF</option>
                </select>
              </Field>
              <Field label="Time">
                <input
                  type="time"
                  className={inputClass}
                  value={time}
                  onChange={(event) => setTime(event.target.value)}
                  required
                />
              </Field>
              <Field label="Timezone">
                <select
                  className={inputClass}
                  value={timezone}
                  onChange={(event) => setTimezone(event.target.value)}
                >
                  <option value="UTC">UTC</option>
                  <option value="Europe/London">Europe/London</option>
                  <option value="America/New_York">America/New_York</option>
                  <option value="Asia/Kolkata">Asia/Kolkata</option>
                  <option value="Australia/Sydney">Australia/Sydney</option>
                </select>
              </Field>
            </div>
            <div>
              <span className="mb-2 block text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500">
                Days
              </span>
              <div className="flex flex-wrap gap-2">
                {dayLabels.map((label, day) => {
                  const selected = days.includes(day)
                  return (
                    <button
                      key={label}
                      type="button"
                      aria-pressed={selected}
                      onClick={() => toggleDay(day)}
                      className={`rounded-full border px-3 py-1 text-xs transition ${
                        selected
                          ? 'border-indigo-300/30 bg-indigo-500/20 text-white'
                          : 'border-white/10 text-slate-400 hover:bg-white/5'
                      }`}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(event) => setEnabled(event.target.checked)}
                className="accent-indigo-500"
              />
              Enabled
            </label>
          </div>
          <div className="mt-5 flex gap-2">
            <button
              type="submit"
              disabled={busy || days.length === 0}
              className="rounded-full bg-indigo-500/90 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400 disabled:opacity-50"
            >
              {editingId ? 'Save changes' : 'Create schedule'}
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
          <StatePanel
            loading={schedulesState.loading}
            error={schedulesState.error}
            empty={schedules.length === 0}
            emptyLabel="No schedules configured."
            onRetry={() => void schedulesState.reload()}
          >
            <div className="space-y-3">
              {schedules.map((schedule) => (
                <div
                  key={schedule.id}
                  className="rounded-2xl border border-white/5 bg-slate-950/40 p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-white">
                        {schedule.device_id} → {schedule.action}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {schedule.time} {schedule.timezone} ·{' '}
                        {schedule.days.map((day) => dayLabels[day]).join(', ') || 'no days'}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-1 text-[11px] ${
                        schedule.enabled
                          ? 'bg-emerald-400/10 text-emerald-300'
                          : 'bg-slate-400/10 text-slate-400'
                      }`}
                    >
                      {schedule.enabled ? 'Enabled' : 'Paused'}
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction(async () => {
                          await toggleSchedule(schedule.id)
                          setTone('success')
                          setNotice('Schedule updated.')
                        })
                      }
                      className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
                    >
                      {schedule.enabled ? 'Pause' : 'Resume'}
                    </button>
                    <button
                      type="button"
                      onClick={() => startEdit(schedule)}
                      className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/5"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction(async () => {
                          await deleteSchedule(schedule.id)
                          if (editingId === schedule.id) resetForm()
                          setTone('success')
                          setNotice('Schedule deleted.')
                        })
                      }
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
      </div>
    </section>
  )
}
