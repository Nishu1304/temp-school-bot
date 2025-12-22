import json
import os
import requests
from django.conf import settings

# Local template folder (for static JSON templates)
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


# ---------------------------------------------------------------------
# 🔹 Template Loading Utilities
# ---------------------------------------------------------------------
def load_template_json(template_name: str) -> dict:
    """
    Load JSON template definition from local file (e.g., whatsapp/templates/test_template.json).
    """
    path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# 🔹 Variable Replacement Helper
# ---------------------------------------------------------------------
def _replace_vars(text: str, variables: dict) -> str:
    if not text:
        return text
    for k, v in variables.items():  # k like "1", "2", ...
        text = text.replace(f"{{{{{k}}}}}", str(v))
    return text


# ---------------------------------------------------------------------
# 🔹 Component Builder (Meta-compatible)
# ---------------------------------------------------------------------
def build_components_from_json(tjson: dict) -> list:
    """
    Build the 'components' section for WhatsApp API payload dynamically.
    Supports body variables + buttons (URL / quick_reply).
    """
    comps = []

    # body variables
    variables = tjson.get("body", {}).get("variables", {})
    if variables:
        comps.append({
            "type": "body",
            "parameters": [
                {"type": "text", "text": str(v)} for v in variables.values()
            ]
        })

    # buttons
    for idx, b in enumerate(tjson.get("buttons", [])):
        if b["type"] == "url":
            comps.append({
                "type": "button",
                "sub_type": "url",
                "index": str(idx),
                "parameters": [{"type": "text", "text": b.get("url", "")}]
            })
        elif b["type"] == "quick_reply":
            comps.append({
                "type": "button",
                "sub_type": "quick_reply",
                "index": str(idx),
                "parameters": [{"type": "payload", "payload": b.get("text", "")}]
            })

    return comps


# ---------------------------------------------------------------------
# 🔹 Core WhatsApp API Sender
# ---------------------------------------------------------------------
def send_whatsapp_message(
    phone: str,
    template_name: str,
    language: str,
    components_json_or_none: dict,
    variables: dict
):
    """
    Build and send WhatsApp template message.
    Automatically merges JSON file template and request-provided variables.
    """
    # Prefer inline JSON components if given
    if components_json_or_none:
        tjson = {"name": template_name, "language": language, **components_json_or_none}
    else:
        tjson = load_template_json(template_name)
        tjson["language"] = language or tjson.get("language", "en")

    built_components = build_components_from_json(tjson)

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": tjson["name"],
            "language": {"code": tjson.get("language", "en")},
            "components": built_components
        }
    }

    url = f"https://graph.facebook.com/v24.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            print("❌ WhatsApp API Error:", response.text)
        response.raise_for_status()

        return {"status": "success", "response": response.json()}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Network/API error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# ---------------------------------------------------------------------
# 🔹 Public Internal Service Entry Point
# ---------------------------------------------------------------------
def send_message_service(template_name, phone, variables=None, language="en", buttons=None):
    """
    Send WhatsApp template without needing a .json file.
    Supports body params and quick-reply buttons.
    """

    print("\n================= SEND MESSAGE SERVICE =================")
    print(f"[DEBUG] template_name: {template_name}")
    print(f"[DEBUG] phone: {phone}")
    print(f"[DEBUG] variables: {variables}")
    print(f"[DEBUG] buttons: {buttons}")

    variables = variables or {}
    buttons = buttons or []

    # -----------------------------------------------------
    # Build body parameters
    # -----------------------------------------------------
    body_parameters = []
    for key in sorted(variables.keys(), key=lambda x: int(x)):   # ensure {{1}}, {{2}}, {{3}} ordering
        print(f"[DEBUG] Adding variable {key}: {variables[key]}")
        body_parameters.append({
            "type": "text",
            "text": str(variables[key])
        })

    components = []

    # BODY component
    if body_parameters:
        components.append({
            "type": "body",
            "parameters": body_parameters
        })

    # -----------------------------------------------------
    # BUTTON COMPONENTS (quick replies)
    # -----------------------------------------------------
    for idx, btn in enumerate(buttons):
        print(f"[DEBUG] Adding button #{idx}: {btn}")

        # Ensure payload exists
        payload_value = btn.get("id") or btn.get("payload")
        if not payload_value:
            raise ValueError("Each button must have an 'id' or 'payload' key.")

        components.append({
            "type": "button",
            "sub_type": "quick_reply",
            "index": idx,
            "parameters": [
                {
                    "type": "payload",
                    "payload": payload_value
                }
            ]
        })

    # -----------------------------------------------------
    # Final Payload
    # -----------------------------------------------------
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": components
        }
    }

    print("\n========== FINAL GENERATED PAYLOAD ===========")
    import pprint
    pprint.pprint(payload)
    print("================================================\n")

    return send_whatsapp_message_raw(payload)



def send_whatsapp_message_raw(payload):
    """
    Sends raw JSON payload to the WhatsApp Cloud API.
    """

    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    print("[DEBUG] Sending POST request to Meta API...")
    print(f"[DEBUG] URL: {url}")

    r = requests.post(url, json=payload, headers=headers)

    print("\n=========== WHATSAPP API RESPONSE ===========")
    print(r.text)
    print("==============================================\n")

    return r.json()


def send_whatsapp_text(phone: str, text: str):
    """
    Send a plain text WhatsApp message (no template, valid only inside 24-hour session).
    """
    import requests
    url = f"https://graph.facebook.com/v22.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }
    print(payload)
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code != 200:
            print("❌ WhatsApp text send failed:", r.text)
        return r.json()
    except Exception as e:
        print("⚠️ send_whatsapp_text error:", e)
        return None