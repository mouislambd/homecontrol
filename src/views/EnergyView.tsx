import { fetchEnergy, fetchEnergyLogs, fetchEnergyStats } from '../api/energy'
import { StatePanel } from '../components/StatePanel'
import { SummaryCard } from '../components/SummaryCard'
import { LayersIcon, PowerIcon } from '../components/icons'
import { useFetch } from '../hooks/useFetch'

interface EnergyViewProps {
  revision: number
}

export function EnergyView({ revision }: EnergyViewProps) {
  const { data, loading, error, reload } = useFetch(fetchEnergy, revision)
  const logsState = useFetch(() => fetchEnergyLogs(null, 25), revision)
  const statsState = useFetch(fetchEnergyStats, revision)
  const stats = statsState.data
  const devices = data?.devices ?? []
  const logs = logsState.data ?? []
  const total = data?.total_wh ?? 0
  const max = Math.max(...devices.map((device) => device.energy_wh), 0.0001)

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-white">
            Energy consumption
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Estimated watt-hours derived from rated power and on-time — no physical
            energy meter is attached.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void reload()}
          className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5"
        >
          Refresh
        </button>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Total consumed"
          value={Number(total.toFixed(2))}
          icon={<PowerIcon className="h-5 w-5" />}
          tint="bg-emerald-400/10 text-emerald-300 ring-emerald-300/20"
          caption="Watt-hours this session"
        />
        <SummaryCard
          label="Metering devices"
          value={devices.length}
          icon={<LayersIcon className="h-5 w-5" />}
          tint="bg-indigo-400/10 text-indigo-300 ring-indigo-300/20"
          caption="Reporting energy usage"
        />
        <SummaryCard
          label="Estimated intervals"
          value={stats?.interval_count ?? 0}
          icon={<LayersIcon className="h-5 w-5" />}
          tint="bg-cyan-400/10 text-cyan-300 ring-cyan-300/20"
          caption="Logged on/off periods"
        />
        <SummaryCard
          label="Average interval"
          value={Number((stats?.average_interval_wh ?? 0).toFixed(2))}
          icon={<PowerIcon className="h-5 w-5" />}
          tint="bg-amber-400/10 text-amber-300 ring-amber-300/20"
          caption="Wh per estimated interval"
        />
      </div>

      <div className="mt-6">
        <StatePanel
          loading={loading}
          error={error}
          empty={devices.length === 0}
          emptyLabel="No energy readings available."
          onRetry={() => void reload()}
        >
          <div className="space-y-4 rounded-3xl border border-white/[0.07] bg-slate-900/40 p-6 backdrop-blur-xl">
            {devices.map((device) => (
              <div key={device.device_id}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-200">{device.name}</span>
                  <span className="font-medium text-white">
                    {device.energy_wh.toFixed(2)} Wh
                  </span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-cyan-400 to-indigo-400 transition-all duration-500"
                    style={{ width: `${(device.energy_wh / max) * 100}%` }}
                  />
                </div>
                <p className="mt-1 text-[11px] text-slate-500">
                  {device.wattage} W rated power
                </p>
              </div>
            ))}
          </div>
        </StatePanel>
      </div>

      <div className="mt-8">
        <h3 className="mb-4 text-sm font-semibold text-white">Recent estimated intervals</h3>
        <StatePanel
          loading={logsState.loading}
          error={logsState.error}
          empty={logs.length === 0}
          emptyLabel="No intervals recorded yet."
          onRetry={() => void logsState.reload()}
        >
          <div className="overflow-hidden rounded-3xl border border-white/[0.07] bg-slate-900/40 backdrop-blur-xl">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 px-5 py-3 text-sm last:border-0"
              >
                <span className="text-slate-200">{log.device_id}</span>
                <span className="text-xs text-slate-500">
                  {new Date(log.started_at).toLocaleString()} · {log.duration_seconds.toFixed(1)} s
                </span>
                <span className="font-medium text-white">
                  {log.estimated_energy_wh.toFixed(4)} Wh
                </span>
                <span className="rounded-full bg-indigo-400/10 px-2.5 py-1 text-[11px] text-indigo-200">
                  {log.measurement_source}
                </span>
              </div>
            ))}
          </div>
        </StatePanel>
      </div>
    </section>
  )
}
