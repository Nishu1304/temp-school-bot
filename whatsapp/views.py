from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.conf import settings
from Account.models import StudentProfile, TeacherProfile
from chat.session_manager import get_or_create_session, set_child_list, select_child, save_last_message
from chat.lang_manager import get_reply, translate_to_hindi
from .utility import send_message_service, send_whatsapp_text


def _format_children_menu(children):
    # children: list of dicts
    lines = ["Which child would you like to use for this session? Reply with the number:"]
    for i, c in enumerate(children, start=1):
        lines.append(f"{i}) {c['student_name']} ({c['class_name']}{c['section_name']})")
    return "\n".join(lines)


@api_view(["POST"])
def send_template_message(request):
    """
    Universal WhatsApp send endpoint.
    Works with simplified variable-only JSON payloads.

    Example:
    {
        "phone": "919876543210",
        "template_name": "test_template",
        "language": "en",
        "variables": {"1": "John"},
        "buttons": [{ "type": "quick_reply", "text": "Thank you" }]
    }
    """
    try:
        data = request.data
        phone = data.get("phone")
        template_name = data.get("template_name")
        language = data.get("language", "en")
        variables = data.get("variables", {})
        buttons = data.get("buttons", [])

        if not phone or not template_name:
            return Response(
                {"error": "phone and template_name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Delegate to shared service used internally & externally
        result = send_message_service(
            template_name=template_name,
            phone=phone,
            variables=variables,
            language=language,
            buttons=buttons
        )

        code = 200 if result.get("status") == "success" else 400
        return Response(result, status=code)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def whatsapp_webhook(request):

    def send_reply(session, phone, reply_text):
        """
        Universal send helper:
         - translates to Hindi if session.language == "hi"
         - ensures reply is string
         - sends via send_whatsapp_text
         - returns a DRF Response so the view returns properly
        """
        try:
            # ensure reply_text is a plain string (handle tuples returned by get_reply)
            if isinstance(reply_text, (tuple, list)):
                reply_text = reply_text[0]
            reply_text = str(reply_text)

            # translate if required
            if getattr(session, "language", "en") == "hi":
                reply_text = translate_to_hindi(reply_text)

            send_whatsapp_text(phone, ensure_whatsapp_text(reply_text))
        except Exception as e:
            # don't crash the webhook; log and fall back to sending original
            print("send_reply error:", e)
            try:
                send_whatsapp_text(phone, ensure_whatsapp_text(str(reply_text)))
            except Exception as e2:
                print("send_reply fallback error:", e2)
        return Response(status=200)

    if request.method == "GET":
        if request.GET.get("hub.verify_token") == settings.VERIFY_TOKEN:
            return HttpResponse(request.GET.get("hub.challenge"))
        return HttpResponse("Invalid verification token", status=403)

    if request.method == "POST":
        payload = request.data
        try:
            message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
            phone = message["from"]
            text = message.get("text", {}).get("body", "").strip()
            interactive = message.get("interactive", {}) or {}
            button_payload = None

            # Interactive button replies
            if interactive.get("type") == "button_reply":
                button_payload = interactive.get("button_reply", {}).get("id")

            # Fallback for old style
            if not button_payload:
                button_payload = message.get("button", {}).get("payload")

            if button_payload:
                print("BUTTON PAYLOAD:", button_payload)

                # Accept appointment
                if button_payload.startswith("approve_appt_"):
                    appt_id = button_payload.replace("approve_appt_", "")
                    return process_appointment_approval(request, appt_id, approved=True)

                # Reject appointment
                if button_payload.startswith("reject_appt_"):
                    appt_id = button_payload.replace("reject_appt_", "")
                    return process_appointment_approval(request, appt_id, approved=False)

                return Response(status=200)
        except (KeyError, IndexError):
            return Response(status=200)

        session = get_or_create_session(phone)

        # 1) Teacher check first
        teacher = TeacherProfile.objects.filter(contact__icontains=phone[-10:]).first()
        if teacher:
            print("YEs yes")
            reply, meta = get_reply(text, session)
            return send_reply(session, phone, reply)

        # 2) Switch child command
        if text.lower() in ["switch", "switch child", "change student", "change", "change child"]:
            if session.child_list:
                session.awaiting_child_selection = True
                session.selected_student_id = None
                session.save()
                return send_reply(session, phone, _format_children_menu(session.child_list))
            else:
                return send_reply(session, phone, "No linked students found for switching.")

        # 3) Child selection flow
        if session.awaiting_child_selection:
            ok = select_child(session, text)
            if ok:
                session.awaiting_child_selection = False
                session.save()
                return send_reply(session, phone, "Child selected. You may now ask about homework, attendance, fees, etc.")
            else:
                return send_reply(session, phone, "Invalid choice.\n" + _format_children_menu(session.child_list))

        # 4) Identify linked students
        students = list(StudentProfile.objects.filter(phone_number__icontains=phone[-10:]))

        if not students:
            # Guest
            save_last_message(session, text)
            reply, meta = get_reply(text, session)
            return send_reply(session, phone, reply)

        # 5) One child only
        if len(students) == 1:
            st = students[0]
            children = [{
                "id": st.id,
                "student_name": st.student_name,
                "class_name": str(st.class_name),
                "section_name": st.section_name
            }]
            set_child_list(session, children)

            session.selected_student_id = st.id
            session.awaiting_child_selection = False
            session.save()

            reply, meta = get_reply(text, session)
            return send_reply(session, phone, reply)

        # 6) Multiple children -> ask to select
        children = [{
            "id": s.id,
            "student_name": s.student_name,
            "class_name": str(s.class_name),
            "section_name": s.section_name
        } for s in students]

        set_child_list(session, children)
        session.awaiting_child_selection = True
        session.selected_student_id = None
        session.save()

        return send_reply(session, phone, _format_children_menu(children))

def ensure_whatsapp_text(msg):
    if isinstance(msg, (tuple, list)):
        msg = msg[0]
    return str(msg).strip()


def handle_teacher_message(phone, text, teacher):
    """
    Handles all messages coming from a Teacher.
    Routes through the same get_reply() pipeline,
    but ensures the session is marked as teacher mode.
    """

    # Create or fetch session
    session = get_or_create_session(phone)

    # Mark session as teacher-mode
    session.is_teacher = True
    session.save(update_fields=["is_teacher"])

    # Pass message to the existing chat engine
    reply, meta = get_reply(text, session)
    # 🔥 TRANSLATE BEFORE SENDING
    if session.language == "hi":
        reply = translate_to_hindi(reply)
    # Send response back
    send_whatsapp_text(phone, reply)

    return Response(status=200)

def send_reply_with_language(session, phone, reply):
    # Translate if Hindi is enabled
    if session.language == "hi":
        reply = translate_to_hindi(reply)

    send_whatsapp_text(phone, ensure_whatsapp_text(reply))

from chat.models import Appointment
def process_appointment_approval(request, appt_id, approved):
    if not str(appt_id).isdigit():
        print("Invalid appt ID:", appt_id)
        return Response(status=200)

    appt = Appointment.objects.filter(id=int(appt_id)).first()
    if not appt:
        return Response(status=200)

    # Update status
    appt.status = "Accepted" if approved else "Rejected"
    appt.save(update_fields=["status"])

    parent_phone = appt.contact_number

    # Message to parent
    if approved:
        parent_msg = (
            f"Your appointment request with "
            f"{appt.teacher.teacher_name if appt.teacher else 'the Principal'} "
            f"on {appt.preferred_datetime} has been approved."
        )
    else:
        parent_msg = (
            f"Your appointment request with "
            f"{appt.teacher.teacher_name if appt.teacher else 'the Principal'} "
            f"has been rejected. Please choose another time."
        )

    send_whatsapp_text(parent_phone, parent_msg)

    # Confirm back to admin also
    admin_phone = request.data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
    send_whatsapp_text(admin_phone, f"Appointment {appt.status} successfully.")

    return Response(status=200)