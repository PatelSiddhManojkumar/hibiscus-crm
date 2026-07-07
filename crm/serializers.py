from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Activity, Automation, Company, Contact, Deal, Tag, Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class CompanySerializer(serializers.ModelSerializer):
    contact_count = serializers.IntegerField(source="contacts.count", read_only=True)

    class Meta:
        model = Company
        fields = ["id", "name", "domain", "industry", "contact_count", "created_at"]


class ContactSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True, default=None)
    owner_detail = UserSerializer(source="owner", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id", "name", "first_name", "last_name", "email", "phone", "role",
            "linkedin", "company", "company_name", "stage", "owner", "owner_detail",
            "tags", "tags_detail", "custom_fields", "created_at", "last_contacted_at",
        ]


class DealSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True, default=None)
    company_name = serializers.CharField(source="company.name", read_only=True, default=None)
    owner_detail = UserSerializer(source="owner", read_only=True)
    weighted_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id", "name", "contact", "contact_name", "company", "company_name",
            "value", "weighted_value", "stage", "probability", "close_date",
            "owner", "owner_detail", "stage_changed_at", "created_at",
        ]


class ActivitySerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source="created_by", read_only=True)
    deal_name = serializers.CharField(source="deal.name", read_only=True, default=None)

    class Meta:
        model = Activity
        fields = [
            "id", "contact", "deal", "deal_name", "kind", "subject", "body",
            "created_by", "created_by_detail", "created_at",
        ]
        read_only_fields = ["created_by"]


class TaskSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source="contact.name", read_only=True, default=None)
    deal_name = serializers.CharField(source="deal.name", read_only=True, default=None)
    assignee_detail = UserSerializer(source="assignee", read_only=True)
    blocked_by_title = serializers.CharField(source="blocked_by.title", read_only=True, default=None)

    class Meta:
        model = Task
        fields = [
            "id", "title", "contact", "contact_name", "deal", "deal_name",
            "assignee", "assignee_detail", "due_at", "completed_at",
            "recurrence", "blocked_by", "blocked_by_title", "created_at",
        ]


class AutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Automation
        fields = [
            "id", "name", "active", "trigger", "condition", "action",
            "script", "run_count", "last_run_at", "created_at",
        ]
