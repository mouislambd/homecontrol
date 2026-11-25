import { CalendarIcon, HomeIcon, ProfileIcon } from './icons'

const formattedDate = new Intl.DateTimeFormat('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
  year: 'numeric',
}).format(new Date())

export function Header() {
  return (
    <header className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-400 to-violet-600 shadow-lg shadow-indigo-950/50">
          <HomeIcon className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            Smart Home
          </h1>
          <p className="mt-0.5 text-sm text-slate-400">Control your home devices</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300 backdrop-blur sm:text-sm">
          <CalendarIcon className="h-4 w-4 shrink-0 text-indigo-300" />
          <span>{formattedDate}</span>
        </div>
        <button
          type="button"
          aria-label="User profile"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/10 bg-gradient-to-br from-slate-700 to-slate-800 text-slate-300 shadow-lg transition-colors hover:border-indigo-400/40 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
        >
          <ProfileIcon className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
