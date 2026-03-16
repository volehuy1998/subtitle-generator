/**
 * Phase Lumen — Cancel confirmation dialog (Sprint L8).
 *
 * Replaces window.confirm() with a styled modal that matches
 * the ConfirmationDialog pattern. Destructive action uses red styling.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { useEffect, useRef } from 'react'

interface CancelConfirmationDialogProps {
  filename: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function CancelConfirmationDialog({
  filename,
  onConfirm,
  onCancel,
}: CancelConfirmationDialogProps) {
  const backdropRef = useRef<HTMLDivElement>(null)

  // Focus the dialog on mount so keyboard events (Escape) work
  useEffect(() => {
    backdropRef.current?.focus()
  }, [])

  return (
    <div
      ref={backdropRef}
      tabIndex={-1}
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        zIndex: 50,
        outline: 'none',
      }}
      onClick={onCancel}
      onKeyDown={(e) => { if (e.key === 'Escape') onCancel() }}
      role="dialog"
      aria-modal="true"
      aria-label="Cancel transcription confirmation"
    >
      <div
        style={{
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '32px',
          maxWidth: '420px',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Warning icon */}
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius)',
            background: 'var(--color-danger-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <circle cx="10" cy="10" r="8" stroke="var(--color-danger)" strokeWidth="1.5" fill="none" />
            <path d="M10 6v5" stroke="var(--color-danger)" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="10" cy="14" r="0.75" fill="var(--color-danger)" />
          </svg>
        </div>

        <h3
          style={{
            margin: '0 0 8px 0',
            fontSize: '18px',
            fontWeight: 600,
            color: 'var(--color-text)',
          }}
        >
          Cancel transcription?
        </h3>

        <p
          style={{
            margin: '0 0 24px 0',
            fontSize: '14px',
            color: 'var(--color-text-2)',
            lineHeight: '1.5',
          }}
        >
          This will stop the transcription of{' '}
          <span style={{ fontWeight: 500, color: 'var(--color-text)' }}>
            {filename}
          </span>
          . Any progress will be lost.
        </p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg)',
              color: 'var(--color-text-2)',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Keep Going
          </button>
          <button
            onClick={onConfirm}
            style={{
              padding: '10px 24px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: 'var(--color-danger)',
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            Cancel Transcription
          </button>
        </div>
      </div>
    </div>
  );
}
