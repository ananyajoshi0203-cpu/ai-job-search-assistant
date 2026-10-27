"""SQLite tracker — the single source of truth.

Mirrors the spreadsheet columns of the original workflow:
Company | Role | Job link | Date found | Date applied | Status |
Resume version used | Recruiter / contact | Outreach channel |
Next follow-up date | Interview dates | Notes
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .models import Job, canonical_link

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company TEXT NOT NULL,
  role TEXT NOT NULL,
  link TEXT NOT NULL,
  dedupe_key TEXT NOT NULL UNIQUE,
  location TEXT DEFAULT '',
  source TEXT DEFAULT '',
  date_posted TEXT DEFAULT '',
  date_found TEXT DEFAULT '',
  date_applied TEXT DEFAULT '',
  status TEXT DEFAULT 'Found',
  resume_version TEXT DEFAULT '',
  recruiter_contact TEXT DEFAULT '',
  outreach_channel TEXT DEFAULT '',
  next_follow_up TEXT DEFAULT '',
  interview_dates TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  description TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS run_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_date TEXT NOT NULL,
  note TEXT NOT NULL
);
"""

STATUSES = {"Found", "Ready to review", "Applied", "Skipped", "Closed"}


class Tracker:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)  # the local review server may serve from another thread
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    # -- dedupe ---------------------------------------------------------
    def seen(self, job: Job) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM jobs WHERE dedupe_key = ?", (job.dedupe_key,)).fetchone()
        return row is not None

    def skipped_keys(self) -> set[str]:
        return {r["dedupe_key"] for r in self.conn.execute(
            "SELECT dedupe_key FROM jobs WHERE status = 'Skipped'")}

    # -- writes ----------------------------------------------------------
    def add(self, job: Job) -> int:
        cur = self.conn.execute(
            """INSERT INTO jobs (company, role, link, dedupe_key, location, source,
               date_posted, date_found, status, notes, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job.company, job.role, job.link, job.dedupe_key, job.location,
             job.source, job.date_posted, job.date_found, job.status,
             job.notes, job.description))
        self.conn.commit()
        return int(cur.lastrowid)

    def set_status(self, job_id: int, status: str):
        assert status in STATUSES, status
        self.conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        self.conn.commit()

    def set_resume(self, job_id: int, resume_version: str):
        self.conn.execute(
            "UPDATE jobs SET resume_version = ? WHERE id = ?", (resume_version, job_id))
        self.conn.commit()

    def append_note(self, job_id: int, note: str):
        row = self.conn.execute("SELECT notes FROM jobs WHERE id = ?", (job_id,)).fetchone()
        notes = (row["notes"] + " " + note).strip() if row else note
        self.conn.execute("UPDATE jobs SET notes = ? WHERE id = ?", (notes, job_id))
        self.conn.commit()

    def add_run_note(self, run_date: str, note: str):
        self.conn.execute("INSERT INTO run_notes (run_date, note) VALUES (?, ?)",
                          (run_date, note))
        self.conn.commit()

    # -- reads -----------------------------------------------------------
    def _row_to_job(self, r: sqlite3.Row) -> Job:
        job = Job(company=r["company"], role=r["role"], link=r["link"],
                  location=r["location"], source=r["source"],
                  date_posted=r["date_posted"], description=r["description"])
        job.id = r["id"]
        job.date_found = r["date_found"]
        job.date_applied = r["date_applied"]
        job.status = r["status"]
        job.resume_version = r["resume_version"]
        job.recruiter_contact = r["recruiter_contact"]
        job.outreach_channel = r["outreach_channel"]
        job.next_follow_up = r["next_follow_up"]
        job.interview_dates = r["interview_dates"]
        job.notes = r["notes"]
        return job

    def list(self, status: str | None = None) -> list[Job]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY id", (status,))
        else:
            rows = self.conn.execute("SELECT * FROM jobs ORDER BY id")
        return [self._row_to_job(r) for r in rows]

    def get(self, job_id: int) -> Job | None:
        r = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(r) if r else None

    # -- export ------------------------------------------------------------
    def export_xlsx(self, out_path: str | Path):
        """Export to the spreadsheet layout of the original workflow."""
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Job Tracker"
        headers = ["Company", "Role", "Job link", "Date found", "Date applied",
                   "Status", "Resume version used", "Recruiter / contact",
                   "Outreach channel", "Next follow-up date", "Interview dates", "Notes"]
        ws.append(headers)
        for j in self.list():
            ws.append([j.company, j.role, j.link, j.date_found, j.date_applied,
                       j.status, j.resume_version, j.recruiter_contact,
                       j.outreach_channel, j.next_follow_up, j.interview_dates, j.notes])
        wb.save(out_path)
