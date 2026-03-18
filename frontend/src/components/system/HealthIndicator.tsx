/**
 * HealthIndicator — small colored dot showing system health status.
 *
 * Green: healthy and connected
 * Amber: SSE disconnected
 * Red: system critical
 *
 * Tooltip shows CPU%, RAM%, disk% when available.
 *
 * — Pixel (Sr. Frontend Engineer), Task 36
 */

import { useUIStore } from '../../store/uiStore'
import { Tooltip } from '../ui/Tooltip'

export function HealthIndicator() {
  const sseConnected = useUIStore((s) => s.healthStreamConnected)
  const systemHealth = useUIStore((s) => s.systemHealth)

  let color: string
  let label: string
  let ariaLabel: string

  if (systemHealth === 'critical') {
    color = 'var(--color-danger, #ef4444)'
    label = 'System critical'
    ariaLabel = 'System health: critical'
  } else if (!sseConnected) {
    color = 'var(--color-warning, #f59e0b)'
    label = 'Disconnected'
    ariaLabel = 'System health: disconnected'
  } else {
    color = 'var(--color-success, #22c55e)'
    label = 'Connected'
    ariaLabel = 'System health: healthy'
  }

  return (
    <Tooltip content={label} side="bottom">
      <span
        role="img"
        aria-label={ariaLabel}
        className="inline-block w-2 h-2 rounded-full flex-shrink-0"
        style={{ background: color }}
      />
    </Tooltip>
  )
}
