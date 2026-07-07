"""Hibiscus Copilot — a Devin-inspired agentic assistant that operates the CRM
through its own tools.

Given a natural-language instruction it produces a *plan* (a sequence of tool
calls), executes each tool against the live database, and returns a transcript
of plan -> tool call -> result.

The planner is pluggable:
  * When ANTHROPIC_API_KEY is set, it drives a real Claude tool-use loop
    (claude-opus-4-8) — Claude decides which CRM tools to call and with what
    arguments.
  * Otherwise it falls back to a deterministic intent parser so the feature is
    fully runnable offline. Same tools, same transcript shape, same execution.

The tool *registry* and the *execution loop* are real either way — only the
brain that picks the calls differs.
"""
import json
import os
import re
from datetime import timedelta

from django.utils import timezone

from .models import Company, Contact, Deal, Task
from .views import WEIGHTED
from django.db.models import Count, Sum

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are Hibiscus Copilot, an assistant that operates a CRM by \
calling its tools. Given the operator's instruction, use the provided tools to \
carry it out. Prefer the fewest tool calls that accomplish the request. When you \
look something up (e.g. a contact or deal by name) and then act on it, chain the \
calls. After the work is done, reply with one short sentence summarizing what you \
changed — no preamble."""


# ── Tool implementations ─────────────────────────────────────
# Each returns a short human-readable result string. `ctx` carries the acting user.

def _find_deal(name):
    return Deal.objects.filter(name__icontains=name).select_related("contact", "company").first()


def _find_contact(name):
    q = Contact.objects.select_related("company")
    for part in name.split():
        q = q.filter(models_Q(part))
    return q.first()


def models_Q(part):
    from django.db.models import Q
    return Q(first_name__icontains=part) | Q(last_name__icontains=part)


def tool_create_contact(ctx, first_name, last_name="", email="", role="", company=None, stage="lead"):
    company_obj = None
    if company:
        company_obj, _ = Company.objects.get_or_create(name=company)
    c = Contact.objects.create(
        first_name=first_name, last_name=last_name, email=email, role=role,
        company=company_obj, stage=stage, owner=ctx["user"],
    )
    return f"Created contact #{c.id}: {c.name}" + (f" at {company}" if company else "")


def tool_move_deal(ctx, deal_name, stage):
    deal = _find_deal(deal_name)
    if not deal:
        return f"No deal matching '{deal_name}'."
    if stage not in dict(Deal.STAGES):
        return f"'{stage}' is not a valid stage."
    old = deal.get_stage_display()
    deal.stage = stage
    deal.probability = Deal.DEFAULT_PROBABILITY.get(stage, deal.probability)
    deal.stage_changed_at = timezone.now()
    deal.save(update_fields=["stage", "probability", "stage_changed_at"])
    return f"Moved '{deal.name}' from {old} to {deal.get_stage_display()}."


def tool_create_task(ctx, title, contact_name="", due_in_days=None):
    contact = _find_contact(contact_name) if contact_name else None
    due_at = timezone.now() + timedelta(days=int(due_in_days)) if due_in_days is not None else None
    t = Task.objects.create(title=title, contact=contact, assignee=ctx["user"], due_at=due_at)
    tail = f" for {contact.name}" if contact else ""
    when = f", due in {due_in_days}d" if due_in_days is not None else ""
    return f"Created task #{t.id}: '{title}'{tail}{when}."


def tool_log_activity(ctx, contact_name, kind, subject="", body=""):
    from .models import Activity
    contact = _find_contact(contact_name)
    if not contact:
        return f"No contact matching '{contact_name}'."
    Activity.objects.create(contact=contact, kind=kind, subject=subject, body=body, created_by=ctx["user"])
    if kind in ("email", "call", "whatsapp"):
        contact.last_contacted_at = timezone.now()
        contact.save(update_fields=["last_contacted_at"])
    return f"Logged {kind} on {contact.name}" + (f": {subject}" if subject else "") + "."


def tool_run_report(ctx):
    open_deals = Deal.objects.exclude(stage__in=["won", "lost"])
    agg = open_deals.aggregate(total=Sum("value"), weighted=Sum(WEIGHTED))
    by_stage = open_deals.values("stage").annotate(count=Count("id"), total=Sum("value")).order_by("stage")
    lines = [f"{r['stage']}: {r['count']} deals, ₹{(r['total'] or 0)/100000:.1f}L" for r in by_stage]
    return (f"Open pipeline ₹{(agg['total'] or 0)/100000:.1f}L, weighted "
            f"₹{(agg['weighted'] or 0)/100000:.1f}L. " + " · ".join(lines))


TOOLS = {
    "create_contact": tool_create_contact,
    "move_deal": tool_move_deal,
    "create_task": tool_create_task,
    "log_activity": tool_log_activity,
    "run_report": tool_run_report,
}

# JSON schemas advertised to Claude.
TOOL_SCHEMAS = [
    {
        "name": "create_contact",
        "description": "Create a new CRM contact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "company": {"type": "string", "description": "Company name; created if new."},
                "stage": {"type": "string", "enum": ["lead", "prospect", "customer"]},
            },
            "required": ["first_name"],
        },
    },
    {
        "name": "move_deal",
        "description": "Move a deal to a different pipeline stage. Match the deal by (partial) name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_name": {"type": "string"},
                "stage": {"type": "string", "enum": ["qualified", "proposal", "negotiation", "won", "lost"]},
            },
            "required": ["deal_name", "stage"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a task, optionally linked to a contact and due in N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "contact_name": {"type": "string"},
                "due_in_days": {"type": "integer"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "log_activity",
        "description": "Log an activity (email, call, whatsapp, or note) against a contact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string"},
                "kind": {"type": "string", "enum": ["email", "call", "whatsapp", "note"]},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["contact_name", "kind"],
        },
    },
    {
        "name": "run_report",
        "description": "Compute a live pipeline-health summary (open value, weighted value, counts by stage).",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _run_tool(ctx, name, args):
    fn = TOOLS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(ctx, **args)
    except TypeError as e:
        return f"Bad arguments for {name}: {e}"


# ── Claude-backed planner ────────────────────────────────────

def _plan_with_claude(instruction, ctx, steps):
    import anthropic

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": instruction}]
    summary = ""
    for _ in range(8):  # bounded agentic loop
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        for block in resp.content:
            if block.type == "text" and block.text.strip():
                steps.append({"type": "thought", "text": block.text.strip()})
                summary = block.text.strip()
        if resp.stop_reason != "tool_use":
            break
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                steps.append({"type": "tool", "name": block.name, "input": block.input})
                result = _run_tool(ctx, block.name, dict(block.input))
                steps.append({"type": "result", "text": result})
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": results})
    return summary or "Done."


# ── Deterministic offline planner ────────────────────────────

_STAGE_WORDS = {
    "qualified": "qualified", "proposal": "proposal", "negotiation": "negotiation",
    "won": "won", "win": "won", "closed won": "won", "lost": "lost", "close": "won",
}


def _plan_offline(instruction, ctx, steps):
    text = instruction.strip()
    low = text.lower()
    calls = []

    # move a deal: "move <deal> to <stage>" / "mark <deal> as won"
    m = re.search(r"(?:move|mark|set|push|advance)\s+(.+?)\s+(?:to|as|into)\s+([a-z ]+)", low)
    if m and ("deal" in low or True):
        stage = next((v for k, v in _STAGE_WORDS.items() if k in m.group(2)), None)
        if stage:
            name = re.sub(r"\bdeal\b|the\b|['\"]", "", m.group(1)).strip()
            calls.append(("move_deal", {"deal_name": name, "stage": stage}))

    # create task: "add a task to <title>" / "remind me to <title>"
    if not calls:
        m = re.search(r"(?:add|create|make)\s+(?:a\s+)?task\s+(?:to\s+)?(.+)", low) or \
            re.search(r"remind me to\s+(.+)", low)
        if m:
            title = text[m.start(1):].strip().rstrip(".")
            cm = re.search(r"for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
            due = re.search(r"in\s+(\d+)\s*day", low)
            title = title.split(" for ")[0]
            title = re.sub(r"\s+in\s+\d+\s*days?\b", "", title, flags=re.I).strip()
            args = {"title": title}
            if cm:
                args["contact_name"] = cm.group(1)
            if due:
                args["due_in_days"] = int(due.group(1))
            calls.append(("create_task", args))

    # log activity: "log a call with <name>" / "note on <name>: ..."
    if not calls:
        m = re.search(r"log(?:ged)?\s+(?:a\s+)?(call|email|whatsapp|note)\s+(?:with|on|to|for)\s+([A-Za-z ]+)", low)
        if m:
            name = re.search(r"(?:with|on|to|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
            calls.append(("log_activity", {
                "contact_name": name.group(1) if name else m.group(2).strip().title(),
                "kind": m.group(1),
            }))

    # create contact: "add contact <First Last> at <Company>"
    if not calls:
        m = re.search(r"(?:add|create|new)\s+contact\s+([A-Z][a-z]+)\s*([A-Z][a-z]+)?(?:\s+at\s+(.+))?", text)
        if m:
            args = {"first_name": m.group(1)}
            if m.group(2):
                args["last_name"] = m.group(2)
            if m.group(3):
                args["company"] = m.group(3).strip().rstrip(".")
            calls.append(("create_contact", args))

    # report
    if not calls and ("report" in low or "pipeline" in low or "how" in low and "pipeline" in low):
        calls.append(("run_report", {}))

    if not calls:
        steps.append({"type": "thought",
                      "text": "Offline planner couldn't map that instruction to a tool. "
                              "Try e.g. \"move Q3 Bulk Order to won\", \"add a task to call Meera in 2 days\", "
                              "or set ANTHROPIC_API_KEY for full natural-language planning."})
        return "No matching action."

    steps.append({"type": "thought", "text": f"Planned {len(calls)} step(s) from your instruction."})
    last = "Done."
    for name, args in calls:
        steps.append({"type": "tool", "name": name, "input": args})
        last = _run_tool(ctx, name, args)
        steps.append({"type": "result", "text": last})
    return last


# ── Public entrypoint ────────────────────────────────────────

def run(instruction, user):
    """Plan and execute an instruction. Returns {engine, steps, summary}."""
    ctx = {"user": user}
    steps = []
    keyed = bool(os.environ.get("ANTHROPIC_API_KEY"))
    engine = "claude" if keyed else "offline"
    try:
        if keyed:
            summary = _plan_with_claude(instruction, ctx, steps)
        else:
            summary = _plan_offline(instruction, ctx, steps)
    except Exception as e:  # never 500 the copilot — surface the error in the transcript
        steps.append({"type": "error", "text": f"{type(e).__name__}: {e}"})
        summary = "The copilot hit an error."
        if keyed:  # fall back so the feature still does something useful
            engine = "offline (claude failed)"
            summary = _plan_offline(instruction, ctx, steps)
    return {"engine": engine, "steps": steps, "summary": summary}
