"""Jobright adapter — enabled by default in this project.

Jobright restricts automated access in its terms. This adapter reads
Jobright's public search pages only, at a strict rate limit, and stops on
any block. Enabling it is your responsibility — read Jobright's terms first.
"""
from __future__ import annotations
import urllib.parse
from ..models import Job
from .base import SourceAdapter

SEARCH = "https://jobright.ai/jobs/recommend"


class JobrightAdapter(SourceAdapter):
    name = "jobright"

    def __init__(self, query: str, location: str = "", **kw):
        super().__init__(delay_seconds=5.0, **kw)
        self.query = query
        self.location = location

    def search(self, profile: dict) -> list[Job]:
        from bs4 import BeautifulSoup
        r = self.get(SEARCH, params={"query": self.query, "location": self.location})
        if r.status_code in (401, 403, 429):
            return []
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        out, seen = [], set()
        for a in soup.select('a[href*="/jobs/info/"], a[href*="/job/"]'):
            href = a.get("href", "")
            text = a.get_text(" ", strip=True)
            if not text or href in seen:
                continue
            seen.add(href)
            link = href if href.startswith("http") else "https://jobright.ai" + href
            out.append(Job(company="", role=text, link=link,
                           location=self.location, source=self.name))
        return out
