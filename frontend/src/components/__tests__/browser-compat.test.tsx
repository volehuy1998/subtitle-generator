/// <reference types="node" />
/**
 * Cross-browser validation tests — Sprint L77
 *
 * Validates browser compatibility patterns: SSE error handling,
 * localStorage fallback, theme system APIs, native HTML elements,
 * and CSS vendor prefix usage.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

// Read source files for static analysis
const readSource = (relPath: string) =>
  fs.readFileSync(path.resolve(__dirname, '../..', relPath), 'utf-8')

describe('L77: Browser compat — SSE hook error handling', () => {
  const sseSource = readSource('hooks/useSSE.ts')

  it('defines onerror handler on EventSource', () => {
    expect(sseSource).toContain('es.onerror')
  })

  it('implements exponential backoff retry logic', () => {
    // Should double the delay on each retry attempt
    expect(sseSource).toContain('retryDelay.current * 2')
    expect(sseSource).toContain('MAX_RETRY')
  })

  it('caps retry delay at MAX_RETRY', () => {
    expect(sseSource).toContain('Math.min(retryDelay.current * 2, MAX_RETRY)')
  })

  it('checks task status before reconnecting', () => {
    // On error, the hook checks if the task finished before reconnecting
    expect(sseSource).toContain('api.progress(taskId)')
  })

  it('handles API call failure in onerror gracefully', () => {
    // The catch block for the progress check should still retry
    expect(sseSource).toContain('.catch(() =>')
  })

  it('implements a watchdog timer for stale connections', () => {
    expect(sseSource).toContain('watchdog')
    expect(sseSource).toContain('45_000')
  })

  it('closes EventSource and timers on cleanup', () => {
    expect(sseSource).toContain('esRef.current?.close()')
    expect(sseSource).toContain('clearTimeout(retryTimer.current)')
    expect(sseSource).toContain('clearInterval(watchdog.current)')
  })
})

describe('L77: Browser compat — localStorage fallback', () => {
  const themeSource = readSource('hooks/useTheme.ts')

  it('checks for window availability before using localStorage', () => {
    // Theme hook checks typeof window === "undefined" for SSR safety
    expect(themeSource).toContain("typeof window === 'undefined'")
  })

  it('provides a default value when localStorage is unavailable', () => {
    // Returns 'system' as fallback when window is undefined
    expect(themeSource).toContain("return 'system'")
  })

  it('wraps localStorage read with OR fallback', () => {
    // Uses || 'system' as fallback
    expect(themeSource).toContain("|| 'system'")
  })

  it('sessionStorage access is wrapped in try-catch', () => {
    // The App.tsx page stores session task count in try-catch
    const appSource = readSource('pages/App.tsx')
    expect(appSource).toContain('sessionStorage')
    expect(appSource).toContain('catch')
  })
})

describe('L77: Browser compat — theme system uses standard APIs', () => {
  const themeSource = readSource('hooks/useTheme.ts')
  const cssSource = readSource('index.css')

  it('uses data-theme attribute for manual theme override', () => {
    expect(themeSource).toContain("setAttribute('data-theme'")
  })

  it('removes data-theme attribute for system mode', () => {
    expect(themeSource).toContain("removeAttribute('data-theme')")
  })

  it('CSS uses prefers-color-scheme media query (standard API)', () => {
    expect(cssSource).toContain('prefers-color-scheme: dark')
  })

  it('CSS uses data-theme attribute selector (standard API)', () => {
    expect(cssSource).toContain('[data-theme="dark"]')
  })

  it('CSS uses :root selector with :not for auto mode', () => {
    expect(cssSource).toContain(':root:not([data-theme="light"])')
  })

  it('theme hook persists choice to localStorage', () => {
    expect(themeSource).toContain("localStorage.setItem('theme'")
  })
})

describe('L77: Browser compat — all interactive elements are native HTML', () => {
  // Verify that components use native <button>, <input>, <select> elements,
  // not div-based clickable elements

  it('Button component renders a <button> element', () => {
    const source = readSource('components/ui/Button.tsx')
    // The component returns a <button> element
    expect(source).toContain('<button')
    // It does not use div onClick as a button substitute
    expect(source).not.toMatch(/<div[^>]*onClick[^>]*role="button"/)
  })

  it('Input component renders a native <input> element', () => {
    const source = readSource('components/ui/Input.tsx')
    expect(source).toContain('<input')
  })

  it('Input component uses <label> with htmlFor', () => {
    const source = readSource('components/ui/Input.tsx')
    expect(source).toContain('htmlFor={inputId}')
  })

  it('Select component renders a native <select> element', () => {
    const source = readSource('components/ui/Select.tsx')
    expect(source).toContain('<select')
    expect(source).toContain('<option')
  })

  it('Select component uses <label> with htmlFor', () => {
    const source = readSource('components/ui/Select.tsx')
    expect(source).toContain('htmlFor={selectId}')
  })

  it('Dialog component uses role="dialog" (not a custom div)', () => {
    const source = readSource('components/ui/Dialog.tsx')
    expect(source).toContain('role="dialog"')
    expect(source).toContain('aria-modal="true"')
  })

  it('TranscribeForm uses native <select> for language dropdown', () => {
    const source = readSource('components/transcribe/TranscribeForm.tsx')
    expect(source).toContain('<select')
    expect(source).toContain('id="language-select"')
  })

  it('TranscribeForm uses role="radiogroup" for device selector', () => {
    const source = readSource('components/transcribe/TranscribeForm.tsx')
    expect(source).toContain('role="radiogroup"')
    expect(source).toContain('role="radio"')
    expect(source).toContain('aria-checked')
  })

  it('DownloadButtons uses role="tablist" for format selector', () => {
    const source = readSource('components/output/DownloadButtons.tsx')
    expect(source).toContain('role="tablist"')
    expect(source).toContain('role="tab"')
    expect(source).toContain('aria-selected')
  })
})

describe('L77: Browser compat — no vendor-prefixed CSS without fallbacks', () => {
  const cssSource = readSource('index.css')

  it('does not use -moz- prefix without standard property', () => {
    // The CSS should not have vendor-prefixed properties without their
    // standard equivalents. We check for common -moz- prefixes.
    const lines = cssSource.split('\n')
    const mozLines = lines.filter((l) => l.includes('-moz-') && !l.includes('/*'))
    // If any -moz- lines exist, they should be paired with standard equivalents
    for (const line of mozLines) {
      // This is a warning-level check; presence alone is not an error
      expect(line).toBeDefined()
    }
    // The current CSS does not use any -moz- prefixes (good)
    expect(mozLines.length).toBe(0)
  })

  it('does not use -ms- prefix without standard property', () => {
    const lines = cssSource.split('\n')
    const msLines = lines.filter((l) => l.includes('-ms-') && !l.includes('/*'))
    expect(msLines.length).toBe(0)
  })

  it('uses -webkit-font-smoothing (acceptable: no standard equivalent)', () => {
    // -webkit-font-smoothing is used intentionally and has no standard equivalent
    expect(cssSource).toContain('-webkit-font-smoothing: antialiased')
  })

  it('uses -webkit-scrollbar selectors (progressive enhancement)', () => {
    // These are progressive enhancement — standard scrollbar-width is also set
    expect(cssSource).toContain('::-webkit-scrollbar')
    expect(cssSource).toContain('scrollbar-width: thin')
  })

  it('does not use -o- prefix (obsolete)', () => {
    const lines = cssSource.split('\n')
    const oLines = lines.filter(
      (l) => /\s-o-/.test(l) && !l.includes('/*'),
    )
    expect(oLines.length).toBe(0)
  })
})
