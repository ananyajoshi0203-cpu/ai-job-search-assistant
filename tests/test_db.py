from jobhunt.db import Tracker
from jobhunt.models import Job


def make_job(**kw):
    base = dict(company="Acme", role="ML Engineer",
                link="https://boards.greenhouse.io/acme/jobs/123?utm_source=x")
    base.update(kw)
    return Job(**base)


def test_dedupe_ignores_tracking_params(tmp_path):
    t = Tracker(tmp_path / "t.db")
    t.add(make_job())
    dupe = make_job(link="https://boards.greenhouse.io/acme/jobs/123?utm_source=other")
    assert t.seen(dupe)
    t.close()


def test_skip_is_terminal_and_listed(tmp_path):
    t = Tracker(tmp_path / "t.db")
    jid = t.add(make_job())
    t.set_status(jid, "Skipped")
    assert make_job().dedupe_key in t.skipped_keys()
    assert [j.id for j in t.list(status="Skipped")] == [jid]
    t.close()


def test_run_note(tmp_path):
    t = Tracker(tmp_path / "t.db")
    t.add_run_note("2026-10-27", "No new roles today")
    rows = t.conn.execute("SELECT note FROM run_notes").fetchall()
    assert rows[0]["note"] == "No new roles today"
    t.close()


def test_resume_approved_flag(tmp_path):
    t = Tracker(tmp_path / "t.db")
    jid = t.add(make_job())
    assert t.get(jid).resume_approved is False
    t.set_resume_approved(jid)
    assert t.get(jid).resume_approved is True
    t.close()
