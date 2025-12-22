from django.utils import timezone
from schoolApp.models import Exam
from chat.lang_manager import get_lang_text

def handle(phone, user, action, student):
    """
    Parent-only — Handles child's exam details (bilingual).
    """
    today = timezone.now().date()
    lang = getattr(user, "language_preference", "English") or "English"

    if not student:
        return get_lang_text("select_student_first", lang)

    # student.class_name is a FK to Class
    exams = Exam.objects.filter(class_name=student.class_name).order_by("exam_date")
    if not exams.exists():
        return get_lang_text("exams_no_data", lang)

    # 🔸 Filter by action
    if action == "exams_upcoming":
        exams = exams.filter(exam_date__gte=today)
        header = get_lang_text("exams_upcoming_title", lang)
    elif action == "exams_ongoing":
        exams = exams.filter(exam_date__lte=today, end_date__gte=today)
        header = get_lang_text("exams_ongoing_title", lang)
    else:
        exams = exams.filter(end_date__lt=today)
        header = get_lang_text("exams_completed_title", lang)

    if not exams.exists():
        return get_lang_text("exams_no_data", lang)

    child_name = student.student_name
    msg = f"{header}\n{get_lang_text('child_label', lang)}: {child_name}\n"
    for e in exams[:5]:
        end_date = e.end_date or "—"
        msg += f"\n• {e.name} ({e.term}) — {e.exam_date} → {end_date}"
    return msg
