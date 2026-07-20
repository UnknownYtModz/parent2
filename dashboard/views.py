from django.core.management import call_command
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Student
from . import services


def ensure_seeded():
    """If the DB has no students yet, run the seed_demo management command."""
    if Student.objects.count() == 0:
        call_command("seed_demo")


@api_view(["GET"])
def student_list(request):
    ensure_seeded()
    students = Student.objects.all().order_by("name")
    data = [
        {
            "id": s.id,
            "name": s.name,
            "grade": s.grade,
            "class": s.student_class,
            "school": s.school,
        }
        for s in students
    ]
    return Response(data)


def _get_student_or_404(student_id):
    ensure_seeded()
    try:
        return Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return None


@api_view(["GET"])
def child_progress_report(request, student_id):
    student = _get_student_or_404(student_id)
    if student is None:
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(services.build_child_progress_report(student))


@api_view(["GET"])
def parent_impact_report(request, student_id):
    student = _get_student_or_404(student_id)
    if student is None:
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(services.build_parent_impact_report(student))


@api_view(["GET"])
def home_support_report(request, student_id):
    student = _get_student_or_404(student_id)
    if student is None:
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(services.build_home_support_report(student))
