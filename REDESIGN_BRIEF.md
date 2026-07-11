═══════════════════════════════════════════════════════════════════
HIBISCUS — REDESIGN PROMPT  ·  v2 "AGENT-NATIVE"
For Fable / Frontend Design Only
═══════════════════════════════════════════════════════════════════

You are a Senior Product Designer + Frontend Engineer with 8+ years
designing operator-grade software — the tools that professionals live
inside, not the ones they demo once. Your references are Linear, Attio,
Raycast, Stripe's internal tooling, Braun instruments, and the plates
of a 19th-century herbarium. Your task is to redesign Hibiscus — an
agent-native CRM — from the studs. Not a reskin. A full rebuild of the
visual identity, the layout system, and above all the way the agent
lives inside the interface.

Hibiscus v1 was warm, floral, editorial — a "workshop, not a showroom."
That identity did its job. It is now retired. Do not carry over the
amaranth-and-chalk palette, the Fraunces serif headlines, or the
Mediterranean editorial mood. If your redesign looks like a recolor of
the old one, delete it and start over.

The reason for the rebuild is that the product changed underneath the
skin. Hibiscus is no longer a place where you *file* customer data. It
is a place where you *command* it. There is an agent — Copilot — that
operates the CRM through the CRM's own tools: you say "move the Porto
deal to won and raise the invoice task," and it writes a plan, calls
the tools, and shows its work. The old design treated the agent as a
feature bolted into a corner. The redesign treats the agent as the
primary surface and the tables, cards, and forms as what the agent
acts upon.

Backend is built. Do not touch backend logic, data models, or API
contracts. This is a pure design + frontend rebuild.

───────────────────────────────────────────────────────────────────
DESIGN PHILOSOPHY
───────────────────────────────────────────────────────────────────

Positioning statement:
  "Hibiscus is the instrument, not the inbox. You state the intent;
   the agent operates the pipeline. Every screen is a control surface
   for something that acts on your behalf — and shows you exactly
   what it did."

The one-line thesis the whole design must serve:
  A CRM should be an operator, not a filing cabinet.

Emotional register:
  Precise without being cold.
  Alive without being decorative.
  Instrumental — like a good synthesizer or a field microscope:
  dense with capability, but every control means one thing.
  A single living accent (the hibiscus bloom) against a quiet,
  botanical, graphite-and-bone instrument body.

Three non-negotiable design principles:

  1. THE AGENT IS A CITIZEN, NOT A CHATBOX.
     The agent's plan, tool calls, and results are first-class UI with
     their own visual language — not grey chat bubbles. A person must
     be able to read what the agent did the way they'd read a flight
     recorder: legible, auditable, trustworthy.

  2. STATE IS SHOWN IN FORM, NOT JUST TEXT.
     Deal stages, agent status, task urgency, sync freshness — all
     carry a visual weight (a stripe, a pip, a fill) so the thing that
     needs attention reads at a glance, before you read a word.

  3. DENSITY IS RESPECT.
     The user lives here six hours a day. Reward familiarity. No
     onboarding coach-marks, no empty hero space in the app, no
     "are you sure?" on reversible actions. Comfortable by default,
     compact on request.

───────────────────────────────────────────────────────────────────
COLOR PALETTE — STRICT
───────────────────────────────────────────────────────────────────

Six colors. This is a botanical-instrument palette: an ink-green body,
warm bone paper, one saturated hibiscus bloom as the single living
accent, and three muted specimen tones. Contrast comes from tint and
opacity, not from adding hues.

  #14201B  Glasshouse Ink   — Signature dark ground, dark surfaces,
                              primary text on light. The near-black is
                              green, not neutral — a night glasshouse.
  #E9E4D6  Herbarium Bone   — Primary light ground, card surfaces,
                              text on dark. Warm paper, cooler than
                              cream — a pressed-specimen sheet.
  #C42348  Hibiscus Bloom   — THE accent. The flower. Primary CTAs,
                              active states, the agent's live presence,
                              destructive confirmation. Use it rarely
                              and it stays loud.
  #7C9A76  Chlorophyll      — Success, positive metrics, "won", healthy
                              sync, the agent's completed steps.
  #C9A227  Pollen           — Warning/attention, data emphasis,
                              highlights, "needs review" states.
  #6B726C  Graphite         — Borders, muted UI, secondary text,
                              ruled separators, disabled.

Distribution (light mode):
  58–64%  Herbarium Bone           — surfaces
  16–20%  Glasshouse Ink           — text, headings, dark chrome
  8–10%   Graphite                 — borders, secondary text, UI
  5–7%    Hibiscus Bloom           — accent, CTAs, agent presence
  3–5%    Chlorophyll + Pollen     — status only

Dark mode is not an inversion — it is the *signature*. The marketing
hero and the agent console default to Glasshouse Ink grounds with Bone
text and a single Bloom accent; the operational tables default to Bone.
Both are first-class. Design both fully; never auto-flip.

Interaction color mapping:
  Default text          → Glasshouse Ink (on Bone) / Bone (on Ink)
  Secondary text        → Graphite
  Primary action        → Hibiscus Bloom bg, Bone text
  Link / interactive    → Hibiscus Bloom (text), Graphite→Bloom on hover
  Agent — thinking      → Graphite, italic, low weight
  Agent — tool call     → Ink surface + Bloom label
  Agent — result/done   → Chlorophyll
  Agent — needs you     → Pollen (a gate that blocks until resolved)
  Success / positive    → Chlorophyll
  Warning / attention   → Pollen
  Destructive           → Hibiscus Bloom (never introduce a new red)
  Border default        → Graphite at 22% opacity
  Border strong         → Graphite at 44% opacity

Forbidden:
  Pure black, pure white, gradients of any kind, neon, blue, purple,
  glassmorphism/frosted panels as decoration, drop shadows that aren't
  Ink-tinted, the old v1 amaranth/chalk set, and the entire "warm
  cream + serif + terracotta" look (that WAS v1 — we're leaving it).
  No emoji as UI iconography.

───────────────────────────────────────────────────────────────────
TYPOGRAPHY
───────────────────────────────────────────────────────────────────

Three typefaces. No editorial serif — the redesign speaks in the
voice of an instrument, not a magazine. Locked.

  Display / Panel labels: A wide, mechanical grotesque with the feel
    of a stamped herbarium label or an instrument faceplate.
    Primary: ABC Diatype Semi-Mono or Neue Haas Grotesk Display
    Fallback: Archivo Expanded (free, variable, Google Fonts)
    Weight: Medium 500 / Semibold 600. Wide, tight-tracked.
    Use for: hero headline, section titles, view headers, empty
             states, the wordmark.
    Sizes: 60–84px hero, 30–40px section, 18–22px view header.
    Letter-spacing: -1px above 40px; UPPERCASE labels +2px.

  UI / Body: A neutral, slightly humanist grotesque. Legible at 13px.
    Primary: Söhne (if licensed)
    Fallback: Archivo or Inter Tight (NOT plain Inter, NOT Space
              Grotesk — both read as the default-safe AI choice).
    Weight: Regular 400, Medium 500, Semibold 600 (rare).
    Use for: all UI text, buttons, table cells, forms, metadata.
    Sizes: 14px default, 13px table cells, 12px meta, 11px eyebrow
           labels (uppercase, +2px tracking).

  Data / Mono: JetBrains Mono. This is the voice of the machine.
    Use for: IDs, timestamps, currency, all agent tool calls and
             arguments, API keys, code, anything the agent emits.
    The agent literally speaks in monospace — it is how you tell the
    machine's words from the human's at a glance.

Rule:
  The monospace is doing narrative work, not just data work. Every
  word the AGENT produces that is a tool call, an argument, or a
  system fact is set in JetBrains Mono. Everything a PERSON writes
  (notes, emails, titles) is set in the grotesque. This typographic
  split is the core of the identity — protect it everywhere.

───────────────────────────────────────────────────────────────────
LAYOUT SYSTEM
───────────────────────────────────────────────────────────────────

Grid: 8pt base. All spacing in multiples of 8 (4 permitted for
      dense table interiors only).

Border radius (tighter than v1 — this is an instrument, not a pillow):
  Cards      8px
  Buttons    6px
  Inputs     6px
  Tags/pips  3px
  Agent tool-call cards 6px
  Avatars    4px (rounded-square, NOT circular — specimen labels,
                  not social avatars)

Shadows (Ink-tinted, restrained — flatness is the default):
  Rest:      none
  Hover:     0 1px 3px rgba(20,32,27,.10)
  Elevated:  0 6px 20px rgba(20,32,27,.14)
  Agent panel / modal: 0 20px 60px rgba(20,32,27,.22)

Structural device — the hairline grid:
  Surfaces are separated by 1px Graphite hairlines, not by shadow or
  gap. Think ledger rules and instrument panel seams. The whole app
  should read as one continuous precision instrument, subdivided.

Density levels (user-toggleable per view):
  Comfortable (default) — 12px row padding
  Compact               — 6px row padding
  No "spacious" tier. This tool does not waste vertical space.

───────────────────────────────────────────────────────────────────
THE AGENT SURFACE  ·  the soul of the redesign
───────────────────────────────────────────────────────────────────

This section did not exist in v1. It is now the most important part
of the whole system. Get this right and the redesign works; get it
wrong and it's just another table app with a chat drawer.

Copilot operates the CRM through its own tools. The design job is to
make its work READABLE and TRUSTWORTHY. Three surfaces:

  A. THE COMMAND BAR (always reachable)
     A single input, invoked with ⌘J, docked or floating depending on
     context. Placeholder is an imperative, not a question:
       "Move the Porto deal to won and raise the invoice…"
     NOT "How can I help you today?" — this is a command line for an
     operator, not a helpdesk. Monospace prompt caret in Bloom.

  B. THE REASONING STREAM (the flight recorder)
     When the agent runs, it emits a vertical stream of typed events.
     Each event type has a FIXED visual grammar so the eye learns it:

       ◇ PLAN / THINKING
         Graphite, italic, grotesque. One or two lines. "Two steps —
         advance the deal, then create the follow-up task."

       → TOOL CALL
         An Ink-surfaced card, 6px radius, Bloom tool name in mono,
         Graphite arguments in mono:
           → move_deal  {deal:"Porto Ceramics", stage:"won"}
         The arrow and the monospace say: the machine is acting.

       ✓ RESULT
         Chlorophyll, medium weight. What actually changed, stated
         plainly: "Moved Retail Line Extension to Won, probability 100%."
         Every result must be auditable — it names the record it touched.

       ▲ GATE (needs you)
         Pollen. A blocking card for anything irreversible or ambiguous:
         "About to email 240 contacts. Approve / Edit / Cancel." The
         stream halts here until the operator acts. Reversible actions
         NEVER gate — they just run and report.

       ✕ ERROR
         Bloom, but quiet. Names the tool and the reason, offers a retry.

     The stream animates in top-to-bottom as steps complete, with a
     single pulsing Bloom pip on the currently-running step. When done,
     a one-sentence summary in the grotesque (the agent's "human" voice)
     closes the run. The stream is scrollable, re-runnable, and every
     run is timestamped in mono.

  C. AMBIENT PRESENCE (the agent is always there, never in the way)
     A small Bloom "✦" mark in the top bar that (a) opens the command
     bar, (b) glows softly while a background run is in progress, and
     (c) badges when a gate is waiting. The agent has a heartbeat; the
     UI shows it without nagging.

Trust rules the visual system must enforce:
  - The agent's words are ALWAYS monospace; the human's are always
    grotesque. Never blur the two.
  - Every mutating result names the exact record and the exact change.
  - Destructive or outbound actions gate in Pollen; reversible ones
    run and report. The color tells you whether you're being asked.
  - The plan is shown BEFORE the tools run when the run is long; short
    runs may plan-and-execute in one pass. Never hide the plan.

───────────────────────────────────────────────────────────────────
LANDING PAGE
───────────────────────────────────────────────────────────────────

Signature ground: Glasshouse Ink (dark). The landing page is the
night glasshouse; the app is the daylight field ledger.

  01. HERO (100vh) — THE LIVE INSTRUMENT
      Left: the thesis, set large in the wide grotesque —
        "The CRM that runs itself."
      Eyebrow (mono, +2px, Bloom): "HIBISCUS · AGENT-NATIVE CRM"
      Sub (Bone at 82%): the gap thesis — every other CRM makes you
        the data-entry robot; Hibiscus flips it.
      Right: a LIVE, looping reasoning-stream terminal — the agent
        typing an instruction, planning, calling tools, returning
        results, then looping through 3 real scenarios. This is the
        hero image. It is not a screenshot; it runs. The most
        characteristic thing in the product's world, on the front door.
      CTAs: "Start free" (Bloom) · "See it operate →" (ghost).
      Meta row (mono): AGENTIC COPILOT · SELF-HOSTED OR CLOUD ·
                       NO PER-SEAT PRICING.

  02. THE GAP
      Eyebrow: "THE GAP NOBODY FILLED".
      A single large grotesque statement:
        "A CRM should be an operator, not a filing cabinet."
      Below: a two-column ledger — "Every CRM you've tried" (Graphite,
      × marks) vs "Hibiscus" (Bone, → marks). Concrete, specific,
      not adjectives.

  03. SIX TOOLS, BUILT FOR OPERATORS
      Copilot featured full-width (with a mini reasoning-stream), then
      five: Deals (weighted forecast), Reports (documents not
      dashboards), Automations (scripting escape hatch), Unified inbox,
      Keyboard-first. Icons: Phosphor, 1.5 stroke, Bloom.

  04. PROOF STRIP
      Four animated counters (contacts/day, table latency, tools the
      agent can call, clone-to-running time). Mono numerals, tabular.

  05. PRICING
      Two plans (Self-hosted Free / Hosted ₹499). One "most popular"
      pip in Bloom. Italic note: no per-seat, no per-contact, ever.

  06. FINAL CALL — the only Bloom-ground section on the site.
      "Stop feeding the CRM. Start commanding it."
      Single CTA. Mono footer: "Built in India. Runs anywhere.
      Made for operators."

Motion: the hero terminal is the orchestrated moment. Elsewhere,
scroll-reveal and counter count-up only. No parallax, no scroll-jack.

───────────────────────────────────────────────────────────────────
APPLICATION UI
───────────────────────────────────────────────────────────────────

Default ground: Herbarium Bone (the daylight field ledger). Dark
mode fully supported via tokens.

GLOBAL LAYOUT:
  Left rail (240px → 56px collapsed): Glasshouse Ink. Workspace
    switcher, then grouped nav with mono section labels
    (WORK / OBJECTS / INTELLIGENCE / SETTINGS). Bloom active state as
    a 2px left stripe, not a fill.
  Top bar (52px): ⌘K search, mono breadcrumbs, and the ambient agent
    "✦" mark on the right with its heartbeat/gate states.
  Command bar: ⌘J anywhere. Reasoning stream opens as a right-docked
    panel (420px) that can pin open beside any view — so you watch the
    agent act on the table you're looking at.

VIEWS TO DESIGN:
  A. Contacts (table) — hairline-ruled, no zebra, 44/32px rows,
     density toggle, filter pips (Chlorophyll/Pollen/Graphite by
     meaning), multi-select on shift, inline actions on hover.
  B. Contact detail — left identity panel (rounded-square avatar,
     mono meta grid), right tabbed activity where the timeline
     interleaves human events (grotesque) and agent events (mono
     reasoning-stream fragments) on one spine. This interleaving is
     the signature detail of the app.
  C. Deals kanban — stage columns with count + weighted value (mono).
     Cards carry a 3px stage-colored top stripe. Drag persists.
  D. AGENT CONSOLE (new view) — a full-page history of every run the
     agent has done in this workspace: timestamped, filterable by
     tool, re-runnable, auditable. This is the "flight recorder"
     writ large — no other CRM has it, so it must feel authoritative.
  E. Reports — documents, not dashboards. Editorial layout, palette-
     only charts (thin marks, one hue per series, direct labels,
     Ink-tinted grid), export to a PDF identical to screen.
  F. Automations builder — trigger / condition / action steps with a
     scripting escape hatch; visually a sibling of the reasoning
     stream so "automation" and "agent" read as one family.
  G. Unified inbox — email/call/WhatsApp threaded per contact.
  H. Settings — workspace / members / integrations, including an
     "Agent" tab: which tools Copilot may call, and which actions
     require a gate. (The trust model is user-configurable and must
     be legible.)
  I. Command menu (⌘K) and Command bar (⌘J) — distinct: ⌘K navigates,
     ⌘J commands the agent. Make the difference obvious.

───────────────────────────────────────────────────────────────────
INTERACTION SYSTEM
───────────────────────────────────────────────────────────────────

Motion budget:
  Hover        120ms ease-out
  Press        100ms ease-in-out
  Panel/modal  200ms ease-out (opacity + 8px slide, no scale bounce)
  Agent-drawer 240ms ease-out
  Stream step reveal 260ms ease-out (opacity + 4px rise)
  Toast        180ms ease-out from bottom

Forbidden: spring/bounce anywhere, anything >300ms in operational UI,
scroll-jacking, infinite decorative loops (the ONE exception is the
landing hero terminal), loading spinners (use Bone-tinted skeletons),
typewriter effects anywhere except the landing hero.

Keyboard (every action has a key; show a cheat sheet on ?):
  ⌘K command menu · ⌘J agent command bar · G then C/D/T go to view ·
  N new (context-aware) · E edit · / focus filter · ? shortcuts.
  Agent gates are resolvable by keyboard (⏎ approve, ⌫ cancel).

Reduced motion: the landing hero renders one run fully, statically;
all reveals resolve instantly.

───────────────────────────────────────────────────────────────────
MOBILE
───────────────────────────────────────────────────────────────────

Desktop-primary. Mobile is for: reading an agent run, approving a
gate on the go, adding a note after a call, marking a task done. Not
for: bulk ops, report building, agent configuration.
  Bottom tab bar (Inbox · Contacts · Deals · Agent · More). Tables
  become card lists (never horizontal scroll). Detail views are
  bottom sheets. The agent command bar is a full-width docked input
  above the keyboard; the reasoning stream is the full screen.

───────────────────────────────────────────────────────────────────
DATA-VIZ / REPORTS NOTE
───────────────────────────────────────────────────────────────────

The palette is intentionally low-chroma; only Hibiscus Bloom is
saturated. For charts: single-hue single-series wherever possible,
direct labels in text ink (never color-alone identity), Chlorophyll/
Pollen reserved for status meaning, thin 2px marks, 4px rounded
data-ends, faint Ink grid, emphasized endpoint. Run any categorical
palette through a CVD check; if series exceed three, fold to "Other"
or small-multiples rather than inventing hues.

───────────────────────────────────────────────────────────────────
DESIGN REFERENCES — STUDY, DO NOT COPY
───────────────────────────────────────────────────────────────────

For the agent surface & command model:
  Raycast, Linear (command menu), Warp terminal, Vercel's build logs,
  a good flight-data recorder readout.
For instrument density & restraint:
  Braun / Dieter Rams control faces, Teenage Engineering, Bloomberg
  Terminal (density, not aesthetics), Attio.
For the botanical soul & one-accent discipline:
  A 19th-century herbarium sheet, Kew botanical plates, riso prints
  with a single spot color, Aesop's restraint (warmth, not the cream).
For type:
  Grilli Type & ABC Dinamo specimens, Typewolf grotesque pairings.

Do NOT reference: Salesforce, HubSpot, Zoho; any ThemeForest "modern
SaaS" template; any purple-gradient AI-startup landing; Hibiscus v1.

───────────────────────────────────────────────────────────────────
DELIVERABLES
───────────────────────────────────────────────────────────────────

  1. Landing page — all sections, desktop + mobile, dark signature.
  2. Login + signup.
  3. App shell — rail + top bar + docked agent panel (desktop+mobile),
     light and dark.
  4. Contacts table (comfortable + compact).
  5. Contact detail — with the interleaved human/agent timeline.
  6. Deals kanban + deals table.
  7. AGENT CONSOLE — the run-history flight recorder.
  8. The reasoning stream in all five states (plan/tool/result/gate/
     error) as a documented component.
  9. Command bar (⌘J) and command menu (⌘K), side by side, distinct.
 10. Reports — one example report end to end, screen + PDF.
 11. Automations builder.
 12. Unified inbox.
 13. Settings — incl. the Agent trust/tools tab.
 14. Empty states for every major view (grotesque, one line, one
     action — no illustrations).
 15. Component library: buttons (5), inputs, selects, checks, radios,
     toggles, pips/tags, filter chips, cards, agent tool-call card,
     gate card, modals, right-dock panel, toasts, skeletons, icons
     (Phosphor 1.5), plus the two-theme token sheet.

───────────────────────────────────────────────────────────────────
FINAL VISUAL SANITY CHECK
───────────────────────────────────────────────────────────────────

A designer opening the file cold should feel:
  "This isn't a CRM with a chatbot stapled on. The agent lives here —
   I can read what it did, I can trust it, and the whole thing reads
   like one precise instrument. And it looks like nothing else in the
   category." If it reads as v1 recolored, or as a generic dark-mode
   SaaS dashboard, it has failed — start over.

═══════════════════════════════════════════════════════════════════
