"""Ad-hoc screenshots of a few routes, for checking a page during development.

    python scripts/ui_check.py --out reports/ui/check analyst.cen /premises/P-CEN-001-069 /zones/TX-CEN-001

Uses the same sign-in as scripts/ui_screenshots.py (local stack: one password for every account).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ui_screenshots import SIZES, chromium, sign_in


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("user")
    parser.add_argument("routes", nargs="+")
    parser.add_argument("--base", default="http://127.0.0.1:4173")
    parser.add_argument("--out", default="reports/ui/check")
    parser.add_argument("--password", default="demo-pass-1")
    parser.add_argument("--theme", choices=["light", "dark"], default="dark")
    parser.add_argument("--lang", choices=["en", "ms"], default="en")
    parser.add_argument("--size", choices=list(SIZES), default="desktop")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    w, h = SIZES[args.size]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium())
        ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=args.theme, is_mobile=args.size == "phone")
        ctx.add_init_script(f"try {{ localStorage.setItem('vg_theme', '{args.theme}'); localStorage.setItem('vg_lang', '{args.lang}'); }} catch (e) {{}}")
        page = ctx.new_page()
        sign_in(page, args.base, args.user, args.password)
        for route in args.routes:
            page.goto(f"{args.base}/#{route}")
            page.wait_for_timeout(2500)
            name = route.strip("/").replace("/", "_").replace("?", "_").replace("=", "-") or "home"
            path = out / f"{name}_{args.size}_{args.theme}_{args.lang}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"saved {path}")
        browser.close()


if __name__ == "__main__":
    main()
