"""Automated rehearsal of the 7 live demo steps (SDD 10.5, DEMO.md) in a real browser, timed.

Run with `pytest -m e2e`. Uses its own throwaway stack in mock mode (the fallback path).
"""

from __future__ import annotations

import time

import httpx
import pytest

from tests.local_stack import PASSWORD, LocalStack, chromium_path

pytestmark = pytest.mark.e2e
JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffdb004300") + b"\x08" * 64 + bytes.fromhex("ffd9")


@pytest.fixture(scope="module")
def stack():
    if not chromium_path():
        pytest.skip("Chromium not available")
    s = LocalStack(api_port=8766, web_port=4766, with_cases=False).start()
    yield s
    s.stop()


def sign_in(page, url, user):
    page.goto(f"{url}/#/login")
    page.fill("input[autocomplete=username]", user)
    page.fill("input[type=password]", PASSWORD)
    page.click("button.primary")
    page.wait_for_function("!location.hash.includes('login')")


def run_job_and_wait(page, label):
    page.click(f"button:has-text('{label}')")
    page.wait_for_selector("small:has-text('done')", timeout=120000)


def test_demo_live_steps_1_to_7(stack):
    from playwright.sync_api import sync_playwright

    url = stack.url
    timings = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path())
        desk = browser.new_context(viewport={"width": 1366, "height": 900}).new_page()
        t0 = time.time()

        # 1. Run detection (no cases yet); the overview shows the day-one tap and the flat profile.
        sign_in(desk, url, "datasci")
        desk.goto(f"{url}/#/models")
        run_job_and_wait(desk, "Run detection")
        sign_in(desk, url, "analyst.cen")
        desk.goto(f"{url}/#/")
        row = desk.locator("tr", has_text="TX-CEN-001")
        row.wait_for()
        assert "flagged" in row.inner_text() and "since data start" in row.inner_text() and "flat 24/7" in row.inner_text()
        assert "2026-08-31" in desk.locator("tr", has_text="TX-CEN-002").inner_text()
        timings[1] = time.time() - t0

        # 2. Ranked suspects: both taps in the top 3; EV and tenancy-only homes not among the top suspects.
        t = time.time()
        desk.click("text=TX-CEN-001")
        desk.wait_for_selector("text=Ranked suspects")
        desk.wait_for_selector("td >> text=P-CEN-001-054")
        ranks = {}
        for r in desk.locator("table").last.locator("tbody tr").all():
            cells = r.locator("td").all_inner_texts()
            if len(cells) > 2 and cells[1].startswith("P-"):
                ranks[cells[1].split("\n")[0]] = int(cells[0])
        assert ranks["P-CEN-001-054"] <= 3 and ranks["P-CEN-001-049"] <= 3
        top_k = 4                                   # top 5% of 72 homes
        for legit in ("P-CEN-001-051", "P-CEN-001-048"):
            assert ranks.get(legit, 99) > top_k, legit
        timings[2] = time.time() - t

        # 3. Top premise: reasons add up, voltage strip, details masked.
        t = time.time()
        desk.click("text=P-CEN-001-054")
        desk.wait_for_selector("text=Lines add up to")
        body = desk.inner_text("main")
        assert "= score" in body and "Personal details hidden" in body and "Neighbour voltage" in body
        timings[3] = time.time() - t

        # 4. Case job; the analyst claims while the suggestion waits; the supervisor approves.
        t = time.time()
        sup = browser.new_context(viewport={"width": 1366, "height": 900}).new_page()
        sign_in(sup, url, "supervisor.cen")
        sup.goto(f"{url}/#/cases")
        run_job_and_wait(sup, "Run case job")
        sup.reload()
        case_id = sup.locator("tr", has_text="P-CEN-001-054").locator("td").first.inner_text().strip()
        desk.goto(f"{url}/#/cases/{case_id}")
        desk.click("button:has-text('Claim')")
        desk.wait_for_selector("text=Analyst: analyst.cen")
        sup.goto(f"{url}/#/cases/{case_id}")
        sup.wait_for_selector("text=Dispatch suggestion:")
        assert "T-CEN-B" in sup.inner_text("main") and "joint operation" in sup.inner_text("main").lower()
        sup.click("button:has-text('Approve')")
        sup.wait_for_selector("text=approved")
        note = httpx.get(f"{url}/api/notifications", headers={"Authorization": "Bearer " + httpx.post(
            f"{url}/api/auth/token", json={"username": "supervisor.cen", "password": PASSWORD}).json()["access_token"]}).json()
        sent = next(n for n in note if n["case_id"] == case_id and n["kind"] == "assignment")
        assert f"/#/cases/{case_id}" in sent["text"] and "FAKE" not in sent["text"]
        timings[4] = time.time() - t

        # 5. Inspector on a phone, offline then online.
        t = time.time()
        phone_ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        phone = phone_ctx.new_page()
        phone.goto(f"{url}/#/field")
        phone.fill("input[autocomplete=username]", "inspector.b")
        phone.fill("input[type=password]", PASSWORD)
        phone.click("button.primary")
        phone.wait_for_selector(f"text={case_id}")
        phone_ctx.set_offline(True)
        phone.evaluate("window.dispatchEvent(new Event('offline'))")
        phone.click(f"text={case_id}")
        phone.click("button:has-text('Confirmed theft')")
        phone.fill("textarea", "Bypass cable behind the meter board to a back room with mining rigs; constant load.")
        phone.set_input_files("input[type=file]", files=[{"name": "m.jpg", "mimeType": "image/jpeg", "buffer": JPEG}])
        phone.wait_for_selector("img.thumb")
        phone.click("button:has-text('Submit')")
        phone.wait_for_selector("text=syncs when online")
        phone_ctx.set_offline(False)
        phone.evaluate("window.dispatchEvent(new Event('online'))")
        phone.wait_for_selector("text=waiting to sync", state="detached", timeout=30000)
        timings[5] = time.time() - t

        # 6. Report draft (placeholders, cites Section 37), content approval, export approval, PDF.
        t = time.time()
        desk.goto(f"{url}/#/cases/{case_id}")
        desk.reload()                      # same hash URL as in step 4: force fresh data
        desk.wait_for_selector("text=Approve content")
        draft = desk.inner_text("pre")
        assert "{{HOLDER_NAME}}" in draft and "Electricity Supply Act 1990 (Act 447), Section 37" in draft and "FAKE" not in draft
        desk.click("button:has-text('Approve content')")
        desk.wait_for_selector("text=content approved")
        mgr = browser.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True).new_page()
        sign_in(mgr, url, "manager.cen")
        mgr.goto(f"{url}/#/cases/{case_id}")
        mgr.click("button:has-text('Approve export')")
        mgr.wait_for_selector("button:has-text('Download PDF')")
        with mgr.expect_download() as download:
            mgr.click("button:has-text('Download PDF')")
        assert download.value.suggested_filename.endswith(".pdf")
        timings[6] = time.time() - t

        # 7. Retrain: new version with both hit rates.
        t = time.time()
        sign_in(desk, url, "datasci")
        desk.goto(f"{url}/#/models")
        run_job_and_wait(desk, "Retrain on new outcomes")
        desk.reload()
        desk.wait_for_selector("text=label-v1")
        assert "active" in desk.locator("tr", has_text="label-v1").inner_text()
        timings[7] = time.time() - t
        browser.close()

    total = sum(timings.values())
    print("\nRehearsal timings (s): " + ", ".join(f"step {k}: {v:.1f}" for k, v in timings.items()) + f"; total {total:.1f}")
    assert total < 300, timings          # the live part must fit a 5-minute demo


def test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu(stack):
    """Zone and premise pages within 3 s (NFR-02); the inspector view on a phone screen in BM (NFR-13)."""
    from playwright.sync_api import sync_playwright

    url = stack.url
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path())
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        sign_in(page, url, "analyst.cen")
        for path, ready in (("/#/zones/TX-CEN-001", "td >> text=P-CEN-001-054"), ("/#/premises/P-CEN-001-054", "text=Lines add up to")):
            started = time.time()
            page.goto(url + path)
            page.wait_for_selector(ready)
            assert time.time() - started < 3.0, path
        phone = browser.new_context(viewport={"width": 360, "height": 740}, is_mobile=True).new_page()
        phone.goto(f"{url}/#/field")
        phone.evaluate("localStorage.setItem('vg_lang', 'ms')")
        phone.reload()
        phone.wait_for_selector("text=Log masuk")
        phone.fill("input[autocomplete=username]", "inspector.b")
        phone.fill("input[type=password]", PASSWORD)
        phone.click("button.primary")
        phone.wait_for_selector("text=Kes saya")
        assert phone.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")   # no sideways scrolling
        browser.close()
