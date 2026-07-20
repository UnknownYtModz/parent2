"""
URL configuration for parent_analytics project.

Serves both the JSON REST API (under /api/) and the static-ish HTML
frontend pages (via Django templates so they can share STATICFILES_DIRS).
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

frontend_pages = [
    ("", "index.html", "landing", {}),
    ("signin.html", "signin.html", "signin", {}),
    ("signup.html", "signup.html", "signup", {}),
    ("dashboard.html", "dashboard.html", "dashboard", {"portal_label": "Parent Portal"}),
    ("child-analysis.html", "child-analysis.html", "child-analysis", {"portal_label": "Parent Portal"}),
    ("parent-impact.html", "parent-impact.html", "parent-impact", {"portal_label": "Parent Portal"}),
    ("home-support.html", "home-support.html", "home-support", {"portal_label": "Parent Portal"}),
    ("teacher-dashboard.html", "teacher-dashboard.html", "teacher-dashboard", {"portal_label": "Teacher Portal"}),
    ("owner-dashboard.html", "owner-dashboard.html", "owner-dashboard", {"portal_label": "Org Owner Portal"}),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("dashboard.urls")),
]

urlpatterns += [
    path(route, TemplateView.as_view(template_name=template, extra_context=ctx), name=name)
    for route, template, name, ctx in frontend_pages
]
