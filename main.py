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
BASE_URL = "https://sync.realnex.com/api/v1"

# === UTILS ===

def get_contacts():
    res = requests.get(
        f"{BASE_URL}/CrmOData/Contacts",
        headers={
            "Authorization": f"Bearer {REALNEX_API_KEY}",
            "Accept": "application/json"
        },
        params={
            "$top": 1000,
            "$orderby": "name"
        }
    )
    print("Contact API status:", res.status_code)
    if res.status_code != 200:
        print("Contact API response:", res.text)
        raise Exception("Failed to fetch contacts")
    return res.json().get("value", [])

def get_notes(contact_key):
    res = requests.get(
        f"{BASE_URL}/Crm/contact/{contact_key}/notes",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"}
    )
    if res.status_code != 200:
        print(f"Failed to fetch notes for {contact_key}: {res.status_code}")
        return []
    return res.json()

def score_contact(contact, notes_text):
    if "1031" in notes_text.lower() or "sell" in notes_text.lower():
        return 18, "Follow up this week"
    if "not interested" in notes_text.lower() or "sold" in notes_text.lower():
        return 4, "Skip — not a lead"
    return 12, "Check in — potential interest"

def write_back(contact_key, score, action, today):
    update_data = {
        "user_3": str(score),
        "user_4": action,
        "user_8": today
    }
    res = requests.put(
        f"{BASE_URL}/Crm/contact/{contact_key}/investor",
        headers={
            "Authorization": f"Bearer {REALNEX_API_KEY}",
            "Content-Type": "application/json"
        },
        json=update_data
    )
    print(f"Write-back for {contact_key}: {res.status_code}")
    return res.status_code

# === MAIN SCRIPT ===

def main():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    contacts = get_contacts()
    top_leads = []

    for contact in contacts:
        key = contact.get("key") or contact.get("contactKey")
        investor = contact.get("investor", {})
        if not key or investor.get("user_8"):  # Skip if already scored
            continue

        notes = get_notes(key)
        notes_text = " ".join(n.get("notes", "") for n in notes)

        score, action = score_contact(contact, notes_text)
        if score < 10:
            continue

        write_back(key, score, action, today)
        top_leads.append(f"{contact.get('name')} — {score} — {action}")

    if top_leads:
        send_summary_email(top_leads)

def send_summary_email(leads):
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    content = "\n".join(leads)
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject="📈 Daily GPT Lead Scores",
        plain_text_content=content
    )
    sg.send(message)

if __name__ == "__main__":
    main()
