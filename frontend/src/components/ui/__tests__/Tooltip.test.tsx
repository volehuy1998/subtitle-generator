import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Tooltip, TooltipProvider } from '../Tooltip'

function renderWithProvider(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>)
}

describe('Tooltip', () => {
  it('renders trigger children', () => {
    renderWithProvider(
      <Tooltip content="Help text"><button>Hover me</button></Tooltip>
    )
    expect(screen.getByRole('button', { name: 'Hover me' })).toBeDefined()
  })

  it('tooltip content is not in DOM initially', () => {
    renderWithProvider(
      <Tooltip content="Hidden tip"><button>Target</button></Tooltip>
    )
    // Radix renders content into portal only on open — not visible initially
    expect(screen.queryByText('Hidden tip')).toBeNull()
  })

  it('accepts side prop without error', () => {
    const sides = ['top', 'right', 'bottom', 'left'] as const
    for (const side of sides) {
      const { unmount } = renderWithProvider(
        <Tooltip content="Tip" side={side}><button>Target</button></Tooltip>
      )
      expect(screen.getByRole('button', { name: 'Target' })).toBeDefined()
      unmount()
    }
  })

  it('accepts delayDuration prop without error', () => {
    renderWithProvider(
      <Tooltip content="Delayed" delayDuration={100}><button>Target</button></Tooltip>
    )
    expect(screen.getByRole('button', { name: 'Target' })).toBeDefined()
  })

  it('TooltipProvider is exported', () => {
    expect(TooltipProvider).toBeDefined()
  })
})
