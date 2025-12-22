from django.db import models
import json

from django.db import models
from django.contrib.postgres.fields import ArrayField  # if using Postgres
import json

class ChatSession(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    menu_state = models.CharField(max_length=100, default="default")
    last_message = models.TextField(blank=True, null=True)
    last_intent = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New fields for student selection flow
    # Use JSONField for sqlite/django 3.1+: from django.db.models import JSONField
    try:
        from django.db.models import JSONField as _JSONField
    except Exception:
        # fallback for older django versions
        from django.contrib.postgres.fields import JSONField as _JSONField

    child_list = _JSONField(blank=True, null=True, default=list)   # list of {id,name,class,section}
    selected_student_id = models.CharField(max_length=50, blank=True, null=True)
    awaiting_child_selection = models.BooleanField(default=False)
    current_form = models.CharField(max_length=50, null=True, blank=True)
    form_step = models.IntegerField(default=0)
    form_data = models.JSONField(default=dict, blank=True)
    is_teacher = models.BooleanField(default=False)
    selected_class_id = models.IntegerField(null=True, blank=True)
    selected_student_for_report = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=5, default="en")

    def __str__(self):
        return self.phone_number

class SchoolDocument(models.Model):
    DOC_TYPES = [
        ("timetable", "Timetable"),
        ("fee", "Fee Structure"),
        ("notice", "Notice / Announcement"),
        ("rules", "Rules & Regulations"),
        ("teachers", "Teacher List"),
        ("general", "General Information"),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()   # Extracted plain text for RAG
    file = models.FileField(upload_to="school_docs/", blank=True, null=True)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES, default="general")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.doc_type})"


class Feedback(models.Model):
    student = models.ForeignKey(
        'Account.StudentProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    parent_name = models.CharField(max_length=100, blank=True, null=True)
    feedback_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.parent_name or 'Guest'} on {self.created_at}"


class Appointment(models.Model):
    APPOINTMENT_WITH = [
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
    ]

    student = models.ForeignKey('Account.StudentProfile', on_delete=models.SET_NULL, null=True)
    parent_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)

    appointment_with = models.CharField(max_length=20, choices=APPOINTMENT_WITH)
    teacher = models.ForeignKey('Account.TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True)

    reason = models.TextField()
    preferred_datetime = models.CharField(max_length=100)

    status = models.CharField(max_length=20, default="Pending")  # Pending/Accepted/Rejected

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parent_name} ({self.appointment_with})"
