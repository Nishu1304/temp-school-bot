
# chat/lang_manager.py
from .rules import match_rule
from .session_manager import get_or_create_session, save_last_message, update_menu_state
from .prompt_templates import build_intent_prompt
import logging
from django.conf import settings
# logger = logging.getLogger(__name__)

from .dynamic_getters import get_homework, get_attendance, get_fees, get_exams, get_results, get_notices
from .dynamic_getters import get_library_books, get_child_info, get_bus_info
from chat.llm_manager import generate_llm_reply
from chat.models import Feedback, Appointment
from Account.models import StudentProfile, TeacherProfile
from schoolApp.models import Class


def handle_dynamic_intent(intent, session, user_text):
    student_id = session.selected_student_id
    print("DYNAMIC INTENT:", intent)

    # GLOBAL ESCAPE
    if intent == "show_menu":
        session.reset()
        session.save()
        return None

    if intent == "back":
        session.current_form = None
        session.form_step = None
        session.form_data = {}
        session.save()
        return "Okay, going back. Type *menu* to see options."

    # LANGUAGE
    if intent == "change_language_hi":
        session.language = "hi"
        session.save(update_fields=["language"])
        return "अब मैं हिंदी में बात करूंगा।", {"source": "language_change"}

    if intent == "change_language_en":
        session.language = "en"
        session.save(update_fields=["language"])
        return "I will now speak in English.", {"source": "language_change"}

    # TEACHER REPORT
    if intent == "student_report" and session.is_teacher:
        classes = Class.objects.all().order_by("class_name")
        session.current_form = "teacher_report"
        session.form_step = 1
        session.form_data = {"class_map": {str(i + 1): c.id for i, c in enumerate(classes)}}
        session.save()

        lines = [f"{i + 1}) {c.class_name} {c.section}" for i, c in enumerate(classes)]
        return "Which class?\n" + "\n".join(lines), {"source": "teacher_report"}

    # APPOINTMENT
    if intent == "appointment_form":
        session.current_form = "appointment"
        session.form_step = 1
        session.form_data = {}
        session.save()
        return (
            "Who would you like to book an appointment with?\n"
            "1️⃣ Principal\n"
            "2️⃣ Teacher",
            {"source": "appointment_start"}
        )

    # FEEDBACK
    if intent == "feedback_form":
        session.current_form = "feedback"
        session.form_step = 1
        session.form_data = {}
        session.save()
        return (
            "Sure! Please type your feedback or complaint in one message.",
            {"source": "feedback_start"}
        )

    # ADMISSION
    if intent == "admission_form":
        session.current_form = "admission"
        session.form_step = 1
        session.form_data = {}
        session.save()
        return (
            "Sure! Let's begin the admission inquiry.\n\n"
            "1️⃣ What is the student's full name?",
            {"source": "admission_start"}
        )

    # CHILD INFO
    if intent == "child_info":
        info = get_child_info(student_id)
        if not info:
            return "I couldn't find your child's details.", {"intent": "child_info"}

        prompt = (
            "Summarize the child profile in under 40 words:\n"
            f"Name: {info['name']}\n"
            f"Class: {info['class']} Section {info['section']}\n"
            f"Parent: {info['father']}\n"
            f"Phone: {info['phone']}\n"
        )
        reply = generate_llm_reply(prompt)
        return reply, {"intent": "child_info"}

    # HOMEWORK
    if intent == "homework":
        data = get_homework(student_id)
        if data.get("error"):
            return "I couldn't fetch homework right now.", {"intent": "homework"}

        if not data["items"]:
            return "There is no homework assigned for today.", {"intent": "homework"}

        hw_text = "".join(
            f"{i+1}) {h['subject']}: {h['title']} — due {h['due_date']}. "
            for i, h in enumerate(data["items"])
        )
        reply = generate_llm_reply("Summarize homework in under 50 words:\n" + hw_text)
        return reply, {"intent": "homework"}

    # ATTENDANCE
    if intent == "attendance":
        data = get_attendance(student_id)
        if not data["today"]:
            return "No attendance marked for today yet.", {"intent": "attendance"}

        today = data["today"]
        recent = data["recent"]
        recent_text = "".join(f"{r['date']}: {r['status']}. " for r in recent)

        prompt = (
            "Summarize attendance in under 40 words. Keep it friendly.\n\n"
            f"Today: {today['date']} - {today['status']}.\n"
            f"Recent: {recent_text}"
        )
        reply = generate_llm_reply(prompt)
        return reply, {"intent": "attendance"}

    # FEES
    if intent == "fees":
        data = get_fees(student_id)
        if data.get("error") or not data["fee"]:
            return "I couldn’t find any fee details right now.", {"intent": "fees"}

        fee = data["fee"]
        prompt = (
            "Summarize this student fee info in under 40 words:\n\n"
            f"Status: {fee['status']}\n"
            f"Total Amount: ₹{fee['total']}\n"
            f"Paid Amount: ₹{fee['paid']}\n"
            f"Due Amount: ₹{fee['due']}\n"
            f"Due Date: {fee['due_date']}\n"
        )
        reply = generate_llm_reply(prompt)
        return reply, {"intent": "fees"}

    # EXAMS
    if intent == "exam":
        data = get_exams(student_id)
        if data.get("error"):
            return "I couldn't fetch the exam schedule right now.", {"intent": "exam"}

        upcoming = data["upcoming"]
        completed = data["completed"]
        if not upcoming and not completed:
            return "No upcoming or recent exams found.", {"intent": "exam"}

        up_text = "".join(f"{ex['name']} on {ex['date']} ({ex['type']}). " for ex in upcoming)
        comp_text = "".join(f"{ex['name']} completed on {ex['date']}. " for ex in completed)

        prompt = (
            "Summarize this exam schedule in under 50 words:\n\n"
            f"Upcoming: {up_text}\n"
            f"Recent: {comp_text}"
        )
        reply = generate_llm_reply(prompt)
        return reply, {"intent": "exam"}

    # RESULTS
    if intent == "result":
        data = get_results(student_id)
        if data.get("error"):
            return "No exam results found for this student.", {"intent": "result"}

        subj_text = "".join(
            f"{s['subject']}: {s['marks']}/{s['max']} ({s['grade']}). "
            for s in data["subjects"]
        )
        overall = data.get("overall")
        overall_text = f"Overall: {overall['percentage']}%, Grade {overall['grade']}." if overall else ""

        prompt = (
            "Summarize these exam results in under 50 words:\n\n"
            f"{subj_text}\n{overall_text}"
        )
        reply = generate_llm_reply(prompt)
        return reply, {"intent": "result"}

    # NOTICE
    if intent == "notice":
        data = get_notices(student_id)
        if data.get("error"):
            return "I couldn't fetch notices right now.", {"intent": "notice"}

        notices = data["notices"]
        if not notices:
            return "No new notices for your class or child.", {"intent": "notice"}

        nt = "".join(f"{n['title']} on {n['date']}. {n['desc']} " for n in notices)
        reply = generate_llm_reply("Summarize notices in under 50 words:\n" + nt)
        return reply, {"intent": "notice"}

    # LIBRARY
    if intent == "library":
        data = get_library_books(student_id)
        if data.get("error"):
            return "I couldn't fetch the library records right now.", {"intent": "library"}

        books = data["books"]
        if not books:
            return "No books are currently issued to this student.", {"intent": "library"}

        bt = "".join(
            f"{b['title']} by {b['author']} — due {b['due_date']}{' (Overdue)' if b['overdue'] else ''}. "
            for b in books
        )
        reply = generate_llm_reply("Summarize library books in under 50 words:\n" + bt)
        return reply, {"intent": "library"}

    # BUS
    if intent == "bus_info":
        data = get_bus_info(student_id)
        if data.get("error"):
            return data["error"], {"intent": "bus_info"}

        bus = data["bus"]
        reply = generate_llm_reply(
            f"Bus {bus['number']}, Driver {bus['driver']} ({bus['phone']}), "
            f"Pickup {bus['start']} {bus['start_time']}, Drop {bus['end']} {bus['end_time']}."
        )
        return reply, {"intent": "bus_info"}

    return "Feature under development.", {"source": "dynamic"}



# def handle_dynamic_intent(intent, session, user_text):
#     student_id = session.selected_student_id
#     print(intent)
#
#     if intent == "change_language":
#         session.language = "hi"
#         session.save(update_fields=["language"])
#         return "अब मैं हिंदी में बात करूंगा।", {"source": "language_change"}
#
#     if intent == "change_language_english":
#         session.language = "en"
#         session.save(update_fields=["language"])
#         return "I will now speak in English.", {"source": "language_set"}
#
#     if intent == "student_report" and session.is_teacher:
#         classes = Class.objects.all().order_by("class_name")
#         session.current_form = "teacher_report"
#         session.form_step = 1
#         session.form_data = {
#             "class_map": {str(i + 1): c.id for i, c in enumerate(classes)}
#         }
#         session.save()
#
#         cl_lines = [f"{i + 1}) {c.class_name} {c.section}" for i, c in enumerate(classes)]
#         return "Which class?\n" + "\n".join(cl_lines), {"source": "teacher_report"}
#
#     if intent == "appointment_form":
#         session.current_form = "appointment"
#         session.form_step = 1
#         session.form_data = {}
#         session.save()
#
#         return (
#             "Who would you like to book an appointment with?\n"
#             "1️⃣ Principal\n"
#             "2️⃣ Teacher"
#         )
#
#     if intent == "feedback_form":
#         session.current_form = "feedback"
#         session.form_step = 1
#         session.form_data = {}
#         session.save()
#
#         return (
#             "Sure! Please tell me your feedback or issue in one message.",
#             {"source": "dynamic", "intent": "feedback_form"}
#         )
#     if intent == "admission_form":
#         session.current_form = "admission"
#         session.form_step = 1
#         session.form_data = {}
#         session.save()
#
#         return ("Sure! Let's begin the admission inquiry.\n\n"
#                 "1️⃣ What is the *student's full name*?",
#                 {"source": "admission_start"})
#
#     if intent == "child_info":
#         info = get_child_info(student_id)
#         print(info)
#         if not info:
#             return ("I couldn't find your child's details.",
#                     {"source": "dynamic", "intent": "child_info"})
#
#         prompt = (
#             "Summarize the child profile in under 40 words:\n"
#             f"Name: {info['name']}\n"
#             f"Class: {info['class']} Section {info['section']}\n"
#             f"Parent: {info['father']}\n"
#             f"Phone: {info['phone']}\n"
#         )
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "child_info"}
#
#
#     if intent == "homework":
#         data = get_homework(student_id)
#
#         if data.get("error"):
#             return ("I couldn't fetch homework right now.",
#                     {"source": "dynamic", "intent": "homework"})
#
#         if not data["items"]:
#             return ("There is no homework assigned for today.",
#                     {"source": "dynamic", "intent": "homework"})
#
#         hw_text = ""
#         for i, hw in enumerate(data["items"], start=1):
#             hw_text += f"{i}) {hw['subject']}: {hw['title']} — due {hw['due_date']}. {hw['description'][:80]}\n"
#
#         prompt = "Summarize this homework list in under 50 words. Be friendly and clear.\n\n" + hw_text
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "homework"}
#
#
#     if intent == "attendance":
#         data = get_attendance(student_id)
#
#         if not data["today"]:
#             return ("No attendance marked for today yet.",
#                     {"source": "dynamic", "intent": "attendance"})
#
#         today = data["today"]
#         recent = data["recent"]
#
#         recent_text = "".join(f"{r['date']}: {r['status']}. " for r in recent)
#
#         prompt = (
#             "Summarize attendance in under 40 words. Keep it friendly.\n\n"
#             f"Today: {today['date']} - {today['status']}.\n"
#             f"Recent: {recent_text}"
#         )
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "attendance"}
#
#
#     if intent == "fees":
#         data = get_fees(student_id)
#
#         if data.get("error") or not data["fee"]:
#             return ("I couldn’t find any fee details right now.",
#                     {"source": "dynamic", "intent": "fees"})
#
#         fee = data["fee"]
#         prompt = (
#             "Summarize this student fee info in under 40 words, friendly tone:\n\n"
#             f"Status: {fee['status']}\n"
#             f"Total Amount: ₹{fee['total']}\n"
#             f"Paid Amount: ₹{fee['paid']}\n"
#             f"Due Amount: ₹{fee['due']}\n"
#             f"Due Date: {fee['due_date']}\n"
#         )
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "fees"}
#
#
#     if intent == "exam":
#         data = get_exams(student_id)
#
#         if data.get("error"):
#             return ("I couldn't fetch the exam schedule right now.",
#                     {"source": "dynamic", "intent": "exam"})
#
#         upcoming = data["upcoming"]
#         completed = data["completed"]
#
#         if not upcoming and not completed:
#             return ("No upcoming or recent exams found.",
#                     {"source": "dynamic", "intent": "exam"})
#
#         up_text = "".join(f"{ex['name']} on {ex['date']} ({ex['type']}). " for ex in upcoming)
#         comp_text = "".join(f"{ex['name']} completed on {ex['date']}. " for ex in completed)
#
#         prompt = (
#             "Summarize this exam schedule in under 50 words, friendly and clear.\n\n"
#             f"Upcoming: {up_text}\n"
#             f"Recent: {comp_text}"
#         )
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "exam"}
#
#
#     if intent == "result":
#         data = get_results(student_id)
#
#         if data.get("error"):
#             return ("No exam results found for this student.",
#                     {"source": "dynamic", "intent": "result"})
#
#         exam_name = data["exam_name"]
#         exam_date = data["exam_date"]
#         subjects = data["subjects"]
#         overall = data["overall"]
#
#         subj_text = "".join(f"{s['subject']}: {s['marks']}/{s['max']} ({s['grade']}). " for s in subjects)
#         overall_text = f"Overall: {overall['percentage']}%, Grade {overall['grade']}. " if overall else ""
#
#         prompt = (
#             "Summarize these exam results in under 50 words, friendly and easy for parents.\n\n"
#             f"Exam: {exam_name} on {exam_date}.\n"
#             f"Marks: {subj_text}\n"
#             f"{overall_text}"
#         )
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "result"}
#
#
#     if intent == "notice":
#         data = get_notices(student_id)
#
#         if data.get("error"):
#             return ("I couldn't fetch notices right now.",
#                     {"source": "dynamic", "intent": "notice"})
#
#         notices = data["notices"]
#         if not notices:
#             return ("No new notices for your class or child.",
#                     {"source": "dynamic", "intent": "notice"})
#
#         nt = "".join(f"{n['title']} on {n['date']}. {n['desc']} " for n in notices)
#
#         prompt = "Summarize these school notices in under 50 words. Be friendly and concise.\n\n" + nt
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "notice"}
#
#
#     if intent == "library":
#         data = get_library_books(student_id)
#
#         if data.get("error"):
#             return ("I couldn't fetch the library records right now.",
#                     {"source": "dynamic", "intent": "library"})
#
#         books = data["books"]
#         if not books:
#             return ("No books are currently issued to this student.",
#                     {"source": "dynamic", "intent": "library"})
#
#         bt = "".join(
#             f"{b['title']} by {b['author']} — issued {b['issue_date']}, due {b['due_date']}{' (Overdue)' if b['overdue'] else ''}. "
#             for b in books
#         )
#
#         prompt = "Summarize these issued library books in under 50 words. Be friendly and direct.\n\n" + bt
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "dynamic", "intent": "library"}
#
#     if intent == "bus_info":
#         data = get_bus_info(student_id)
#
#         if data.get("error"):
#             return f"{data['error']}.", {"source": "bus"}
#
#         bus = data["bus"]
#         stop_lines = "\n".join([f"- {s['name']} ({s['arr']} – {s['dep']})" for s in bus["stops"]])
#
#         prompt = (
#             "Summarize this school bus information in under 50 words:\n"
#             f"Bus Number: {bus['number']}\n"
#             f"Driver: {bus['driver']} ({bus['phone']})\n"
#             f"Pickup: {bus['start']} at {bus['start_time']}\n"
#             f"Drop: {bus['end']} at {bus['end_time']}\n"
#             f"Current Location: {bus['location']}\n"
#             f"Stops:\n{stop_lines}"
#         )
#
#         reply = generate_llm_reply(prompt)
#         return reply, {"source": "bus", "intent": "bus_info"}
#
#
#     return "Feature under development.", {"source": "dynamic"}



# Hook functions (implement these next)
from .llm_manager import generate_llm_reply
from .prompt_templates import build_intent_prompt
def generate_from_intent(intent, user_text, session):
    prompt = build_intent_prompt(intent, user_text, session.menu_state)
    return generate_llm_reply(prompt)



from .rag_retriever import get_context
from .prompt_templates import build_rag_prompt

def handle_fallback(user_text: str, session):
    """
    Intelligent fallback:
    - Retrieve documents using RAG
    - Build context prompt
    - Let LLM generate a short, friendly answer
    """
    # 1) Retrieve relevant docs
    docs = get_context(user_text, top_k=3)

    # 2) If no docs match → generic LLM fallback
    if not docs:
        prompt = (
            "Reply in under 35 words. "
            "User asked something unrelated to school documents. "
            f"User said: '{user_text}'. "
            "Give a polite helpful suggestion."
        )
        reply = generate_llm_reply(prompt)
        return reply, {"source": "fallback_generic"}

    # 3) Build RAG context prompt
    rag_prompt = build_rag_prompt(user_text, docs)

    # 4) Generate short final answer using Groq
    reply = generate_llm_reply(rag_prompt)

    return reply, {
        "source": "fallback_rag",
        "docs_used": len(docs)
    }


# Main entrypoint
def get_reply(user_text: str, session):
    try:
        # ---------------------------------------------------------
        # 0) Detect rule early (used for both teacher/parent)
        # ---------------------------------------------------------
        rule = match_rule(user_text)
        intent = rule["intent"] if rule else None
        print(intent, session.is_teacher, session.phone_number)
        teacher = TeacherProfile.objects.filter(contact=session.phone_number)
        print(teacher, len(teacher))
        if len(teacher) == 0:
            session.is_teacher= False
        else:
            session.is_teacher = True
        # ---------------------------------------------------------
        # 1) TEACHER MODE ALWAYS WINS
        # ---------------------------------------------------------
        if session.is_teacher:
            print("teacher here")
            # Teacher is in middle of report flow
            if session.current_form == "teacher_report":
                print(1)
                reply = handle_teacher_report(user_text, session)
                return reply, {"source": "teacher_report"}

            # Teacher starts report: "report" / "analysis" / etc
            if intent == "student_report":
                print(22)
                return handle_dynamic_intent("student_report", session, user_text)

            # Teacher saying random text
            return (
                "Teacher mode active.\nSend *report* to generate student performance reports.",
                {"source": "teacher_idle"}
            )

        # ---------------------------------------------------------
        # 2) MENU CONTEXT SETUP (parent or guest)
        # ---------------------------------------------------------
        if not session.selected_student_id:
            session.menu_state = "guest"
        else:
            session.menu_state = "parent"

        # ---------------------------------------------------------
        # 3) FIRST MESSAGE → AUTO MENU
        # ---------------------------------------------------------
        if session.last_message is None or session.last_message.strip() == "":
            session.last_message = user_text
            session.save(update_fields=["last_message"])

            prompt = build_intent_prompt("show_menu", user_text, session.menu_state)
            reply = generate_llm_reply(prompt)
            return reply, {"source": "first_menu"}

        # ---------------------------------------------------------
        # 4) AWAITING CHILD SELECTION (parent flow only)
        # ---------------------------------------------------------
        if session.awaiting_child_selection:
            return "Please reply with the number next to your child’s name.", {
                "source": "awaiting_child"
            }

        # ---------------------------------------------------------
        # 5) MULTI-STEP FORM ROUTING
        # ---------------------------------------------------------
        if session.current_form == "admission":
            reply = handle_admission_form(user_text, session)
            return reply, {"source": "admission_form"}

        if session.current_form == "feedback":
            reply = handle_feedback_form(user_text, session)
            return reply, {"source": "feedback_form"}

        if session.current_form == "appointment":
            reply = handle_appointment_form(user_text, session)
            return reply, {"source": "appointment_form"}

        # ---------------------------------------------------------
        # 6) GUEST MODE (no student linked)
        # ---------------------------------------------------------
        if not session.selected_student_id:
            if intent:
                # Guest cannot access certain features
                if intent in ("homework", "attendance", "fees", "timetable"):
                    return (
                        "This feature is available only for registered parents. "
                        "For general school info, you can ask anything.",
                        {"source": "guest_block"}
                    )

                reply = generate_from_intent(intent, user_text, session)
                return reply, {"source": "intent", "intent": intent}

            # No match → RAG fallback
            reply = handle_fallback(user_text, session)
            return reply, {"source": "guest_fallback"}

        # ---------------------------------------------------------
        # 7) PARENT MODE (normal user flow)
        # ---------------------------------------------------------
        if intent:
            # Dynamic intents (student-specific)
            if intent in (
                "homework",
                "attendance",
                "timetable",
                "fees",
                "exam",
                "result",
                "notice",
                "library",
                "child_info",
                "admission_form",
                "feedback_form",
                "appointment_form",
                "bus_info",
                "change_language",
                "change_language_english",

            ):
                update_menu_state(session, intent)
                reply = handle_dynamic_intent(intent, session, user_text)
                return reply, {"source": "dynamic_intent", "intent": intent}

            # Normal LLM reply (non-dynamic)
            reply = generate_from_intent(intent, user_text, session)
            return reply, {"source": "intent", "intent": intent}

        # ---------------------------------------------------------
        # 8) FALLBACK (no rule matched)
        # ---------------------------------------------------------
        reply = handle_fallback(user_text, session)
        return reply, {"source": "fallback"}


    except Exception as e:

        print("LANG MANAGER ERROR:", e)

        # 🔥 HARD RESET SESSION

        from .session_manager import reset_session

        reset_session(session)

        return (

            "Something went wrong. I've reset the conversation. Please type *menu* to continue.",

            {"source": "error_reset"}

        )

def handle_admission_form(text, session):
    step = session.form_step
    data = session.form_data

    if step == 1:
        data["student_name"] = text
        session.form_step = 2

        session.form_data = data
        session.save()
        return "2️⃣ Parent's full name?"

    if step == 2:
        data["parent_name"] = text
        session.form_step = 3
        session.form_data = data
        session.save()
        return "3️⃣ Parent contact number?"

    if step == 3:
        data["contact_number"] = text
        session.form_step = 4
        session.form_data = data
        session.save()
        return "4️⃣ Which class are you applying for?"

    if step == 4:
        data["class_name"] = text
        session.form_step = 5
        session.form_data = data
        session.save()
        return "5️⃣ Any message you'd like to add? (optional)\nType 'skip' to continue."

    if step == 5:
        if text.lower() != "skip":
            data["message"] = text
        else:
            data["message"] = ""

        # Save to DB
        from schoolApp.models import AdmissionInquiry
        print(data)
        AdmissionInquiry.objects.create(
            student_name=data["student_name"],
            parent_name=data["parent_name"],
            contact_number=data["contact_number"],
            email="",
            class_name=data["class_name"],
            message=data["message"],
        )

        # Notify school admin
        from whatsapp.utility import send_message_service

        admin_phone = settings.SCHOOL_ADMIN_WHATSAPP  # Store in settings.py

        send_message_service(
            template_name="form_submitted",  # Template name in Meta
            phone=admin_phone,
            variables={
                "1": data["student_name"],
                "2": data["contact_number"]
            },
            language="en"
        )

        # Reset
        session.current_form = None
        session.form_step = 0
        session.form_data = {}
        session.save()

        return "Thank you! Your admission inquiry has been submitted. Our school team will contact you soon."



def handle_feedback_form(text, session):
    step = session.form_step
    data = session.form_data

    if step == 1:
        data["feedback_text"] = text
        student_id = session.selected_student_id



        parent_name = "Guest"
        if student_id:
            student = StudentProfile.objects.filter(id=student_id).first()
            if student:
                parent_name = student.parent_name

        Feedback.objects.create(
            student_id=student_id,
            parent_name=parent_name,
            feedback_text=text,
        )

        from whatsapp.utility import send_message_service
        admin_phone = settings.SCHOOL_ADMIN_WHATSAPP

        send_message_service(
            template_name="feedback_form",
            phone=admin_phone,
            variables={
                "1": parent_name,
                "2": text
            },
            language="en"
        )

        # Reset session
        session.current_form = None
        session.form_step = 0
        session.form_data = {}
        session.save()

        return (
            "Thank you! Your feedback has been shared with the school.",
            {"source": "dynamic", "intent": "feedback_form"}
        )

    return (
        "Sorry, something went wrong with the feedback form.",
        {"source": "dynamic", "intent": "feedback_error"}
    )


def handle_appointment_form(text, session):
    print(f"[DEBUG] Incoming text: {text}")
    print(f"[DEBUG] Current step: {session.form_step}")
    print(f"[DEBUG] Current session data: {session.form_data}")

    step = session.form_step
    data = session.form_data or {}
    student_id = session.selected_student_id

    # STEP 1 — PICK PRINCIPAL OR TEACHER
    if step == 1:
        print("[DEBUG] Step 1: Pick principal or teacher")

        if text == "1":
            print("[DEBUG] User selected Principal")
            data["appointment_with"] = "principal"
            session.form_step = 2
            session.form_data = data
            session.save()

            return "Please tell me the reason for the meeting."

        elif text == "2":
            print("[DEBUG] User selected Teacher")

            teachers = TeacherProfile.objects.all().order_by("teacher_name")
            print(f"[DEBUG] Teachers fetched: {teachers.count()}")

            teacher_list = [
                f"{idx + 1}) {t.teacher_name} ({t.specialization or 'Teacher'})"
                for idx, t in enumerate(teachers)
            ]

            data["teacher_map"] = {str(i + 1): t.id for i, t in enumerate(teachers)}
            print(f"[DEBUG] Generated teacher_map: {data['teacher_map']}")

            session.form_data = data
            session.form_step = 100  # teacher selection
            session.save()

            return "Please select a teacher:\n" + "\n".join(teacher_list)

        print("[DEBUG] Invalid choice in Step 1")
        return "Who would you like to meet?\n1️⃣ Principal\n2️⃣ Teacher"

    # STEP 100 — Teacher selection
    if step == 100:
        print("[DEBUG] Step 100: Teacher selection")

        teacher_map = data.get("teacher_map", {})
        print(f"[DEBUG] teacher_map: {teacher_map}")

        if text not in teacher_map:
            print("[DEBUG] Invalid teacher selection")
            return "Invalid choice. Please send a valid number from the list."

        selected_teacher_id = teacher_map[text]
        print(f"[DEBUG] Selected teacher ID: {selected_teacher_id}")

        data["teacher_id"] = selected_teacher_id
        session.form_step = 2
        session.form_data = data
        session.save()

        return "Please tell me the reason for the meeting."

    # STEP 2 — Reason
    if step == 2:
        print("[DEBUG] Step 2: Capturing reason")

        data["reason"] = text
        session.form_step = 3
        session.form_data = data
        session.save()

        return "Please share your preferred date & time (e.g., 15 Dec at 11 AM)."

    # STEP 3 — Preferred date/time
    if step == 3:
        print("[DEBUG] Step 3: Preferred datetime received")

        data["preferred_datetime"] = text

        student = StudentProfile.objects.filter(id=student_id).first()
        print(f"[DEBUG] Student fetched: {student}")

        # Create appointment
        appt = Appointment.objects.create(
            student_id=student_id,
            parent_name=student.parent_name if student else "",
            contact_number=student.parent_contact if student else "",
            appointment_with=data["appointment_with"],
            teacher_id=data.get("teacher_id"),
            reason=data["reason"],
            preferred_datetime=data["preferred_datetime"],
        )

        print(f"[DEBUG] Appointment created with ID: {appt.id}")

        # Determine teacher/principal display name
        if data["appointment_with"] == "teacher":
            teacher_name = TeacherProfile.objects.get(id=data["teacher_id"]).teacher_name
        else:
            teacher_name = "Principal"

        print(f"[DEBUG] appointment_with: {data['appointment_with']}, teacher/principal: {teacher_name}")

        # SEND TEMPLATE TO ADMIN
        from whatsapp.utility import send_message_service
        admin_phone = settings.SCHOOL_ADMIN_WHATSAPP

        print(f"[DEBUG] Sending template message to admin: {admin_phone}")

        send_message_service(
            template_name="ptm_form",
            phone=admin_phone,
            variables={
                "1": student.parent_name if student else "A Parent",
                "2": student.student_name if student else "the child",
                "3": appt.appointment_with.capitalize(),
                "4": teacher_name,
                "5": appt.reason,
                "6": appt.preferred_datetime
            },
            language="en",
            buttons=[
                {"type": "quick_reply", "text": "Accept", "id": f"approve_appt_{appt.id}"},
                {"type": "quick_reply", "text": "Reject", "id": f"reject_appt_{appt.id}"}
            ]
        )

        print("[DEBUG] Template message sent successfully")

        # Reset session
        print("[DEBUG] Resetting session")
        session.current_form = None
        session.form_step = 0
        session.form_data = {}
        session.save()

        return "Your appointment request has been submitted. The school will confirm shortly."

    print("[DEBUG] Unknown state reached")
    return "Something went wrong with the appointment form."


def handle_teacher_report(text, session):
    step = session.form_step
    data = session.form_data

    from schoolApp.models import Class

    # STEP 1 — Select class
    if step == 1:
        class_map = data["class_map"]
        if text not in class_map:
            return "Invalid choice. Please select a class number."

        class_id = class_map[text]
        session.selected_class_id = class_id

        # show students
        students = StudentProfile.objects.filter(class_name_id=class_id)
        session.form_data = {
            "student_map": {str(i+1): s.id for i, s in enumerate(students)}
        }
        session.form_step = 2
        session.save()

        st_lines = [f"{i+1}) {s.student_name}" for i, s in enumerate(students)]
        return "Select a student:\n" + "\n".join(st_lines)

    # STEP 2 — Select student
    if step == 2:
        student_map = data["student_map"]
        if text not in student_map:
            return "Invalid student. Choose a valid number."

        student_id = student_map[text]
        session.selected_student_for_report = student_id
        session.form_step = 3
        session.save()

        # generate final report
        report_text = build_student_performance_report(student_id)
        session.current_form = None
        session.form_step = 0
        session.form_data = {}
        session.save()

        return report_text

    return "Something went wrong."

def build_student_performance_report(student_id):
    from schoolApp.models import (
         Attendance, Grade, BookIssue, Homework, ReportCard
    )
    from datetime import date

    s = StudentProfile.objects.get(id=student_id)

    # ATTENDANCE
    att = Attendance.objects.filter(student_id=student_id)
    total_days = att.count()
    present = att.filter(status="Present").count()
    absent = att.filter(status="Absent").count()
    leave = att.filter(status="Leave").count()

    attendance_summary = (
        f"Attendance: Present {present}/{total_days}, "
        f"Absent {absent}, Leave {leave}"
    )

    # GRADES
    grades = Grade.objects.filter(student_id=student_id)
    grade_summary = "\n".join(
        f"{g.subject.subject}: {g.marks_obtained}/{g.max_marks} ({g.grade})"
        for g in grades
    ) or "No exam data."

    # LIBRARY
    books = BookIssue.objects.filter(issued_to_id=student_id)
    library_summary = (
        f"Books taken: {books.count()}, "
        f"Late returns: {books.filter(is_returned=False).count()}"
    )

    # HOMEWORK
    hw = Homework.objects.filter(class_name_id=s.class_name.id)
    homework_summary = f"Homework count this month: {hw.count()}"

    # Combine raw data
    raw_text = (
        f"Student: {s.student_name}\n"
        f"Class: {s.class_name} {s.section_name}\n\n"
        f"{attendance_summary}\n\n"
        f"Grades:\n{grade_summary}\n\n"
        f"Library: {library_summary}\n\n"
        f"{homework_summary}\n\n"
    )

    # Send to LLM for analysis
    prompt = (
        "Analyze this student performance report. "
        "Give strengths, weaknesses, improvement suggestions, and next steps.\n\n"
        f"{raw_text}"
    )


    return generate_llm_reply(prompt)




def translate_to_hindi(text: str) -> str:
    """
    Translate English text to simple, natural Hindi using the LLM.
    Returns the translated string. If translation fails, returns original text.
    """
    if not text:
        return text
    try:
        prompt = f"Translate the following into natural, simple Hindi (keep formatting):\n\n{text}"
        # generate_llm_reply should return a string
        translated = generate_llm_reply(prompt)
        # some LLM helpers return tuple/meta — ensure string
        if isinstance(translated, (tuple, list)):
            translated = translated[0]
        return str(translated).strip()
    except Exception as e:
        # fallback to original text if something goes wrong
        print("translate_to_hindi error:", e)
        return text