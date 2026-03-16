/* Icon — centralized SVG icon utility — Prism (UI/UX), Sprint L27 */

const ICONS = {
  check: (
    <path d="M4 8l3 3 5-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  ),
  x: (
    <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  ),
  warning: (
    <>
      <path d="M7 4v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="7" cy="10.5" r="0.75" fill="currentColor" />
    </>
  ),
  download: (
    <>
      <path d="M7 2v7M3.5 6.5l3.5 3.5 3.5-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </>
  ),
  upload: (
    <>
      <path d="M7 9V2M3.5 4.5L7 1l3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </>
  ),
  trash: (
    <>
      <path d="M3 4h8M5 4V3a1 1 0 011-1h2a1 1 0 011 1v1M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  play: <path d="M4 2l7 5-7 5V2z" fill="currentColor" />,
  pause: (
    <>
      <rect x="3" y="2" width="3" height="10" rx="1" fill="currentColor" />
      <rect x="8" y="2" width="3" height="10" rx="1" fill="currentColor" />
    </>
  ),
  settings: (
    <path d="M7 9a2 2 0 100-4 2 2 0 000 4z" stroke="currentColor" strokeWidth="1.2" />
  ),
  info: (
    <>
      <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" fill="none" />
      <path d="M7 5v1M7 8v2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </>
  ),
} as const

type IconName = keyof typeof ICONS

interface IconProps {
  name: IconName
  size?: number
  className?: string
  style?: React.CSSProperties
}

export function Icon({ name, size = 14, className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 14 14"
      fill="none"
      aria-hidden="true"
      className={className}
      style={style}
    >
      {ICONS[name]}
    </svg>
  )
}
