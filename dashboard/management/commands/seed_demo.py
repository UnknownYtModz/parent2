import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import Student, Assessment, WellbeingLog, ParentActivity


SUBJECTS = ["Math", "Science", "English", "Social Studies"]
ACTIVITIES = [
    "homework_help",
    "reading_together",
    "screen_time_limit",
    "parent_teacher_chat",
    "outdoor_play",
    "praise_encouragement",
    "routine_check_in",
]
MOODS = ["thriving", "stable", "stressed", "struggling"]


def _mood_label_for_score(score):
    if score >= 7.5:
        return "thriving"
    if score >= 5.5:
        return "stable"
    if score >= 3.5:
        return "stressed"
    return "struggling"


class Command(BaseCommand):
    help = "Seed the database with a demo student (Aarav Shah) and historical data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks", type=int, default=12, help="How many weeks of history to generate."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        weeks = options["weeks"]
        random.seed(42)

        student, created = Student.objects.get_or_create(
            name="Aarav Shah",
            defaults={"grade": "8", "student_class": "B", "school": "Vridhi Demo School"},
        )
        if not created:
            self.stdout.write("Demo student already exists — skipping re-seed.")
            return

        today = date.today()
        start = today - timedelta(weeks=weeks)

        # Academic assessments: roughly 1 per subject every 2 weeks, with a
        # gentle upward trend and a couple of realistic dips.
        base_scores = {"Math": 58, "Science": 65, "English": 72, "Social Studies": 68}
        for week in range(0, weeks, 2):
            d = start + timedelta(weeks=week)
            for subject in SUBJECTS:
                drift = week * 0.9
                dip = -18 if week in (4, 5) and subject == "Math" else 0
                noise = random.uniform(-4, 4)
                score = max(30, min(98, base_scores[subject] + drift + dip + noise))
                Assessment.objects.create(
                    student=student,
                    subject=subject,
                    score=round(score, 1),
                    date=d,
                    term_label=f"Week {week + 1}",
                )

        # Wellbeing logs: weekly, with a dip aligned to the Math dip above.
        base_mood = 6.5
        for week in range(weeks):
            d = start + timedelta(weeks=week)
            dip = -3.0 if week in (4, 5) else 0
            drift = week * 0.05
            noise = random.uniform(-0.6, 0.6)
            mood = max(1.0, min(10.0, base_mood + drift + dip + noise))
            WellbeingLog.objects.create(
                student=student,
                date=d,
                mood_score=round(mood, 1),
                mood_label=_mood_label_for_score(mood),
                sleep_hours=round(max(4.5, min(9.5, 7.2 + dip * 0.2 + random.uniform(-0.5, 0.5))), 1),
                note="Auto-generated demo entry.",
            )

        # Parent activities: a handful per week across varied activity types.
        for week in range(weeks):
            d = start + timedelta(weeks=week)
            sessions_this_week = random.randint(2, 5)
            for i in range(sessions_this_week):
                activity_type = random.choice(ACTIVITIES)
                ParentActivity.objects.create(
                    student=student,
                    activity_type=activity_type,
                    date=d + timedelta(days=random.randint(0, 6)),
                    duration_minutes=random.choice([10, 15, 20, 30, 45]),
                    notes="Auto-generated demo entry.",
                )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded demo student '{student.name}' with {weeks} weeks of history."
        ))
