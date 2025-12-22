# chat/session_manager.py
import json
from .models import ChatSession
from Account.models import StudentProfile, TeacherProfile  # adjust import path if different
from datetime import timedelta
from django.utils import timezone


SESSION_EXPIRY_MINUTES = 2
#phone_norm = phone.strip()
def get_or_create_session(phone):
    phone_norm = phone.strip()
    session, created = ChatSession.objects.get_or_create(phone_number=phone_norm)
    teacher = TeacherProfile.objects.filter(contact=phone_norm)
    print(teacher)
    if teacher is None:
        is_teacher = False
    else:
        is_teacher = True
    # 🔥 Expiry check
    if not created:
        if timezone.now() - session.updated_at > timedelta(minutes=SESSION_EXPIRY_MINUTES):
            # RESET instead of delete (safer)
            session.current_form = None
            session.form_step = 0
            session.form_data = {}
            session.awaiting_child_selection = False
            session.selected_student_id = None
            session.is_teacher = is_teacher
            session.last_message = None
            session.language = "en"
            session.save()

    return session
def update_menu_state(session: ChatSession, new_state: str):
    session.menu_state = new_state
    session.save(update_fields=["menu_state", "updated_at"])

def save_last_message(session: ChatSession, text: str):
    session.last_message = text
    session.save(update_fields=["last_message", "updated_at"])

def set_child_list(session: ChatSession, children: list):
    """
    children: list of dicts [{id:..., 'student_name':..., 'class_name':..., 'section_name':...}, ...]
    """
    session.child_list = children
    session.awaiting_child_selection = True if len(children) > 1 else False
    # if only 1 child, you may auto-select it
    if len(children) == 1:
        session.selected_student_id = str(children[0]['id'])
        session.awaiting_child_selection = False
    session.save()

def select_child(session: ChatSession, child_index: int):
    """
    child_index: 1-based index from user reply (1,2,...)
    """
    try:
        idx = int(child_index) - 1
        children = session.child_list or []
        if 0 <= idx < len(children):
            session.selected_student_id = str(children[idx]['id'])
            session.awaiting_child_selection = False
            session.save()
            return True
        return False
    except Exception:
        return False

def reset_child_selection(session: ChatSession):
    session.child_list = []
    session.selected_student_id = None
    session.awaiting_child_selection = False
    session.save()


def reset_session(session):
    session.current_form = None
    session.form_step = 0
    session.form_data = {}
    session.awaiting_child_selection = False
    session.selected_student_id = None
    session.is_teacher = False
    session.last_message = None
    session.save()
