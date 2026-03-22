import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useToastStore } from '../toastStore'

const store = () => useToastStore.getState()
const reset = () => useToastStore.setState({ toasts: [] })

describe('toastStore', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    reset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // ── addToast ──────────────────────────────────────────────────────────────

  it('addToast creates toast with unique id, correct type, message, and default duration', () => {
    store().addToast('success', 'Saved')
    const toasts = store().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].type).toBe('success')
    expect(toasts[0].message).toBe('Saved')
    expect(toasts[0].duration).toBe(4000)
    expect(toasts[0].id).toBeTruthy()
  })

  it('addToast with duration 0 means no auto-remove', () => {
    store().addToast('error', 'Failed', 0)
    const toasts = store().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].duration).toBe(0)

    // Advance time well past default — toast should remain
    vi.advanceTimersByTime(10000)
    expect(store().toasts).toHaveLength(1)
  })

  it('multiple toasts grow array with unique ids', () => {
    store().addToast('success', 'First')
    store().addToast('error', 'Second')
    store().addToast('warning', 'Third')

    const toasts = store().toasts
    expect(toasts).toHaveLength(3)

    const ids = toasts.map(t => t.id)
    const uniqueIds = new Set(ids)
    expect(uniqueIds.size).toBe(3)
  })

  // ── Auto-dismiss ──────────────────────────────────────────────────────────

  it('auto-dismiss removes toast after duration elapses', () => {
    store().addToast('success', 'Disappears')
    expect(store().toasts).toHaveLength(1)

    vi.advanceTimersByTime(4001)
    expect(store().toasts).toHaveLength(0)
  })

  it('auto-dismiss removes only the expired toast', () => {
    store().addToast('success', 'Short', 1000)
    store().addToast('info', 'Long', 5000)
    expect(store().toasts).toHaveLength(2)

    vi.advanceTimersByTime(1001)
    expect(store().toasts).toHaveLength(1)
    expect(store().toasts[0].message).toBe('Long')
  })

  // ── removeToast ───────────────────────────────────────────────────────────

  it('removeToast removes exactly the specified toast by id', () => {
    store().addToast('success', 'Keep')
    store().addToast('error', 'Remove')
    store().addToast('info', 'Keep too')

    const idToRemove = store().toasts[1].id
    store().removeToast(idToRemove)

    const remaining = store().toasts
    expect(remaining).toHaveLength(2)
    expect(remaining.map(t => t.message)).toEqual(['Keep', 'Keep too'])
  })

  it('removeToast with non-existent id does nothing', () => {
    store().addToast('success', 'Only one')
    store().removeToast('non-existent-id')
    expect(store().toasts).toHaveLength(1)
  })

  // ── state isolation ───────────────────────────────────────────────────────

  it('each test starts with empty toasts (beforeEach verification)', () => {
    expect(store().toasts).toHaveLength(0)
  })
})
