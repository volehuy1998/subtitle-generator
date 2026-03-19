import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { Tabs } from '../../components/ui/Tabs'

const tabs = [
  { id: 'general', label: 'General' },
  { id: 'advanced', label: 'Advanced' },
  { id: 'about', label: 'About' },
]

describe('Tabs', () => {
  it('renders all tab labels', () => {
    const { getByText } = render(<Tabs tabs={tabs} activeTab="general" onChange={() => {}} />)
    expect(getByText('General')).toBeTruthy()
    expect(getByText('Advanced')).toBeTruthy()
    expect(getByText('About')).toBeTruthy()
  })

  it('marks active tab with aria-selected', () => {
    const { getAllByRole } = render(<Tabs tabs={tabs} activeTab="advanced" onChange={() => {}} />)
    const tabElements = getAllByRole('tab')
    expect(tabElements[1].getAttribute('aria-selected')).toBe('true')
    expect(tabElements[0].getAttribute('aria-selected')).toBe('false')
  })

  it('calls onChange with tab id on click', () => {
    const onChange = vi.fn()
    const { getByText } = render(<Tabs tabs={tabs} activeTab="general" onChange={onChange} />)
    fireEvent.click(getByText('About'))
    expect(onChange).toHaveBeenCalledWith('about')
  })

  it('renders with tablist role', () => {
    const { getByRole } = render(<Tabs tabs={tabs} activeTab="general" onChange={() => {}} />)
    expect(getByRole('tablist')).toBeTruthy()
  })

  it('renders tab icons when provided', () => {
    const tabsWithIcons = [{ id: 'a', label: 'A', icon: <span data-testid="icon">*</span> }]
    const { getByTestId } = render(<Tabs tabs={tabsWithIcons} activeTab="a" onChange={() => {}} />)
    expect(getByTestId('icon')).toBeTruthy()
  })
})
