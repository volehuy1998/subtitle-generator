/**
 * Tooltip — hover-activated tooltip with configurable position and delay.
 * Pure presentational, CSS-only positioning, no portal.
 * — Pixel (Sr. Frontend), Sprint L33
 */

import { useCallback, useId, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right'

interface TooltipProps {
  content: string
  children: ReactNode
  position?: TooltipPosition
  delay?: number
}

const ARROW_SIZE = 5

const tooltipBase: CSSProperties = {
  position: 'absolute',
  background: '#1E293B',
  color: '#fff',
  fontSize: '12px',
  lineHeight: 1.4,
  fontWeight: 500,
  padding: '6px 10px',
  borderRadius: '6px',
  maxWidth: '250px',
  whiteSpace: 'normal',
  wordWrap: 'break-word',
  zIndex: 50,
  pointerEvents: 'none',
}

const arrowBase: CSSProperties = {
  position: 'absolute',
  width: 0,
  height: 0,
  borderStyle: 'solid',
}

const positionStyles: Record<TooltipPosition, { tooltip: CSSProperties; arrow: CSSProperties }> = {
  top: {
    tooltip: {
      bottom: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      marginBottom: `${ARROW_SIZE + 2}px`,
    },
    arrow: {
      top: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      borderWidth: `${ARROW_SIZE}px ${ARROW_SIZE}px 0 ${ARROW_SIZE}px`,
      borderColor: '#1E293B transparent transparent transparent',
    },
  },
  bottom: {
    tooltip: {
      top: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      marginTop: `${ARROW_SIZE + 2}px`,
    },
    arrow: {
      bottom: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      borderWidth: `0 ${ARROW_SIZE}px ${ARROW_SIZE}px ${ARROW_SIZE}px`,
      borderColor: `transparent transparent #1E293B transparent`,
    },
  },
  left: {
    tooltip: {
      right: '100%',
      top: '50%',
      transform: 'translateY(-50%)',
      marginRight: `${ARROW_SIZE + 2}px`,
    },
    arrow: {
      left: '100%',
      top: '50%',
      transform: 'translateY(-50%)',
      borderWidth: `${ARROW_SIZE}px 0 ${ARROW_SIZE}px ${ARROW_SIZE}px`,
      borderColor: `transparent transparent transparent #1E293B`,
    },
  },
  right: {
    tooltip: {
      left: '100%',
      top: '50%',
      transform: 'translateY(-50%)',
      marginLeft: `${ARROW_SIZE + 2}px`,
    },
    arrow: {
      right: '100%',
      top: '50%',
      transform: 'translateY(-50%)',
      borderWidth: `${ARROW_SIZE}px ${ARROW_SIZE}px ${ARROW_SIZE}px 0`,
      borderColor: `transparent #1E293B transparent transparent`,
    },
  },
}

export function Tooltip({ content, children, position = 'top', delay = 300 }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const tooltipId = useId()

  const show = useCallback(() => {
    timerRef.current = setTimeout(() => setVisible(true), delay)
  }, [delay])

  const hide = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    setVisible(false)
  }, [])

  const pos = positionStyles[position]

  return (
    <div
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      <div aria-describedby={visible ? tooltipId : undefined}>
        {children}
      </div>
      {visible && (
        <div
          id={tooltipId}
          role="tooltip"
          style={{
            ...tooltipBase,
            ...pos.tooltip,
            animation: 'tooltip-fade-in 0.15s ease-out',
          }}
        >
          {content}
          <span style={{ ...arrowBase, ...pos.arrow }} />
        </div>
      )}
    </div>
  )
}
