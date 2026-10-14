# Forma Automations

Email and WhatsApp-draft marketing automation for Forma Pilates (Catford, London), built as Python code in this repo and run on a schedule by GitHub Actions.
Client contact and approver: Eren (Forma owner). Draft and approval inbox: hello@formapilates.co.uk.
The developer cannot code: explain every step in plain English, one step at a time, and show proof it worked.

## Scope (in)
- Automatic emails, checked daily from Mindbody data:
  - Welcome: new client
  - Intro offer follow-up
  - Win-back: no visit in 30 days
  - Pack expiry: 2 days before a pack expires
  - Regulars offer: 8+ classes in the last 30 days
- One-off emails from the Google Sheet (only when the row is marked Approved):
  - Announcements
  - Discount codes (Eren creates codes in Mindbody; the automation only sends them)
- WhatsApp drafts from the Google Sheet, emailed to hello@formapilates.co.uk for a human to post:
  - New drink launch: first 10 get 50% off (single code, staff tally at the bar; drinks are paid via SumUp)
  - Drink polls: question and options only; a human creates the poll in WhatsApp
  - Run club info: time, meeting point, pacers

## Scope (out)
- Cancellation detection and automatic rebooking (scrapped)
- Posting directly into WhatsApp (the group runs from a normal phone; unofficial automation tools are banned)
- Meta / WhatsApp Business API (not needed)
- Creating discount codes via API

## Non-negotiable rules
- Email only clients who have opted in to promotional emails in Mindbody. Every marketing email has an unsubscribe link.
- Nothing one-off is sent unless its Google Sheet row is marked Approved.
- Every send is logged to the Log tab, and no client gets the same automatic email twice inside its cooldown.
- A DRY_RUN switch (Settings tab) logs what would be sent without sending. Default: ON until go-live is signed off.
- Build and test against the Mindbody sandbox site (-99). Switch to Forma's live site ID only at go-live.
- Secrets (Mindbody API key, Brevo API key, Google service account JSON) live in GitHub Actions secrets only (a local, git-ignored .env is allowed for testing). Never put them in code or commit them.
- Do not delete or overwrite GitHub Actions secrets, workflows, branches or Google Sheet tabs/rows without warning in bold and asking first.
- Git commit before every major change.
- A step is done only with a verification artifact: command output, screenshot, log row or received email.

## Infrastructure
- Language: Python 3.12 (best-supported official libraries for Google Sheets and Brevo, readable for a non-coder, runs natively on GitHub Actions).
- Runner: GitHub Actions. No server, no n8n, no Proxmox. The code lives in this repo and GitHub runs it on a schedule.
- Code: `src/forma/`. Email templates: `templates/emails/`. Sheet tab templates (CSV): `sheet_template/`. Tests: `tests/`.
- Workflows (`.github/workflows/`):
  - `tests.yml`: runs the test suite (pytest) on every push. Must be green before anything is called done.
  - `mindbody-fetch.yml`: manual (and on PRs touching the Mindbody code) read-only sandbox check; prints counts and field names only, never personal data.
  - `daily-emails.yml` (step 5): the five automatic emails, once a day at 09:00 Europe/London.
  - `sheet-check.yml` (step 6-7): checks the Sheet for Approved rows every hour, 09:00-21:00 Europe/London.
- Timezone: GitHub cron runs in UTC only. Each scheduled workflow is triggered at both UTC hours that can equal the London time (GMT and BST), and the code checks the Europe/London clock and exits if it is not the right hour. GitHub may start scheduled runs a few minutes late; this is acceptable.
- Scheduled workflows only run from the default branch (`main`), and GitHub pauses them after 60 days with no repo activity on public repos.
- Every run (including DRY_RUN and runs that send nothing) writes at least one row to the Log tab.
- DRY_RUN is read from the Settings tab and defaults to TRUE. If the Settings tab cannot be read, treat DRY_RUN as TRUE.
- Secrets (GitHub repo > Settings > Secrets and variables > Actions): `MINDBODY_API_KEY`, `MINDBODY_SITE_ID` (-99 until go-live), `MINDBODY_STAFF_USERNAME`, `MINDBODY_STAFF_PASSWORD` (staff login; the code swaps it for a fresh token each run), `BREVO_API_KEY`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SHEET_ID`.
- Email provider: Brevo (handles unsubscribes); sending domain formapilates.co.uk, which needs SPF/DKIM/DMARC records set at go-live.
- Control panel: Google Sheet with tabs: Campaigns, WhatsApp, Log, Settings. Headers and examples in `sheet_template/`.

## Build steps
1. Repo skeleton: folders, READMEs, sheet template CSVs, test workflow with a passing placeholder test.
2. Mindbody sandbox (-99): read clients, visits and packs; add the key as a GitHub secret; tests using saved sample data.
3. Brevo: add the key as a GitHub secret and send one test email to the developer's inbox.
4. Google Sheet: create it from `sheet_template/`, share it with the service account, read Settings and write a Log row from Actions.
5. The five automatic emails + `daily-emails.yml` (DRY_RUN on).
6. The one-off email flow (Campaigns tab, Approved rows only) + `sheet-check.yml`.
7. The WhatsApp draft flow (WhatsApp tab, Approved rows only, drafts emailed to hello@formapilates.co.uk).
8. Go-live: live Mindbody site ID, set up the domain records, 1 week in DRY_RUN with Eren reviewing the Log, then switch DRY_RUN to FALSE.

## Model routing
- Sonnet or subagents: file reads, git status, writing code and tests from a written spec, CSV/template edits.
- Opus: planning, debugging failed runs, recipient and cooldown logic, reviewing verification artifacts.

## Status
- Step 1: done (repo skeleton, test workflow green)
- Step 2: in progress (Mindbody read-only fetch + tests; awaiting live sandbox run)
- Mindbody cost note: visits and packs need one request per client each. Keep request counts low and report them.
