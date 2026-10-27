"""The daily loop, as a pipeline:

  search sources -> dedupe vs tracker (Skipped is forever) -> verify open
  -> add as Found -> tailor truthfully -> draft answers -> Ready to review

Closed postings are recorded as Closed and never tailored.
Nothing in this module submits or sends anything, ever.
"""
from __future__ import annotations
import datetime as dt
from pathlib import Path
import yaml

from .db import Tracker
from .models import Job, slug
from .verify import is_open
from .sources.ats import GreenhouseAdapter, LeverAdapter, AshbyAdapter
from .sources.linkedin import LinkedInAdapter
from .sources.wellfound import WellfoundAdapter
from .sources.jobright import JobrightAdapter


def load_config(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_adapters(config: dict) -> list:
    src = config.get("sources", {}) or {}
    adapters = []
    for token in src.get("greenhouse", []) or []:
        adapters.append(GreenhouseAdapter(token))
    for token in src.get("lever", []) or []:
        adapters.append(LeverAdapter(token))
    for token in src.get("ashby", []) or []:
        adapters.append(AshbyAdapter(token))
    li = src.get("linkedin") or {}
    if li.get("enabled"):
        adapters.append(LinkedInAdapter(li.get("query", ""), li.get("location", "")))
    wf = src.get("wellfound") or {}
    if wf.get("enabled"):
        adapters.append(WellfoundAdapter(wf.get("query", ""), wf.get("location", "")))
    jr = src.get("jobright") or {}
    if jr.get("enabled"):
        adapters.append(JobrightAdapter(jr.get("query", ""), jr.get("location", "")))
    return adapters


def run_crawl(config: dict, tracker: Tracker, today: str | None = None,
              max_new: int = 10) -> dict:
    today = today or dt.date.today().isoformat()
    profile = config.get("profile", {}) or {}
    stats = {"found_new": 0, "ready": 0, "closed": 0, "duplicates": 0, "errors": []}
    skipped = tracker.skipped_keys()
    new_ready: list[Job] = []

    tailor_on = (config.get("tailoring", {}) or {}).get("enabled", False)
    llm = None
    master = ""
    if tailor_on:
        from .tailor import LLMClient, tailor_resume
        from .answers import draft_answers
        llm_cfg = config.get("llm", {}) or {}
        llm = LLMClient(llm_cfg.get("base_url", "https://api.openai.com/v1"),
                        llm_cfg.get("model", "gpt-4o-mini"),
                        llm_cfg.get("api_key_env", "OPENAI_API_KEY"))
        master = Path(profile["master_resume_path"]).read_text()

    for adapter in build_adapters(config):
        try:
            results = adapter.search(profile)
        except Exception as e:                       # one bad source must not kill the run
            stats["errors"].append(f"{adapter.name}: {e}")
            continue
        for job in results:
            if stats["found_new"] >= max_new:
                break
            if job.dedupe_key in skipped or tracker.seen(job):
                stats["duplicates"] += 1
                continue
            job.date_found = today
            open_, reason = is_open(job.link)
            if not open_:
                job.status = "Closed"
                job.notes = f"Closed at crawl: {reason}"
                tracker.add(job)
                stats["closed"] += 1
                continue
            job.status = "Found"
            job.id = tracker.add(job)
            stats["found_new"] += 1
            if tailor_on and llm is not None:
                try:
                    tailored, keywords = tailor_resume(
                        master, job.company, job.role, job.description or job.role, llm)
                    out_dir = Path((config.get("tailoring", {}) or {}).get(
                        "output_dir", "tailored"))
                    out_dir.mkdir(parents=True, exist_ok=True)
                    fname = f"{slug(job.company)}_{slug(job.role)}.md"
                    (out_dir / fname).write_text(tailored)
                    answers = draft_answers(tailored, job.company, job.role, llm)
                    (out_dir / f"{slug(job.company)}_{slug(job.role)}_draft_answers.md"
                     ).write_text(answers)
                    tracker.set_resume(job.id, fname)
                    tracker.append_note(
                        job.id, f"Shared keywords: {', '.join(keywords) or 'none verified'}. "
                                f"Draft answers: {fname.replace('.md', '_draft_answers.md')}")
                    tracker.set_status(job.id, "Ready to review")
                    job.status = "Ready to review"
                    job.resume_version = fname
                    new_ready.append(job)
                    stats["ready"] += 1
                except Exception as e:
                    tracker.append_note(job.id, f"Tailoring failed: {e}")
                    stats["errors"].append(f"tailor {job.company}/{job.role}: {e}")

    if stats["found_new"] == 0 and stats["closed"] == 0:
        tracker.add_run_note(today, "No new roles today")
    stats["ready_jobs"] = new_ready
    return stats


def tailor_found(config: dict, tracker: Tracker, limit: int = 10) -> dict:
    """Tailor roles already sitting at Status=Found (e.g. from a crawl run
    with tailoring off, or before an API key was set). Explicitly invoking
    this command IS the intent to tailor, so it runs regardless of the
    tailoring.enabled flag. Closed postings become Closed, never tailored."""
    from .tailor import LLMClient, tailor_resume
    from .answers import draft_answers
    profile = config.get("profile", {}) or {}
    llm_cfg = config.get("llm", {}) or {}
    llm = LLMClient(llm_cfg.get("base_url", "https://api.openai.com/v1"),
                    llm_cfg.get("model", "gpt-4o-mini"),
                    llm_cfg.get("api_key_env", "OPENAI_API_KEY"))
    master = Path(profile["master_resume_path"]).read_text()
    out_dir = Path((config.get("tailoring", {}) or {}).get("output_dir", "tailored"))
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = {"ready": 0, "closed": 0, "errors": []}
    for job in tracker.list(status="Found")[:limit]:
        open_, reason = is_open(job.link)
        if not open_:
            tracker.set_status(job.id, "Closed")
            tracker.append_note(job.id, f"Closed at tailor: {reason}")
            stats["closed"] += 1
            continue
        try:
            tailored, keywords = tailor_resume(
                master, job.company, job.role, job.description or job.role, llm)
            fname = f"{slug(job.company)}_{slug(job.role)}.md"
            (out_dir / fname).write_text(tailored)
            answers = draft_answers(tailored, job.company, job.role, llm)
            (out_dir / f"{slug(job.company)}_{slug(job.role)}_draft_answers.md"
             ).write_text(answers)
            tracker.set_resume(job.id, fname)
            tracker.append_note(
                job.id, f"Shared keywords: {', '.join(keywords) or 'none verified'}. "
                        f"Draft answers: {fname.replace('.md', '_draft_answers.md')}")
            tracker.set_status(job.id, "Ready to review")
            stats["ready"] += 1
        except Exception as e:
            tracker.append_note(job.id, f"Tailoring failed: {e}")
            stats["errors"].append(f"tailor {job.company}/{job.role}: {e}")
    return stats
