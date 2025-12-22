# from chat.lang_manager import get_lang_text
#
# def get_menu_text(menu_key, lang, student=None):
#     """
#     Fetch localized menu text and format placeholders.
#     Compatible with updated StudentProfile (no user.username).
#     """
#     return get_lang_text(menu_key, lang).format(
#         student_name=student.student_name if student else "",
#         class_sec=f"{student.class_name.class_name}{student.section}" if student else ""
#     )
#
#
# MENUS = {
#     "main_menu": {
#         "options": {
#             "1": "attendance_menu",
#             "2": "fees_menu",
#             "3": "marks_menu",
#             "4": "exams_menu",
#             "5": "library_menu",
#             "6": "notices_menu",
#         },
#     },
#
#     "attendance_menu": {
#         "options": {
#             "1": "attendance_today",
#             "2": "attendance_month",
#             "3": "attendance_percentage",
#             "0": "main_menu",
#         },
#     },
#
#     "fees_menu": {
#         "options": {
#             "1": "fees_summary",
#             "2": "fees_paid",
#             "3": "fees_due",
#             "0": "main_menu",
#         },
#     },
#
#     "marks_menu": {
#         "options": {
#             "1": "marks_recent",
#             "2": "marks_subjectwise",
#             "3": "marks_overall",
#             "0": "main_menu",
#         },
#     },
#
#     "exams_menu": {
#         "options": {
#             "1": "exams_upcoming",
#             "2": "exams_ongoing",
#             "3": "exams_completed",
#             "0": "main_menu",
#         },
#     },
#
#     "library_menu": {
#         "options": {
#             "1": "library_issued",
#             "2": "library_due",
#             "3": "library_summary",
#             "0": "main_menu",
#         },
#     },
#
#     "notices_menu": {
#         "options": {
#             "1": "notices_recent",
#             "0": "main_menu",
#         },
#     },
# }
