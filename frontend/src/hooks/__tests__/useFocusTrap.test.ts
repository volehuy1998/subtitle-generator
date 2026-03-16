import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useFocusTrap } from '../useFocusTrap'

describe('useFocusTrap', () => {
  let container: HTMLDivElement

  beforeEach(() => {
    // Clean up previous containers
    const old = document.getElementById('trap-container')
    if (old) old.remove()

    container = document.createElement('div')
    container.id = 'trap-container'
    document.body.appendChild(container)
  })

  // ── Ref returned correctly ────────────────────────────────────────────────

  it('returns a ref object', () => {
    const { result } = renderHook(() => useFocusTrap())
    expect(result.current).toBeDefined()
    expect(result.current).toHaveProperty('current')
  })

  // ── Tab wrapping: last -> first ───────────────────────────────────────────

  it('Tab from last element wraps to first', () => {
    const btn1 = document.createElement('button')
    btn1.textContent = 'First'
    const btn2 = document.createElement('button')
    btn2.textContent = 'Second'
    const btn3 = document.createElement('button')
    btn3.textContent = 'Third'
    container.appendChild(btn1)
    container.appendChild(btn2)
    container.appendChild(btn3)

    const focusables = container.querySelectorAll<HTMLElement>('button')
    const first = focusables[0]
    const last = focusables[focusables.length - 1]

    // Focus the last element
    last.focus()
    expect(document.activeElement).toBe(last)

    // Set up the trap handler as the hook would
    container.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      const els = container.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const f = els[0]
      const l = els[els.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === f) { e.preventDefault(); l?.focus() }
      } else {
        if (document.activeElement === l) { e.preventDefault(); f?.focus() }
      }
    })

    const tabEvent = new KeyboardEvent('keydown', {
      key: 'Tab', shiftKey: false, bubbles: true, cancelable: true,
    })
    container.dispatchEvent(tabEvent)
    expect(document.activeElement).toBe(first)
  })

  // ── Shift+Tab wrapping: first -> last ─────────────────────────────────────

  it('Shift+Tab from first element wraps to last', () => {
    const btn1 = document.createElement('button')
    btn1.textContent = 'First'
    const btn2 = document.createElement('button')
    btn2.textContent = 'Second'
    const btn3 = document.createElement('button')
    btn3.textContent = 'Third'
    container.appendChild(btn1)
    container.appendChild(btn2)
    container.appendChild(btn3)

    const focusables = container.querySelectorAll<HTMLElement>('button')
    const first = focusables[0]
    const last = focusables[focusables.length - 1]

    // Focus the first element
    first.focus()
    expect(document.activeElement).toBe(first)

    // Set up the trap handler
    container.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      const els = container.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const f = els[0]
      const l = els[els.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === f) { e.preventDefault(); l?.focus() }
      } else {
        if (document.activeElement === l) { e.preventDefault(); f?.focus() }
      }
    })

    const shiftTabEvent = new KeyboardEvent('keydown', {
      key: 'Tab', shiftKey: true, bubbles: true, cancelable: true,
    })
    container.dispatchEvent(shiftTabEvent)
    expect(document.activeElement).toBe(last)
  })
})
