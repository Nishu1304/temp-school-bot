# from .menus import MENUS, get_menu_text
# from .state_manager import (
#     get_user_state, set_user_state, touch_state, is_session_stale,
#     get_selected_student, set_selected_student
# )
# from Account.models import StudentProfile
# from .handlers import (
#     attendance_handler, fees_handler, marks_handler,
#     exams_handler, library_handler, notices_handler, summary_handler
# )
# from chat.lang_manager import get_lang_text
#
#
# SHORTCUTS = {
#     "attendance": "attendance_menu",
#     "fees": "fees_menu",
#     "marks": "marks_menu",
#     "exams": "exams_menu",
#     "library": "library_menu",
#     "notices": "notices_menu",
#     "today": "attendance_today",
#     "report": "summary_now",
#     "help": "main_menu",
#     "menu": "main_menu",
#     "switch": "switch_student",
#     "language": "language_switch_prompt"
# }
#
#
# # 🔹 Format menu text using STUDENT NEW FIELDS
# def _format_menu_text(key: str, student, lang="English"):
#     translated = get_lang_text(key, lang)
#     if translated.startswith("[Missing"):
#         translated = get_lang_text(key, "English")
#
#     student_name = student.student_name if student else "—"
#     class_sec = f"{student.class_name.class_name}{student.section_name}" if student else "—"
#
#     return (
#         translated.format(student_name=student_name, class_sec=class_sec)
#         + "\n\n"
#         + get_lang_text("change_language_footer", lang)
#     )
#
#
# # 🔹 Student list (updated)
# def _prompt_student_list(children):
#     msg = "👨‍👩‍👧 Please choose the student:\n"
#     for i, c in enumerate(children, 1):
#         class_sec = f"{c.class_name.class_name}{c.section_name}"
#         msg += f"{i}️⃣ {c.student_name} ({class_sec})\n"
#     msg += "\nReply with a number."
#     return msg
#
#
# def handle_menu_navigation(phone, text, user=None):
#     text = (text or "").strip().lower()
#     touch_state(phone)
#
#     lang = getattr(user, "language_preference", "English") or "English"
#
#     # parent-only restriction
#     if not user:
#         return "⚠️ Access restricted. Only registered parents can use this service."
#
#     # 🌍 language switch start
#     if text == "language":
#         return get_lang_text("language_switch_prompt", lang)
#
#     if text.lower() in ["hindi", "english"]:
#         user.language_preference = text.title()
#         user.save(update_fields=["language_preference"])
#         lang = user.language_preference
#
#         reply = get_lang_text("language_switched", lang)
#
#         selected = get_selected_student(phone)
#         if selected:
#             reply += "\n\n" + get_lang_text("main_menu", lang).format(
#                 student_name=selected.student_name,
#                 class_sec=f"{selected.class_name.class_name}{selected.section_name}"
#             )
#             reply += "\n\n" + get_lang_text("change_language_footer", lang)
#
#         return reply
#
#     # ⭐ NEW: Get parent’s children via phone number
#     parent_phone = phone[-10:]
#     children = StudentProfile.objects.filter(parent_contact__icontains=parent_phone).order_by("id")
#
#     if not children.exists():
#         return "No students found for this phone number. Please contact the school."
#
#     selected = get_selected_student(phone)
#
#     # stale session reset
#     if is_session_stale(phone, minutes=10):
#         set_user_state(phone, "main_menu")
#
#     # initial selection (pick child if only 1)
#     if not selected:
#         if children.count() == 1:
#             child = children.first()
#             set_selected_student(phone, child.id)
#             set_user_state(phone, "main_menu")
#             return (
#                 f"✅ Selected *{child.student_name} ({child.class_name.class_name}{child.section_name})*\n\n"
#                 + _format_menu_text("main_menu", child, lang)
#             )
#         set_user_state(phone, "select_student")
#         return _prompt_student_list(children)
#
#     # GLOBAL SHORTCUTS
#     if text in SHORTCUTS:
#         action = SHORTCUTS[text]
#
#         if action == "switch_student":
#             set_user_state(phone, "select_student")
#             return _prompt_student_list(children)
#
#         if action == "summary_now":
#             return summary_handler.handle(phone, user, selected)
#
#         if action in MENUS:
#             set_user_state(phone, action)
#             return _format_menu_text(action, selected, lang)
#
#         if action.startswith("attendance_"):
#             return _wrap_with_footer(
#                 attendance_handler.handle(phone, user, action, selected),
#                 selected
#             )
#
#     # NORMAL MENU FLOW
#     state = get_user_state(phone)
#     current_menu = state.current_menu
#     options = MENUS.get(current_menu, MENUS["main_menu"]).get("options", {})
#
#     # student selection
#     if current_menu == "select_student":
#         try:
#             idx = int(text) - 1
#             chosen = list(children)[idx]
#             set_selected_student(phone, chosen.id)
#             set_user_state(phone, "main_menu")
#             return (
#                 f"✅ Selected *{chosen.student_name} ({chosen.class_name.class_name}{chosen.section_name})*\n\n"
#                 + _format_menu_text("main_menu", chosen, lang)
#             )
#         except:
#             return "❌ Invalid choice. Please reply with a valid number."
#
#     # normal option selection
#     if text in options:
#         next_action = options[text]
#
#         if next_action in MENUS:
#             set_user_state(phone, next_action)
#             return _format_menu_text(next_action, selected, lang)
#
#         # handlers
#         if next_action.startswith("attendance_"):
#             return _wrap_with_footer(attendance_handler.handle(phone, user, next_action, selected), selected)
#         if next_action.startswith("fees_"):
#             return _wrap_with_footer(fees_handler.handle(phone, user, next_action, selected), selected)
#         if next_action.startswith("marks_"):
#             return _wrap_with_footer(marks_handler.handle(phone, user, next_action, selected), selected)
#         if next_action.startswith("exams_"):
#             return _wrap_with_footer(exams_handler.handle(phone, user, next_action, selected), selected)
#         if next_action.startswith("library_"):
#             return _wrap_with_footer(library_handler.handle(phone, user, next_action, selected), selected)
#         if next_action.startswith("notices_"):
#             return _wrap_with_footer(notices_handler.handle(phone, user, next_action, selected), selected)
#
#     # INVALID fallback
#     return (
#         get_lang_text("invalid_option", lang)
#         + "\n\n"
#         + _format_menu_text(current_menu, selected, lang)
#     )
#
#
# def _wrap_with_footer(msg, student):
#     class_sec = f"{student.class_name.class_name}{student.section_name}"
#     footer = (
#         f"\n\nCurrently viewing: *{student.student_name} ({class_sec})*\n"
#         "Type *menu* to go back or *switch* to change student."
#     )
#     return msg + footer
