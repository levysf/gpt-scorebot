import requests
import datetime
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# === CONFIG ===
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TO_EMAIL = "joe@levysf.com"
FROM_EMAIL = "Joe's AI Assistant <aiassistant@levysf.com>"

# === UTILS ===
def get_contacts():
    res = requests.get(
        "https://api.realnex.com/api/investors",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"},
        params={"limit": 1000}
    )
    return res.json()

def get_history(contact_id):
    res = requests.get(
        f"https://api.realnex.com/api/history?contact_id={contact_id}",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"}
    )
    return res.json()

def score_contact(contact, history_notes):
    # GPT scoring logic — placeholder
    name = contact.get("name", "Unnamed")
    if "1031" in history_notes.lower() or "sell" in history_notes.lower():
        return 18, "Follow up this week"
    if "not interested" in history_notes.lower() or "sold" in history_notes.lower():
        return 4, "Skip — not a lead"
    return 12, "Check in — potential interest"

def write_back(contact_id, score, action, today):
    update_data = {
        "investor_info": {
            "user_3": str(score),
            "user_4": action,
            "user_8": today
        }
    }
    requests.patch(
        f"https://api.realnex.com/api/investors/{contact_id}",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"}

