/**
 * SettingsPage tests — tabbed settings interface with reset.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SettingsPage } from '../../pages/SettingsPage'
import { usePreferencesStore } from '../../store/preferencesStore'

// Mock settings sub-components to isolate SettingsPage logic
vi.mock('../../components/settings/GeneralSettings', () => ({
  GeneralSettings: () => <div data-testid="general-settings">GeneralSettings</div>,
}))
vi.mock('../../components/settings/TranscriptionSettings', () => ({
  TranscriptionSettings: () => <div data-testid="transcription-settings">TranscriptionSettings</div>,
}))
vi.mock('../../components/settings/EmbedSettings', () => ({
  EmbedSettings: () => <div data-testid="embed-settings">EmbedSettings</div>,
}))
vi.mock('../../components/settings/AppearanceSettings', () => ({
  AppearanceSettings: () => <div data-testid="appearance-settings">AppearanceSettings</div>,
}))

describe('SettingsPage', () => {
  beforeEach(() => {
    usePreferencesStore.getState().reset()
  })

  it('renders the heading and subtitle', () => {
    render(<SettingsPage />)
    expect(screen.getByText('Settings')).toBeDefined()
    expect(screen.getByText('Manage your preferences and defaults.')).toBeDefined()
  })

  it('renders all four tabs', () => {
    render(<SettingsPage />)
    expect(screen.getByRole('tab', { name: /General/i })).toBeDefined()
    expect(screen.getByRole('tab', { name: /Transcription/i })).toBeDefined()
    expect(screen.getByRole('tab', { name: /Embedding/i })).toBeDefined()
    expect(screen.getByRole('tab', { name: /Appearance/i })).toBeDefined()
  })

  it('shows GeneralSettings panel by default', () => {
    render(<SettingsPage />)
    expect(screen.getByTestId('general-settings')).toBeDefined()
    expect(screen.queryByTestId('transcription-settings')).toBeNull()
  })

  it('switches to Transcription tab on click', () => {
    render(<SettingsPage />)
    fireEvent.click(screen.getByRole('tab', { name: /Transcription/i }))
    expect(screen.getByTestId('transcription-settings')).toBeDefined()
    expect(screen.queryByTestId('general-settings')).toBeNull()
  })

  it('switches to Embedding tab on click', () => {
    render(<SettingsPage />)
    fireEvent.click(screen.getByRole('tab', { name: /Embedding/i }))
    expect(screen.getByTestId('embed-settings')).toBeDefined()
  })

  it('switches to Appearance tab on click', () => {
    render(<SettingsPage />)
    fireEvent.click(screen.getByRole('tab', { name: /Appearance/i }))
    expect(screen.getByTestId('appearance-settings')).toBeDefined()
  })

  it('renders Reset all button', () => {
    render(<SettingsPage />)
    expect(screen.getByText('Reset all')).toBeDefined()
  })

  it('calls preferences reset when Reset all is clicked', () => {
    // Change a preference first
    usePreferencesStore.getState().setPreferredFormat('vtt')
    expect(usePreferencesStore.getState().preferredFormat).toBe('vtt')

    render(<SettingsPage />)
    fireEvent.click(screen.getByText('Reset all'))

    // After reset, the store should be back to default
    expect(usePreferencesStore.getState().preferredFormat).toBe('srt')
  })
})
