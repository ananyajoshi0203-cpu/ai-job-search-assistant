"""Official ATS public APIs — the reliable, terms-clean sources.

Greenhouse: https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true
Lever:      https://api.lever.co/v0/postings/<token>?mode=json
Ashby:      https://api.ashbyhq.com/posting-api/job-board/<token>
"""
from __future__ import annotations
from ..models import Job
from .base import SourceAdapter


def _matches(job: Job, profile: dict) -> bool:
    hay = f"{job.role} {job.location}".lower()
    keywords = [k.lower() for k in profile.get("keywords", [])]
    return any(k in hay for k in keywords) if keywords else True


class GreenhouseAdapter(SourceAdapter):
    name = "greenhouse"

    def __init__(self, board_token: str, **kw):
        super().__init__(**kw)
        self.board = board_token

    def search(self, profile: dict) -> list[Job]:
        r = self.get(f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs",
                     params={"content": "true"})
        r.raise_for_status()
        out = []
        for j in r.json().get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            job = Job(company=self.board, role=j.get("title", ""), link=j.get("absolute_url", ""),
                      location=loc, description=j.get("content", "") or "",
                      source=self.name, date_posted=(j.get("updated_at", "") or "")[:10])
            if _matches(job, profile):
                out.append(job)
        return out


class LeverAdapter(SourceAdapter):
    name = "lever"

    def __init__(self, board_token: str, **kw):
        super().__init__(**kw)
        self.board = board_token

    def search(self, profile: dict) -> list[Job]:
        r = self.get(f"https://api.lever.co/v0/postings/{self.board}", params={"mode": "json"})
        r.raise_for_status()
        out = []
        for j in r.json():
            cats = j.get("categories") or {}
            job = Job(company=self.board, role=j.get("text", ""), link=j.get("hostedUrl", ""),
                      location=cats.get("location", ""),
                      description=j.get("descriptionPlain", "") or "",
                      source=self.name)
            if _matches(job, profile):
                out.append(job)
        return out


class AshbyAdapter(SourceAdapter):
    name = "ashby"

    def __init__(self, board_token: str, **kw):
        super().__init__(**kw)
        self.board = board_token

    def search(self, profile: dict) -> list[Job]:
        r = self.get(f"https://api.ashbyhq.com/posting-api/job-board/{self.board}",
                     params={"includeCompensation": "false"})
        r.raise_for_status()
        out = []
        for j in r.json().get("jobs", []):
            job = Job(company=self.board, role=j.get("title", ""), link=j.get("jobUrl", ""),
                      location=j.get("location", "") or "",
                      description=j.get("descriptionText", "") or "",
                      source=self.name,
                      date_posted=(j.get("publishedAt", "") or "")[:10])
            if _matches(job, profile):
                out.append(job)
        return out
