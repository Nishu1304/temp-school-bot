from django.db.models import Q
from schoolApp.models import NoticeModel
from chat.lang_manager import get_lang_text

def handle(phone, user, action, student):
    """
    Parent-only — Fetches relevant school notices (bilingual).
    Matches notices by class_name or specific_students (comma-separated names).
    """
    lang = getattr(user, "language_preference", "English") or "English"

    if not student:
        return get_lang_text("select_student_first", lang)

    # Build query: published notices for the student's class OR specifically mentioning the student
    class_name_str = student.class_name.class_name
    student_name = student.student_name

    notices = NoticeModel.objects.filter(is_published=True).filter(
        Q(class_name__iexact=class_name_str) |
        Q(specific_students__icontains=student_name) |
        Q(target__iexact="student")
    ).order_by("-created_at")[:5]

    # If none, fall back to class-wide or all (posted without class)
    if not notices.exists():
        notices = NoticeModel.objects.filter(is_published=True).filter(
            Q(class_name__isnull=True) | Q(class_name__exact="")
        ).order_by("-created_at")[:5]

    if not notices.exists():
        return get_lang_text("notices_no_data", lang)

    msg = f"{get_lang_text('notices_title', lang)}\n"
    msg += f"{get_lang_text('child_label', lang)}: {student_name}\n"

    for n in notices:
        short = (n.description or "")[:60]
        msg += f"\n• {n.title}\n  {short}...\n"

    return msg
