/**
 * Phase Lumen — Embed confirmation dialog.
 *
 * Shows a summary of video file, subtitle file, embed mode, and style
 * settings. Requires explicit user confirmation before embedding starts.
 * Follows the same pattern as transcribe/ConfirmationDialog.tsx.
 *
 * — Prism (UI/UX Engineer) — Sprint L8
 */

import type { EmbedMode } from '@/store/uiStore'

interface EmbedConfirmationDialogProps {
  videoFile: File
  subtitleFile: File
  mode: EmbedMode
  color?: string
  fontSize?: number
  translateTo?: string
  onConfirm: () => void
  onCancel: () => void
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const MODE_LABELS: Record<EmbedMode, string> = {
  soft: 'Soft Mux (selectable track)',
  hard: 'Hard Burn (burned into video)',
}

export function EmbedConfirmationDialog({
  videoFile,
  subtitleFile,
  mode,
  color,
  fontSize,
  translateTo,
  onConfirm,
  onCancel,
}: EmbedConfirmationDialogProps) {
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
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-label="Confirm subtitle embedding"
    >
      <div
        style={{
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '32px',
          maxWidth: '480px',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius)',
              background: 'var(--color-primary-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <rect x="2" y="3" width="14" height="10" rx="2" stroke="var(--color-primary)" strokeWidth="1.3" fill="none" />
              <path d="M5 16h8M9 13v3" stroke="var(--color-primary)" strokeWidth="1.3" strokeLinecap="round" />
              <path d="M5 8h8M5 10.5h5" stroke="var(--color-primary)" strokeWidth="1.1" strokeLinecap="round" />
            </svg>
          </div>
          <h3
            style={{
              margin: 0,
              fontSize: '20px',
              fontWeight: 600,
              color: 'var(--color-text)',
            }}
          >
            Ready to embed
          </h3>
        </div>

        <p
          style={{
            margin: '0 0 24px 0',
            fontSize: '14px',
            color: 'var(--color-text-2)',
          }}
        >
          Please confirm the settings below before embedding subtitles.
        </p>

        {/* Settings summary */}
        <div
          style={{
            background: 'var(--color-surface)',
            borderRadius: 'var(--radius)',
            padding: '16px',
            marginBottom: '24px',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <tbody>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)', width: '110px', verticalAlign: 'top' }}>
                  Video
                </td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)', fontWeight: 500 }}>
                  {videoFile.name}
                  <span style={{ color: 'var(--color-text-3)', marginLeft: '8px' }}>
                    ({formatFileSize(videoFile.size)})
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)', verticalAlign: 'top' }}>
                  Subtitle
                </td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)', fontWeight: 500 }}>
                  {subtitleFile.name}
                  <span style={{ color: 'var(--color-text-3)', marginLeft: '8px' }}>
                    ({formatFileSize(subtitleFile.size)})
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Mode</td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>
                  {MODE_LABELS[mode]}
                </td>
              </tr>
              {mode === 'hard' && color && (
                <tr>
                  <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Text color</td>
                  <td style={{ padding: '6px 0', color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        width: '14px',
                        height: '14px',
                        borderRadius: '3px',
                        background: color,
                        border: '1px solid var(--color-border)',
                      }}
                    />
                    {color.toUpperCase()}
                  </td>
                </tr>
              )}
              {mode === 'hard' && fontSize && (
                <tr>
                  <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Font size</td>
                  <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>
                    {fontSize}px
                  </td>
                </tr>
              )}
              {translateTo && (
                <tr>
                  <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Translate to</td>
                  <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>{translateTo}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Hard burn warning */}
        {mode === 'hard' && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              background: 'var(--color-warning-light)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
              marginBottom: '24px',
              fontSize: '13px',
              color: 'var(--color-text-2)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" style={{ flexShrink: 0, marginTop: '1px' }}>
              <path d="M8 1.5L1 14h14L8 1.5z" stroke="var(--color-warning)" strokeWidth="1.3" fill="none" />
              <path d="M8 6v4M8 12v1" stroke="var(--color-warning)" strokeWidth="1.3" strokeLinecap="round" />
            </svg>
            <span>
              Hard burn re-encodes the video. This takes longer and subtitles cannot be removed afterward.
            </span>
          </div>
        )}

        {/* Action buttons */}
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
            Cancel
          </button>
          <button
            onClick={onConfirm}
            style={{
              padding: '10px 24px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: 'var(--color-primary)',
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            Embed Subtitles
          </button>
        </div>
      </div>
    </div>
  )
}
