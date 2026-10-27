"""Application pre-fill — with a hard stop.

Given a job's apply page and an answers file, this fills the form and then
STOPS. Clicking any submit-type control is refused by design: the forbidden
button list below is checked before every click, and there is intentionally
no code path that submits. The human reviews the filled form and clicks
Submit themselves.

Requires the optional extra:  pip install -e ".[prefill]"  &&  playwright install chromium
"""
from __future__ import annotations
import re

FORBIDDEN_BUTTON_TEXT = re.compile(
    r"submit|apply now$|send application|confirm application", re.I)


def fill_application(apply_url: str, answers: dict[str, str],
                     resume_path: str | None = None,
                     hold_seconds: int = 0):  # pragma: no cover
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("prefill extra not installed: pip install -e '.[prefill]'") from e

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(apply_url)
        for label, value in answers.items():
            if not value:
                continue  # blank means blank — fields not covered stay empty
            loc = page.get_by_label(label, exact=False)
            if loc.count():
                loc.first.fill(value)
        if resume_path:
            file_input = page.locator("input[type=file]").first
            if file_input.count():
                file_input.set_input_files(resume_path)
        # Guard: refuse, loudly, if anything tries to go further.
        for btn in page.locator("button, input[type=submit]").all():
            text = (btn.inner_text() if btn.evaluate("e => e.tagName") == "BUTTON"
                    else btn.get_attribute("value") or "")
            if FORBIDDEN_BUTTON_TEXT.search(text or ""):
                print(f"STOP: filled form is displayed. Final button '{text}' "
                      "was NOT clicked. Review it and submit it yourself.")
        if hold_seconds:
            import time
            print(f"Review the filled form in the browser window — it stays open "
                  f"{hold_seconds} seconds. Nothing was submitted; submit it yourself "
                  "in that window if it looks right.")
            time.sleep(hold_seconds)
        else:
            input("Form filled. Press Enter to close the browser (nothing was submitted). ")
        browser.close()
