import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useToastStore } from '../../store/toastStore'

describe('toastStore', () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] })
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds a toast', () => {
    useToastStore.getState().addToast({ type: 'success', title: 'Done!' })
    expect(useToastStore.getState().toasts).toHaveLength(1)
    expect(useToastStore.getState().toasts[0].title).toBe('Done!')
    expect(useToastStore.getState().toasts[0].type).toBe('success')
  })

  it('assigns unique IDs', () => {
    useToastStore.getState().addToast({ type: 'info', title: 'A' })
    useToastStore.getState().addToast({ type: 'info', title: 'B' })
    const [a, b] = useToastStore.getState().toasts
    expect(a.id).not.toBe(b.id)
  })

  it('removes a toast by id', () => {
    useToastStore.getState().addToast({ type: 'info', title: 'Hello' })
    const id = useToastStore.getState().toasts[0].id
    useToastStore.getState().removeToast(id)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('auto-removes after duration', () => {
    useToastStore.getState().addToast({ type: 'success', title: 'Temp', duration: 1000 })
    expect(useToastStore.getState().toasts).toHaveLength(1)
    vi.advanceTimersByTime(1001)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('persists forever when duration is 0', () => {
    useToastStore.getState().addToast({ type: 'warning', title: 'Sticky', duration: 0 })
    vi.advanceTimersByTime(60000)
    expect(useToastStore.getState().toasts).toHaveLength(1)
  })

  it('defaults duration to 5000', () => {
    useToastStore.getState().addToast({ type: 'info', title: 'Default' })
    expect(useToastStore.getState().toasts[0].duration).toBe(5000)
  })
})
