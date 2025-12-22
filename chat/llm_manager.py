# chat/llm_manager.py

from groq import Groq
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

GROQ_API_KEY = getattr(settings, "GROQ_API_KEY", None)

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Choose model
DEFAULT_MODEL = "llama-3.1-8b-instant"     # Fast + free + great quality
MAX_TOKENS = getattr(settings, "LLM_MAX_TOKENS", 200)


def generate_llm_reply(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS) -> str:
    """
    Sends a prompt to Groq LLM and returns the generated reply.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the SchoolBOS Assistant. "
                        "Your job is to answer simply, clearly, and in a friendly tone. "
                        "Always keep your answers short (under 60 words). "
                        "Do not create a personal identity or backstory. "
                        "Do not mention fake names, teachers, or school names. "
                        "You must not hallucinate details. "
                        "If a question is unclear, ask the user for the exact class/section/date. "
                        "Follow menu rules if the user types numbers like 1, 2, 3. "
                        "Be concise and practical."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=0.9,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.exception("Groq LLM error: %s", e)
        return "Sorry, I'm having some difficulty answering right now."
