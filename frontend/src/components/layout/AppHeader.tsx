import { useHealthStream } from '@/hooks/useHealthStream'
import { useUIStore } from '@/store/uiStore'

function HealthDot({ status }: { status: 'ok' | 'degraded' | 'error' | null }) {
  if (status === 'ok') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-success)' }}
    />
  )
  if (status === 'degraded') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-warning)' }}
    />
  )
  if (status === 'error') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-danger)' }}
    />
  )
  // null = loading
  return (
    <span
      className="inline-block w-2 h-2 rounded-full animate-pulse"
      style={{ background: 'var(--color-border-2)' }}
    />
  )
}

function LoadBar({ load }: { load: number | undefined }) {
  const pct = Math.min(100, Math.round((load ?? 0) * 100))
  let barColor = 'var(--color-success)'
  if (pct > 80) barColor = 'var(--color-danger)'
  else if (pct > 60) barColor = 'var(--color-warning)'

  return (
    <div
      className="w-10 h-0.5 rounded-full overflow-hidden mt-0.5"
      style={{ background: 'var(--color-border)' }}
    >
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, background: barColor }}
      />
    </div>
  )
}

export function AppHeader() {
  const health = useHealthStream()
  const { healthPanelOpen, setHealthPanelOpen } = useUIStore()

  const statusLabel =
    health === null ? 'Connecting' :
    health.status === 'ok' ? 'Healthy' :
    health.status === 'degraded' ? 'Degraded' :
    'Error'

  const labelColor =
    health?.status === 'ok' ? 'var(--color-success)' :
    health?.status === 'degraded' ? 'var(--color-warning)' :
    health?.status === 'error' ? 'var(--color-danger)' :
    'var(--color-text-3)'

  return (
    <header
      className="sticky top-0 z-40 flex items-center px-6"
      style={{
        height: '52px',
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 flex-1">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
          <rect width="22" height="22" rx="6" fill="var(--color-primary)" />
          <path
            d="M11 15.5V6.5M7 10l4-4 4 4"
            stroke="white"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span
          className="font-semibold tracking-tight"
          style={{ fontSize: '15px', color: 'var(--color-text)' }}
        >
          SubForge
        </span>
      </div>

      {/* Health indicator */}
      <button
        type="button"
        onClick={() => setHealthPanelOpen(!healthPanelOpen)}
        className="flex flex-col items-end gap-0 px-3 py-1.5 rounded-lg transition-colors"
        style={{
          background: healthPanelOpen ? 'var(--color-surface-2)' : 'transparent',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        <div className="flex items-center gap-1.5">
          <HealthDot status={health?.status ?? null} />
          <span
            className="text-xs font-medium"
            style={{ color: labelColor }}
          >
            {statusLabel}
          </span>
        </div>
        <LoadBar load={health?.load} />
      </button>
    </header>
  )
}
