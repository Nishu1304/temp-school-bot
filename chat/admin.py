from django.contrib import admin
from .models import ChatSession, SchoolDocument


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "menu_state", "last_intent", "updated_at", "selected_student_id", "awaiting_child_selection")
    search_fields = ("phone_number", "last_intent", "selected_student_id")
    list_filter = ("menu_state", "awaiting_child_selection", "updated_at")
    readonly_fields = ("updated_at",)
    ordering = ("-updated_at",)


@admin.register(SchoolDocument)
class SchoolDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "doc_type", "created_at")
    search_fields = ("title", "doc_type")
    list_filter = ("doc_type", "created_at")
    ordering = ("-created_at",)
