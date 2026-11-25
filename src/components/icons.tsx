import type { ReactElement, ReactNode } from 'react'

export interface IconProps {
  className?: string
}

export type IconComponent = (props: IconProps) => ReactElement

interface BaseIconProps extends IconProps {
  children: ReactNode
}

function BaseIcon({ children, className }: BaseIconProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

export function HomeIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="M3 10.2 12 3l9 7.2" />
      <path d="M5.5 9.4V20a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V9.4" />
      <path d="M9.5 21v-6h5v6" />
    </BaseIcon>
  )
}

export function LightIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="M9 18h6" />
      <path d="M10 21h4" />
      <path d="M12 3a6 6 0 0 0-3.5 10.9c.6.4.9 1.1 1 1.8l.1.3h4.8l.1-.3c.1-.7.4-1.4 1-1.8A6 6 0 0 0 12 3Z" />
    </BaseIcon>
  )
}

export function FanIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <g fill="currentColor" stroke="none" opacity="0.9">
        <ellipse cx="12" cy="7.2" rx="2.2" ry="4.1" />
        <ellipse cx="12" cy="7.2" rx="2.2" ry="4.1" transform="rotate(120 12 12)" />
        <ellipse cx="12" cy="7.2" rx="2.2" ry="4.1" transform="rotate(240 12 12)" />
      </g>
      <circle cx="12" cy="12" r="2.3" fill="#0b1224" />
    </BaseIcon>
  )
}

export function AirConditionerIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="2.5" y="4" width="19" height="8" rx="2" />
      <path d="M12 5.8v4.4M10 6.8l4 2.4M14 6.8l-4 2.4" />
      <path d="M6 16h2M11 16h2M16 16h2" />
      <path d="M6 19h3M11 19h3M16 19h2" />
    </BaseIcon>
  )
}

export function CalendarIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="3" y="5" width="18" height="16" rx="2.5" />
      <path d="M8 3v4M16 3v4M3 10h18" />
    </BaseIcon>
  )
}

export function ProfileIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" />
    </BaseIcon>
  )
}

export function LayersIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="m12 3 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5" />
      <path d="m3 16 9 5 9-5" />
    </BaseIcon>
  )
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12 2.7 2.7L16 9.5" />
    </BaseIcon>
  )
}

export function PowerIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="M12 3v9" />
      <path d="M6.3 6.3a8 8 0 1 0 11.4 0" />
    </BaseIcon>
  )
}
