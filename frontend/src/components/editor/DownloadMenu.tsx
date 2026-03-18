import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Download } from 'lucide-react'
import { Button } from '../ui/Button'
import { cn } from '../ui/cn'
import { usePreferencesStore } from '../../store/preferencesStore'

export interface DownloadMenuProps {
  taskId: string
}

const FORMATS = [
  { label: 'SRT', value: 'srt' },
  { label: 'VTT', value: 'vtt' },
  { label: 'JSON', value: 'json' },
] as const

export function DownloadMenu({ taskId }: DownloadMenuProps) {
  const [open, setOpen] = useState(false)
  const defaultMaxChars = usePreferencesStore(s => s.maxLineChars)
  const [maxChars, setMaxChars] = useState(defaultMaxChars)
  const containerRef = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const buildUrl = (format: string) =>
    `/download/${taskId}?format=${format}&max_line_chars=${maxChars}`

  return (
    <div ref={containerRef} data-testid="download-menu-wrapper" className="relative">
      <Button
        variant="secondary"
        size="sm"
        leftIcon={<Download className="h-3.5 w-3.5" />}
        rightIcon={<ChevronDown className="h-3.5 w-3.5" />}
        onClick={() => setOpen(o => !o)}
        aria-haspopup="true"
        aria-expanded={open}
      >
        Download
      </Button>

      {open && (
        <div
          className={cn(
            'absolute left-0 top-full mt-1 z-50 min-w-[180px]',
            'rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg',
            'p-1'
          )}
          role="menu"
        >
          {FORMATS.map(f => (
            <a
              key={f.value}
              href={buildUrl(f.value)}
              download
              role="menuitem"
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 text-sm rounded-md',
                'text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-colors'
              )}
              onClick={() => setOpen(false)}
            >
              {f.label}
            </a>
          ))}

          <div className="border-t border-[var(--color-border)] mt-1 pt-1 px-3 pb-1">
            <label className="text-xs text-[var(--color-text-muted)] block mb-1">
              Max line chars
            </label>
            <input
              type="number"
              min={20}
              max={120}
              value={maxChars}
              onChange={e => setMaxChars(Number(e.target.value))}
              className={cn(
                'w-full h-7 px-2 text-xs rounded-md border border-[var(--color-border)]',
                'bg-[var(--color-surface)] text-[var(--color-text)]',
                'focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)]'
              )}
              onClick={e => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  )
}
