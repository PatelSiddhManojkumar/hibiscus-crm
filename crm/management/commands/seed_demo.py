"""Seed Darvin with demo data: `python manage.py seed_demo`.
Creates admin/darvin2026 plus two operators, companies, contacts, deals,
activities, tasks, and automations. Idempotent-ish: skips if contacts exist."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Activity, Automation, Company, Contact, Deal, Tag, Task


class Command(BaseCommand):
    help = "Seed demo data for Darvin CRM"

    def handle(self, *args, **options):
        if Contact.objects.exists():
            self.stdout.write("Data already present — skipping seed.")
            return

        now = timezone.now()

        admin, _ = User.objects.get_or_create(
            username="admin", defaults={"is_staff": True, "is_superuser": True, "first_name": "S.", "last_name": "Patel"})
        admin.set_password("darvin2026"); admin.save()
        ravi = User.objects.create_user("ravi", password="darvin2026", first_name="R.", last_name="Iyer")
        nisha = User.objects.create_user("nisha", password="darvin2026", first_name="N.", last_name="Rao")

        t_tex = Tag.objects.create(name="textiles", color="thulian")
        t_south = Tag.objects.create(name="south-india", color="brook")
        t_prio = Tag.objects.create(name="priority", color="olive")

        companies = {}
        for name, domain, industry in [
            ("Svaram Textiles", "svaramtextiles.in", "Textiles"),
            ("Deccan Logistics", "deccanlogistics.in", "Logistics"),
            ("Porto Ceramics", "portoceramics.pt", "Ceramics"),
            ("Harbourline Pte", "harbourline.sg", "Freight"),
            ("Kolam Foods", "kolamfoods.in", "FMCG"),
            ("Atlas Trading Co", "atlastrading.ma", "Trading"),
        ]:
            companies[name] = Company.objects.create(name=name, domain=domain, industry=industry)

        def contact(first, last, email, role, co, stage, owner, days_ago, tags=()):
            c = Contact.objects.create(
                first_name=first, last_name=last, email=email, role=role,
                company=companies[co], stage=stage, owner=owner,
                last_contacted_at=now - timedelta(days=days_ago),
            )
            c.tags.set(tags)
            return c

        meera = contact("Meera", "Raghavan", "meera@svaramtextiles.in", "Head of Procurement",
                        "Svaram Textiles", "customer", admin, 2, [t_tex, t_south, t_prio])
        arjun = contact("Arjun", "Khanna", "arjun@deccanlogistics.in", "Operations Director",
                        "Deccan Logistics", "prospect", admin, 0)
        lucia = contact("Lucia", "Ferreira", "lucia@portoceramics.pt", "Founder",
                        "Porto Ceramics", "customer", ravi, 1)
        thomas = contact("Thomas", "Ng", "thomas@harbourline.sg", "Procurement Lead",
                         "Harbourline Pte", "prospect", ravi, 3)
        priya = contact("Priya", "Deshmukh", "priya@kolamfoods.in", "CEO",
                        "Kolam Foods", "lead", admin, 7)
        hakim = contact("Hakim", "Benali", "hakim@atlastrading.ma", "Managing Partner",
                        "Atlas Trading Co", "customer", nisha, 0, [t_prio])

        def deal(name, c, value, stage, owner, close_days, stage_days_ago):
            d = Deal.objects.create(
                name=name, contact=c, company=c.company, value=value,
                stage=stage, probability=Deal.DEFAULT_PROBABILITY[stage],
                owner=owner, close_date=(now + timedelta(days=close_days)).date(),
            )
            Deal.objects.filter(pk=d.pk).update(stage_changed_at=now - timedelta(days=stage_days_ago))
            return d

        q3 = deal("Q3 Bulk Order", meera, 1420000, "negotiation", admin, 22, 4)
        deal("Annual Supply Contract", meera, 4800000, "proposal", admin, 86, 30)
        deal("Retail Line Extension", lucia, 1210000, "negotiation", ravi, 15, 9)
        deal("Container Trial Run", thomas, 1080000, "qualified", ravi, 40, 2)
        deal("Packaging Refresh Pilot", priya, 380000, "qualified", admin, 35, 6)
        deal("Ramadan Season Stock", hakim, 890000, "proposal", nisha, 28, 25)
        deal("Uniform Programme", arjun, 450000, "proposal", admin, 30, 3)
        for name, c, v, days in [("Summer Catalogue Order", lucia, 940000, 20),
                                 ("Q2 Restock", hakim, 1560000, 35),
                                 ("Festive Packaging", priya, 670000, 50),
                                 ("Spring Sampler", thomas, 310000, 80),
                                 ("Winter Line", lucia, 1240000, 110),
                                 ("New Year Stock", hakim, 820000, 140)]:
            d = deal(name, c, v, "won", ravi, 0, days)

        def act(c, kind, subject, body, by, hours_ago, d=None):
            a = Activity.objects.create(contact=c, deal=d, kind=kind, subject=subject, body=body, created_by=by)
            Activity.objects.filter(pk=a.pk).update(created_at=now - timedelta(hours=hours_ago))

        act(meera, "email", "Re: Q3 fabric order — revised quantities",
            "Confirming the increase to 4,000 units. Can we split delivery across two dates?", admin, 40, q3)
        act(meera, "call", "Pricing discussion — 22 min",
            "Needs board sign-off above 12L. Follow-up scheduled.", admin, 170, q3)
        act(meera, "note", "",
            "Prefers WhatsApp for anything urgent. Never call before 10am.", admin, 175)
        act(hakim, "whatsapp", "Stock query — Amaranth line",
            "Do you have the 40-count in stock for August?", nisha, 5)
        act(lucia, "email", "Retail line — final artwork approval",
            "The board approved option B. Signed copy attached.", ravi, 28)
        act(arjun, "call", "Missed call — voicemail 0:42",
            "Calling about the uniform programme quote.", admin, 20)

        Task.objects.create(title="Send updated proforma — split delivery", contact=meera, deal=q3,
                            assignee=admin, due_at=now - timedelta(days=2))
        follow = Task.objects.create(title="Follow-up call — board sign-off status", contact=meera, deal=q3,
                                     assignee=admin, due_at=now + timedelta(hours=5))
        Task.objects.create(title="Draft split-delivery schedule", contact=meera, deal=q3,
                            assignee=ravi, due_at=now + timedelta(days=1), blocked_by=follow)
        Task.objects.create(title="Return Arjun's voicemail re: uniforms", contact=arjun,
                            assignee=admin, due_at=now - timedelta(days=1))
        Task.objects.create(title="Weekly pipeline review", assignee=admin,
                            due_at=now + timedelta(days=1), recurrence="weekly")
        Task.objects.create(title="Reopen trade-fair prospect list — first 50", assignee=nisha,
                            due_at=now + timedelta(days=4))

        Automation.objects.create(
            name="Stale proposal flag", trigger="daily 07:00",
            condition='deal.stage == "proposal" and stage_age_days > 21',
            action='create_task("Revive or close: {deal.name}", due="+2d") and tag("stale")',
            run_count=14, last_run_at=now - timedelta(hours=8),
        )
        Automation.objects.create(
            name="Deal won → invoice task", trigger="deal.stage_changed",
            condition='deal.stage == "won"',
            action='create_task("Raise invoice: {deal.name}", assignee=deal.owner)',
            run_count=3, last_run_at=now - timedelta(days=1),
        )
        Automation.objects.create(
            name="Weekly pipeline digest", trigger="weekly mon 08:00",
            action='email(owners, report("pipeline-health"))',
            run_count=27, last_run_at=now - timedelta(days=1),
        )

        self.stdout.write(self.style.SUCCESS(
            "Seeded. Users: admin / ravi / nisha — password: darvin2026"))
