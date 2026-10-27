"""Verify a posting is still open before anyone tailors anything for it."""
from __future__ import annotations
import requests
from .sources.base import USER_AGENT

CLOSED_MARKERS = (
    "no longer accepting applications", "this job is closed", "position has been filled",
    "job posting has expired", "this position is no longer available",
    "applications are closed", "job not found",
)


def is_open(link: str, timeout: int = 30) -> tuple[bool, str]:
    """Return (open?, reason). A dead page or an explicit closed marker
    counts as closed; anything ambiguous counts as open with a note."""
    try:
        r = requests.get(link, timeout=timeout, headers={"User-Agent": USER_AGENT},
                         allow_redirects=True)
    except requests.RequestException as e:
        return False, f"unreachable ({e.__class__.__name__})"
    if r.status_code in (404, 410):
        return False, f"HTTP {r.status_code}"
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code}"
    text = r.text.lower()
    for marker in CLOSED_MARKERS:
        if marker in text:
            return False, f"closed marker: '{marker}'"
    return True, "page loads, no closed marker"
