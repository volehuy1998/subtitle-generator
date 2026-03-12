
import { useUIStore } from '@/store/uiStore'
import type { HealthStatus } from '@/api/types'

function HealthDot({ status }: { status: HealthStatus['status'] | null }) {
  if (status === 'ok' || status === 'healthy') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-success)' }}
    />
  )
  if (status === 'degraded' || status === 'warning') return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: 'var(--color-warning)' }}
    />
  )
  if (status === 'error' || status === 'critical') return (
    <span
      className="inline-block w-2 h-2 rounded-full animate-pulse"
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
  const { healthPanelOpen, setHealthPanelOpen, health } = useUIStore()


  const isOk = health?.status === 'ok' || health?.status === 'healthy'
  const isWarn = health?.status === 'degraded' || health?.status === 'warning'
  const isCrit = health?.status === 'error' || health?.status === 'critical'

  const statusLabel =
    health === null ? 'Connecting' :
    isOk ? 'Healthy' :
    isWarn ? 'Degraded' :
    isCrit ? 'Error' :
    'Unknown'

  const labelColor =
    isOk ? 'var(--color-success)' :
    isWarn ? 'var(--color-warning)' :
    isCrit ? 'var(--color-danger)' :
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
        <svg width="22" height="22" viewBox="0 0 48 46" fill="none" aria-hidden="true">
          <path d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z" fill="#863bff"/>
        </svg>
        <span
          className="font-semibold tracking-tight"
          style={{ fontSize: '15px', color: 'var(--color-text)' }}
        >
          SubForge
        </span>
      </div>

      {/* GPU/CPU badge */}
      {health !== null && (
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md mr-2"
          style={{
            background: health.gpu_available ? 'var(--color-success-light)' : 'rgba(245,158,11,0.12)',
            border: `1px solid ${health.gpu_available ? 'var(--color-success)' : '#F59E0B'}`,
          }}
          title={health.gpu_available ? (health.gpu_name ?? 'GPU acceleration active') : 'No GPU detected — running on CPU only (slower)'}
        >
          {health.gpu_available ? (
            <>
              <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <rect x="1" y="3" width="10" height="6" rx="1.5"
                  stroke="var(--color-success)" strokeWidth="1.2" fill="none" />
                <path d="M4 3V1.5M8 3V1.5M4 9v1.5M8 9v1.5"
                  stroke="var(--color-success)" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
              <span className="text-xs font-semibold" style={{ color: 'var(--color-success)' }}>GPU</span>
            </>
          ) : (
            <>
              <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <path d="M6 1.5L11 10.5H1L6 1.5Z" stroke="#F59E0B" strokeWidth="1.2" strokeLinejoin="round" />
                <path d="M6 5v2.5" stroke="#F59E0B" strokeWidth="1.2" strokeLinecap="round" />
                <circle cx="6" cy="9" r="0.5" fill="#F59E0B" />
              </svg>
              <span className="text-xs font-semibold" style={{ color: '#F59E0B' }}>No GPU</span>
            </>
          )}
        </div>
      )}

      {/* Health indicator */}
      <button
        type="button"
        data-health-toggle
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
