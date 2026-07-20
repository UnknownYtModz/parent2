from django.db import models


class Student(models.Model):
    """A student tracked by the growth analytics engine."""

    name = models.CharField(max_length=150)
    grade = models.CharField(max_length=20, default="8")
    student_class = models.CharField(max_length=20, default="A", db_column="class")
    school = models.CharField(max_length=150, blank=True, default="Vridhi Demo School")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Grade {self.grade}{self.student_class})"


class Assessment(models.Model):
    """A single academic assessment / test score for a student over time."""

    SUBJECT_CHOICES = [
        ("Math", "Math"),
        ("Science", "Science"),
        ("English", "English"),
        ("Social Studies", "Social Studies"),
    ]

    student = models.ForeignKey(Student, related_name="assessments", on_delete=models.CASCADE)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default="Math")
    score = models.FloatField(help_text="Score out of 100")
    max_score = models.FloatField(default=100)
    date = models.DateField()
    term_label = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.student.name} - {self.subject} - {self.score}"


class WellbeingLog(models.Model):
    """A periodic emotional / wellbeing check-in for a student."""

    MOOD_CHOICES = [
        ("thriving", "Thriving"),
        ("stable", "Stable"),
        ("stressed", "Stressed"),
        ("struggling", "Struggling"),
    ]

    student = models.ForeignKey(Student, related_name="wellbeing_logs", on_delete=models.CASCADE)
    date = models.DateField()
    mood_score = models.FloatField(help_text="0-10 wellbeing index")
    mood_label = models.CharField(max_length=20, choices=MOOD_CHOICES, default="stable")
    sleep_hours = models.FloatField(default=7.5)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.mood_label}"


class ParentActivity(models.Model):
    """A logged parent-child engagement activity, used for impact analysis."""

    ACTIVITY_CHOICES = [
        ("homework_help", "Homework Help"),
        ("reading_together", "Reading Together"),
        ("screen_time_limit", "Screen Time Limit"),
        ("parent_teacher_chat", "Parent-Teacher Chat"),
        ("outdoor_play", "Outdoor Play"),
        ("praise_encouragement", "Praise & Encouragement"),
        ("routine_check_in", "Routine Check-in"),
    ]

    student = models.ForeignKey(Student, related_name="parent_activities", on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    date = models.DateField()
    duration_minutes = models.PositiveIntegerField(default=20)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.student.name} - {self.activity_type} - {self.date}"
