"""Hibiscus Copilot — a Devin-inspired agentic assistant that operates the CRM
through its own tools.

Given a natural-language instruction it produces a *plan* (a sequence of tool
calls), executes the safe ones against the live database, and *gates* the risky
ones (outbound / hard-to-reverse) behind an approval step. It returns a
transcript of plan -> tool call -> result -> gate, persists it as an AgentRun
(the Agent Console flight recorder), and can execute a gated action later once
the operator approves it.

The planner is pluggable:
  * ANTHROPIC_API_KEY set  -> a real Claude tool-use loop (claude-opus-4-8).
  * otherwise              -> a deterministic intent parser, fully offline.
Same tools, same execution, same transcript shape.
"""
import os
import re
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import Activity, AgentRun, Company, Contact, Deal, Task
from .views import WEIGHTED

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You are Hibiscus Copilot, an assistant that operates a CRM by \
calling its tools. Carry out the operator's instruction with the fewest tool \
calls that do the job. Look things up with `search` or `summarize_contact` when \
you need to before acting. Outbound or hard-to-reverse actions (send_email) are \
queued for the operator's approval — call them normally; the system handles the \
gate. After the work is done, reply with one short sentence summarizing what you \
changed or queued. No preamble."""

# Tools whose effect leaves the workspace or is hard to reverse: gated, not auto-run.
GATED = {"send_email"}


# ── lookup helpers ───────────────────────────────────────────
def _find_deal(name):
    return Deal.objects.filter(name__icontains=name).select_related("contact", "company").first()


def _find_contact(name):
    q = Contact.objects.select_related("company")
    for part in (name or "").split():
        q = q.filter(Q(first_name__icontains=part) | Q(last_name__icontains=part))
    return q.first()


# ── tool implementations (each returns a short result string) ─
def tool_create_contact(ctx, first_name, last_name="", email="", role="", company=None, stage="lead"):
    company_obj = Company.objects.get_or_create(name=company)[0] if company else None
    c = Contact.objects.create(first_name=first_name, last_name=last_name, email=email, role=role,
                               company=company_obj, stage=stage, owner=ctx["user"])
    return f"Created contact #{c.id}: {c.name}" + (f" at {company}" if company else "") + "."


def tool_update_contact(ctx, contact_name, stage=None, role=None, email=None, owner=None):
    c = _find_contact(contact_name)
    if not c:
        return f"No contact matching '{contact_name}'."
    changed = []
    if stage and stage in dict(Contact.STAGES):
        c.stage = stage; changed.append(f"stage→{stage}")
    if role is not None:
        c.role = role; changed.append("role")
    if email is not None:
        c.email = email; changed.append("email")
    c.save()
    return f"Updated {c.name} ({', '.join(changed) or 'no changes'})."


def tool_create_deal(ctx, name, contact_name="", value=0, stage="qualified"):
    contact = _find_contact(contact_name) if contact_name else None
    d = Deal.objects.create(name=name, contact=contact, company=contact.company if contact else None,
                            value=value or 0, stage=stage,
                            probability=Deal.DEFAULT_PROBABILITY.get(stage, 20), owner=ctx["user"])
    return f"Created deal #{d.id}: '{d.name}'" + (f" for {contact.name}" if contact else "") + f" (₹{float(d.value):,.0f})."


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
    Activity.objects.create(contact=deal.contact, deal=deal, kind="system",
                            subject=f"Deal moved {old} → {deal.get_stage_display()}", created_by=ctx["user"])
    return f"Moved '{deal.name}' from {old} to {deal.get_stage_display()} (probability {deal.probability}%)."


def tool_update_deal(ctx, deal_name, value=None, probability=None, name=None):
    deal = _find_deal(deal_name)
    if not deal:
        return f"No deal matching '{deal_name}'."
    changed = []
    if value is not None:
        deal.value = value; changed.append(f"value→₹{float(value):,.0f}")
    if probability is not None:
        deal.probability = max(0, min(100, int(probability))); changed.append(f"probability→{deal.probability}%")
    if name:
        deal.name = name; changed.append("name")
    deal.save()
    return f"Updated '{deal.name}' ({', '.join(changed) or 'no changes'})."


def tool_create_task(ctx, title, contact_name="", due_in_days=None):
    contact = _find_contact(contact_name) if contact_name else None
    due_at = timezone.now() + timedelta(days=int(due_in_days)) if due_in_days is not None else None
    t = Task.objects.create(title=title, contact=contact, assignee=ctx["user"], due_at=due_at)
    tail = f" for {contact.name}" if contact else ""
    when = f", due in {due_in_days}d" if due_in_days is not None else ""
    return f"Created task #{t.id}: '{title}'{tail}{when}."


def tool_log_activity(ctx, contact_name, kind, subject="", body=""):
    contact = _find_contact(contact_name)
    if not contact:
        return f"No contact matching '{contact_name}'."
    Activity.objects.create(contact=contact, kind=kind, subject=subject, body=body, created_by=ctx["user"])
    if kind in ("email", "call", "whatsapp"):
        contact.last_contacted_at = timezone.now()
        contact.save(update_fields=["last_contacted_at"])
    return f"Logged {kind} on {contact.name}" + (f": {subject}" if subject else "") + "."


def tool_send_email(ctx, contact_name, subject, body):
    """GATED. On approval this 'sends' by logging an email activity to the contact."""
    contact = _find_contact(contact_name)
    if not contact:
        return f"No contact matching '{contact_name}'."
    Activity.objects.create(contact=contact, kind="email", subject=subject, body=body, created_by=ctx["user"])
    contact.last_contacted_at = timezone.now()
    contact.save(update_fields=["last_contacted_at"])
    return f"Sent email to {contact.name} — “{subject}” (logged to timeline)."


def tool_search(ctx, query):
    contacts = Contact.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(company__name__icontains=query)
    )[:5]
    deals = Deal.objects.filter(Q(name__icontains=query) | Q(company__name__icontains=query))[:5]
    parts = []
    if contacts:
        parts.append("Contacts: " + ", ".join(f"{c.name} ({c.stage})" for c in contacts))
    if deals:
        parts.append("Deals: " + ", ".join(f"{d.name} [{d.stage}]" for d in deals))
    return " · ".join(parts) if parts else f"No contacts or deals match '{query}'."


def tool_summarize_contact(ctx, contact_name):
    c = _find_contact(contact_name)
    if not c:
        return f"No contact matching '{contact_name}'."
    deals = c.deals.exclude(stage__in=["won", "lost"])
    tasks = c.tasks.filter(completed_at__isnull=True)
    last = c.activities.first()
    bits = [f"{c.name} — {c.role or 'contact'}{' at ' + c.company.name if c.company else ''}, stage {c.stage}."]
    if deals:
        bits.append(f"{deals.count()} open deal(s): " + ", ".join(f"{d.name} (₹{float(d.value):,.0f}, {d.stage})" for d in deals))
    if tasks:
        bits.append(f"{tasks.count()} open task(s).")
    if last:
        bits.append(f"Last activity: {last.get_kind_display()} {('- ' + last.subject) if last.subject else ''}.")
    return " ".join(bits)


def tool_run_report(ctx):
    open_deals = Deal.objects.exclude(stage__in=["won", "lost"])
    agg = open_deals.aggregate(total=Sum("value"), weighted=Sum(WEIGHTED))
    by_stage = open_deals.values("stage").annotate(count=Count("id"), total=Sum("value")).order_by("stage")
    lines = [f"{r['stage']}: {r['count']} deals, ₹{(r['total'] or 0)/100000:.1f}L" for r in by_stage]
    return (f"Open pipeline ₹{(agg['total'] or 0)/100000:.1f}L, weighted "
            f"₹{(agg['weighted'] or 0)/100000:.1f}L. " + " · ".join(lines))


TOOLS = {
    "create_contact": tool_create_contact, "update_contact": tool_update_contact,
    "create_deal": tool_create_deal, "move_deal": tool_move_deal, "update_deal": tool_update_deal,
    "create_task": tool_create_task, "log_activity": tool_log_activity, "send_email": tool_send_email,
    "search": tool_search, "summarize_contact": tool_summarize_contact, "run_report": tool_run_report,
}

TOOL_SCHEMAS = [
    {"name": "create_contact", "description": "Create a new CRM contact.",
     "input_schema": {"type": "object", "properties": {
        "first_name": {"type": "string"}, "last_name": {"type": "string"}, "email": {"type": "string"},
        "role": {"type": "string"}, "company": {"type": "string"},
        "stage": {"type": "string", "enum": ["lead", "prospect", "customer"]}}, "required": ["first_name"]}},
    {"name": "update_contact", "description": "Update an existing contact's stage, role, or email. Match by name.",
     "input_schema": {"type": "object", "properties": {
        "contact_name": {"type": "string"}, "stage": {"type": "string", "enum": ["lead", "prospect", "customer"]},
        "role": {"type": "string"}, "email": {"type": "string"}}, "required": ["contact_name"]}},
    {"name": "create_deal", "description": "Create a new deal, optionally linked to a contact.",
     "input_schema": {"type": "object", "properties": {
        "name": {"type": "string"}, "contact_name": {"type": "string"}, "value": {"type": "number"},
        "stage": {"type": "string", "enum": ["qualified", "proposal", "negotiation", "won", "lost"]}}, "required": ["name"]}},
    {"name": "move_deal", "description": "Move a deal to a different pipeline stage. Match by name.",
     "input_schema": {"type": "object", "properties": {
        "deal_name": {"type": "string"}, "stage": {"type": "string", "enum": ["qualified", "proposal", "negotiation", "won", "lost"]}},
        "required": ["deal_name", "stage"]}},
    {"name": "update_deal", "description": "Update a deal's value, probability, or name. Match by name.",
     "input_schema": {"type": "object", "properties": {
        "deal_name": {"type": "string"}, "value": {"type": "number"}, "probability": {"type": "integer"}, "name": {"type": "string"}},
        "required": ["deal_name"]}},
    {"name": "create_task", "description": "Create a task, optionally linked to a contact and due in N days.",
     "input_schema": {"type": "object", "properties": {
        "title": {"type": "string"}, "contact_name": {"type": "string"}, "due_in_days": {"type": "integer"}}, "required": ["title"]}},
    {"name": "log_activity", "description": "Log an activity (email, call, whatsapp, note) against a contact.",
     "input_schema": {"type": "object", "properties": {
        "contact_name": {"type": "string"}, "kind": {"type": "string", "enum": ["email", "call", "whatsapp", "note"]},
        "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["contact_name", "kind"]}},
    {"name": "send_email", "description": "Draft and send an email to a contact. This is OUTBOUND and requires operator approval — draft a clear subject and body.",
     "input_schema": {"type": "object", "properties": {
        "contact_name": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
        "required": ["contact_name", "subject", "body"]}},
    {"name": "search", "description": "Search contacts and deals by name or company. Read-only.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "summarize_contact", "description": "Summarize a contact: open deals, open tasks, last activity. Read-only.",
     "input_schema": {"type": "object", "properties": {"contact_name": {"type": "string"}}, "required": ["contact_name"]}},
    {"name": "run_report", "description": "Compute a live pipeline-health summary. Read-only.",
     "input_schema": {"type": "object", "properties": {}}},
]


def execute_tool(ctx, name, args):
    fn = TOOLS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(ctx, **args)
    except TypeError as e:
        return f"Bad arguments for {name}: {e}"


def _handle(ctx, name, args, steps, gates):
    """Run a tool, or queue it as a gate if it's gated. Returns the result string."""
    steps.append({"type": "tool", "name": name, "input": args})
    if name in GATED:
        gates.append({"name": name, "input": args, "approved": False, "cancelled": False})
        preview = args.get("body") or args.get("subject") or ""
        steps.append({"type": "gate", "name": name, "input": args, "preview": preview,
                      "gate_index": len(gates) - 1})
        return f"Queued {name} for your approval."
    result = execute_tool(ctx, name, args)
    steps.append({"type": "result", "text": result})
    return result


# ── Claude planner ───────────────────────────────────────────
def _plan_with_claude(instruction, ctx, steps, gates):
    import anthropic
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": instruction}]
    summary = ""
    for _ in range(8):
        resp = client.messages.create(model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT,
                                      tools=TOOL_SCHEMAS, messages=messages)
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
                result = _handle(ctx, block.name, dict(block.input), steps, gates)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": results})
    return summary or "Done."


# ── deterministic offline planner ────────────────────────────
_STAGE_WORDS = {"qualified": "qualified", "proposal": "proposal", "negotiation": "negotiation",
                "won": "won", "win": "won", "lost": "lost", "close": "won"}


def _plan_offline(instruction, ctx, steps, gates):
    text = instruction.strip(); low = text.lower()
    calls = []

    # send email (gated)
    m = re.search(r"(?:send|draft|email|write)\s+(?:an?\s+)?(?:email|note)?\s*(?:to\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s+about\s+(.+))?", text)
    if ("email" in low or "draft" in low) and m:
        name = m.group(1); about = (m.group(2) or "a quick follow-up").strip().rstrip(".")
        calls.append(("send_email", {"contact_name": name,
                                     "subject": f"Following up: {about}",
                                     "body": f"Hi {name.split()[0]},\n\nJust following up about {about}. "
                                             f"Happy to jump on a quick call if useful.\n\nBest,\n{ctx['user'].first_name or 'the team'}"}))

    # move / mark deal
    if not calls:
        m = re.search(r"(?:move|mark|set|push|advance)\s+(.+?)\s+(?:to|as|into)\s+([a-z ]+)", low)
        if m:
            stage = next((v for k, v in _STAGE_WORDS.items() if k in m.group(2)), None)
            if stage:
                name = re.sub(r"\bdeal\b|the\b|['\"]", "", m.group(1)).strip()
                calls.append(("move_deal", {"deal_name": name, "stage": stage}))

    # update contact stage: "mark <name> as a customer/prospect/lead"
    if not calls:
        m = re.search(r"(?:mark|set|make)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:as\s+)?(?:an?\s+)?(customer|prospect|lead)", text)
        if m:
            calls.append(("update_contact", {"contact_name": m.group(1), "stage": m.group(2).lower()}))

    # create deal: "create a deal <name> for <contact> worth <n>"
    if not calls:
        m = re.search(r"(?:create|add|new)\s+(?:a\s+)?deal\s+(.+?)(?:\s+for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))?(?:\s+(?:worth|of|at)\s+₹?([\d,]+))?$", text)
        if m:
            args = {"name": m.group(1).strip().rstrip(".")}
            if m.group(2): args["contact_name"] = m.group(2)
            if m.group(3): args["value"] = float(m.group(3).replace(",", ""))
            calls.append(("create_deal", args))

    # task
    if not calls:
        m = re.search(r"(?:add|create|make)\s+(?:a\s+)?task\s+(?:to\s+)?(.+)", low) or re.search(r"remind me to\s+(.+)", low)
        if m:
            title = text[m.start(1):].strip().rstrip(".")
            cm = re.search(r"for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
            due = re.search(r"in\s+(\d+)\s*day", low)
            title = re.sub(r"\s+in\s+\d+\s*days?\b", "", title.split(" for ")[0], flags=re.I).strip()
            args = {"title": title}
            if cm: args["contact_name"] = cm.group(1)
            if due: args["due_in_days"] = int(due.group(1))
            calls.append(("create_task", args))

    # log activity
    if not calls:
        m = re.search(r"log(?:ged)?\s+(?:a\s+)?(call|email|whatsapp|note)\s+(?:with|on|to|for)\s+([A-Za-z ]+)", low)
        if m:
            name = re.search(r"(?:with|on|to|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
            calls.append(("log_activity", {"contact_name": name.group(1) if name else m.group(2).strip().title(), "kind": m.group(1)}))

    # summarize / brief
    if not calls:
        m = re.search(r"(?:summari[sz]e|brief me on|tell me about|catch me up on)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        if m:
            calls.append(("summarize_contact", {"contact_name": m.group(1)}))

    # search / find
    if not calls:
        m = re.search(r"(?:search|find|look up|who is)\s+(?:for\s+)?(.+)", low)
        if m and "report" not in low:
            calls.append(("search", {"query": text[m.start(1):].strip().rstrip("?.")}))

    # create contact
    if not calls:
        m = re.search(r"(?:add|create|new)\s+contact\s+([A-Z][a-z]+)\s*([A-Z][a-z]+)?(?:\s+at\s+(.+))?", text)
        if m:
            args = {"first_name": m.group(1)}
            if m.group(2): args["last_name"] = m.group(2)
            if m.group(3): args["company"] = m.group(3).strip().rstrip(".")
            calls.append(("create_contact", args))

    # report
    if not calls and ("report" in low or "pipeline" in low or "forecast" in low):
        calls.append(("run_report", {}))

    if not calls:
        steps.append({"type": "thought", "text":
            "Offline planner couldn't map that to a tool. Try e.g. \"move Q3 Bulk Order to won\", "
            "\"draft an email to Meera about the proforma\", \"summarize Arjun Khanna\", or set "
            "ANTHROPIC_API_KEY for full natural-language planning."})
        return "No matching action."

    steps.append({"type": "thought", "text": f"Planned {len(calls)} step(s) from your instruction."})
    last = "Done."
    for name, args in calls:
        last = _handle(ctx, name, args, steps, gates)
    return last


# ── public entrypoints ───────────────────────────────────────
def run(instruction, user):
    """Plan and execute. Persists an AgentRun and returns {run_id, engine, steps, summary, gates}."""
    ctx = {"user": user}
    steps, gates = [], []
    keyed = bool(os.environ.get("ANTHROPIC_API_KEY"))
    engine = "claude" if keyed else "offline"
    try:
        summary = _plan_with_claude(instruction, ctx, steps, gates) if keyed else _plan_offline(instruction, ctx, steps, gates)
    except Exception as e:
        steps.append({"type": "error", "text": f"{type(e).__name__}: {e}"})
        engine = "offline (claude failed)" if keyed else engine
        summary = _plan_offline(instruction, ctx, steps, gates) if keyed else "The copilot hit an error."
    run = AgentRun.objects.create(instruction=instruction, engine=engine, steps=steps,
                                  pending=gates, summary=summary, actor=user)
    return {"run_id": run.id, "engine": engine, "steps": steps, "summary": summary,
            "gates": gates, "status": run.status}


def approve(run_id, gate_index, user, cancel=False):
    """Approve (execute) or cancel a gated action from a persisted run."""
    try:
        run = AgentRun.objects.get(pk=run_id)
    except AgentRun.DoesNotExist:
        return {"detail": "run not found"}
    if gate_index < 0 or gate_index >= len(run.pending):
        return {"detail": "gate not found"}
    gate = run.pending[gate_index]
    if gate.get("approved") or gate.get("cancelled"):
        return {"detail": "already resolved", "gate": gate}
    if cancel:
        gate["cancelled"] = True
        result = f"Cancelled {gate['name']}."
    else:
        result = execute_tool({"user": user}, gate["name"], gate["input"])
        gate["approved"] = True
    run.pending[gate_index] = gate
    run.steps.append({"type": "result", "text": result})
    run.save(update_fields=["pending", "steps"])
    return {"run_id": run.id, "result": result, "cancelled": cancel, "status": run.status}
