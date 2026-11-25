import type { AccentTheme, DeviceAccent } from './types'

export const accentThemes: Record<DeviceAccent, AccentTheme> = {
  light: {
    iconWrapper: 'bg-amber-400/10 text-amber-300 ring-amber-300/20',
    dot: 'bg-amber-300',
    dotGlow: 'shadow-[0_0_10px_2px_rgba(252,211,77,0.55)]',
    statusText: 'text-amber-200',
    toggleTrack: 'from-amber-400 to-orange-400',
    cardGlow: 'bg-amber-500/20',
  },
  fan: {
    iconWrapper: 'bg-cyan-400/10 text-cyan-300 ring-cyan-300/20',
    dot: 'bg-cyan-300',
    dotGlow: 'shadow-[0_0_10px_2px_rgba(103,232,249,0.55)]',
    statusText: 'text-cyan-200',
    toggleTrack: 'from-cyan-400 to-sky-500',
    cardGlow: 'bg-cyan-500/20',
  },
  ac: {
    iconWrapper: 'bg-violet-400/10 text-violet-300 ring-violet-300/20',
    dot: 'bg-violet-300',
    dotGlow: 'shadow-[0_0_10px_2px_rgba(196,181,253,0.55)]',
    statusText: 'text-violet-200',
    toggleTrack: 'from-violet-400 to-fuchsia-500',
    cardGlow: 'bg-violet-500/20',
  },
}
