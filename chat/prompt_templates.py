# chat/prompt_templates.py

"""
Centralized templates for LLM prompts.
Ensures consistent tone, short replies, and predictable outputs.
"""


# ---------------------------------------------------------
# GLOBAL STYLE
# ---------------------------------------------------------
STYLE = (
    "Reply in under 50 words. Be clear, friendly, and direct. "
    "Avoid unnecessary details. No personal identities. "
    "Do not invent information not provided. "
)


# ---------------------------------------------------------
# INTENT-BASED PROMPT TEMPLATES
# ---------------------------------------------------------
def build_intent_prompt(intent, user_text, menu_state):
    """
    Intent-based prompting for concise LLM responses.
    Guest and Parent menus are kept fully structured
    while LLM shortens wording automatically.
    """

    # -------------------------
    # MENU
    # -------------------------
    if intent == "show_menu":
        if menu_state == "guest":
            return (
                    STYLE +
                    "Create a concise, clean menu for a guest user. "
                    "Keep the formatting and options EXACTLY as below but make the wording short:\n\n"

                    "📌 Main Menu\n"
                    "1. Admission Inquiry\n"
                    "2. School Fees & Rules\n"
                    "3. Contact Details\n"
                    "4. School Notices & Events\n\n"

                    "🔍 You may also ask:\n"
                    "- “Show admission process”\n"
                    "- “What are the school timings?”\n"
                    "- “Tell me about school facilities”\n"
                    "- “When is the next holiday?”\n\n"

                    "End with: 'Type a number or ask anything directly.' "
                    "Do NOT change the structure. Only make wording concise."
            )
        else:
            return (
                    STYLE +
                    "Create a concise parent menu. "
                    "Keep the formatting and options EXACTLY as written below. "
                    "Shorten wording only, do NOT modify structure:\n\n"

                    "👋 Hello parent! Here’s everything you can check about your child:\n\n"

                    "📌 Student Menu\n"
                    "1. Homework\n"
                    "2. Attendance\n"
                    "3. Timetable\n"
                    "4. Fees Status\n"
                    "5. Notices\n"
                    "6. Exam Schedule\n"
                    "7. Results\n"
                    "8. Library Records\n"
                    "9. Bus Information\n\n"

                    "📁 Forms & Services\n"
                    "10. Admission Form (for another child)\n"
                    "11. Appointment Booking (Teacher / Principal)\n"
                    "12. Feedback / Complaint\n\n"

                    "🔄 Other Options\n"
                    "- Switch Child\n"
                    "- Change Language (Hindi / English)\n"
                    "- Show Menu\n\n"

                    "Make the introduction short but keep lists EXACTLY the same."
            )

    # -------------------------
    # HELP
    # -------------------------
    if intent == "help":
        return (
                STYLE +
                "User asked for help. Provide a very short explanation that they can "
                "use the menu or ask about homework, attendance, fees, timetable, results, notices, etc."
        )

    # -------------------------
    # BACK
    # -------------------------
    if intent == "back":
        return (
                STYLE +
                "User wants to go back. Confirm briefly and show the short menu again."
        )

    # -------------------------
    # Default fallback
    # -------------------------
    return (
            STYLE +
            f"User said: '{user_text}'. Provide a very short, helpful school-related response."
    )


# ---------------------------------------------------------
# RAG PROMPT
# ---------------------------------------------------------
def build_rag_prompt(query, documents):
    """
    Convert RAG-retrieved docs into a short context prompt for the LLM.
    """

    context_text = ""
    for d in documents:
        snippet = (d.content[:200] + "...") if len(d.content) > 200 else d.content
        context_text += f"- {d.title}: {snippet}\n"

    return (
        STYLE +
        "Use ONLY this school information to answer the question. "
        "Do not hallucinate or add extra details.\n\n"
        f"QUESTION: {query}\n\n"
        f"DOCUMENTS:\n{context_text}"
    )
