from __future__ import annotations
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

# Query params that never change which job a URL points to.
_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                    "utm_content", "ref", "source", "gh_src"}


def canonical_link(url: str) -> str:
    """Normalize a job URL for dedupe: lowercase host, drop tracking params
    and fragments, strip trailing slash."""
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query)
                       if k.lower() not in _TRACKING_PARAMS])
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


@dataclass
class Job:
    company: str
    role: str
    link: str
    location: str = ""
    description: str = ""
    source: str = ""
    date_posted: str = ""          # "" = not verified, never invented
    id: int | None = None
    date_found: str = ""
    date_applied: str = ""
    status: str = "Found"
    resume_version: str = ""
    recruiter_contact: str = ""
    outreach_channel: str = ""
    next_follow_up: str = ""
    interview_dates: str = ""
    notes: str = ""

    @property
    def dedupe_key(self) -> str:
        return canonical_link(self.link)
