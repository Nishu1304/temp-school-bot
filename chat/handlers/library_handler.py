from schoolApp.models import BookIssue
from django.utils import timezone
from chat.lang_manager import get_lang_text

def handle(phone, user, action, student):
    """
    Parent-only — Handles child's library info (bilingual).
    Uses issued_to__email lookup because issued_to is a User FK in current schema.
    """
    lang = getattr(user, "language_preference", "English") or "English"
    today = timezone.now().date()

    if not student:
        return get_lang_text("select_student_first", lang)

    issues = BookIssue.objects.filter(issued_to__email=student.email).order_by("-issue_date")
    if not issues.exists():
        return get_lang_text("library_no_data", lang)

    child_name = student.student_name

    # 🔸 ACTION: Issued Books
    if action == "library_issued":
        active = issues.filter(is_returned=False)
        if not active.exists():
            return get_lang_text("library_no_active_books", lang)
        msg = f"{get_lang_text('library_issued_title', lang)}\n"
        msg += f"{get_lang_text('child_label', lang)}: {child_name}\n"
        for i in active:
            msg += f"• {i.book.title} — {get_lang_text('due_date_label', lang)}: {i.due_date}\n"
        return msg

    # 🔸 ACTION: Overdue Books
    elif action == "library_due":
        due = issues.filter(due_date__lt=today, is_returned=False)
        if not due.exists():
            return get_lang_text("library_no_due_books", lang)
        msg = f"{get_lang_text('library_due_title', lang)}\n"
        msg += f"{get_lang_text('child_label', lang)}: {child_name}\n"
        for i in due:
            msg += f"• {i.book.title} ({get_lang_text('due_date_label', lang)}: {i.due_date})\n"
        return msg

    # 🔸 ACTION: Library Summary
    elif action == "library_summary":
        total = issues.count()
        active = issues.filter(is_returned=False).count()
        msg = (
            f"{get_lang_text('library_summary_title', lang)}\n"
            f"{get_lang_text('child_label', lang)}: {child_name}\n"
            f"{get_lang_text('library_total_issued', lang)}: {total}\n"
            f"{get_lang_text('library_currently_borrowed', lang)}: {active}"
        )
        return msg

    return get_lang_text("invalid_option", lang)
