# Forma Automations

Email and WhatsApp-draft marketing automation for Forma Pilates (Catford, London), built in n8n.
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
- Secrets (Mindbody API key, email provider key, Google credentials) live in n8n credentials or .env. Never commit them.
- Do not stop, remove, recreate or change ports of any existing Proxmox container or VM. Warn in bold and ask before any such action.
- Git commit before every major change.
- A step is done only with a verification artifact: command output, screenshot, log row or received email.

## Infrastructure
- Host: user's Proxmox server, in a NEW dedicated LXC container for n8n (not the existing Ubuntu dev container).
- Existing services to leave untouched: LibreChat at 192.168.0.201:3080 and anything else already running.
- n8n runs in Docker on that container, port 5678, LAN only (no public exposure).
- Email provider: Brevo (handles unsubscribes); sending domain formapilates.co.uk, which needs SPF/DKIM/DMARC records set at go-live.
- Control panel: Google Sheet with tabs: Campaigns, WhatsApp, Log, Settings.

## Build steps
1. Create the n8n container and install Docker + n8n. Init this repo.
2. Connect n8n to the Mindbody sandbox and read clients, visits and packs.
3. Set up Brevo and send a test email to the developer's inbox.
4. Create the Google Sheet control panel and connect it to n8n.
5. Build the five automatic email workflows (DRY_RUN on).
6. Build the one-off email workflow.
7. Build the WhatsApp draft workflow.
8. Go-live: live Mindbody site ID, set up the domain records, 1 week in DRY_RUN with Eren reviewing the log, then switch on.

## Model routing
- Sonnet or subagents: installs, file reads, git status, building workflows from a written spec.
- Opus: planning, debugging, recipient logic, reviewing verification.

## Status
- Step 1: not started
