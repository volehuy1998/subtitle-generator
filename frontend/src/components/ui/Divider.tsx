/* Divider — horizontal rule with optional label — Pixel (Sr. Frontend), Sprint L38 */

interface DividerProps {
  label?: string
  spacing?: 'sm' | 'md' | 'lg'
}

export function Divider({ label, spacing = 'md' }: DividerProps) {
  const gap = spacing === 'sm' ? '8px' : spacing === 'md' ? '16px' : '24px'

  if (!label) {
    return <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: `${gap} 0` }} />
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: `${gap} 0` }}>
      <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
      <span
        style={{
          fontSize: '12px',
          fontWeight: 500,
          color: 'var(--color-text-3)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        {label}
      </span>
      <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }} />
    </div>
  )
}
