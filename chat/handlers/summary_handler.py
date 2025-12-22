from django.utils import timezone
from schoolApp.models import Attendance, FeeModel, Grade
from chat.lang_manager import get_lang_text

def handle(phone, user, student):
    """
    Parent-only — Gives a quick summary (attendance, fees, and marks) in bilingual mode.
    """
    lang = getattr(user, "language_preference", "English") or "English"

    if not student:
        return get_lang_text("select_student_first", lang)

    child_name = student.student_name

    # 🔸 Attendance percentage
    all_att = Attendance.objects.filter(student=student)
    total = all_att.count()
    present = all_att.filter(status="Present").count()
    att_pct = (present / total * 100) if total else 0

    # 🔸 Fees summary (FeeModel currently links to User; using email lookup)
    fee = FeeModel.objects.filter(student__email=student.email).last()
    if fee:
        due = float(fee.total_amount) - float(fee.paid_amount)
        fee_line = (
            f"{get_lang_text('total_label', lang)} ₹{fee.total_amount}, "
            f"{get_lang_text('paid_label', lang)} ₹{fee.paid_amount}, "
            f"{get_lang_text('due_label', lang)} ₹{due}"
        )
    else:
        fee_line = get_lang_text("fees_no_data", lang)

    # 🔸 Marks summary (last 3)
    grades = Grade.objects.filter(student=student).order_by("-created_at")[:3]
    if grades:
        marks_lines = "\n".join(
            f"• {g.subject.subject}: {g.marks_obtained}/{g.max_marks} ({g.grade})"
            for g in grades
        )
    else:
        marks_lines = get_lang_text("marks_no_data", lang)

    # 🔸 Encouragement badge
    if att_pct >= 90:
        badge = get_lang_text("summary_encourage_excellent", lang)
    elif att_pct >= 75:
        badge = get_lang_text("summary_encourage_good", lang)
    else:
        badge = get_lang_text("summary_encourage_improve", lang)

    # 🔸 Final summary message
    title = get_lang_text("summary_title", lang)
    return (
        f"{title}\n"
        f"{child_name} — {badge}\n\n"
        f"{get_lang_text('attendance_label', lang)}: {att_pct:.1f}%\n"
        f"{get_lang_text('fees_label', lang)}: {fee_line}\n"
        f"{get_lang_text('recent_marks_label', lang)}:\n{marks_lines}\n\n"
        f"{get_lang_text('summary_footer', lang)}"
    )
