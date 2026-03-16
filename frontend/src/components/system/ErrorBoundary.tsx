import { Component, type ReactNode } from 'react'

/**
 * ErrorBoundary — catches rendering crashes and shows a friendly recovery UI.
 * — Pixel (Sr. Frontend), Sprint L18
 */

interface Props { children: ReactNode }
interface State { hasError: boolean; error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: '60vh', gap: '16px',
          padding: '32px', textAlign: 'center',
        }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '50%',
            background: 'var(--color-danger-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontSize: '24px', color: 'var(--color-danger)', fontWeight: 700, lineHeight: 1 }}>!</span>
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-text)', margin: 0 }}>
            Something went wrong
          </h2>
          <p style={{ fontSize: '14px', color: 'var(--color-text-2)', maxWidth: '400px', margin: 0 }}>
            An unexpected error occurred. Please refresh the page to try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 24px', borderRadius: 'var(--radius-sm, 8px)',
              border: 'none', background: 'var(--color-primary)',
              color: 'white', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
            }}
          >
            Refresh Page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
