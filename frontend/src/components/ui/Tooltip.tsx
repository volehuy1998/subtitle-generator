import * as RadixTooltip from '@radix-ui/react-tooltip'
import React, { type ReactNode } from 'react'

interface TooltipProps {
  content: ReactNode
  children: ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  delayDuration?: number
}

export function Tooltip({ content, children, side = 'top', delayDuration = 500 }: TooltipProps) {
  return (
    <RadixTooltip.Root delayDuration={delayDuration}>
      <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content
          side={side}
          sideOffset={6}
          className="z-50 rounded-md bg-[var(--color-text)] px-2.5 py-1 text-xs text-[var(--color-text-inverse)] shadow-lg animate-fade-in max-w-[200px]"
        >
          {content}
          <RadixTooltip.Arrow className="fill-[var(--color-text)]" />
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  )
}

export function TooltipProvider({ children, ...props }: React.ComponentPropsWithoutRef<typeof RadixTooltip.Provider>) {
  return <RadixTooltip.Provider {...props}>{children}</RadixTooltip.Provider>
}
