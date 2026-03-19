import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Switch } from '../components/ui/Switch'
import { Badge } from '../components/ui/Badge'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'

describe('Dark Mode — Component Rendering', () => {
  beforeEach(() => {
    document.documentElement.setAttribute('data-theme', 'dark')
  })

  afterEach(() => {
    document.documentElement.removeAttribute('data-theme')
  })

  it('Button renders in dark mode without crashing', () => {
    const { getByText } = render(<Button>Click me</Button>)
    expect(getByText('Click me')).toBeTruthy()
  })

  it('Card renders in dark mode', () => {
    const { getByText } = render(<Card>Content</Card>)
    expect(getByText('Content')).toBeTruthy()
  })

  it('Input renders in dark mode', () => {
    const { container } = render(<Input placeholder="Type here" />)
    expect(container.querySelector('input')).toBeTruthy()
  })

  it('Switch renders in dark mode', () => {
    const { getByRole } = render(<Switch checked={false} onChange={() => {}} label="Toggle" />)
    expect(getByRole('switch')).toBeTruthy()
  })

  it('Badge renders all variants in dark mode', () => {
    const variants = ['default', 'info', 'success', 'warning', 'danger'] as const
    for (const variant of variants) {
      const { getByText, unmount } = render(<Badge variant={variant}>{variant}</Badge>)
      expect(getByText(variant)).toBeTruthy()
      unmount()
    }
  })

  it('ConfirmDialog renders in dark mode', () => {
    const { getByText } = render(
      <ConfirmDialog open={true} onClose={() => {}} onConfirm={() => {}} title="Dark dialog" />
    )
    expect(getByText('Dark dialog')).toBeTruthy()
  })
})
