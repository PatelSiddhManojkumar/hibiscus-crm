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

urlpatterns = [
    path("auth/login/", views.login_view, name="api-login"),
    path("reports/summary/", views.report_summary, name="report-summary"),
    path("", include(router.urls)),
]
