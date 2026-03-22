/**
 * Dialog — reusable modal dialog wrapper with focus trapping,
 * Escape-to-close, and overlay click-to-close.
 *
 * Created as a shared primitive for future dialogs. Existing dialogs
 * (ConfirmationDialog, CancelConfirmationDialog, EmbedConfirmationDialog)
 * are not refactored — this is for new usage going forward.
 *
 * — Pixel (Sr. Frontend), Sprint L22
 */

import type { ReactNode } from 'react'
import { useFocusTrap } from '@/hooks/useFocusTrap'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
  actions?: ReactNode
  maxWidth?: string
  ariaLabel?: string
}

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  actions,
  maxWidth = '480px',
  ariaLabel,
}: DialogProps) {
  const trapRef = useFocusTrap()

  if (!open) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        zIndex: 50,
      }}
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel || title}
    >
      <div
        ref={trapRef}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '32px',
          maxWidth,
          width: '90%',
        }}
      >
        <h3
          style={{
            margin: '0 0 8px',
            fontSize: '20px',
            fontWeight: 600,
            color: 'var(--color-text)',
          }}
        >
          {title}
        </h3>

        {description && (
          <p
            style={{
              margin: '0 0 24px',
              fontSize: '14px',
              color: 'var(--color-text-2)',
            }}
          >
            {description}
          </p>
        )}

        {children}

        {actions && (
          <div
            style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end',
              marginTop: '24px',
            }}
          >
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}
