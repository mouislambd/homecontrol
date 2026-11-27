import { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { Tabs } from './components/Tabs'
import type { TabItem } from './components/Tabs'
import { WS_URL } from './config/api'
import type { ViewId } from './types'
import { ActivityView } from './views/ActivityView'
import { DevicesView } from './views/DevicesView'
import { EnergyView } from './views/EnergyView'
import { NotificationsView } from './views/NotificationsView'
import { RoomsView } from './views/RoomsView'
import { RulesView } from './views/RulesView'
import { SchedulesView } from './views/SchedulesView'

const tabs: TabItem[] = [
  { id: 'devices', label: 'Devices' },
  { id: 'rooms', label: 'Rooms' },
  { id: 'schedules', label: 'Schedules' },
  { id: 'rules', label: 'Automations' },
  { id: 'energy', label: 'Energy' },
  { id: 'activity', label: 'History' },
  { id: 'notifications', label: 'Notifications' },
]

function App() {
  const [view, setView] = useState<ViewId>('devices')
  const [revision, setRevision] = useState(0)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    let disposed = false
    let socket: WebSocket | null = null
    let timer: number | undefined

    const schedule = () => {
      if (disposed) return
      if (timer !== undefined) window.clearTimeout(timer)
      timer = window.setTimeout(connect, 3000)
    }

    const connect = () => {
      if (disposed) return
      try {
        socket = new WebSocket(WS_URL)
      } catch {
        schedule()
        return
      }
      socket.onopen = () => {
        if (!disposed) setConnected(true)
      }
      socket.onmessage = (event: MessageEvent<string>) => {
        try {
          const message: { event?: string } = JSON.parse(event.data)
          if (message.event && message.event !== 'connected') {
            setRevision((current) => current + 1)
          }
        } catch {
          return
        }
      }
      socket.onerror = () => socket?.close()
      socket.onclose = () => {
        if (disposed) return
        setConnected(false)
        schedule()
      }
    }

    connect()
    return () => {
      disposed = true
      if (timer !== undefined) window.clearTimeout(timer)
      socket?.close()
    }
  }, [])

  return (
    <div className="relative min-h-screen overflow-hidden font-sans text-slate-100">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute -right-36 top-10 h-[30rem] w-[30rem] rounded-full bg-violet-600/10 blur-[130px]" />
        <div className="absolute -bottom-48 left-1/3 h-[30rem] w-[30rem] rounded-full bg-cyan-500/10 blur-[130px]" />
      </div>

      <main className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-8 sm:px-8 sm:py-12">
        <Header />

        <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              connected ? 'animate-pulse-soft bg-emerald-300' : 'bg-slate-500'
            }`}
          />
          {connected ? 'Real-time connected' : 'Reconnecting to real-time feed…'}
        </div>

        <Tabs tabs={tabs} active={view} onChange={setView} />

        {view === 'devices' && <DevicesView revision={revision} />}
        {view === 'rooms' && <RoomsView revision={revision} />}
        {view === 'schedules' && <SchedulesView revision={revision} />}
        {view === 'rules' && <RulesView revision={revision} />}
        {view === 'energy' && <EnergyView revision={revision} />}
        {view === 'activity' && <ActivityView revision={revision} />}
        {view === 'notifications' && <NotificationsView revision={revision} />}

        <footer className="mt-auto pt-12 text-center text-xs text-slate-600">
          Smart Home Controller · Simulation dashboard
        </footer>
      </main>
    </div>
  )
}

export default App
