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


def test_toolbar_and_list_view(tmp_path):
    t = Tracker(tmp_path / "t.db")
    t.add(Job(company="Acme", role="ML Engineer", link="https://example.com/1",
              date_found="2026-10-27"))
    page = render(t)
    assert 'action="/run"' in page and 'href="/export"' in page and 'href="/list"' in page
    lst = render_list(t)
    assert "Acme" in lst and "ML Engineer" in lst and "Found" in lst
    assert "No roles with this status." in render_list(t, status="Applied")
    t.close()
