"""
Analytics engine for Vridhi Parent Analytics.

Pure-python business logic that turns raw Assessment / WellbeingLog /
ParentActivity rows into the three report payloads the frontend expects:

    - child-progress   (growth score, trajectory, timelines, critical events)
    - parent-impact    (parent involvement score, communication effectiveness)
    - home-support     (learning profile, do's & don'ts, weekly plan)

Kept deliberately dependency-free (no numpy/pandas) so the project installs
with just Django + DRF, per requirements.txt.
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_mean(values):
    values = [v for v in values if v is not None]
    return round(statistics.mean(values), 2) if values else 0.0


def _pearson(xs, ys):
    """Simple Pearson correlation coefficient, 0 if not computable."""
    n = min(len(xs), len(ys))
    if n < 2:
        return 0.0
    xs, ys = xs[:n], ys[:n]
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 2)


def _trend(values):
    """Return 'up' | 'down' | 'flat' comparing first half vs second half."""
    if len(values) < 2:
        return "flat"
    mid = len(values) // 2
    first, second = values[:mid] or values[:1], values[mid:]
    delta = _safe_mean(second) - _safe_mean(first)
    if delta > 2:
        return "up"
    if delta < -2:
        return "down"
    return "flat"


# ---------------------------------------------------------------------------
# Report 1: Child Progress
# ---------------------------------------------------------------------------

def build_child_progress_report(student):
    assessments = list(student.assessments.all())
    wellbeing = list(student.wellbeing_logs.all())

    academic_timeline = [
        {
            "date": a.date.isoformat(),
            "subject": a.subject,
            "score": a.score,
        }
        for a in assessments
    ]

    emotional_timeline = [
        {
            "date": w.date.isoformat(),
            "mood_score": w.mood_score,
            "mood_label": w.mood_label,
            "sleep_hours": w.sleep_hours,
        }
        for w in wellbeing
    ]

    academic_scores = [a.score for a in assessments]
    mood_scores = [w.mood_score for w in wellbeing]

    academic_avg = _safe_mean(academic_scores)
    mood_avg = _safe_mean(mood_scores)
    academic_trend = _trend(academic_scores)
    mood_trend = _trend(mood_scores)

    # Growth score blends academic performance with wellbeing stability.
    growth_score = round(min(100, max(0, academic_avg * 0.7 + mood_avg * 10 * 0.3)), 1)

    if growth_score >= 80:
        phase = "Accelerating"
    elif growth_score >= 60:
        phase = "Steady Growth"
    elif growth_score >= 40:
        phase = "Needs Support"
    else:
        phase = "At Risk"

    critical_events = []
    for w in wellbeing:
        if w.mood_score <= 3.5:
            critical_events.append({
                "date": w.date.isoformat(),
                "type": "wellbeing_dip",
                "description": f"Wellbeing dropped to {w.mood_score}/10 ({w.mood_label}).",
            })
    for a in assessments:
        if a.score < 50:
            critical_events.append({
                "date": a.date.isoformat(),
                "type": "academic_dip",
                "description": f"{a.subject} score fell to {a.score}.",
            })
    critical_events.sort(key=lambda e: e["date"])

    insights = []
    corr = _pearson(mood_scores, academic_scores)
    if corr >= 0.5:
        insights.append(
            "Strong positive link between wellbeing and academic scores — "
            "supporting emotional health is likely to lift grades directly."
        )
    elif corr <= -0.3:
        insights.append(
            "Academic pressure may be weighing on wellbeing — consider "
            "easing workload during high-stress periods."
        )
    else:
        insights.append(
            "Wellbeing and academics are moving independently right now."
        )

    if academic_trend == "up":
        insights.append("Academic performance is trending upward over the recent period.")
    elif academic_trend == "down":
        insights.append("Academic performance has been trending downward — worth a check-in.")

    if mood_trend == "down":
        insights.append("Emotional wellbeing has dipped recently.")

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "class": student.student_class,
            "school": student.school,
        },
        "growth_snapshot": {
            "growth_score": growth_score,
            "phase": phase,
            "academic_average": academic_avg,
            "wellbeing_average": mood_avg,
            "academic_trend": academic_trend,
            "wellbeing_trend": mood_trend,
            "wellbeing_academic_correlation": corr,
        },
        "academic_timeline": academic_timeline,
        "emotional_timeline": emotional_timeline,
        "critical_events": critical_events,
        "insights": insights,
    }


# ---------------------------------------------------------------------------
# Report 2: Parent Impact
# ---------------------------------------------------------------------------

def build_parent_impact_report(student):
    activities = list(student.parent_activities.all())
    assessments = list(student.assessments.all())

    total_minutes = sum(a.duration_minutes for a in activities)
    activity_count = len(activities)

    impact_by_activity = {}
    for a in activities:
        bucket = impact_by_activity.setdefault(a.activity_type, {
            "activity_type": a.activity_type,
            "sessions": 0,
            "total_minutes": 0,
        })
        bucket["sessions"] += 1
        bucket["total_minutes"] += a.duration_minutes

    impact_by_activity_list = sorted(
        impact_by_activity.values(), key=lambda b: b["total_minutes"], reverse=True
    )

    # Parent involvement score: weighted by frequency + minutes, capped 0-100.
    weeks_span = 8
    sessions_per_week = activity_count / weeks_span if weeks_span else 0
    parent_impact_score = round(
        min(100, sessions_per_week * 12 + (total_minutes / max(activity_count, 1)) * 0.4), 1
    )

    optimal_band = {"low": 55, "high": 85}

    # Communication effectiveness: correlate parent_teacher_chat frequency
    # with academic scores in the following window.
    chat_dates = sorted(a.date for a in activities if a.activity_type == "parent_teacher_chat")
    academic_scores = [a.score for a in assessments]
    communication_effectiveness = "insufficient_data"
    if chat_dates and academic_scores:
        pre_avg = _safe_mean(academic_scores[: len(academic_scores) // 2] or academic_scores)
        post_avg = _safe_mean(academic_scores[len(academic_scores) // 2:] or academic_scores)
        if post_avg - pre_avg > 2:
            communication_effectiveness = "positive"
        elif post_avg - pre_avg < -2:
            communication_effectiveness = "declining"
        else:
            communication_effectiveness = "stable"

    if parent_impact_score < optimal_band["low"]:
        behavior_signal = "Increase engagement frequency — currently below the optimal involvement band."
    elif parent_impact_score > optimal_band["high"]:
        behavior_signal = "Engagement is very high — ensure it stays supportive rather than pressuring."
    else:
        behavior_signal = "Engagement sits within the optimal band. Keep the current rhythm going."

    return {
        "student_id": student.id,
        "parent_impact_score": parent_impact_score,
        "optimal_band": optimal_band,
        "communication_effectiveness": communication_effectiveness,
        "impact_by_activity": impact_by_activity_list,
        "behavior_signal": behavior_signal,
        "total_engagement_minutes": total_minutes,
        "total_sessions": activity_count,
    }


# ---------------------------------------------------------------------------
# Report 3: Home Support Plan
# ---------------------------------------------------------------------------

_SUBJECT_TIPS = {
    "Math": {
        "do": "Break problems into smaller steps and celebrate each correct step.",
        "dont": "Don't rush through problem sets against the clock — it raises anxiety.",
    },
    "Science": {
        "do": "Connect concepts to everyday objects and hands-on experiments.",
        "dont": "Don't rely only on memorising definitions without context.",
    },
    "English": {
        "do": "Encourage daily reading aloud and discussing the story together.",
        "dont": "Don't correct every small grammar mistake mid-sentence.",
    },
    "Social Studies": {
        "do": "Use maps, timelines and current events to make topics concrete.",
        "dont": "Don't reduce it to rote date-and-name memorisation.",
    },
}

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_home_support_report(student):
    assessments = list(student.assessments.all())
    wellbeing = list(student.wellbeing_logs.all())

    subject_scores = {}
    for a in assessments:
        subject_scores.setdefault(a.subject, []).append(a.score)

    strongest_subject, weakest_subject = None, None
    if subject_scores:
        averaged = {s: _safe_mean(v) for s, v in subject_scores.items()}
        strongest_subject = max(averaged, key=averaged.get)
        weakest_subject = min(averaged, key=averaged.get)

    mood_scores = [w.mood_score for w in wellbeing]
    avg_mood = _safe_mean(mood_scores)
    avg_sleep = _safe_mean([w.sleep_hours for w in wellbeing])

    if avg_mood >= 7:
        learning_style_note = "Confident and resilient learner — responds well to challenge."
    elif avg_mood >= 5:
        learning_style_note = "Generally steady, but benefits from consistent encouragement."
    else:
        learning_style_note = "Currently more sensitive to stress — needs a calm, low-pressure environment."

    learning_profile = {
        "strongest_subject": strongest_subject,
        "weakest_subject": weakest_subject,
        "average_wellbeing": avg_mood,
        "average_sleep_hours": avg_sleep,
        "learning_style_note": learning_style_note,
    }

    do_and_dont = []
    if weakest_subject and weakest_subject in _SUBJECT_TIPS:
        tip = _SUBJECT_TIPS[weakest_subject]
        do_and_dont.append({"type": "do", "text": tip["do"], "subject": weakest_subject})
        do_and_dont.append({"type": "dont", "text": tip["dont"], "subject": weakest_subject})
    do_and_dont.append({"type": "do", "text": "Keep a predictable daily routine and consistent bedtime.", "subject": "general"})
    if avg_sleep and avg_sleep < 7:
        do_and_dont.append({"type": "dont", "text": "Don't allow late-night screen use — sleep is below the healthy range.", "subject": "general"})

    weekly_home_plan = []
    focus_subjects = [s for s in [weakest_subject, strongest_subject] if s]
    for i, day in enumerate(_WEEKDAYS):
        if i < 5:
            focus = focus_subjects[i % len(focus_subjects)] if focus_subjects else "General Review"
            weekly_home_plan.append({
                "day": day,
                "focus": focus,
                "activity": f"20-30 min focused practice on {focus}, followed by 10 min of parent check-in.",
            })
        else:
            weekly_home_plan.append({
                "day": day,
                "focus": "Rest & Connection",
                "activity": "Light review, outdoor play, and quality family time — no formal study pressure.",
            })

    risk_alert = None
    if avg_mood and avg_mood < 4:
        risk_alert = "Wellbeing scores indicate elevated stress — consider speaking with the school counsellor."
    elif weakest_subject and subject_scores.get(weakest_subject) and _safe_mean(subject_scores[weakest_subject]) < 45:
        risk_alert = f"{weakest_subject} performance is significantly below average — early intervention recommended."

    mentor_tip = (
        "Small, consistent daily engagement beats occasional long study sessions — "
        "aim for short, positive touchpoints rather than pressure-filled marathons."
    )

    return {
        "student_id": student.id,
        "learning_profile": learning_profile,
        "do_and_dont": do_and_dont,
        "weekly_home_plan": weekly_home_plan,
        "risk_alert": risk_alert,
        "mentor_tip": mentor_tip,
    }
