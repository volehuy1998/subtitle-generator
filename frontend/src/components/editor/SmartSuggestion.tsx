import { X } from 'lucide-react'
import { Button } from '../ui/Button'
import { useUIStore } from '../../store/uiStore'

export interface SmartSuggestionProps {
  id: string
  title: string
  description?: string
  actionLabel: string
  onAction: () => void
}

export function SmartSuggestion({ id, title, description, actionLabel, onAction }: SmartSuggestionProps) {
  const dismissedSuggestions = useUIStore(s => s.dismissedSuggestions)
  const dismissSuggestion = useUIStore(s => s.dismissSuggestion)

  if (dismissedSuggestions.includes(id)) return null

  return (
    <div className="rounded-lg border border-[--color-primary] bg-[--color-primary-light] p-3 relative">
      <button
        className="absolute top-2 right-2 p-0.5 rounded text-[--color-primary] hover:opacity-70 transition-opacity"
        aria-label="Dismiss suggestion"
        onClick={() => dismissSuggestion(id)}
      >
        <X className="h-3.5 w-3.5" />
      </button>

      <p className="text-sm font-medium text-[--color-text] pr-6">{title}</p>

      {description && (
        <p className="text-xs text-[--color-text-secondary] mt-1">{description}</p>
      )}

      <div className="mt-2">
        <Button
          variant="primary"
          size="sm"
          onClick={onAction}
        >
          {actionLabel}
        </Button>
      </div>
    </div>
  )
}
