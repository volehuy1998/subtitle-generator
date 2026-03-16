/**
 * Skeleton — loading placeholder with pulse animation.
 * — Pixel (Sr. Frontend), Sprint L18
 */

export function Skeleton({ width = '100%', height = '16px', borderRadius = '4px' }: {
  width?: string; height?: string; borderRadius?: string;
}) {
  return (
    <div
      className="animate-pulse"
      style={{
        width, height, borderRadius,
        background: 'var(--color-surface-2)',
      }}
    />
  )
}

export function SkeletonLine({ lines = 3 }: { lines?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} width={i === lines - 1 ? '60%' : '100%'} height="12px" />
      ))}
    </div>
  )
}
