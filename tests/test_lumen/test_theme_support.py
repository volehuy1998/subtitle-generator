"""Phase Lumen L29-L32 — Theme support and HTML structure tests.

Validates CSS design tokens, dark mode support, HTML document structure,
and response quality for the served frontend (React SPA or Jinja templates).
— Scout (QA Lead)
"""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")

# Detect which UI is being served
_REACT_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
_IS_REACT = (_REACT_DIST / "index.html").exists()


def _get_css_content() -> str:
    """Get CSS content from external file (React) or inline HTML (Jinja)."""
    res = client.get("/")
    if _IS_REACT:
        match = re.search(r'href="(/assets/[^"]+\.css)"', res.text)
        if match:
            css_res = client.get(match.group(1))
            return css_res.text
    return res.text


def _get_home_html() -> str:
    """Get the home page HTML."""
    return client.get("/").text


# ══════════════════════════════════════════════════════════════════════════════
# CSS VARIABLES / DESIGN TOKENS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not _IS_REACT, reason="CSS variable tests require React SPA build (frontend/dist/)")
class TestCSSVariables:
    """CSS design tokens and theme variables are properly defined."""

    @pytest.fixture(autouse=True)
    def _load_css(self):
        self.css = _get_css_content()

    def test_css_contains_color_bg(self):
        """CSS contains --color-bg custom property."""
        assert "--color-bg" in self.css, "Missing --color-bg CSS variable"

    def test_css_contains_color_primary(self):
        """CSS contains --color-primary custom property."""
        assert "--color-primary" in self.css, "Missing --color-primary CSS variable"

    def test_css_contains_color_text(self):
        """CSS contains --color-text custom property."""
        assert "--color-text" in self.css, "Missing --color-text CSS variable"

    def test_css_references_design_tokens(self):
        """CSS file references design tokens (custom properties with -- prefix)."""
        token_count = len(re.findall(r"--[\w-]+\s*:", self.css))
        assert token_count >= 3, f"Only {token_count} design tokens found — expected at least 3"

    def test_dark_mode_css_block_exists(self):
        """CSS contains a dark mode block (class, attribute, or media query)."""
        has_dark = (
            "dark" in self.css.lower() or "prefers-color-scheme: dark" in self.css or '[data-theme="dark"]' in self.css
        )
        assert has_dark, "No dark mode CSS block found"

    def test_data_theme_attribute_selector(self):
        """CSS contains data-theme attribute selector for theming."""
        assert "data-theme" in self.css, "Missing data-theme attribute selector in CSS"

    def test_font_family_references_inter(self):
        """CSS references the Inter font family."""
        has_inter = "inter" in self.css.lower()
        assert has_inter, "CSS does not reference Inter font"

    def test_css_contains_color_surface(self):
        """CSS contains --color-surface for layered backgrounds."""
        assert "--color-surface" in self.css, "Missing --color-surface CSS variable"

    def test_css_contains_color_white(self):
        """CSS defines --color-white or references white color."""
        has_white = "--color-white" in self.css or "color-white" in self.css
        assert has_white, "Missing white color definition"

    def test_css_has_sufficient_custom_properties(self):
        """CSS defines a meaningful number of custom properties for a design system."""
        props = re.findall(r"--([\w-]+)\s*:", self.css)
        unique_props = set(props)
        assert len(unique_props) >= 5, f"Only {len(unique_props)} unique CSS properties — too few for a design system"

    def test_css_uses_rem_or_em_units(self):
        """CSS uses relative units (rem/em) for scalable typography."""
        has_relative = "rem" in self.css or "em" in self.css
        assert has_relative, "CSS should use rem or em units for scalability"

    def test_css_defines_transition_or_animation(self):
        """CSS includes transitions or animations for interactive feel."""
        has_motion = "transition" in self.css or "animation" in self.css or "@keyframes" in self.css
        assert has_motion, "CSS should include transitions or animations"


# ══════════════════════════════════════════════════════════════════════════════
# HTML STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════


class TestHTMLStructure:
    """HTML document structure follows web standards."""

    @pytest.fixture(autouse=True)
    def _load_html(self):
        self.html = _get_home_html()

    def test_html_has_lang_attribute(self):
        """HTML tag has lang='en' attribute."""
        assert 'lang="en"' in self.html, "HTML tag missing lang='en' attribute"

    def test_html_has_doctype(self):
        """HTML has proper DOCTYPE declaration."""
        assert "<!doctype html>" in self.html.lower() or "<!DOCTYPE html>" in self.html, "Missing DOCTYPE declaration"

    def test_head_contains_charset_meta(self):
        """Head contains charset meta tag."""
        has_charset = 'charset="UTF-8"' in self.html or 'charset="utf-8"' in self.html
        assert has_charset, "Missing charset meta tag"

    def test_head_contains_viewport_meta(self):
        """Head contains viewport meta tag for responsive design."""
        assert "viewport" in self.html, "Missing viewport meta tag"

    def test_body_has_no_inline_dark_colors(self):
        """Body tag does not have inline style with dark background colors."""
        body_match = re.search(r"<body[^>]*>", self.html)
        if body_match:
            body_tag = body_match.group()
            # Body tag should not have hardcoded dark inline styles
            has_dark_inline = re.search(r'style="[^"]*background[^"]*#[0-2][0-2][0-2]', body_tag)
            assert not has_dark_inline, "Body has inline dark background — use CSS classes instead"

    def test_scripts_loaded_from_assets(self):
        """JavaScript files are loaded from /assets/ path."""
        if _IS_REACT:
            js_refs = re.findall(r'src="(/assets/[^"]+\.js)"', self.html)
            assert len(js_refs) > 0, "No JS files loaded from /assets/"
        else:
            pytest.skip("Jinja templates may inline scripts")

    def test_stylesheets_loaded_from_assets(self):
        """CSS files are loaded from /assets/ path."""
        if _IS_REACT:
            css_refs = re.findall(r'href="(/assets/[^"]+\.css)"', self.html)
            assert len(css_refs) > 0, "No CSS files loaded from /assets/"
        else:
            pytest.skip("Jinja templates may inline styles")

    def test_html_has_closing_tags(self):
        """HTML has proper closing head and body tags."""
        assert "</head>" in self.html, "Missing closing </head> tag"
        assert "</body>" in self.html, "Missing closing </body> tag"
        assert "</html>" in self.html, "Missing closing </html> tag"

    def test_head_contains_title_or_meta(self):
        """Head section contains a title tag or relevant meta information."""
        has_title = "<title" in self.html
        has_meta = "<meta" in self.html
        assert has_title or has_meta, "Head missing both title and meta tags"

    def test_no_javascript_errors_in_static_html(self):
        """Static HTML does not contain obvious JS error patterns."""
        # Check for common error patterns that indicate build failures
        error_patterns = ["SyntaxError", "ReferenceError", "TypeError: Cannot"]
        for pattern in error_patterns:
            assert pattern not in self.html, f"HTML contains JS error pattern: {pattern}"


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE QUALITY
# ══════════════════════════════════════════════════════════════════════════════


class TestResponseQuality:
    """Response quality: compression, validity, and integrity."""

    def test_gzip_compression_active(self):
        """Gzip compression is active when client sends Accept-Encoding: gzip."""
        res = client.get("/", headers={"Accept-Encoding": "gzip"})
        encoding = res.headers.get("content-encoding", "")
        assert "gzip" in encoding, f"Expected gzip encoding, got '{encoding}'"

    def test_html_has_closing_tags_valid(self):
        """HTML response has properly matched opening and closing tags."""
        html = _get_home_html()
        assert "</html>" in html, "HTML missing closing </html>"
        assert "<head" in html and "</head>" in html, "Unmatched <head> tag"
        assert "<body" in html and "</body>" in html, "Unmatched <body> tag"

    def test_no_broken_image_references(self):
        """HTML does not contain broken image references (empty src)."""
        html = _get_home_html()
        broken = re.findall(r'<img[^>]*src=""', html)
        assert len(broken) == 0, f"Found {len(broken)} broken image references (empty src)"

    def test_no_mixed_content_references(self):
        """HTML does not mix http and https scheme references."""
        html = _get_home_html()
        # Look for http:// references when serving on https
        http_refs = re.findall(r'(?:src|href)="http://', html)
        # Filter out localhost references which are acceptable in dev
        external_http = [r for r in http_refs if "localhost" not in r and "127.0.0.1" not in r]
        assert len(external_http) == 0, f"Found {len(external_http)} mixed content (http://) references"

    def test_css_file_serves_correct_content_type(self):
        """CSS files are served with text/css content type."""
        html = _get_home_html()
        css_match = re.search(r'href="(/assets/[^"]+\.css)"', html)
        if css_match:
            res = client.get(css_match.group(1))
            ct = res.headers.get("content-type", "")
            assert "css" in ct or "text/" in ct, f"CSS file has wrong content-type: {ct}"
        else:
            pytest.skip("No external CSS file found")
