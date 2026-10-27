"""Local review page — the open-source version of the chat review list.

Shows every 'Ready to review' role as a card: role name linked to the full
job description, a link to the exact tailored resume for that role, live
counters, and [Apply] / [No] buttons under each pair.

- No  -> Status becomes Skipped (never shown again).
- Apply -> records 'Pre-fill requested' in Notes. It NEVER submits an
  application; it tells you the prefill command to run yourself.
"""
from __future__ import annotations
import html
import os
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse, quote
from .db import Tracker

CSS = """
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, sans-serif; margin: 0;
       background: #f6f7f9; color: #1a1d21; }
.wrap { max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }
header h1 { font-size: 22px; margin: 0 0 4px; }
header p { color: #5b6470; margin: 0 0 16px; font-size: 14px; }
.counters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.chip { background: #fff; border: 1px solid #dfe3e8; border-radius: 999px;
        padding: 6px 12px; font-size: 13px; }
.chip b { font-size: 15px; }
.chip.ready { border-color: #2f7d4f; color: #2f7d4f; }
.toast { background: #e8f5ec; border: 1px solid #2f7d4f; color: #205c39;
         border-radius: 10px; padding: 10px 14px; margin-bottom: 16px;
         font-size: 14px; }
.card { background: #fff; border: 1px solid #dfe3e8; border-radius: 12px;
        padding: 16px; margin: 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
.card h3 { margin: 0 0 6px; font-size: 17px; }
.card h3 a { color: #0b5cad; text-decoration: none; }
.card h3 a:hover { text-decoration: underline; }
.meta { color: #5b6470; font-size: 13px; margin: 0 0 10px; }
.meta a { color: #0b5cad; }
.pill { display: inline-block; background: #fff4d6; color: #7a5b00;
        border: 1px solid #e5cf8a; border-radius: 999px; padding: 1px 8px;
        font-size: 12px; margin-left: 6px; }
.actions { display: flex; gap: 8px; margin-top: 10px; }
button { font-size: 14px; border-radius: 8px; padding: 8px 16px; cursor: pointer;
         border: 1px solid transparent; }
button.apply { background: #2f7d4f; color: #fff; }
button.no { background: #fff; border-color: #c3cBD2; color: #444; }
.notes { color: #5b6470; font-size: 13px; margin: 10px 0 0; white-space: pre-wrap; }
.empty { background: #fff; border: 1px dashed #c3cbd2; border-radius: 12px;
         padding: 24px; text-align: center; color: #5b6470; }
.toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.toolbar form { margin: 0; }
button.tool, a.tool { font-size: 14px; border-radius: 8px; padding: 8px 14px;
        cursor: pointer; border: 1px solid #c3cbd2; background: #fff; color: #1a1d21;
        text-decoration: none; display: inline-block; }
button.tool.primary { background: #0b5cad; border-color: #0b5cad; color: #fff; }
.row { background: #fff; border: 1px solid #dfe3e8; border-radius: 10px;
       padding: 10px 14px; margin: 8px 0; font-size: 14px; }
.row a { color: #0b5cad; text-decoration: none; }
.row .meta { margin: 2px 0 0; }
.pill.found { background: #e8eef7; color: #0b5cad; border-color: #b9cfea; }
.pill.ready { background: #fff4d6; color: #7a5b00; border-color: #e5cf8a; }
.pill.applied { background: #e8f5ec; color: #205c39; border-color: #9fd3ae; }
.pill.skipped { background: #f3e8e8; color: #8a3030; border-color: #dfb3b3; }
.pill.closed { background: #eceff1; color: #546e7a; border-color: #c3cbd2; }
@media (prefers-color-scheme: dark) {
  body { background: #14171a; color: #e8eaed; }
  .card, .chip, .empty, button.no, .row, button.tool, a.tool { background: #1d2126; border-color: #333a42; color: #e8eaed; }
  button.tool.primary { background: #0b5cad; color: #fff; }
  .meta, .notes, header p, .empty { color: #9aa4ae; }
  .card h3 a, .meta a { color: #6cb2f5; }
}
"""


TOOLBAR = """
<div class="toolbar">
  <form method="post" action="/run"><button class="tool primary" name="action" value="crawl">Run crawl</button></form>
  <form method="post" action="/run"><button class="tool" name="action" value="tailor">Tailor Found roles</button></form>
  <a class="tool" href="/list">All roles</a>
  <a class="tool" href="/export">Export .xlsx</a>
  <a class="tool" href="/">Review</a>
</div>"""


def _page(title: str, inner: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{CSS}</style></head>
<body><div class="wrap">{TOOLBAR}{inner}</div></body></html>"""


def render_list(tracker: Tracker, status: str | None = None) -> str:
    jobs = tracker.list(status=status)
    filters = "".join(
        f'<a class="tool" href="/list?status={quote(s)}">{s}</a>' if s != status
        else f'<span class="chip"><b>{s}</b></span>'
        for s in ("Found", "Ready to review", "Applied", "Skipped", "Closed"))
    rows = []
    pill_class = {"Found": "found", "Ready to review": "ready", "Applied": "applied",
                  "Skipped": "skipped", "Closed": "closed"}
    for j in jobs:
        rows.append(f"""
        <div class="row"><b>{html.escape(j.company)}</b> —
          <a href="{html.escape(j.link)}" target="_blank" rel="noopener">{html.escape(j.role)}</a>
          <span class="pill {pill_class.get(j.status, 'found')}">{html.escape(j.status)}</span>
          <p class="meta">{html.escape(j.location)} · Found {html.escape(j.date_found)} ·
          Resume: {html.escape(j.resume_version or '—')}</p></div>""")
    body = "\n".join(rows) or '<div class="empty">No roles with this status.</div>'
    inner = (f"<header><h1>All roles</h1><p>{len(jobs)} shown. "
             f"Filter:</p></header><div class='toolbar'>{filters}</div>{body}")
    return _page("Job Search — All roles", inner)


def render(tracker: Tracker, msg: str = "") -> str:
    all_jobs = tracker.list()
    counts = {s: sum(1 for j in all_jobs if j.status == s)
              for s in ("Ready to review", "Applied", "Skipped", "Found", "Closed")}
    ready = [j for j in all_jobs if j.status == "Ready to review"]
    chips = (f'<span class="chip ready">Ready to review <b>{counts["Ready to review"]}</b></span>'
             f'<span class="chip">Applied <b>{counts["Applied"]}</b></span>'
             f'<span class="chip">Skipped <b>{counts["Skipped"]}</b></span>'
             f'<span class="chip">Found <b>{counts["Found"]}</b></span>'
             f'<span class="chip">Closed <b>{counts["Closed"]}</b></span>')
    toast = f'<div class="toast">{html.escape(msg)}</div>' if msg else ""
    cards = []
    for j in ready:
        cards.append(f"""
        <div class="card">
          <h3>{html.escape(j.company)} — <a href="{html.escape(j.link)}" target="_blank" rel="noopener">{html.escape(j.role)}</a><span class="pill">Ready to review</span></h3>
          <p class="meta">{html.escape(j.location)} · Found {html.escape(j.date_found)} ·
             Resume: <a href="file://{html.escape(j.resume_version)}">{html.escape(j.resume_version)}</a></p>
          <form method="post" action="/decide" class="actions">
            <input type="hidden" name="id" value="{j.id}">
            <button class="apply" name="decision" value="apply">Apply</button>
            <button class="no" name="decision" value="no">No</button>
          </form>
          <p class="notes">{html.escape(j.notes)}</p>
        </div>""")
    body = "\n".join(cards) or '<div class="empty">No applications ready for review.</div>'
    inner = f"""
<header><h1>Applications ready for review</h1>
<p>Apply pre-fills the form and stops before Submit. No marks a role Skipped — it never comes back.</p></header>
<div class="counters">{chips}</div>{toast}{body}"""
    return _page("Job Search — Review", inner)


def serve(tracker: Tracker, port: int = 8765):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            msg = parse_qs(urlparse(self.path).query).get("msg", [""])[0]
            out = render(tracker, msg=msg).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            form = parse_qs(self.rfile.read(length).decode())
            job_id = int(form["id"][0])
            decision = form["decision"][0]
            msg = ""
            if decision == "no":
                tracker.set_status(job_id, "Skipped")
                msg = "Marked Skipped — it will never be shown again."
            elif decision == "apply":
                job = tracker.get(job_id)
                tracker.append_note(
                    job_id,
                    "Pre-fill requested from review page. Run: jobhunt prefill "
                    f"--job-id {job_id}  (fills the form, stops before Submit).")
                msg = (f"Apply noted for {job.company} — {job.role}. "
                       f"Run: jobhunt prefill --job-id {job_id} (stops before Submit).")
            self.send_response(303)
            self.send_header("Location", "/?msg=" + quote(msg))
            self.end_headers()

        def log_message(self, *a):
            pass

    print(f"Review page: http://localhost:{port}  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", port), H).serve_forever()
