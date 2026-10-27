"""LinkedIn adapter — enabled by default in this project.

LinkedIn's User Agreement prohibits automated scraping. This adapter is
provided for users who choose to enable it for personal, low-volume use of
LinkedIn's *public, logged-out* job search pages. It never logs in, never
bypasses a CAPTCHA or sign-in wall, and backs off immediately on HTTP 429/999.
Enabling it is your responsibility — read LinkedIn's terms first.
"""
from __future__ import annotations
import urllib.parse
from ..models import Job
from .base import SourceAdapter

GUEST_SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


class LinkedInAdapter(SourceAdapter):
    name = "linkedin"

    def __init__(self, query: str, location: str, **kw):
        super().__init__(delay_seconds=5.0, **kw)
        self.query = query
        self.location = location

    def search(self, profile: dict) -> list[Job]:
        from bs4 import BeautifulSoup
        params = {"keywords": self.query, "location": self.location, "start": 0}
        r = self.get(GUEST_SEARCH, params=params)
        if r.status_code in (429, 999):          # rate-limited / blocked: stop, don't push
            return []
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        for card in soup.select("li"):
            a = card.select_one("a.base-card__full-link")
            title = card.select_one(".base-search-card__title")
            company = card.select_one(".base-search-card__subtitle")
            loc = card.select_one(".job-search-card__location")
            if not (a and title):
                continue
            out.append(Job(
                company=company.get_text(strip=True) if company else "",
                role=title.get_text(strip=True),
                link=a["href"].split("?")[0],
                location=loc.get_text(strip=True) if loc else "",
                source=self.name))
        return out
