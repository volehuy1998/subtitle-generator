/**
 * ErrorBoundary — catches rendering crashes and shows a friendly recovery UI.
 * React class component — hooks cannot implement error boundaries.
 *
 * — Pixel (Sr. Frontend Engineer), Task 37
 */

import { Component, type ReactNode, type ErrorInfo } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}
interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex items-center justify-center min-h-screen bg-[var(--color-bg)]">
          <div className="max-w-md w-full mx-4 p-8 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] text-center">
            <h1 className="text-xl font-semibold text-[var(--color-text)] mb-2">Something went wrong</h1>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">An unexpected error occurred. Please reload the page.</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
