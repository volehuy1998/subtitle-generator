import { describe, it, expect, beforeEach } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { ThemeToggle } from '../../components/ui/ThemeToggle'
import { usePreferencesStore } from '../../store/preferencesStore'

describe('ThemeToggle', () => {
  beforeEach(() => {
    usePreferencesStore.getState().reset()
  })

  it('renders with aria-label showing current theme', () => {
    const { getByRole } = render(<ThemeToggle />)
    const btn = getByRole('button')
    expect(btn.getAttribute('aria-label')).toContain('System')
  })

  it('cycles theme on click: system -> dark -> light -> system', () => {
    const { getByRole } = render(<ThemeToggle />)
    const btn = getByRole('button')
    fireEvent.click(btn)
    expect(usePreferencesStore.getState().theme).toBe('dark')
    fireEvent.click(btn)
    expect(usePreferencesStore.getState().theme).toBe('light')
    fireEvent.click(btn)
    expect(usePreferencesStore.getState().theme).toBe('system')
  })

  it('has title attribute', () => {
    const { getByRole } = render(<ThemeToggle />)
    expect(getByRole('button').getAttribute('title')).toBeTruthy()
  })

  it('renders an SVG icon', () => {
    const { container } = render(<ThemeToggle />)
    expect(container.querySelector('svg')).toBeTruthy()
  })
})
