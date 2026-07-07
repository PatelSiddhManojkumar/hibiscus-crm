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

Open http://127.0.0.1:8000 — sign in as `admin` / `ravi` / `nisha`,
password `hibiscus2026`. Django admin lives at `/admin/`.

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
