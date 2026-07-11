"""Hibiscus CRM core models: companies, contacts, deals, activities, tasks, automations."""
from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    domain = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    COLORS = [("thulian", "Thulian"), ("brook", "Brook"), ("olive", "Olive")]
    name = models.CharField(max_length=60, unique=True)
    color = models.CharField(max_length=10, choices=COLORS, default="olive")

    def __str__(self):
        return self.name


class Contact(models.Model):
    STAGES = [("lead", "Lead"), ("prospect", "Prospect"), ("customer", "Customer")]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    role = models.CharField(max_length=120, blank=True)
    linkedin = models.URLField(blank=True)
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name="contacts")
    stage = models.CharField(max_length=10, choices=STAGES, default="lead")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="contacts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")
    custom_fields = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_contacted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_contacted_at", "-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def name(self):
        return str(self)


class Deal(models.Model):
    STAGES = [
        ("qualified", "Qualified"),
        ("proposal", "Proposal"),
        ("negotiation", "Negotiation"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]
    DEFAULT_PROBABILITY = {"qualified": 20, "proposal": 40, "negotiation": 70, "won": 100, "lost": 0}

    name = models.CharField(max_length=200)
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    stage = models.CharField(max_length=12, choices=STAGES, default="qualified")
    probability = models.PositiveSmallIntegerField(default=20)
    close_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    stage_changed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def weighted_value(self):
        return self.value * self.probability / 100


class Activity(models.Model):
    """Unified timeline: emails, calls, whatsapp, notes, and system events."""
    KINDS = [
        ("email", "Email"),
        ("call", "Call"),
        ("whatsapp", "WhatsApp"),
        ("note", "Note"),
        ("system", "System"),
    ]
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.CASCADE, related_name="activities")
    deal = models.ForeignKey(Deal, null=True, blank=True, on_delete=models.CASCADE, related_name="activities")
    kind = models.CharField(max_length=10, choices=KINDS, default="note")
    subject = models.CharField(max_length=250, blank=True)
    body = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind}: {self.subject or self.body[:40]}"


class Task(models.Model):
    RECURRENCES = [("", "None"), ("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")]
    title = models.CharField(max_length=250)
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    deal = models.ForeignKey(Deal, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    recurrence = models.CharField(max_length=10, choices=RECURRENCES, blank=True, default="")
    blocked_by = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="blocks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completed_at", "due_at"]

    def __str__(self):
        return self.title


class Automation(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    trigger = models.CharField(max_length=200, help_text='e.g. "daily 07:00" or "deal.stage_changed"')
    condition = models.CharField(max_length=400, blank=True, help_text='e.g. deal.stage == "proposal" and stage_age_days > 21')
    action = models.CharField(max_length=400, help_text='e.g. create_task("Revive or close: {deal.name}")')
    script = models.TextField(blank=True)
    run_count = models.PositiveIntegerField(default=0)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AgentRun(models.Model):
    """A persisted Copilot run — the flight recorder for the Agent Console."""
    instruction = models.TextField()
    engine = models.CharField(max_length=40, default="offline")
    steps = models.JSONField(default=list)       # the plan -> tool -> result transcript
    pending = models.JSONField(default=list)     # gated actions awaiting approval
    summary = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Run {self.id}: {self.instruction[:50]}"

    @property
    def status(self):
        if any(not g.get("approved") and not g.get("cancelled") for g in self.pending):
            return "awaiting_approval"
        return "done"
