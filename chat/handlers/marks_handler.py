from schoolApp.models import Grade
from chat.lang_manager import get_lang_text

def handle(phone, user, action, student):
    """
    Parent-only — Handles child's marks/grades with bilingual (English/Hindi) support and feedback.
    """
    lang = getattr(user, "language_preference", "English") or "English"

    if not student:
        return get_lang_text("select_student_first", lang)

    grades = Grade.objects.filter(student=student).order_by("-created_at")
    if not grades.exists():
        return get_lang_text("marks_no_data", lang)

    child_name = student.student_name

    # 🔸 Utility: encouragement feedback
    def encouragement(pct):
        if pct >= 90:
            return get_lang_text("marks_encourage_excellent", lang)
        elif pct >= 75:
            return get_lang_text("marks_encourage_good", lang)
        elif pct >= 60:
            return get_lang_text("marks_encourage_average", lang)
        else:
            return get_lang_text("marks_encourage_poor", lang)

    # 🔸 Recent Marks
    if action == "marks_recent":
        title = get_lang_text("marks_recent_title", lang)
        msg = f"{title}\n{get_lang_text('child_label', lang)}: {child_name}\n"
        for g in grades[:5]:
            msg += f"• {g.subject.subject}: {g.marks_obtained}/{g.max_marks} ({g.grade})\n"
        return msg + "\n" + encouragement(_average(grades))

    # 🔸 Subject-wise Averages
    elif action == "marks_subjectwise":
        subjects = {}
        for g in grades:
            subjects.setdefault(g.subject.subject, []).append(float(g.marks_obtained))

        title = get_lang_text("marks_subjectwise_title", lang)
        msg = f"{title}\n{get_lang_text('child_label', lang)}: {child_name}\n"

        for sub, marks in subjects.items():
            avg = sum(marks) / len(marks)
            msg += f"• {sub}: {get_lang_text('average_label', lang)} {avg:.1f}\n"

        overall = _average(grades)
        msg += f"\n{get_lang_text('overall_avg_label', lang)} {overall:.1f}%\n{encouragement(overall)}"
        return msg

    # 🔸 Overall Summary
    elif action == "marks_overall":
        total = sum(float(g.max_marks) for g in grades)
        obtained = sum(float(g.marks_obtained) for g in grades)
        pct = (obtained / total * 100) if total else 0

        title = get_lang_text("marks_overall_title", lang)
        msg = (
            f"{title}\n"
            f"{get_lang_text('child_label', lang)}: {child_name}\n"
            f"{get_lang_text('total_marks_label', lang)}: {obtained}/{total}\n"
            f"{get_lang_text('percentage_label', lang)}: {pct:.1f}%\n\n"
            f"{encouragement(pct)}"
        )
        return msg

    return get_lang_text("invalid_option", lang)


# Helper function
def _average(grades):
    total = sum(float(g.max_marks) for g in grades)
    obtained = sum(float(g.marks_obtained) for g in grades)
    return (obtained / total * 100) if total else 0
