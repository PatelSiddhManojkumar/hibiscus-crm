from datetime import timedelta

from django.contrib.auth import authenticate
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Activity, Automation, Company, Contact, Deal, Tag, Task
from .serializers import (
    ActivitySerializer, AutomationSerializer, CompanySerializer,
    ContactSerializer, DealSerializer, TagSerializer, TaskSerializer,
    UserSerializer,
)

WEIGHTED = ExpressionWrapper(
    F("value") * F("probability") / 100.0,
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        username=request.data.get("username", ""),
        password=request.data.get("password", ""),
    )
    if not user:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    search_fields = ["name", "domain", "industry"]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    search_fields = ["first_name", "last_name", "email", "role", "company__name"]
    ordering_fields = ["created_at", "last_contacted_at", "first_name"]

    def get_queryset(self):
        qs = Contact.objects.select_related("company", "owner").prefetch_related("tags")
        stage = self.request.query_params.get("stage")
        owner = self.request.query_params.get("owner")
        if stage:
            qs = qs.filter(stage=stage)
        if owner:
            qs = qs.filter(owner_id=owner)
        return qs

    def perform_create(self, serializer):
        contact = serializer.save()
        Activity.objects.create(
            contact=contact, kind="system",
            subject="Contact created",
            created_by=self.request.user,
        )

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        acts = self.get_object().activities.select_related("created_by", "deal")
        return Response(ActivitySerializer(acts, many=True).data)

    @action(detail=True, methods=["post"])
    def merge(self, request, pk=None):
        """Merge another contact into this one (activities, deals, tasks move here)."""
        target = self.get_object()
        try:
            source = Contact.objects.get(pk=request.data.get("source_id"))
        except Contact.DoesNotExist:
            return Response({"detail": "source_id not found."}, status=404)
        source.activities.update(contact=target)
        source.deals.update(contact=target)
        source.tasks.update(contact=target)
        target.tags.add(*source.tags.all())
        source.delete()
        Activity.objects.create(
            contact=target, kind="system",
            subject=f"Merged duplicate contact #{request.data.get('source_id')}",
            created_by=request.user,
        )
        return Response(ContactSerializer(target).data)


class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer
    search_fields = ["name", "company__name", "contact__first_name", "contact__last_name"]
    ordering_fields = ["value", "close_date", "created_at"]

    def get_queryset(self):
        qs = Deal.objects.select_related("contact", "company", "owner")
        stage = self.request.query_params.get("stage")
        if stage:
            qs = qs.filter(stage=stage)
        return qs

    def perform_update(self, serializer):
        old = self.get_object()
        deal = serializer.save()
        if old.stage != deal.stage:
            deal.probability = Deal.DEFAULT_PROBABILITY.get(deal.stage, deal.probability)
            deal.stage_changed_at = timezone.now()
            deal.save(update_fields=["probability", "stage_changed_at"])
            Activity.objects.create(
                contact=deal.contact, deal=deal, kind="system",
                subject=f'Deal moved {old.get_stage_display()} → {deal.get_stage_display()}',
                created_by=self.request.user,
            )

    @action(detail=False, methods=["get"])
    def board(self, request):
        """Kanban payload: deals grouped by stage with count + value rollups."""
        board = []
        for key, label in Deal.STAGES:
            qs = self.get_queryset().filter(stage=key)
            agg = qs.aggregate(total=Sum("value"), weighted=Sum(WEIGHTED))
            board.append({
                "stage": key, "label": label,
                "count": qs.count(),
                "total": agg["total"] or 0,
                "weighted": agg["weighted"] or 0,
                "deals": DealSerializer(qs, many=True).data,
            })
        return Response(board)


class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    search_fields = ["subject", "body"]

    def get_queryset(self):
        qs = Activity.objects.select_related("contact", "deal", "created_by")
        contact = self.request.query_params.get("contact")
        kind = self.request.query_params.get("kind")
        if contact:
            qs = qs.filter(contact_id=contact)
        if kind:
            qs = qs.filter(kind=kind)
        return qs

    def perform_create(self, serializer):
        activity = serializer.save(created_by=self.request.user)
        if activity.contact and activity.kind in ("email", "call", "whatsapp"):
            activity.contact.last_contacted_at = activity.created_at
            activity.contact.save(update_fields=["last_contacted_at"])


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    search_fields = ["title"]
    ordering_fields = ["due_at", "created_at"]

    def get_queryset(self):
        qs = Task.objects.select_related("contact", "deal", "assignee", "blocked_by")
        if self.request.query_params.get("open") == "1":
            qs = qs.filter(completed_at__isnull=True)
        assignee = self.request.query_params.get("assignee")
        if assignee == "me":
            qs = qs.filter(assignee=self.request.user)
        elif assignee:
            qs = qs.filter(assignee_id=assignee)
        return qs

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.completed_at = timezone.now()
        task.save(update_fields=["completed_at"])
        # Recurring tasks respawn on completion
        if task.recurrence:
            delta = {"daily": 1, "weekly": 7, "monthly": 30}[task.recurrence]
            Task.objects.create(
                title=task.title, contact=task.contact, deal=task.deal,
                assignee=task.assignee, recurrence=task.recurrence,
                due_at=(task.due_at or timezone.now()) + timedelta(days=delta),
            )
        return Response(TaskSerializer(task).data)


class AutomationViewSet(viewsets.ModelViewSet):
    queryset = Automation.objects.order_by("-active", "name")
    serializer_class = AutomationSerializer

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """Manual trigger. Ships with one built-in rule: stale-proposal flagging."""
        auto = self.get_object()
        created = 0
        if "stale" in auto.name.lower() or "proposal" in (auto.condition or ""):
            cutoff = timezone.now() - timedelta(days=21)
            stale = Deal.objects.filter(stage="proposal", stage_changed_at__lt=cutoff)
            for deal in stale:
                title = f"Revive or close: {deal.name}"
                exists = Task.objects.filter(
                    title=title, deal=deal, completed_at__isnull=True
                ).exists()
                if not exists:
                    Task.objects.create(
                        title=title, deal=deal, contact=deal.contact,
                        assignee=deal.owner,
                        due_at=timezone.now() + timedelta(days=2),
                    )
                    created += 1
        auto.run_count += 1
        auto.last_run_at = timezone.now()
        auto.save(update_fields=["run_count", "last_run_at"])
        return Response({"ran": True, "tasks_created": created})


@api_view(["POST"])
def copilot(request):
    """Hibiscus Copilot — plan and execute a natural-language instruction via CRM tools."""
    from . import copilot as copilot_engine
    instruction = (request.data.get("instruction") or "").strip()
    if not instruction:
        return Response({"detail": "instruction is required."}, status=400)
    result = copilot_engine.run(instruction, request.user)
    return Response(result)


@api_view(["GET"])
def report_summary(request):
    """Aggregates for the editorial report: pipeline by stage, won by month, stats."""
    open_deals = Deal.objects.exclude(stage__in=["won", "lost"])
    by_stage = list(
        open_deals.values("stage")
        .annotate(count=Count("id"), total=Sum("value"), weighted=Sum(WEIGHTED))
        .order_by("stage")
    )
    won_by_month = list(
        Deal.objects.filter(stage="won")
        .annotate(month=TruncMonth("stage_changed_at"))
        .values("month")
        .annotate(total=Sum("value"), count=Count("id"))
        .order_by("month")
    )
    totals = open_deals.aggregate(total=Sum("value"), weighted=Sum(WEIGHTED))
    return Response({
        "generated_at": timezone.now(),
        "open_total": totals["total"] or 0,
        "open_weighted": totals["weighted"] or 0,
        "contact_count": Contact.objects.count(),
        "open_task_count": Task.objects.filter(completed_at__isnull=True).count(),
        "by_stage": by_stage,
        "won_by_month": won_by_month,
    })
