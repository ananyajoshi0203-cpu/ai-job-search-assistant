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
| LinkedIn | Public logged-out job search pages | **Off** |
| Wellfound | Public search pages | **Off** |
| Jobright | Public search pages | **Off** |

> ⚠️ LinkedIn, Wellfound and Jobright restrict automated access in their Terms of Service. Those adapters ship **disabled**, use public pages only (no login, no CAPTCHA bypass), rate-limit strictly, and stop on blocks. Enabling one is your decision and your responsibility. The ATS APIs are the reliable, terms-clean path and are what we recommend.

## Quick start

```bash
git clone https://github.com/joshi0203-cpu/ai-job-search-assistant.git
cd ai-job-search-assistant
pip install -e .
cp config.example.yaml config.yaml     # edit: your profile, roles, locations, ATS boards
export OPENAI_API_KEY=...               # your own key, any OpenAI-compatible endpoint

jobhunt init                            # create the SQLite tracker (data/tracker.db)
jobhunt crawl                           # one full run
jobhunt review                          # local review page at http://localhost:8765
jobhunt export --out tracker.xlsx       # spreadsheet export
```

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
