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
from pathlib import Path

FORBIDDEN_BUTTON_TEXT = re.compile(
    r"submit|apply now$|send application|confirm application", re.I)


def upload_resume_path(resume_path: str | None) -> str | None:
    """The uploadable version of a tailored resume: .md becomes .docx
    (forms reject Markdown); anything else passes through unchanged."""
    if not resume_path:
        return None
    p = Path(resume_path)
    if p.suffix.lower() == ".md" and p.exists():
        from .resume_docx import markdown_to_docx
        docx = p.with_suffix(".docx")
        markdown_to_docx(p.read_text(), docx)
        return str(docx)
    return resume_path


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
        page.wait_for_load_state("domcontentloaded")
        # Many boards (Greenhouse included) put the form behind an
        # 'Apply for this job' button or further down the same page.
        # Opening the form is navigation, not submission.
        if not page.locator("input[type=file]").count() and not page.get_by_label(
                "First Name", exact=False).count():
            for sel in ("a:has-text('Apply for this job')",
                        "button:has-text('Apply for this job')",
                        "a:has-text('Apply Now')", "a:has-text('Apply')"):
                loc = page.locator(sel).first
                if loc.count():
                    try:
                        loc.click(timeout=3000)
                        page.wait_for_load_state("domcontentloaded")
                    except Exception:
                        pass
                    break
        for label, value in answers.items():
            if not value:
                continue  # blank means blank — fields not covered stay empty
            loc = page.get_by_label(label, exact=False)
            if loc.count():
                loc.first.fill(value)
        upload = upload_resume_path(resume_path)
        if upload:
            # Prefer the resume upload specifically (a form may also have a
            # cover-letter input); fall back to the first file input.
            target = None
            inputs = page.locator("input[type=file]")
            for i in range(inputs.count()):
                el = inputs.nth(i)
                hint = " ".join([
                    el.get_attribute("id") or "",
                    el.get_attribute("name") or "",
                    el.get_attribute("aria-label") or "",
                    el.get_attribute("accept") or ""]).lower()
                if "resume" in hint or "cv" in hint or "doc" in hint or "pdf" in hint:
                    target = el
                    break
            if target is None and inputs.count():
                target = inputs.first
            if target is not None:
                target.set_input_files(upload)
                print(f"Attached resume: {upload}")
            else:
                print("WARNING: no file upload field found on the form — "
                      "resume was NOT attached.")
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
