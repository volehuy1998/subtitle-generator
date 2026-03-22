import { useState } from 'react'
import type { StepTimings } from '@/api/types'

interface Props {
  timings: StepTimings
}

interface Row {
  label: string
  key: keyof StepTimings | 'total'
}

const ROWS: Row[] = [
  { label: 'Upload', key: 'upload' },
  { label: 'Extract', key: 'extract' },
  { label: 'Transcribe', key: 'transcribe' },
  { label: 'Finalize', key: 'finalize' },
  { label: 'Total', key: 'total' },
]

function formatTiming(sec: number | undefined): string {
  if (sec === undefined || sec === null) return '—'
  if (sec < 60) return `${sec.toFixed(2)}s`
  const m = Math.floor(sec / 60)
  const s = (sec % 60).toFixed(1)
  return `${m}m ${s}s`
}

export function TimingBreakdown({ timings }: Props) {
  const [open, setOpen] = useState(false)

  const total =
    (timings.upload ?? 0) +
    (timings.extract ?? 0) +
    (timings.transcribe ?? 0) +
    (timings.finalize ?? 0)

  const hasAny = Object.values(timings).some((v) => v !== undefined)
  if (!hasAny) return null

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{ border: '1px solid var(--color-border)' }}
    >
      {/* Header toggle */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2.5 transition-colors"
        style={{
          background: 'transparent',
          border: 'none',
          borderBottom: open ? '1px solid var(--color-border)' : 'none',
          cursor: 'pointer',
        }}
      >
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: 'var(--color-text-2)', letterSpacing: '0.07em' }}
        >
          TIMING BREAKDOWN
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          aria-hidden="true"
          style={{
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
          }}
        >
          <path
            d="M2 4l4 4 4-4"
            stroke="var(--color-text-3)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {/* Body */}
      {open && (
        <div className="flex flex-col">
          {ROWS.map(({ label, key }) => {
            const isTotal = key === 'total'
            const value = isTotal ? total : timings[key as keyof StepTimings]
            if (!isTotal && value === undefined) return null

            return (
              <div
                key={label}
                className="flex items-center justify-between px-3 py-2"
                style={{
                  borderTop: isTotal ? '1px solid var(--color-border)' : 'none',
                  background: isTotal ? 'var(--color-surface-2)' : 'transparent',
                }}
              >
                <span
                  className="text-xs"
                  style={{
                    color: 'var(--color-text-2)',
                    fontWeight: isTotal ? 600 : 400,
                  }}
                >
                  {label}
                </span>
                <span
                  className="text-xs font-mono tabular-nums"
                  style={{
                    color: isTotal ? 'var(--color-text)' : 'var(--color-text)',
                    fontWeight: isTotal ? 600 : 400,
                  }}
                >
                  {isTotal ? formatTiming(total) : formatTiming(value)}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
