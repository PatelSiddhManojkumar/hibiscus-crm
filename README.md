# Hibiscus CRM

A full-stack CRM in the workshop-not-showroom tradition: dense, keyboard-driven,
editorial. Django + DRF backend, zero-build single-page frontend, five-color
design system. This is the productionized, advanced version of the
[Hibiscus design mockups](https://github.com/PatelSiddhManojkumar/hibiscus-crm-design) —
a working application, not screens.

## Quick start

```bash
python -m venv venv
venv/Scripts/activate          # Windows · use source venv/bin/activate on unix
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo     # demo workspace + users
python manage.py runserver
```

Open http://127.0.0.1:8000 — the **landing page** is the home page; the CRM app
is at **`/app`**. Sign in as `admin` / `ravi` / `nisha`, password `hibiscus2026`.
Django admin lives at `/admin/`.

## ✦ Copilot — the gap nobody else fills

Every other CRM makes *you* the data-entry robot: drag the card, remember to log
the call, update the field. **Hibiscus Copilot inverts that** — you give an
instruction in plain English and it *operates the CRM through the CRM's own
tools*, showing its work step by step (Devin-style plan → tool call → result).

```
› Move the Porto deal to won and add a task to raise the invoice
  ◇ Two steps — advance the deal, then create the follow-up task.
  → move_deal   {deal:"Porto Ceramics", stage:"won"}
  ✓ Moved Retail Line Extension to Won
  → create_task {title:"Raise invoice — Porto"}
  ✓ Task created, assigned to you
```

`POST /api/copilot/ {"instruction": "..."}` returns `{engine, steps[], summary}`.
Open it in the app with the **✦ Copilot** button or **⌘J**.

**The planner is pluggable:**
- With `ANTHROPIC_API_KEY` set, it runs a real Claude tool-use loop
  (`claude-opus-4-8`) — Claude chooses which CRM tools to call.
- Without a key, a deterministic intent parser handles the common instructions,
  so the feature is fully runnable offline. Same tools, same execution, same
  transcript shape — only the brain that picks the calls differs.

**Eleven tools** (all real, all scoped to the requesting user):
`create_contact` · `update_contact` · `create_deal` · `move_deal` · `update_deal`
· `create_task` · `log_activity` · `send_email` · `search` · `summarize_contact`
· `run_report`. Read-only tools (`search`, `summarize_contact`, `run_report`) let
the agent look things up before it acts.

**Approval gates.** Outbound / hard-to-reverse actions (`send_email`) don't run
automatically — Copilot *queues* them and the transcript shows a gate the operator
must **Approve & send** or **Cancel** (`POST /api/copilot/approve/`). Reversible
actions just run and report. This is the trust model: the color of the step tells
you whether you're being asked.

**Agent Console** (`/app#/agent`, `GET /api/agent-runs/`). Every run is persisted
as an `AgentRun` — instruction, engine, full step transcript, gate status,
timestamp — and browsable as an auditable flight recorder.

**Insights** (`/app#/insights`, `GET /api/insights/`). Rule-based analytics from
the data you already have: weighted forecast, deals **at risk** (ranked by how far
past a stage-age threshold they've sat), and **next-best-actions** — each with a
"Run in Copilot →" button that hands the suggestion straight to the agent.

There's also a standalone marketing landing page (`landing.html`, served at `/`)
with a live looping Copilot demo in the hero.

## What's inside

**Backend — Django 5 + DRF, token auth, SQLite by default.**

| Endpoint | What it does |
|---|---|
| `POST /api/auth/login/` | Token auth |
| `/api/contacts/` | CRUD, `?search=`, `?stage=`, `?owner=` · `/:id/timeline/` · `POST /:id/merge/` (merge duplicates) |
| `/api/companies/`, `/api/tags/` | CRUD |
| `/api/deals/` | CRUD · `GET /board/` returns the kanban grouped by stage with count/total/weighted rollups |
| `/api/activities/` | Unified timeline: email, call, WhatsApp, note, system. Logging a touch updates `contact.last_contacted_at` |
| `/api/tasks/` | CRUD, `?open=1`, `?assignee=me` · `POST /:id/complete/` — recurring tasks respawn on completion; tasks support `blocked_by` dependencies |
| `/api/automations/` | CRUD · `POST /:id/run/` — ships with a working stale-proposal rule (proposal > 21 days → creates revive-or-close tasks) |
| `GET /api/reports/summary/` | Live aggregates: pipeline by stage, won-by-month, weighted totals |
| `POST /api/copilot/` | Agentic Copilot — plans and executes an instruction via CRM tools |
| `POST /api/copilot/approve/` | Approve or cancel a gated Copilot action |
| `/api/agent-runs/` | Agent Console — persisted history of every Copilot run |
| `GET /api/insights/` | Weighted forecast, at-risk deals, next-best-actions |

Domain behavior baked in:
- Moving a deal to a new stage resets its probability to the stage default,
  stamps `stage_changed_at`, and writes a system activity to the contact timeline.
- Contact merge moves activities, deals, tasks, and tags, then deletes the duplicate.
- Custom fields on contacts via a JSON field.

**Frontend — one template + `static/hibiscus.js`, no build step.**
Hash-routed SPA wired to the API: contacts table (live search, stage filter
chips, density toggle), contact detail (identity card + grouped timeline +
add-note/log-call), deals kanban with **drag-and-drop that persists** via
`PATCH`, task groups (overdue/today/upcoming) with one-click complete,
live editorial report with palette-only SVG charts, automations panel with
run-now and pause toggles, and a `⌘K` command menu with live contact search.

Keyboard: `⌘K` search · `G` then `C`/`D`/`T`/`R`/`A` to navigate · `/` focus
filter · `Esc` closes everything.

## Design system

Five colors only (contrast via opacity, never new hues): Amaranth `#933B5B`,
Thulian `#B5728A`, Brook `#AABAAE`, Chalk `#E3D6BF`, Pomelo Olive `#9F9679`.
Fraunces for headlines and empty states, Inter for operational UI, JetBrains
Mono for data. Full token sheet in `static/hibiscus.css`; the component
reference lives in the design repo.

## Production notes

- Set `HIBISCUS_SECRET_KEY`, `HIBISCUS_DEBUG=0`, `HIBISCUS_ALLOWED_HOSTS`.
- `python manage.py collectstatic` — WhiteNoise serves static files.
- Swap `DATABASES` to Postgres for real deployments.
