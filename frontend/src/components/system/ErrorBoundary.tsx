import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean; error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-danger)' }}>
          <h2>Something went wrong</h2>
          <p style={{ color: 'var(--color-text-2)', fontSize: '14px' }}>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()} style={{ marginTop: '1rem', padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--color-border)', cursor: 'pointer', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
