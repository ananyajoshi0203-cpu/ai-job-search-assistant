"""Wellfound adapter — DISABLED BY DEFAULT.

Wellfound (formerly AngelList Talent) restricts automated access in its
terms. This adapter reads Wellfound's public job search pages only, at a
strict rate limit, and stops on any block. Enabling it is your
responsibility — read Wellfound's terms first.
"""
from __future__ import annotations
import urllib.parse
from ..models import Job
from .base import SourceAdapter

SEARCH = "https://wellfound.com/role/{query}"


class WellfoundAdapter(SourceAdapter):
    name = "wellfound"

    def __init__(self, query: str, location: str = "", **kw):
        super().__init__(delay_seconds=5.0, **kw)
        self.query = query
        self.location = location

    def search(self, profile: dict) -> list[Job]:
        from bs4 import BeautifulSoup
        url = SEARCH.format(query=urllib.parse.quote(self.query))
        r = self.get(url)
        if r.status_code in (401, 403, 429):
            return []
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        out, seen = [], set()
        for a in soup.select('a[href^="/l/"], a[href^="/jobs/"], a[href^="/company/"]'):
            href = a.get("href", "")
            text = a.get_text(" ", strip=True)
            if not text or href in seen:
                continue
            if "/jobs/" not in href and "/l/" not in href:
                continue
            seen.add(href)
            out.append(Job(company="", role=text, link="https://wellfound.com" + href,
                           location=self.location, source=self.name))
        return out
