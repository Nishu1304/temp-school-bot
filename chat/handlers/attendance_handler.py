from schoolApp.models import Attendance
from django.utils import timezone
from chat.lang_manager import get_lang_text

def handle(phone, user, action, student):
    """
    Parent-only — Handles child's attendance queries with bilingual support.
    Works with UPDATED StudentProfile (no student.user).
    """
    today = timezone.now().date()
    lang = getattr(user, "language_preference", "English") or "English"

    if not student:
        return get_lang_text("select_student_first", lang)

    child_name = student.student_name  # ✅ updated
    class_sec = f"{student.class_name.class_name}{student.section_name}"

    # 🔸 Encouragement helper
    def encouragement(pct):
        if pct >= 95:
            return get_lang_text("attendance_encourage_excellent", lang)
        elif pct >= 85:
            return get_lang_text("attendance_encourage_good", lang)
        elif pct >= 70:
            return get_lang_text("attendance_encourage_ok", lang)
        else:
            return get_lang_text("attendance_encourage_poor", lang)

    # 🔸 TODAY'S ATTENDANCE
    if action == "attendance_today":
        rec = Attendance.objects.filter(student=student, date=today).first()

        if rec:
            title = get_lang_text("attendance_today_title", lang)
            present_msg = get_lang_text("attendance_present_msg", lang)
            absent_msg = get_lang_text("attendance_absent_msg", lang)

            return (
                f"{title}\n"
                f"{get_lang_text('child_label', lang)}: {child_name}\n"
                f"{get_lang_text('status_label', lang)}: *{rec.status}*\n"
                f"{get_lang_text('remark_label', lang)}: {rec.remark or '—'}\n\n"
                f"{present_msg if rec.status == 'Present' else absent_msg}"
            )

        return get_lang_text("attendance_no_data", lang)

    # 🔸 THIS MONTH
    elif action == "attendance_month":
        records = Attendance.objects.filter(student=student, date__month=today.month)
        total = records.count()
        present = records.filter(status="Present").count()
        pct = (present / total * 100) if total else 0

        title = get_lang_text("attendance_month_title", lang)

        return (
            f"{title}\n"
            f"{get_lang_text('child_label', lang)}: {child_name}\n"
            f"{get_lang_text('present_label', lang)}: {present}/{total} ({pct:.1f}%)\n\n"
            f"{encouragement(pct)}"
        )

    # 🔸 OVERALL PERCENTAGE
    elif action == "attendance_percentage":
        all_records = Attendance.objects.filter(student=student)
        total = all_records.count()
        present = all_records.filter(status="Present").count()
        pct = (present / total * 100) if total else 0

        title = get_lang_text("attendance_overall_title", lang)

        return (
            f"{title}\n"
            f"{get_lang_text('child_label', lang)}: {child_name}\n"
            f"{get_lang_text('present_label', lang)}: {present}/{total}\n"
            f"{get_lang_text('percentage_label', lang)}: {pct:.1f}%\n\n"
            f"{encouragement(pct)}"
        )

    return get_lang_text("invalid_option", lang)
