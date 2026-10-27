"""HTML -> PDF for approved case reports (FR-UI-05): Playwright (Chromium) with an fpdf2 fallback."""

from __future__ import annotations

import html
import logging
import os
from pathlib import Path

log = logging.getLogger("voltguard.pdf")


def _chromium() -> str | None:
    explicit = os.environ.get("PLAYWRIGHT_CHROMIUM")
    if explicit and Path(explicit).exists():
        return explicit
    found = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux64/chrome")) if Path("/opt/pw-browsers").exists() else []
    return str(found[-1]) if found else None


def html_to_pdf(document: str) -> tuple[bytes, str]:
    """Returns (pdf bytes, engine). Playwright first; fpdf2 text rendering if no browser is available."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception:
                path = _chromium()
                if not path:
                    raise
                browser = p.chromium.launch(executable_path=path)
            page = browser.new_page()
            page.set_content(document, wait_until="load")
            data = page.pdf(format="A4", print_background=True, margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
            browser.close()
            return data, "playwright"
    except Exception as exc:  # no browser on this machine: plain text PDF rather than no PDF
        log.warning("Playwright PDF failed (%s); using fpdf2", exc.__class__.__name__)
        return _fpdf(document), "fpdf2"


def _fpdf(document: str) -> bytes:
    import re

    from fpdf import FPDF

    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", document, flags=re.S)
    text = re.sub(r"<svg.*?</svg>", "[chart]", text, flags=re.S)
    text = re.sub(r"<br\s*/?>|</p>|</h\d>|</li>|</tr>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in text.splitlines():
        pdf.multi_cell(0, 5, line.encode("latin-1", "replace").decode("latin-1"))
    return bytes(pdf.output())
