import { useState } from 'react'
import { fetchActivity } from '../api/activity'
import { StatePanel } from '../components/StatePanel'
import { inputClass, labelClass } from '../components/FormFields'
import { useDevices } from '../hooks/useDevices'
import { useFetch } from '../hooks/useFetch'

interface ActivityViewProps {
  revision: number
}

export function ActivityView({ revision }: ActivityViewProps) {
  const [deviceId, setDeviceId] = useState('')
  const [limit, setLimit] = useState(50)
  const [source, setSource] = useState('')
  const devicesState = useDevices(revision)
  const activityState = useFetch(
    () => fetchActivity(deviceId || null, limit, source || null),
    `${revision}:${deviceId}:${limit}:${source}`,
  )
  const events = activityState.data ?? []
  const devices = devicesState.data ?? []

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-white">
            Device activity
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Newest first, including schedules and automations.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <label className="block">
            <span className={labelClass}>Device</span>
            <select
              className={`${inputClass} w-40 py-1.5`}
              value={deviceId}
              onChange={(event) => setDeviceId(event.target.value)}
            >
              <option value="">All devices</option>
              {devices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className={labelClass}>Limit</span>
            <select
              className={`${inputClass} w-24 py-1.5`}
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
          <label className="block">
            <span className={labelClass}>Source</span>
            <select
              className={`${inputClass} w-32 py-1.5`}
              value={source}
              onChange={(event) => setSource(event.target.value)}
            >
              <option value="">All</option>
              <option value="api">API</option>
              <option value="schedule">Schedule</option>
              <option value="automation">Automation</option>
              <option value="system">System</option>
            </select>
          </label>
        </div>
      </div>

      <div className="mt-6">
        <StatePanel
          loading={activityState.loading}
          error={activityState.error}
          empty={events.length === 0}
          emptyLabel="No activity recorded yet."
          onRetry={() => void activityState.reload()}
        >
          <div className="overflow-hidden rounded-3xl border border-white/[0.07] bg-slate-900/40 backdrop-blur-xl">
            {events.map((event) => (
              <div
                key={event.id}
                className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 px-5 py-4 last:border-0"
              >
                <div>
                  <p className="text-sm text-slate-200">
                    <span className="font-medium text-white">{event.device_id}</span>{' '}
                    {event.action}
                    {event.previous_status !== event.status &&
                      ` (from ${event.previous_status})`}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {new Date(event.occurred_at).toLocaleString()}
                  </p>
                </div>
                <span className="rounded-full bg-indigo-400/10 px-2.5 py-1 text-[11px] text-indigo-200">
                  {event.source}
                </span>
              </div>
            ))}
          </div>
        </StatePanel>
      </div>
    </section>
  )
}
