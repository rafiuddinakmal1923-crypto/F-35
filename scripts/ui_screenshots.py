"""Screenshots of every web page at desktop (1440x900) and phone (390x844) size.

    python scripts/ui_screenshots.py --base http://127.0.0.1:4173 --out reports/ui/after --password demo-pass-1

Signs in as the test account each page is meant for (local stack: one password for all), finds a
case and a premise through the API, and saves `<page>_desktop.png` and `<page>_phone.png`.
Pages that a build does not have (for example /validation before the UI upgrade) are skipped.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import httpx

# (name, account, hash route); {premise} and {case} are filled in from the API.
PAGES = [
    ("login", None, "/login"),
    ("overview", "manager.cen", "/"),
    ("work", "analyst.cen", "/work"),
    ("zone", "analyst.cen", "/zones/{zone}"),
    ("zone_drawer", "analyst.cen", "/zones/{zone}?premise={premise}"),
    ("premise", "analyst.cen", "/premises/{premise}"),
    ("cases", "supervisor.cen", "/cases"),
    ("case", "supervisor.cen", "/cases/{case}"),
    ("assistant", "manager.cen", "/assistant"),
    ("weekly", "manager.cen", "/weekly"),
    ("dispatch", "supervisor.cen", "/dispatch"),
    ("models", "datasci", "/models"),
    ("validation", "manager.cen", "/validation"),
    ("backtest", "analyst.cen", "/backtest"),
    ("landlord_concept", "manager.cen", "/concept/landlord"),
    ("data_manager", "admin", "/data"),
    ("settings", "admin", "/settings"),
    ("audit", "auditor", "/audit"),
    ("field", "inspector.a", "/field"),
]
SIZES = {"desktop": (1440, 900), "phone": (390, 844)}


def chromium() -> str | None:
    for candidate in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                      r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if Path(candidate).exists():
            return candidate
    return None


def token(base: str, user: str, password: str) -> str:
    r = httpx.post(f"{base}/api/auth/token", json={"username": user, "password": password}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def ids(base: str, password: str) -> dict:
    analyst = {"Authorization": f"Bearer {token(base, 'analyst.cen', password)}"}
    zones = httpx.get(f"{base}/api/zones", headers=analyst, timeout=30).json()["zones"]
    demo = next((z["transformer_id"] for z in zones if z["transformer_id"] == "TX-CEN-001" and z.get("flagged")), None)
    zone = demo or next((z["transformer_id"] for z in zones if z.get("flagged")), zones[0]["transformer_id"])
    suspects = httpx.get(f"{base}/api/zones/{zone}/suspects", headers=analyst, timeout=30).json()["suspects"]
    sup = {"Authorization": f"Bearer {token(base, 'supervisor.cen', password)}"}
    cases = httpx.get(f"{base}/api/cases", headers=sup, timeout=30).json()["cases"]
    case = next((c["case_id"] for c in cases if c.get("premise_id") == suspects[0]["premise_id"]), cases[0]["case_id"] if cases else "C-0000-0000")
    return {"zone": zone, "premise": suspects[0]["premise_id"], "case": case}


def sign_in(page, base: str, user: str, password: str) -> None:
    if user.startswith("inspector"):
        page.goto(f"{base}/#/field")
        page.wait_for_selector("input[autocomplete=username]")
    else:
        page.goto(f"{base}/#/login")
        # The demo role picker may hide the form behind a link; open it when present.
        manual = page.locator("[data-manual-sign-in]")
        if manual.count():
            manual.first.click()
    page.fill("input[autocomplete=username]", user)
    page.fill("input[type=password]", password)
    page.locator("form button[type=submit], form button.primary").first.click()
    if user.startswith("inspector"):
        page.wait_for_selector(".field-tabs, .field nav", timeout=20000)
    else:
        page.wait_for_function("!location.hash.includes('login')", timeout=20000)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:4173")
    parser.add_argument("--out", required=True)
    parser.add_argument("--password", default=os.environ.get("VG_STACK_PASSWORD", "demo-pass-1"))
    parser.add_argument("--theme", choices=["light", "dark"], default="dark")
    parser.add_argument("--lang", choices=["en", "ms"], default="en")
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    known = ids(args.base, args.password)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium())
        for size, (w, h) in SIZES.items():
            for name, user, route in PAGES:
                if args.only and name not in args.only:
                    continue
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=args.theme,
                                          is_mobile=size == "phone", has_touch=size == "phone")
                ctx.add_init_script(f"try {{ localStorage.setItem('vg_theme', '{args.theme}'); localStorage.setItem('vg_lang', '{args.lang}'); }} catch (e) {{}}")
                page = ctx.new_page()
                try:
                    if user:
                        sign_in(page, args.base, user, args.password)
                    page.goto(f"{args.base}/#{route.format(**known)}")
                    page.wait_for_timeout(2500)
                    if user and "login" in page.url and name != "login":
                        print(f"skip {name}: not available")
                        continue
                    if route != "/" and page.url.endswith("#/"):
                        print(f"skip {name}: not in this build")
                        continue
                    page.screenshot(path=str(out / f"{name}_{size}.png"), full_page=True)
                    print(f"saved {name}_{size}.png")
                finally:
                    ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
