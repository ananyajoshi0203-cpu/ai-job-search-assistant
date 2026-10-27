from jobhunt.db import Tracker
from jobhunt.models import Job
from jobhunt.review import render


def test_render_shows_ready_card_and_counters(tmp_path):
    t = Tracker(tmp_path / "t.db")
    jid = t.add(Job(company="Acme", role="ML Engineer",
                    link="https://example.com/job/1", date_found="2026-10-27"))
    t.set_status(jid, "Ready to review")
    page = render(t)
    assert "Acme" in page and "ML Engineer" in page
    assert 'value="apply"' in page and 'value="no"' in page
    assert "Ready to review <b>1</b>" in page
    t.close()


def test_render_empty_state(tmp_path):
    t = Tracker(tmp_path / "t.db")
    assert "No applications ready for review." in render(t)
    t.close()
