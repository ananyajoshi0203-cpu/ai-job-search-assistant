"""Local review page — the open-source version of the chat review list.

Shows every 'Ready to review' role: role name linked to the full job
description, a link to the exact tailored resume for that role, and
[Apply] / [No] buttons under each pair.

- No  -> Status becomes Skipped (never shown again).
- Apply -> records 'Pre-fill requested' in Notes and prints the prefill
  command for you to run. It NEVER submits an application.
"""
from __future__ import annotations
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from .db import Tracker


def render(tracker: Tracker) -> str:
    cards = []
    for j in tracker.list(status="Ready to review"):
        cards.append(f"""
        <div class="card">
          <h3>{html.escape(j.company)} — <a href="{html.escape(j.link)}" target="_blank">{html.escape(j.role)}</a></h3>
          <p>{html.escape(j.location)} · Found {html.escape(j.date_found)} ·
             Resume: <a href="file://{html.escape(j.resume_version)}">{html.escape(j.resume_version)}</a></p>
          <form method="post" action="/decide">
            <input type="hidden" name="id" value="{j.id}">
            <button name="decision" value="apply">[Apply]</button>
            <button name="decision" value="no">[No]</button>
          </form>
          <p class="notes">{html.escape(j.notes)}</p>
        </div>""")
    body = "\n".join(cards) or "<p>No applications ready for review.</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Job Search — Review</title>
<style>body{{font-family:system-ui;max-width:760px;margin:2rem auto}}
.card{{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0}}
.notes{{color:#555;font-size:.9em}}</style></head>
<body><h2>{len(cards)} applications ready for review</h2>{body}</body></html>"""


def serve(tracker: Tracker, port: int = 8765):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            out = render(tracker).encode()
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
            if decision == "no":
                tracker.set_status(job_id, "Skipped")
            elif decision == "apply":
                job = tracker.get(job_id)
                tracker.append_note(
                    job_id,
                    "Pre-fill requested from review page. Run: jobhunt prefill "
                    f"--job-id {job_id}  (fills the form, stops before Submit).")
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, *a):
            pass

    print(f"Review page: http://localhost:{port}  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", port), H).serve_forever()
