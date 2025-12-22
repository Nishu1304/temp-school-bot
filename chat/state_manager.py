from datetime import timedelta
from django.utils import timezone
from chat.models import ChatState
from Account.models import StudentProfile

def get_user_state(phone: str):
    state, _ = ChatState.objects.get_or_create(phone=phone)
    return state

def set_user_state(phone: str, menu: str):
    state, _ = ChatState.objects.get_or_create(phone=phone)
    state.current_menu = menu
    state.save(update_fields=["current_menu", "updated_at"])

def set_selected_student(phone: str, student_id: int):
    state, _ = ChatState.objects.get_or_create(phone=phone)
    state.selected_student_id = student_id
    state.save(update_fields=["selected_student_id", "updated_at"])

def get_selected_student(phone: str):
    try:
        state = ChatState.objects.get(phone=phone)
        if state.selected_student_id:
            return StudentProfile.objects.get(id=state.selected_student_id)
    except (ChatState.DoesNotExist, StudentProfile.DoesNotExist):
        pass
    return None

def touch_state(phone: str):
    state, _ = ChatState.objects.get_or_create(phone=phone)
    state.updated_at = timezone.now()
    state.save(update_fields=["updated_at"])

def is_session_stale(phone: str, minutes: int = 10) -> bool:
    try:
        state = ChatState.objects.get(phone=phone)
        return timezone.now() - state.updated_at > timedelta(minutes=minutes)
    except ChatState.DoesNotExist:
        return True
