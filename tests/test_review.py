from jobhunt.db import Tracker
from jobhunt.models import Job
from jobhunt.review import render, render_list


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



def test_serve_routes(tmp_path):
    import threading, time, urllib.request
    from jobhunt.review import serve
    t = Tracker(tmp_path / "t.db")
    t.add(Job(company="Acme", role="ML Engineer", link="https://example.com/1",
              date_found="2026-10-27"))
    port = 8799
    th = threading.Thread(target=serve, args=(t,), kwargs={"port": port}, daemon=True)
    th.start()
    time.sleep(0.5)
    lst = urllib.request.urlopen(f"http://127.0.0.1:{port}/list").read().decode()
    assert "Acme" in lst
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/export") as r:
        assert "spreadsheetml" in r.headers["Content-Type"]
        assert len(r.read()) > 100
    home = urllib.request.urlopen(f"http://127.0.0.1:{port}/").read().decode()
    assert 'action="/run"' in home
    t.close()


def test_mark_applied_button_and_status(tmp_path):
    t = Tracker(tmp_path / "t.db")
    jid = t.add(Job(company="Acme", role="ML Engineer", link="https://example.com/1"))
    t.set_status(jid, "Ready to review")
    assert 'value="applied"' in render(t) and "Mark as Applied" in render(t)
    t.mark_applied(jid, "2026-10-27")
    j = t.get(jid)
    assert j.status == "Applied" and j.date_applied == "2026-10-27"
    t.close()


def test_resume_viewer_and_approve(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "tailored"
    out.mkdir()
    (out / "acme_ml-engineer.md").write_text("# ALEX RIVERA\nPython, RAG, LangChain.")
    (out / "acme_ml-engineer_draft_answers.md").write_text("Name: Alex Rivera")
    t = Tracker(tmp_path / "t.db")
    jid = t.add(Job(company="Acme", role="ML Engineer", link="https://example.com/1"))
    t.set_status(jid, "Ready to review")
    t.set_resume(jid, "acme_ml-engineer.md")
    page = render(t)
    assert f'href="/resume?id={jid}"' in page
    assert 'href="/list?status=Applied"' in page
    job = t.get(jid)
    from jobhunt.review import resume_files, render_resume
    rpath, apath = resume_files({"tailoring": {"output_dir": "tailored"}}, job)
    view = render_resume(t, job, rpath.read_text(), apath.read_text())
    assert "ALEX RIVERA" in view and "Approve this resume" in view
    t.set_resume_approved(jid)
    assert "Resume approved" in render(t)
    t.close()
