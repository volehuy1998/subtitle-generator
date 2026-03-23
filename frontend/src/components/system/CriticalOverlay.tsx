import { useUIStore } from '@/store/uiStore'

/**
 * Full-screen overlay displayed when the backend reports system_critical state.
 * Blocks all user interaction and shows the reasons + auto-check message.
 *
 * Returns null when the system is healthy (zero render overhead).
 */
export default function CriticalOverlay() {
  const healthMetrics = useUIStore((s) => s.healthMetrics)

  if (healthMetrics?.system_critical !== true) return null

  const reasons: string[] = healthMetrics.system_critical_reasons ?? []

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
      }}
    >
      <div
        style={{
          maxWidth: 480,
          width: '90%',
          padding: '2rem',
          borderRadius: '1rem',
          backgroundColor: 'var(--color-surface, #ffffff)',
          color: 'var(--color-text, #111111)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
          textAlign: 'center',
        }}
      >
        {/* Warning icon */}
        <div
          style={{
            fontSize: '3rem',
            lineHeight: 1,
            marginBottom: '0.75rem',
            color: 'var(--color-danger, #dc2626)',
          }}
          aria-hidden="true"
        >
          {'\u26A0'}
        </div>

        {/* Heading */}
        <h2
          style={{
            margin: '0 0 1rem',
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--color-danger, #dc2626)',
          }}
        >
          System Critical
        </h2>

        {/* Reasons list */}
        {reasons.length > 0 && (
          <ul
            style={{
              listStyle: 'none',
              padding: 0,
              margin: '0 0 1.25rem',
              textAlign: 'left',
            }}
          >
            {reasons.map((reason: string, i: number) => (
              <li
                key={i}
                style={{
                  padding: '0.5rem 0.75rem',
                  marginBottom: '0.5rem',
                  borderRadius: '0.5rem',
                  backgroundColor: 'var(--color-danger-light, #fef2f2)',
                  color: 'var(--color-text-secondary, #374151)',
                  fontSize: '0.875rem',
                  lineHeight: 1.5,
                }}
              >
                {reason}
              </li>
            ))}
          </ul>
        )}

        {/* Informational messages */}
        <p
          style={{
            margin: '0 0 0.5rem',
            fontSize: '0.875rem',
            color: 'var(--color-text-secondary, #374151)',
          }}
        >
          All operations are paused to protect your data.
        </p>
        <p
          style={{
            margin: 0,
            fontSize: '0.8125rem',
            color: 'var(--color-text-muted, #6b7280)',
          }}
        >
          Checking automatically...
        </p>
      </div>
    </div>
  )
}
