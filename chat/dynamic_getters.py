# chat/dynamic_getters.py
from schoolApp.models import Homework, Attendance, FeeModel, Exam, Grade, ReportCard, NoticeModel, Bus, Stop
from schoolApp.models import BookIssue
from Account.models import StudentProfile
from django.utils import timezone
from datetime import datetime
def parse_time(t):
    """Convert '7:15 AM' into datetime.time safely."""
    try:
        return datetime.strptime(t.strip(), "%I:%M %p").time()
    except:
        return None

def estimate_location(bus):
    """Return an approximate bus location based on current time."""
    now = datetime.now().time()
    stops = bus.stops.all().order_by("id")

    last_stop = None
    next_stop = None

    for s in stops:
        arr = parse_time(s.arrivalTime)
        if arr and now < arr:
            next_stop = s
            break
        last_stop = s

    if not last_stop:
        return "Bus has not started yet."
    if not next_stop:
        return "Bus has likely reached the destination."

    return f"Between {last_stop.name} and {next_stop.name} (approximate)."


def get_bus_info(student_id):


    student = StudentProfile.objects.filter(id=student_id).first()
    if not student:
        return {"error": "Student not found"}

    bus = student.bus
    if not bus:
        return {"error": "No bus assigned"}

    stops = list(bus.stops.all())

    return {
        "error": None,
        "bus": {
            "number": bus.busNumber,
            "driver": bus.driverName,
            "phone": bus.driverPhone,
            "start": bus.start,
            "start_time": bus.startDeparture,
            "end": bus.end,
            "end_time": bus.endArrival,
            "stops": [{"name": s.name, "arr": s.arrivalTime, "dep": s.departureTime} for s in stops],
            "location": estimate_location(bus),
        }
    }

def get_child_info(student_id):
    try:
        s = StudentProfile.objects.get(id=student_id)
        return {
            "name": s.student_name,
            "class": str(s.class_name),
            "section": s.section_name,
            "father": s.parent_name,
            "phone": s.parent_contact,
        }
    except:
        return None

def get_library_books(student_id):
    """
    Returns books currently issued to the student.
    Includes due date and whether overdue.
    """

    today = timezone.now().date()

    issues = BookIssue.objects.filter(
        issued_to_id=student_id,
        is_returned=False
    )

    if not issues.exists():
        return {"error": None, "books": []}

    books = []

    for issue in issues:
        due = issue.due_date
        overdue = (today > due)

        books.append({
            "title": issue.book.title,
            "author": issue.book.author,
            "issue_date": issue.issue_date.strftime("%d %b"),
            "due_date": due.strftime("%d %b"),
            "overdue": overdue,
        })

    return {"error": None, "books": books}

def get_notices(student_id):
    """
    Returns notices applicable to the student (class-wide OR student-specific).
    Only returns published notices.
    """

    today = timezone.now().date()

    try:
        student = StudentProfile.objects.get(id=student_id)
    except StudentProfile.DoesNotExist:
        return {"error": "Student not found", "notices": []}

    class_name = str(student.class_name)

    # 1) Notices for all students
    general_notices = NoticeModel.objects.filter(
        target="student",
        is_published=True,
        class_name__isnull=True
    )

    # 2) Notices for this class
    class_notices = NoticeModel.objects.filter(
        target="classes",
        class_name=class_name,
        is_published=True
    )

    # 3) Notices for specific students
    specific_notices = NoticeModel.objects.filter(
        is_published=True,
        specific_students__icontains=student.student_name
    )

    combined = list(general_notices) + list(class_notices) + list(specific_notices)

    final = []
    for n in combined:
        final.append({
            "title": n.title,
            "desc": n.description[:200],  # short
            "date": n.applicable_date.strftime("%d %b"),
        })

    return {"error": None, "notices": final}

def get_results(student_id):
    """
    Returns marks for the latest exam for this student.
    Includes subject-wise marks + overall report card.
    """

    # Find latest completed exam for the student's class
    completed_exams = Exam.objects.filter(
        examsubjects__grade__student_id=student_id,
        status="completed"
    ).distinct().order_by("-exam_date")

    if not completed_exams.exists():
        return {"error": "No completed exams found"}

    exam = completed_exams.first()

    # Subject-wise marks
    marks = Grade.objects.filter(student_id=student_id, exam=exam)

    if not marks.exists():
        return {"error": "No marks found for exam"}

    subject_marks = []
    for m in marks:
        subject_marks.append({
            "subject": m.subject.subject,
            "marks": float(m.marks_obtained),
            "max": float(m.max_marks),
            "grade": m.grade,
            "remarks": m.remarks or ""
        })

    # Overall report card
    report = ReportCard.objects.filter(student_id=student_id, exam=exam).first()

    overall = None
    if report:
        overall = {
            "percentage": float(report.overall_percentage),
            "grade": report.overall_grade,
            "rank": report.rank
        }

    return {
        "error": None,
        "exam_name": exam.name,
        "exam_date": exam.exam_date.strftime("%d %b"),
        "subjects": subject_marks,
        "overall": overall
    }

def get_exams(student_id):
    """
    Returns upcoming and current exams for the student's class.
    Also returns recently completed exams.
    """
    today = timezone.now().date()

    try:
        student = StudentProfile.objects.get(id=student_id)
    except StudentProfile.DoesNotExist:
        return {"error": "Student not found", "upcoming": [], "completed": []}

    class_obj = student.class_name

    # Upcoming or ongoing exams
    upcoming = Exam.objects.filter(
        class_name=class_obj,
        exam_date__gte=today
    ).order_by("exam_date")

    # Recently completed exams (last 14 days)
    completed = Exam.objects.filter(
        class_name=class_obj,
        end_date__lt=today,
        end_date__gte=today - timezone.timedelta(days=14)
    ).order_by("-end_date")

    upcoming_list = []
    for ex in upcoming:
        upcoming_list.append({
            "name": ex.name,
            "date": ex.exam_date.strftime("%d %b"),
            "status": ex.status,
            "type": ex.exam_type,
            "description": ex.description or "",
        })

    completed_list = []
    for ex in completed:
        completed_list.append({
            "name": ex.name,
            "date": ex.exam_date.strftime("%d %b"),
            "status": ex.status,
            "type": ex.exam_type
        })

    return {
        "error": None,
        "upcoming": upcoming_list,
        "completed": completed_list
    }

def get_fees(student_id):
    """
    Returns the latest fee record for the student.
    """

    fee = FeeModel.objects.filter(student_id=student_id).order_by("-due_date").first()

    if not fee:
        return {"error": "No fee record found", "fee": None}

    data = {
        "status": fee.status,
        "total": float(fee.total_amount),
        "paid": float(fee.paid_amount),
        "due": float(fee.total_amount - fee.paid_amount),
        "due_date": fee.due_date.strftime("%d %b %Y"),
    }

    return {"error": None, "fee": data}


def get_attendance(student_id):
    """
    Returns today's attendance + optionally recent attendance (last 7 days).
    """

    today = timezone.now().date()

    # Today's attendance
    today_record = Attendance.objects.filter(student_id=student_id, date=today).first()

    # Last 7 days
    last_7 = Attendance.objects.filter(
        student_id=student_id,
        date__gte=today - timezone.timedelta(days=7)
    ).order_by("-date")

    data = {
        "today": None,
        "recent": [],
    }

    if today_record:
        data["today"] = {
            "date": today_record.date.strftime("%d %b"),
            "status": today_record.status,
            "remark": today_record.remark or ""
        }

    for a in last_7:
        data["recent"].append({
            "date": a.date.strftime("%d %b"),
            "status": a.status,
            "remark": a.remark or ""
        })

    return data


def get_homework(student_id):
    """
    Returns a list of homework items for the student's class & section.
    Uses today's date or future due dates.
    """

    try:
        student = StudentProfile.objects.get(id=student_id)
    except StudentProfile.DoesNotExist:
        return {"error": "Student not found", "items": []}

    # Whole class homework
    class_hw = Homework.objects.filter(
        class_name=student.class_name,
        assignment_type="class"
    )

    # Homework assigned to this specific student
    personal_hw = Homework.objects.filter(
        students=student,
        assignment_type="student"
    )

    items = []

    for hw in class_hw:
        items.append({
            "title": hw.title,
            "subject": hw.subject,
            "description": hw.description,
            "due_date": hw.due_date.strftime("%d %b %Y")
        })

    for hw in personal_hw:
        items.append({
            "title": hw.title,
            "subject": hw.subject,
            "description": hw.description,
            "due_date": hw.due_date.strftime("%d %b %Y")
        })

    if not items:
        return {"error": None, "items": []}

    return {"error": None, "items": items}
