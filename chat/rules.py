"""
Rule-based intent matcher.
Priority order:
1. Global commands (menu, back, help) → can interrupt any flow
2. Exact keyword match
3. Safe contains-based match
"""

# -------------------------
# GLOBAL COMMANDS
# -------------------------
GLOBAL_COMMANDS = {
    "menu": {"intent": "show_menu", "force_reset": True},
    "back": {"intent": "back"},
    "help": {"intent": "help"},
}

# -------------------------
# INTENT DEFINITIONS
# -------------------------
INTENTS = {
    # Student Core
    "homework": ["homework"],
    "fees": ["fees", "fee"],
    "timetable": ["timetable", "time table"],
    "attendance": ["attendance", "attend", "present", "absent"],

    # Exams / Results
    "exam": ["exam", "exams", "test"],
    "result": ["result", "marks", "grade"],

    # Notices / Library
    "notice": ["notice", "notices", "event"],
    "library": ["library", "books"],

    # Student / Child
    "child_info": ["child", "my child", "son", "daughter", "student", "children"],

    # Forms
    "admission_form": ["admission", "admission form", "apply"],
    "feedback_form": ["feedback", "complaint", "complain", "issue", "suggestion"],
    "appointment_form": ["appointment", "meeting", "ptm", "meet"],

    # Transport
    "bus_info": ["bus", "transport", "pickup", "drop", "driver"],

    # Report
    "student_report": ["report", "performance", "analysis", "progress"],

    # Language
    "change_language_hi": ["hindi", "switch to hindi", "change language"],
    "change_language_en": ["english", "eng", "switch to english", "speak english"],
}

# -------------------------
# NORMALIZER
# -------------------------
def normalize(text: str) -> str:
    return text.lower().strip().replace("\\", "")

# -------------------------
# MAIN MATCHER
# -------------------------
def match_rule(text: str):
    if not text:
        return None

    t = normalize(text)

    # 1️⃣ GLOBAL OVERRIDES (menu / back / help)
    if t in GLOBAL_COMMANDS:
        return GLOBAL_COMMANDS[t]

    # 2️⃣ EXACT MATCH (strong intent)
    for intent, keywords in INTENTS.items():
        if t in keywords:
            return {"intent": intent}

    # 3️⃣ CONTAINS MATCH (controlled & safe)
    for intent, keywords in INTENTS.items():
        for kw in keywords:
            if kw in t:
                return {"intent": intent}

    return None



# # chat/rules.py
# """
# Keep rule definitions simple: mapping from user input -> intent + optional metadata.
# Extend or load from DB/JSON later.
# """
# RULES = {
#     # MAIN MENU
#     "menu": {"intent": "show_menu"},
#
#     # DIRECT NUMBER SELECTIONS
#     "1": {"intent": "homework"},
#     "2": {"intent": "fees"},
#     "3": {"intent": "timetable"},
#
#     # STANDARD FEATURE INTENTS
#     "homework": {"intent": "homework"},
#     "fees": {"intent": "fees"},
#     "timetable": {"intent": "timetable"},
#     "attendance": {"intent": "attendance"},
#     "attendence": {"intent": "attendance"},  # common misspelling
#
#     # EXAM / MARKS / RESULTS
#     "exam": {"intent": "exam"},
#     "exams": {"intent": "exam"},
#     "test": {"intent": "exam"},
#     "result": {"intent": "result"},
#     "marks": {"intent": "result"},
#     "grade": {"intent": "result"},
#
#     # NOTICES
#     "notice": {"intent": "notice"},
#     "notices": {"intent": "notice"},
#
#     # LIBRARY
#     "library": {"intent": "library"},
#     "books": {"intent": "library"},
#
#     # GENERIC
#     "help": {"intent": "help"},
#     "back": {"intent": "back"},
#
#     #Student details
#     "child": {"intent": "child_info"},
#     "my child": {"intent": "child_info"},
#     "student": {"intent": "child_info"},
#     "son": {"intent": "child_info"},
#     "daughter": {"intent": "child_info"},
#     "children": {"intent": "child_info"},
#
#     # Admission
#     "admission": {"intent": "admission_form"},
#     "admission form": {"intent": "admission_form"},
#     "apply": {"intent": "admission_form"},
#
#     #feedback
#     "feedback": {"intent": "feedback_form"},
#     "complaint": {"intent": "feedback_form"},
#     "suggestion": {"intent": "feedback_form"},
#     "issue": {"intent": "feedback_form"},
#
#     # PTM/Appointment
#     "appointment": {"intent": "appointment_form"},
#     "meeting": {"intent": "appointment_form"},
#     "ptm": {"intent": "appointment_form"},
#     "meet": {"intent": "appointment_form"},
#
#     # Transport
#     "bus": {"intent": "bus_info"},
#     "transport": {"intent": "bus_info"},
#     "pickup": {"intent": "bus_info"},
#     "drop": {"intent": "bus_info"},
#     "driver": {"intent": "bus_info"},
#
#     # Report Card
#     "report": {"intent": "student_report"},
#     "performance": {"intent": "student_report"},
#     "analysis": {"intent": "student_report"},
#     "progress": {"intent": "student_report"},
#
#     # Language
#     "language": {"intent": "change_language"},
#     "hindi": {"intent": "change_language"},
#     "switch language": {"intent": "change_language"},
#     "change language": {"intent": "change_language"},
#     "switch to hindi": {"intent": "change_language"},
#
#     # English again
#     "english" : {"intent": "change_language_english"},
#     "eng" : {"intent": "change_language_english"},
#     "switch to english" : {"intent": "change_language_english"},
#     "speak english" : {"intent": "change_language_english"},
#
# }
#
# def match_rule(text: str):
#     if not text:
#         return None
#
#     t = text.lower().strip()
#
#     # exact match first
#     if t in RULES:
#         return RULES[t]
#
#     # contains-based (light fuzzy matching)
#
#     if "report" in t or "performance" in t or "analysis" in t or "report card" in t or "student report" in t:
#         return RULES["report"]
#
#     if "homework" in t:
#         return RULES["homework"]
#
#     if "fee" in t or "fees" in t:
#         return RULES["fees"]
#
#     if "time table" in t or "timetable" in t or "time table" in t:
#         return RULES["timetable"]
#
#     if "attend" in t or "present" in t or "absent" in t:
#         return RULES["attendance"]
#
#     if "exam" in t or "test" in t:
#         return RULES["exam"]
#
#     if "mark" in t or "result" in t or "grade" in t:
#         return RULES["result"]
#
#     if "notice" in t or "event" in t:
#         return RULES["notice"]
#
#     if "books" in t or "library" in t:
#         return RULES["library"]
#
#     if "menu" in t:
#         return RULES["menu"]
#
#     if "child" in t or "son" in t or "student" in t or "daughter" in t or "children" in t:
#         return RULES["child"]
#     if "admission" in t or "apply" in t:
#         return RULES["admission"]
#
#     if "feedback" in t or "complaint" in t or "issue" in t or "suggestion" in t:
#         return RULES["feedback"]
#
#
#
#     if "bus" in t or "transport" in t or "schoolbus" in t:
#         return RULES["bus"]
#
#     if "driver" in t or "pickup" in t or "drop" in t:
#         return RULES["bus"]
#
#     if "appointment" in t or "meeting" in t or "ptm" in t or "book an appointment":
#         return RULES["appointment"]
#
#     if "hindi" in t or "language" in t or "change language":
#         return RULES["language"]
#
#     if "english" in t or "speak english" in t or "switch to english" in t:
#         return {"intent": "change_language_english"}
#
#     return None
#
