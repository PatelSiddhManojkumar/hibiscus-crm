from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"companies", views.CompanyViewSet, basename="company")
router.register(r"tags", views.TagViewSet, basename="tag")
router.register(r"contacts", views.ContactViewSet, basename="contact")
router.register(r"deals", views.DealViewSet, basename="deal")
router.register(r"activities", views.ActivityViewSet, basename="activity")
router.register(r"tasks", views.TaskViewSet, basename="task")
router.register(r"automations", views.AutomationViewSet, basename="automation")
router.register(r"agent-runs", views.AgentRunViewSet, basename="agent-run")

urlpatterns = [
    path("auth/login/", views.login_view, name="api-login"),
    path("copilot/", views.copilot, name="copilot"),
    path("copilot/approve/", views.copilot_approve, name="copilot-approve"),
    path("insights/", views.insights, name="insights"),
    path("reports/summary/", views.report_summary, name="report-summary"),
    path("", include(router.urls)),
]
