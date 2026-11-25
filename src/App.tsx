import { useState } from 'react'
import { DeviceCard } from './components/DeviceCard'
import { Header } from './components/Header'
import { SummarySection } from './components/SummarySection'
import { initialDevices } from './data/devices'
import type { Device } from './types'

function App() {
  const [devices, setDevices] = useState<Device[]>(initialDevices)

  const toggleDevice = (id: string) => {
    setDevices((current) =>
      current.map((device) =>
        device.id === id ? { ...device, isOn: !device.isOn } : device,
      ),
    )
  }

  const activeCount = devices.filter((device) => device.isOn).length
  const inactiveCount = devices.length - activeCount

  return (
    <div className="relative min-h-screen overflow-hidden font-sans text-slate-100">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute -right-36 top-10 h-[30rem] w-[30rem] rounded-full bg-violet-600/10 blur-[130px]" />
        <div className="absolute -bottom-48 left-1/3 h-[30rem] w-[30rem] rounded-full bg-cyan-500/10 blur-[130px]" />
      </div>

      <main className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-8 sm:px-8 sm:py-12">
        <Header />

        <section className="mt-12 sm:mt-16">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-white">
                Your devices
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                Manage and monitor your connected devices
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
              <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-emerald-300" />
              Live
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {devices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                onToggle={() => toggleDevice(device.id)}
              />
            ))}
          </div>
        </section>

        <SummarySection
          total={devices.length}
          active={activeCount}
          inactive={inactiveCount}
        />

        <footer className="mt-auto pt-12 text-center text-xs text-slate-600">
          Smart Home Controller · Frontend preview
        </footer>
      </main>
    </div>
  )
}

export default App
