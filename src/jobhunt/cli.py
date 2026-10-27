from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path

from .db import Tracker
from .crawler import load_config, run_crawl, tailor_found


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jobhunt",
                                 description="AI job-search assistant — never submits.")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", default="data/tracker.db")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the SQLite tracker")
    p_crawl = sub.add_parser("crawl", help="Run one crawl (search, dedupe, verify, tailor)")
    p_crawl.add_argument("--max-new", type=int, default=10)
    sub.add_parser("list", help="List tracker rows").add_argument(
        "--status", default=None)
    p_tailor = sub.add_parser(
        "tailor", help="Tailor roles already at Status=Found and move them to Ready to review")
    p_tailor.add_argument("--limit", type=int, default=10)
    sub.add_parser("review", help="Serve the local review page").add_argument(
        "--port", type=int, default=8765)
    p_export = sub.add_parser("export", help="Export tracker to .xlsx")
    p_export.add_argument("--out", default="tracker.xlsx")
    p_skip = sub.add_parser("skip", help="Mark a job Skipped (never shown again)")
    p_skip.add_argument("job_id", type=int)
    p_prefill = sub.add_parser(
        "prefill", help="Pre-fill one application form and STOP before Submit")
    p_prefill.add_argument("--job-id", type=int, required=True)
    p_prefill.add_argument("--answers", required=True,
                           help="JSON file of label -> value; blanks stay blank")

    args = ap.parse_args(argv)
    tracker = Tracker(args.db)

    if args.cmd == "init":
        print(f"Tracker ready at {args.db}")
    elif args.cmd == "crawl":
        config = load_config(args.config)
        stats = run_crawl(config, tracker, max_new=args.max_new)
        ready = stats.pop("ready_jobs", [])
        print(json.dumps(stats, indent=2))
        if ready:
            print(f"{len(ready)} applications are ready for review.")
            for j in ready:
                print(f"- {j.company} — {j.role} — {j.link} — resume: {j.resume_version}")
        elif stats["found_new"] == 0 and stats["closed"] == 0:
            print("No new roles today.")
    elif args.cmd == "tailor":
        config = load_config(args.config)
        stats = tailor_found(config, tracker, limit=args.limit)
        print(json.dumps(stats, indent=2))
        if stats["ready"]:
            print(f"{stats['ready']} applications are ready for review.")
    elif args.cmd == "list":
        for j in tracker.list(status=args.status):
            print(f"[{j.id}] {j.status:16} {j.company} — {j.role} — {j.link}")
    elif args.cmd == "review":
        from .review import serve
        serve(tracker, port=args.port)
    elif args.cmd == "export":
        tracker.export_xlsx(args.out)
        print(f"Exported to {args.out}")
    elif args.cmd == "skip":
        tracker.set_status(args.job_id, "Skipped")
        print(f"Job {args.job_id} marked Skipped.")
    elif args.cmd == "prefill":
        job = tracker.get(args.job_id)
        if not job:
            raise SystemExit(f"No job with id {args.job_id}")
        answers = json.loads(Path(args.answers).read_text())
        from .prefill import fill_application
        fill_application(job.link, answers, resume_path=job.resume_version or None)
    tracker.close()


if __name__ == "__main__":
    main()
