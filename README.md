# AI Job Search Assistant

An open-source job-search assistant that does the daily grind — and refuses to cross the two lines that matter:

1. **It never invents anything.** Resume tailoring uses a job description's keywords *only* where your master resume already shows that skill or experience. Every tailored output passes a programmatic no-invention check.
2. **It never submits anything.** It can pre-fill an application form for you — then it stops, with the filled form on screen, before the employer's Submit button. You review, you click.

Built from a real daily workflow (originally a conference-demo assistant for students), rebuilt as a standalone tool anyone can run with their own resume and their own AI API key.

## What it does, every run

1. **Crawls** your configured sources for roles matching your profile
2. **Dedupes** against your tracker (SQLite) — a role you've marked *Skipped* is never shown again
3. **Verifies** each new posting is still open — closed/filled postings are recorded as `Closed` and never tailored
4. **Adds** new open roles to the tracker as `Found`
5. **Tailors** your resume per role (own file per role, master never overwritten) and drafts application answers from the tailored resume only → status becomes `Ready to review`
6. **Reviews with you**: a local page lists ready applications — role name linked to the full job description, the exact tailored resume next to it, and **[Apply] / [No]** buttons under each pair. *No* = Skipped forever. *Apply* = pre-fill, stop before Submit.
7. **Exports** the tracker to the familiar spreadsheet layout (`.xlsx`) any time

Statuses: `Found` → `Ready to review` → `Applied` · `Skipped` · `Closed`

## Sources

| Source | How | Default |
|---|---|---|
| Greenhouse, Lever, Ashby | Official public ATS APIs — add board tokens in config | On (ATS) |
| LinkedIn | Public logged-out job search pages | On |
| Wellfound | Public search pages | On |
| Jobright | Public search pages | On |

> ⚠️ LinkedIn, Wellfound and Jobright restrict automated access in their Terms of Service. Their adapters are **enabled by default** in this project and use public pages only (no login, no CAPTCHA bypass), rate-limit strictly, and stop on blocks. Using them is your decision and your responsibility — set `enabled: false` in config for any you don't want. The ATS APIs are the most reliable path.

## Quick start

You need Python 3.10+ (check with `python3 --version`; if it's missing, install it from [python.org/downloads](https://www.python.org/downloads/)).

```bash
git clone https://github.com/ananyajoshi0203-cpu/ai-job-search-assistant.git
cd ai-job-search-assistant

python3 -m venv .venv
source .venv/bin/activate               # Windows: .venv\Scripts\activate
python -m pip install -e .

cp config.example.yaml config.yaml     # edit: your profile, roles, locations, ATS boards
export OPENAI_API_KEY=...               # your own key, any OpenAI-compatible endpoint

jobhunt init                            # create the SQLite tracker (data/tracker.db)
jobhunt crawl                           # one full run
jobhunt tailor                          # only if you crawled before setting a key (see below)
jobhunt review                          # local review page at http://localhost:8765
jobhunt export --out tracker.xlsx       # spreadsheet export
```

**One config, one database — for every command.** All commands share two
global flags, which go BEFORE the subcommand: `--config` (default
`config.yaml`) and `--db` (default `data/tracker.db`). If you crawl with
non-default flags, every later command needs the *same* flags, or it will
look at a different (or nonexistent) tracker. Skipping `--config` when you
never created `config.yaml` gives `FileNotFoundError: 'config.yaml'`.

**Crawled first, key later?** If a crawl ran with tailoring off or before
you set `OPENAI_API_KEY`, your roles sit at `Found`. Don't re-crawl (known
roles are skipped as duplicates) — run `jobhunt tailor` with the same
flags instead. It re-checks each Found role is still open, tailors it, and
moves it to `Ready to review`.

**Try the sample profile first** (fictional data, same flag pair throughout):

```bash
jobhunt --config sample/sample_config.yaml --db data/demo.db crawl
export OPENAI_API_KEY=...               # needed for the tailor step
jobhunt --config sample/sample_config.yaml --db data/demo.db tailor
jobhunt --db data/demo.db review
```

Notes that save everyone time:

- The command is **`jobhunt`** — one word, no space.
- **Every new terminal window** needs `source .venv/bin/activate` again (your prompt shows `(.venv)` when it's active). Skip it and you'll get `command not found: jobhunt`.
- Never call bare `pip` — on macOS it often doesn't exist. Always `python -m pip` inside the venv (or `python3 -m pip` outside it). The venv also avoids macOS's `externally-managed-environment` error.
- No entry point? Run the module directly from the repo folder: `PYTHONPATH=src python3 -m jobhunt.cli crawl`.
- `invalid choice: 'tailor'` (or any subcommand)? Your clone is behind — run `git pull`. The usage line in the error always lists what your copy actually has.

Try it safely with the fictional sample profile first (no API key needed if tailoring is off):

```bash
jobhunt --config sample/sample_config.yaml --db data/demo.db crawl
```

## Run it daily

- **GitHub Actions:** a ready workflow is in `.github/workflows/daily-crawl.yml` — fork, add your `OPENAI_API_KEY` secret and your `config.yaml`, adjust the cron line.
- **Locally:** `0 8 * * *  cd ai-job-search-assistant && jobhunt crawl` in your crontab.

When a run finds roles, it prints `N applications are ready for review.` When it finds nothing, it logs a dated run note in the tracker and prints `No new roles today.`

## Your data stays yours

Your real resume, tracker database, tailored resumes and config are all git-ignored by default. Everything runs locally (or in your own GitHub Actions). The only external call is to the LLM endpoint *you* configure, with *your* key. The sample data in `sample/` is a fictional student ("Alex Rivera") created for demos — use it to test, then replace it with your own files kept outside the repo.

## Configuration

See `config.example.yaml` — profile (roles, locations, keywords, master resume path), sources (ATS board tokens; aggregator toggles), tailoring on/off, and your LLM endpoint/model.

## Roadmap

- More ATS adapters (Workday, SmartRecruiters)
- Notification hooks (email / Telegram) after each run
- One-click hosted demo with sample data only

## License

MIT — see `LICENSE`. Contributions welcome; the never-submit and no-invention rules are non-negotiable (see `CONTRIBUTING.md`).
