import * as RadixDialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { type ReactNode } from 'react'
import { cn } from './cn'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

const sizeMap = {
  sm: 'max-w-[400px]',
  md: 'max-w-[500px]',
  lg: 'max-w-[640px]',
}

export function Dialog({ open, onClose, title, description, size = 'md', children }: DialogProps) {
  return (
    <RadixDialog.Root open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in" />
        <RadixDialog.Content
          className={cn(
            'fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50',
            'w-[calc(100vw-2rem)] rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-6 shadow-[var(--shadow-xl)]',
            'animate-fade-in',
            sizeMap[size]
          )}
          onEscapeKeyDown={onClose}
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <RadixDialog.Title className="text-base font-semibold text-[var(--color-text)]">
                {title}
              </RadixDialog.Title>
              {description && (
                <RadixDialog.Description className="text-sm text-[var(--color-text-secondary)] mt-1">
                  {description}
                </RadixDialog.Description>
              )}
            </div>
            <button
              onClick={onClose}
              className="ml-4 p-1 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-colors"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          {children}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  )
}
