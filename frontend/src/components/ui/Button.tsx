/* Button — variant button component — Prism (UI/UX), Sprint L28 */

import type React from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  icon?: React.ReactNode
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    background: 'var(--color-primary)',
    color: '#fff',
    border: '1px solid var(--color-primary)',
    boxShadow: 'var(--shadow-sm)',
  },
  secondary: {
    background: 'var(--color-bg)',
    color: 'var(--color-text-2)',
    border: '1px solid var(--color-border)',
    boxShadow: 'none',
  },
  danger: {
    background: 'var(--color-danger)',
    color: '#fff',
    border: '1px solid var(--color-danger)',
    boxShadow: 'none',
  },
  ghost: {
    background: 'transparent',
    color: 'var(--color-text-2)',
    border: '1px solid transparent',
    boxShadow: 'none',
  },
}

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: { padding: '4px 8px', fontSize: '14px', borderRadius: 'var(--radius-sm)' },
  md: { padding: '6px 10px', fontSize: '14px', borderRadius: 'var(--radius-sm)' },
  lg: { padding: '8px 12px', fontSize: '16px', borderRadius: 'var(--radius)' },
}

const spinnerStyle: React.CSSProperties = {
  display: 'inline-block',
  width: '12px',
  height: '12px',
  border: '2px solid currentColor',
  borderTopColor: 'transparent',
  borderRadius: '50%',
  animation: 'spin 0.6s linear infinite',
  flexShrink: 0,
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  disabled,
  children,
  className = '',
  style,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading

  const merged: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    fontFamily: 'var(--font-family-sans)',
    fontWeight: 500,
    lineHeight: 1,
    cursor: isDisabled ? 'not-allowed' : 'pointer',
    opacity: isDisabled ? 0.5 : 1,
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  }

  return (
    <button
      className={`btn-interactive ${className}`.trim()}
      style={merged}
      disabled={isDisabled}
      {...rest}
    >
      {loading ? <span style={spinnerStyle} aria-hidden="true" /> : icon}
      {children}
    </button>
  )
}
