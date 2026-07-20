from django.urls import path
from . import views

urlpatterns = [
    path("students/", views.student_list, name="student-list"),
    path("students/<int:student_id>/reports/child-progress/", views.child_progress_report, name="child-progress"),
    path("students/<int:student_id>/reports/parent-impact/", views.parent_impact_report, name="parent-impact"),
    path("students/<int:student_id>/reports/home-support/", views.home_support_report, name="home-support"),
]
