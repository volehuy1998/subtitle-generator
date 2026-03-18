/**
 * Footer — Drop, See, Refine minimal site footer.
 *
 * Renders a full-width footer with copyright on the left and nav links
 * on the right. Uses navigate() for SPA-safe link handling.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { navigate } from '../../navigation'

const currentYear = new Date().getFullYear()

export function Footer() {
  return (
    <footer data-testid="footer" className="border-t border-[--color-border] bg-[--color-surface] mt-auto">
      <div className="max-w-[1280px] mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-xs text-[--color-text-muted]">
          &copy; {currentYear} SubForge. Open source subtitle generation.
        </p>
        <nav className="flex items-center gap-4" aria-label="Footer navigation">
          {[
            { href: '/about', label: 'About' },
            { href: '/status', label: 'Status' },
            { href: '/security', label: 'Security' },
            { href: '/contact', label: 'Contact' },
          ].map(({ href, label }) => (
            <button
              key={href}
              onClick={() => navigate(href)}
              className="text-xs text-[--color-text-muted] hover:text-[--color-text] transition-colors"
            >
              {label}
            </button>
          ))}
        </nav>
      </div>
    </footer>
  )
}
