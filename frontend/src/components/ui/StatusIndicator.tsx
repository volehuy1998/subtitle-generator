/**
 * StatusIndicator — colored dot with optional label and pulse animation.
 * Pure presentational, no state or side effects.
 * — Pixel (Sr. Frontend), Sprint L26
 */

type Status = 'online' | 'offline' | 'warning' | 'loading' | 'idle'

interface StatusIndicatorProps {
  status: Status
  label?: string
  size?: 'sm' | 'md'
  pulse?: boolean
}

const statusColors: Record<Status, string> = {
  online: 'var(--color-success)',
  offline: 'var(--color-danger)',
  warning: 'var(--color-warning)',
  loading: 'var(--color-primary)',
  idle: 'var(--color-text-3)',
}

const defaultPulse: Record<Status, boolean> = {
  online: true,
  offline: false,
  warning: false,
  loading: true,
  idle: false,
}

const dotSizes: Record<'sm' | 'md', number> = {
  sm: 6,
  md: 8,
}

export function StatusIndicator({
  status,
  label,
  size = 'md',
  pulse,
}: StatusIndicatorProps) {
  const color = statusColors[status]
  const shouldPulse = pulse ?? defaultPulse[status]
  const dotSize = dotSizes[size]

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: label ? '6px' : undefined,
      }}
    >
      <span
        style={{
          position: 'relative',
          width: `${dotSize}px`,
          height: `${dotSize}px`,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            backgroundColor: color,
          }}
        />
        {shouldPulse && (
          <span
            className="animate-ping"
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              backgroundColor: color,
              opacity: 0.75,
            }}
          />
        )}
      </span>
      {label && (
        <span
          style={{
            fontSize: size === 'sm' ? '12px' : '13px',
            color: 'var(--color-text-2)',
            lineHeight: 1.4,
          }}
        >
          {label}
        </span>
      )}
    </span>
  )
}
