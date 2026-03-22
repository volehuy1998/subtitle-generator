/* Input — text input with label and validation — Pixel (Sr. Frontend), Sprint L37 */

import type React from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

export function Input({ label, error, helperText, id, style, ...props }: InputProps) {
  const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {label && (
        <label htmlFor={inputId} style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-2)' }}>
          {label}
        </label>
      )}
      <input
        id={inputId}
        {...props}
        style={{
          padding: '8px 12px',
          borderRadius: 'var(--radius)',
          border: `1px solid ${error ? 'var(--color-danger)' : 'var(--color-border)'}`,
          background: 'var(--color-bg)',
          color: 'var(--color-text)',
          fontSize: '14px',
          fontFamily: 'var(--font-family-sans)',
          outline: 'none',
          ...style,
        }}
      />
      {error && <span style={{ fontSize: '12px', color: 'var(--color-danger)' }}>{error}</span>}
      {!error && helperText && <span style={{ fontSize: '12px', color: 'var(--color-text-3)' }}>{helperText}</span>}
    </div>
  )
}
