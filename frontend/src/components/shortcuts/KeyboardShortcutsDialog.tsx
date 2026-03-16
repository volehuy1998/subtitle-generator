/**
 * KeyboardShortcutsDialog — modal showing all available keyboard shortcuts.
 * Triggered by pressing "?" (Shift+/).
 *
 * — Pixel (Sr. Frontend), Sprint L48
 */

import { Dialog } from '@/components/ui/Dialog'

interface Props {
  open: boolean
  onClose: () => void
}

interface ShortcutEntry {
  keys: string[]
  description: string
}

const SHORTCUTS: ShortcutEntry[] = [
  { keys: ['1'], description: 'Switch to Transcribe tab' },
  { keys: ['2'], description: 'Switch to Embed tab' },
  { keys: ['Esc'], description: 'Close dialog / panel' },
  { keys: ['?'], description: 'Show keyboard shortcuts' },
]

function KeyBadge({ children }: { children: string }) {
  return (
    <kbd
      className="inline-flex items-center justify-center rounded font-mono text-xs font-semibold"
      style={{
        minWidth: '24px',
        height: '24px',
        padding: '0 6px',
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        color: 'var(--color-text)',
        boxShadow: '0 1px 0 var(--color-border-2)',
        lineHeight: '24px',
      }}
    >
      {children}
    </kbd>
  )
}

export function KeyboardShortcutsDialog({ open, onClose }: Props) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Keyboard Shortcuts"
      description="Navigate the app faster with these shortcuts."
      maxWidth="400px"
      actions={
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{
            background: 'var(--color-primary)',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Got it
        </button>
      }
    >
      <div className="flex flex-col gap-0">
        {SHORTCUTS.map((shortcut, i) => (
          <div
            key={i}
            className="flex items-center justify-between py-2.5"
            style={{
              borderBottom: i < SHORTCUTS.length - 1 ? '1px solid var(--color-border)' : 'none',
            }}
          >
            <span
              className="text-sm"
              style={{ color: 'var(--color-text)' }}
            >
              {shortcut.description}
            </span>
            <div className="flex items-center gap-1">
              {shortcut.keys.map((key) => (
                <KeyBadge key={key}>{key}</KeyBadge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Dialog>
  )
}
