"""Browser end-to-end test of demo steps 4-5 (SDD 10.5) and the inspector app's device rules (NFR-16).

Run with `pytest -m e2e` (needs Node, the built web app and Chromium). It starts its own local
stack (throwaway PostgreSQL, API, web preview), so it runs separately from the other tests.
"""

from __future__ import annotations

import json

import httpx
import pytest

from tests.local_stack import PASSWORD, LocalStack, chromium_path

pytestmark = pytest.mark.e2e
JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffdb004300") + b"\x08" * 64 + bytes.fromhex("ffd9")

READ_IDB = """async () => {
  const db = await new Promise((res, rej) => { const r = indexedDB.open('voltguard-field', 1); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
  const values = await new Promise((res) => { const t = db.transaction('kv').objectStore('kv').getAll(); t.onsuccess = () => res(t.result); });
  const keys = await new Promise((res) => { const t = db.transaction('kv').objectStore('kv').getAllKeys(); t.onsuccess = () => res(t.result); });
  db.close();
  const text = values.map((v) => { if (!v || !v.data) return ''; try { return new TextDecoder().decode(v.data); } catch (e) { return ''; } }).join(' ');
  return { keys, readable: text, keyType: values.find((v) => v && v.type === 'secret') ? 'CryptoKey' : typeof values[0] };
}"""


@pytest.fixture(scope="module")
def stack():
    if not chromium_path():
        pytest.skip("Chromium not available")
    s = LocalStack(api_port=8765, web_port=4765, with_cases=True).start()
    yield s
    s.stop()


def api_login(stack, user):
    r = httpx.post(f"{stack.url}/api/auth/token", json={"username": user, "password": PASSWORD})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def sign_in(page, url, user):
    page.goto(f"{url}/#/login")
    # With DEMO_MODE on, the role cards come first and the password form opens from a link.
    page.wait_for_selector("input[autocomplete=username], [data-manual-sign-in]")
    if page.locator("[data-manual-sign-in]").count():
        page.click("[data-manual-sign-in]")
    page.fill("input[autocomplete=username]", user)
    page.fill("input[type=password]", PASSWORD)
    page.click("button.primary")
    page.wait_for_function("!location.hash.includes('login')")


def test_demo_steps_4_5_dispatch_claim_offline_outcome_and_wipe(stack):
    from playwright.sync_api import sync_playwright

    url = stack.url
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path())
        desk = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()

        # Step 4: the supervisor approves the dispatch suggestion; the analyst claims the case.
        sign_in(desk, url, "supervisor.cen")
        desk.goto(f"{url}/#/cases")
        desk.click("text=C-2026-0001")
        desk.click("button:has-text('Approve')")
        desk.wait_for_selector("text=approved")
        assert "T-CEN-B" in desk.inner_text("main")
        desk.click("button:has-text('Sign out')")
        sign_in(desk, url, "analyst.cen")
        desk.goto(f"{url}/#/cases/C-2026-0001")
        desk.click("button:has-text('Claim')")
        desk.wait_for_selector(".notice.warn >> text=FAKE")      # details appear only now, on the open case

        # Step 5: the inspector records the outcome on a phone, offline then online.
        phone_ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        phone = phone_ctx.new_page()
        phone.goto(f"{url}/#/field")
        phone.fill("input[autocomplete=username]", "inspector.b")
        phone.fill("input[type=password]", PASSWORD)
        phone.click("button.primary")
        phone.wait_for_selector("text=C-2026-0001")
        stored = phone.evaluate(READ_IDB)
        assert "Jalan" not in stored["readable"] and "FAKE" not in stored["readable"]   # encrypted at rest
        assert {"session", "cases", "__key"} <= set(stored["keys"])

        phone_ctx.set_offline(True)
        phone.evaluate("window.dispatchEvent(new Event('offline'))")
        phone.click("text=C-2026-0001")
        phone.click("button:has-text('Confirmed theft')")
        phone.fill("textarea", "Bypass cable behind the meter board. Owner Encik Ahmad bin Ali, phone 012-345 6789.")
        phone.set_input_files("input[type=file]", files=[{"name": "meter.jpg", "mimeType": "image/jpeg", "buffer": JPEG}])
        phone.wait_for_selector("img.thumb")
        phone.click("button:has-text('Submit')")
        phone.wait_for_selector("text=syncs when online")
        stored = phone.evaluate(READ_IDB)
        assert "queue" in stored["keys"] and any(k.startswith("photo:") for k in stored["keys"])
        assert "Ahmad" not in stored["readable"] and "Bypass" not in stored["readable"]

        phone_ctx.set_offline(False)
        phone.evaluate("window.dispatchEvent(new Event('online'))")
        try:
            phone.wait_for_selector("text=waiting to sync", state="detached", timeout=20000)
        except Exception:
            raise AssertionError("sync did not finish: " + phone.inner_text("body")[:600])
        stored = phone.evaluate(READ_IDB)
        assert "queue" in stored["keys"] and not any(k.startswith("photo:") for k in stored["keys"])   # synced items wiped

        detail = httpx.get(f"{url}/api/cases/C-2026-0001", headers=api_login(stack, "analyst.cen")).json()
        assert detail["case"]["status"] == "reporting"
        assert "Ahmad" not in json.dumps(detail["outcomes"]) and detail["outcomes"][0]["photo_keys"]
        audit = httpx.get(f"{url}/api/audit", params={"action": "case.outcome"}, headers=api_login(stack, "auditor")).json()
        assert any(r["object_ref"] == "case:C-2026-0001" for r in audit["rows"])

        # Lost phone: remote sign-out wipes everything on the next contact.
        assert httpx.post(f"{url}/api/users/inspector.b/sign-out", headers=api_login(stack, "supervisor.cen")).status_code == 200
        phone.click("button:has-text('Sync')")
        phone.wait_for_selector("text=signed out remotely", timeout=20000)
        assert phone.evaluate("indexedDB.databases ? indexedDB.databases().then(d => d.map(x => x.name)) : []") in ([], ["voltguard-field"])
        stored = phone.evaluate(READ_IDB)
        assert not set(stored["keys"]) & {"session", "cases", "queue"}
        browser.close()
