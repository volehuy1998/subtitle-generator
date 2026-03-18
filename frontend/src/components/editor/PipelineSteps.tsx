import { Check, Circle } from 'lucide-react'
import { Spinner } from '../ui/Spinner'
import { cn } from '../ui/cn'

const STEPS = ['extracting', 'transcribing', 'formatting', 'saving'] as const

interface PipelineStepsProps {
  currentStep: string | null
}

export function PipelineSteps({ currentStep }: PipelineStepsProps) {
  const currentIndex = currentStep ? STEPS.indexOf(currentStep as typeof STEPS[number]) : -1

  return (
    <ol className="flex flex-col gap-2" aria-label="Pipeline steps">
      {STEPS.map((step, index) => {
        const isPast = currentIndex > index
        const isCurrent = currentIndex === index
        const isFuture = currentIndex < index

        return (
          <li key={step} className="flex items-center gap-2.5">
            <span
              className={cn(
                'flex h-5 w-5 shrink-0 items-center justify-center rounded-full',
                isPast && 'text-[var(--color-success)]',
                isCurrent && 'text-[var(--color-primary)]',
                isFuture && 'text-[var(--color-text-muted)]',
              )}
              aria-hidden="true"
            >
              {isPast ? (
                <Check className="h-4 w-4" />
              ) : isCurrent ? (
                <Spinner size="sm" />
              ) : (
                <Circle className="h-4 w-4" />
              )}
            </span>
            <span
              className={cn(
                'text-sm',
                isPast && 'text-[var(--color-text-secondary)] line-through',
                isCurrent && 'font-medium text-[var(--color-text)]',
                isFuture && 'text-[var(--color-text-muted)]',
              )}
            >
              {step.charAt(0).toUpperCase() + step.slice(1)}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
