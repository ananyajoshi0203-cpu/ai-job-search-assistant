from __future__ import annotations
import time
import requests
from ..models import Job

USER_AGENT = "ai-job-search-assistant/0.1 (+https://github.com/ananyajoshi0203-cpu/ai-job-search-assistant; personal job search; polite rate limits)"


class SourceAdapter:
    """One job source. Adapters return Job objects; dedupe/verify/tailoring
    happen later in the crawler, never inside an adapter."""
    name = "base"

    def __init__(self, delay_seconds: float = 2.0):
        self.delay = delay_seconds
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def get(self, url: str, **kw) -> requests.Response:
        time.sleep(self.delay)
        return self.session.get(url, timeout=kw.pop("timeout", 30), **kw)

    def search(self, profile: dict) -> list[Job]:  # pragma: no cover
        raise NotImplementedError
