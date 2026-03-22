/**
 * ToastContainer — renders stacked toast notifications at bottom-right.
 * Max 5 visible, fade-in animation, auto-dismiss, manual dismiss via X.
 * — Pixel (Sr. Frontend), Sprint L21
 */

import { useToastStore } from '@/store/toastStore'
import type { ToastType } from '@/store/toastStore'

const TOAST_COLORS: Record<ToastType, string> = {
  success: 'var(--color-success)',
  error: 'var(--color-danger)',
  warning: 'var(--color-warning)',
  info: 'var(--color-primary)',
}

function ToastIcon({ type }: { type: ToastType }) {
  const color = TOAST_COLORS[type]

  if (type === 'success') {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
        <circle cx="9" cy="9" r="8" stroke={color} strokeWidth="1.5" fill="none" />
        <path d="M5.5 9.5l2.5 2.5 4.5-5" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }

  if (type === 'error') {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
        <circle cx="9" cy="9" r="8" stroke={color} strokeWidth="1.5" fill="none" />
        <path d="M6.5 6.5l5 5M11.5 6.5l-5 5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    )
  }

  if (type === 'warning') {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
        <path d="M9 2l7.5 14H1.5L9 2z" stroke={color} strokeWidth="1.5" strokeLinejoin="round" fill="none" />
        <path d="M9 7.5v3.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="9" cy="13.5" r="0.7" fill={color} />
      </svg>
    )
  }

  // info
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="8" stroke={color} strokeWidth="1.5" fill="none" />
      <path d="M9 8v4.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="9" cy="5.5" r="0.7" fill={color} />
    </svg>
  )
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts)
  const removeToast = useToastStore((s) => s.removeToast)

  const visible = toasts.slice(-5)

  if (visible.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        zIndex: 100,
        pointerEvents: 'none',
      }}
      aria-live="polite"
      aria-label="Notifications"
    >
      {visible.map((toast) => (
        <div
          key={toast.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            background: 'var(--color-bg)',
            border: `1px solid ${TOAST_COLORS[toast.type]}`,
            borderRadius: 'var(--radius)',
            boxShadow: 'var(--shadow-lg)',
            minWidth: '280px',
            maxWidth: '420px',
            pointerEvents: 'auto',
            animation: 'toast-fade-in 0.25s ease-out',
          }}
          role="status"
        >
          <ToastIcon type={toast.type} />
          <span
            style={{
              flex: 1,
              fontSize: '13px',
              fontWeight: 500,
              color: 'var(--color-text)',
              lineHeight: 1.4,
            }}
          >
            {toast.message}
          </span>
          <button
            type="button"
            onClick={() => removeToast(toast.id)}
            style={{
              background: 'none',
              border: 'none',
              padding: '2px',
              cursor: 'pointer',
              color: 'var(--color-text-3)',
              flexShrink: 0,
              lineHeight: 1,
            }}
            aria-label="Dismiss"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M4 4l6 6M10 4l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  )
}
