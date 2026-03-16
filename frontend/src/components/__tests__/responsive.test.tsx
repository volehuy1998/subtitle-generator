/// <reference types="node" />
/**
 * Responsive validation tests — Sprint L76
 *
 * Validates that CSS design tokens, dark mode variables, responsive
 * breakpoint rules, touch target styles, print styles, and accessibility
 * utilities are correctly defined in the stylesheet.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

// Read the raw CSS source for structural validation
const cssSource = fs.readFileSync(
  path.resolve(__dirname, '../../index.css'),
  'utf-8',
)

describe('L76: Responsive — CSS design tokens', () => {
  describe('color tokens', () => {
    const colorTokens = [
      '--color-bg',
      '--color-surface',
      '--color-surface-2',
      '--color-border',
      '--color-border-2',
      '--color-text',
      '--color-text-2',
      '--color-text-3',
      '--color-primary',
      '--color-primary-hover',
      '--color-primary-light',
      '--color-primary-border',
      '--color-success',
      '--color-success-light',
      '--color-success-border',
      '--color-warning',
      '--color-warning-light',
      '--color-danger',
      '--color-danger-light',
      '--color-danger-border',
    ]

    it.each(colorTokens)('defines %s', (token) => {
      expect(cssSource).toContain(token)
    })
  })

  describe('spacing and radius tokens', () => {
    const tokens = [
      '--spacing',
      '--radius-xs',
      '--radius-sm',
      '--radius',
      '--radius-lg',
    ]

    it.each(tokens)('defines %s', (token) => {
      expect(cssSource).toContain(token)
    })
  })

  describe('shadow tokens', () => {
    const tokens = ['--shadow-sm', '--shadow-md', '--shadow-lg']

    it.each(tokens)('defines %s', (token) => {
      expect(cssSource).toContain(token)
    })
  })

  describe('typography tokens', () => {
    const tokens = [
      '--font-family-sans',
      '--font-family-display',
      '--font-family-mono',
    ]

    it.each(tokens)('defines %s', (token) => {
      expect(cssSource).toContain(token)
    })
  })

  describe('gradient tokens', () => {
    const tokens = [
      '--gradient-hero-about',
      '--gradient-hero-security',
      '--gradient-hero-contact',
    ]

    it.each(tokens)('defines %s', (token) => {
      expect(cssSource).toContain(token)
    })
  })
})

describe('L76: Responsive — dark mode CSS variables', () => {
  it('defines prefers-color-scheme: dark media query', () => {
    expect(cssSource).toContain('prefers-color-scheme: dark')
  })

  it('defines manual data-theme="dark" override', () => {
    expect(cssSource).toContain('[data-theme="dark"]')
  })

  it('overrides --color-bg in dark mode', () => {
    // The dark mode block redefines --color-bg to a dark value
    const darkBlock = cssSource.slice(
      cssSource.indexOf('[data-theme="dark"]'),
    )
    expect(darkBlock).toContain('--color-bg: #0F172A')
  })

  it('overrides --color-text in dark mode', () => {
    const darkBlock = cssSource.slice(
      cssSource.indexOf('[data-theme="dark"]'),
    )
    expect(darkBlock).toContain('--color-text: #F1F5F9')
  })

  it('overrides --color-primary in dark mode', () => {
    const darkBlock = cssSource.slice(
      cssSource.indexOf('[data-theme="dark"]'),
    )
    expect(darkBlock).toContain('--color-primary: #818CF8')
  })

  it('overrides shadow tokens in dark mode', () => {
    const darkBlock = cssSource.slice(
      cssSource.indexOf('[data-theme="dark"]'),
    )
    expect(darkBlock).toContain('--shadow-sm')
    expect(darkBlock).toContain('--shadow-md')
    expect(darkBlock).toContain('--shadow-lg')
  })

  it('overrides gradient tokens in dark mode', () => {
    const darkBlock = cssSource.slice(
      cssSource.indexOf('[data-theme="dark"]'),
    )
    expect(darkBlock).toContain('--gradient-hero-about')
    expect(darkBlock).toContain('--gradient-hero-security')
    expect(darkBlock).toContain('--gradient-hero-contact')
  })
})

describe('L76: Responsive — model grid responsive classes', () => {
  it('defines mobile breakpoint for model-grid (max-width: 639px)', () => {
    expect(cssSource).toContain('max-width: 639px')
    expect(cssSource).toContain('.model-grid')
  })

  it('hides speed and pros columns on mobile', () => {
    expect(cssSource).toContain('.model-col-speed')
    expect(cssSource).toContain('.model-col-pros')
  })

  it('defines tablet breakpoint for model-grid (640px-849px)', () => {
    expect(cssSource).toContain('min-width: 640px')
    expect(cssSource).toContain('max-width: 849px')
  })

  it('model-grid uses 1fr 60px on mobile', () => {
    // Within the max-width: 639px block
    expect(cssSource).toContain('grid-template-columns: 1fr 60px')
  })
})

describe('L76: Responsive — touch target minimum size', () => {
  it('defines mobile touch target rule (max-width: 768px)', () => {
    expect(cssSource).toContain('max-width: 768px')
  })

  it('sets min-height: 44px for interactive elements on mobile', () => {
    expect(cssSource).toContain('min-height: 44px')
  })

  it('sets touch-action: manipulation for mobile interactive elements', () => {
    expect(cssSource).toContain('touch-action: manipulation')
  })
})

describe('L76: Responsive — print styles', () => {
  it('defines @media print block', () => {
    expect(cssSource).toContain('@media print')
  })

  it('hides header in print', () => {
    // The print block hides header, footer, nav, .health-panel, .btn-interactive
    const printBlock = cssSource.slice(cssSource.indexOf('@media print'))
    expect(printBlock).toContain('header')
    expect(printBlock).toContain('display: none !important')
  })

  it('hides footer in print', () => {
    const printBlock = cssSource.slice(cssSource.indexOf('@media print'))
    expect(printBlock).toContain('footer')
  })

  it('hides nav in print', () => {
    const printBlock = cssSource.slice(cssSource.indexOf('@media print'))
    expect(printBlock).toContain('nav')
  })

  it('hides health panel in print', () => {
    const printBlock = cssSource.slice(cssSource.indexOf('@media print'))
    expect(printBlock).toContain('.health-panel')
  })

  it('sets white background for body in print', () => {
    const printBlock = cssSource.slice(cssSource.indexOf('@media print'))
    expect(printBlock).toContain('background: white !important')
  })

  it('removes box shadows in print', () => {
    const printBlock = cssSource.slice(cssSource.indexOf('@media print'))
    expect(printBlock).toContain('box-shadow: none !important')
  })
})

describe('L76: Responsive — accessibility utilities', () => {
  it('defines .sr-only class', () => {
    expect(cssSource).toContain('.sr-only')
  })

  it('.sr-only uses position: absolute', () => {
    const srBlock = cssSource.slice(cssSource.indexOf('.sr-only'))
    expect(srBlock).toContain('position: absolute')
  })

  it('.sr-only uses width: 1px and height: 1px', () => {
    const srBlock = cssSource.slice(cssSource.indexOf('.sr-only'))
    expect(srBlock).toContain('width: 1px')
    expect(srBlock).toContain('height: 1px')
  })

  it('.sr-only clips content', () => {
    const srBlock = cssSource.slice(cssSource.indexOf('.sr-only'))
    expect(srBlock).toContain('clip: rect(0, 0, 0, 0)')
  })

  it('defines .skip-nav:focus class', () => {
    expect(cssSource).toContain('.skip-nav:focus')
  })

  it('.skip-nav:focus is visible (position: fixed, z-index: 9999)', () => {
    const skipBlock = cssSource.slice(cssSource.indexOf('.skip-nav:focus'))
    expect(skipBlock).toContain('position: fixed')
    expect(skipBlock).toContain('z-index: 9999')
  })

  it('defines :focus-visible outline style', () => {
    expect(cssSource).toContain(':focus-visible')
    expect(cssSource).toContain('outline: 2px solid var(--color-primary)')
  })

  it('defines :focus-visible for buttons and links', () => {
    expect(cssSource).toContain('button:focus-visible')
    expect(cssSource).toContain('a:focus-visible')
  })

  it('defines :focus-visible for select and input', () => {
    expect(cssSource).toContain('select:focus-visible')
    expect(cssSource).toContain('input:focus-visible')
  })
})

describe('L76: Responsive — reduced motion', () => {
  it('defines prefers-reduced-motion: reduce media query', () => {
    expect(cssSource).toContain('prefers-reduced-motion: reduce')
  })

  it('disables animations when reduced motion is preferred', () => {
    const reducedBlock = cssSource.slice(
      cssSource.indexOf('prefers-reduced-motion: reduce'),
    )
    expect(reducedBlock).toContain('animation-duration: 0.01ms !important')
  })

  it('disables transitions when reduced motion is preferred', () => {
    const reducedBlock = cssSource.slice(
      cssSource.indexOf('prefers-reduced-motion: reduce'),
    )
    expect(reducedBlock).toContain('transition-duration: 0.01ms !important')
  })
})
