/**
 * Phase Lumen — Footer component (Sprint L20).
 *
 * Clean, minimal footer with nav links, tagline, and branding.
 * Uses CSS design tokens exclusively — no hardcoded colors.
 * Responsive: stacks on mobile, inline on desktop.
 *
 * — Pixel (Sr. Frontend Engineer)
 */

const footerLinks = [
  { href: '/status', label: 'Status' },
  { href: '/about', label: 'About' },
  { href: '/security', label: 'Security' },
  { href: '/contact', label: 'Contact' },
]

export function Footer() {
  return (
    <footer
      className="w-full mt-8"
      style={{ borderTop: '1px solid var(--color-border)' }}
    >
      <div className="max-w-6xl mx-auto px-3 sm:px-4 py-6 sm:py-8 flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
        {/* Left: branding */}
        <div className="flex flex-col items-center sm:items-start gap-1">
          <span
            className="text-sm font-semibold font-display"
            style={{ color: 'var(--color-text)', letterSpacing: '-0.2px' }}
          >
            SubForge
          </span>
          <span
            className="text-xs"
            style={{ color: 'var(--color-text-3)' }}
          >
            Powered by Whisper &middot; Open Source
          </span>
        </div>

        {/* Center spacer */}
        <div className="flex-1" />

        {/* Nav links */}
        <nav className="flex items-center gap-4 sm:gap-5" aria-label="Footer navigation">
          {footerLinks.map(({ href, label }) => (
            <a
              key={href}
              href={href}
              onClick={(e) => {
                e.preventDefault()
                if (window.location.pathname === href) return
                history.pushState(null, '', href)
                window.dispatchEvent(new Event('spa-navigate'))
              }}
              className="text-xs font-medium transition-colors"
              style={{ color: 'var(--color-text-3)', textDecoration: 'none' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-primary)' }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-text-3)' }}
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
    </footer>
  )
}
