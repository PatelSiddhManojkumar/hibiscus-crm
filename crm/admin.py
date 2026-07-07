from django.contrib import admin

from .models import Activity, Automation, Company, Contact, Deal, Tag, Task

admin.site.site_header = "Darvin CRM"

for model in (Company, Tag, Contact, Deal, Activity, Task, Automation):
    admin.site.register(model)
