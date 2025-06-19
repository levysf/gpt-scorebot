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
BASE_URL = "https://sync.realnex.com/api/v1/Crm"

# === UTILS ===
def get_contacts():
    res = requests.get(
        f"{BASE_URL}/contact",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"},
        params={"limit": 1000}
    )
    print(f"Contact API status: {res.status_code}")
    print(f"Contact API response: {res.text}")
    try:
        return res.json()
    except Exception as e:
        print(f"Error parsing contact JSON: {e}")
        raise

def get_notes(contact_key):
    res = requests.get(
        f"{BASE_URL}/contact/{contact_key}/notes",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"}
    )
    print(f"Notes API status: {res.status_code}")
    print(f"Notes API response: {res.text}")
    try:
        return res.json()
    except Exception as e:
        print(f"Error parsing notes JSON: {e}")
        raise

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
        f"{BASE_URL}/contact/{contact_key}/investor",
        headers={"Authorization": f"Bearer {REALNEX_API_KEY}"},
        json=update_data
    )
    print(f"Write-back status for {contact_key}: {res.status_code}")
    print(f"Write-back response: {res.text}")
    return res.status_code

def send_summary_email(leads):
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    content = "\n".join(leads)
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject="📈 Daily GPT Lead Scores",
        plain_text_content=content
    )
    print("Sending summary email...")
    response = sg.send(message)
    print(f"Email status: {response.status_code}")
    print(f"Email body: {response.body}")

# === MAIN SCRIPT ===
def main():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    try:
        contacts = get_contacts()
    except Exception as e:
        print(f"Fatal error getting contacts: {e}")
        return

    top_leads = []

    for contact in contacts:
        key = contact.get("contactKey")
        investor = contact.get("investor", {})
        if not key or investor.get("user_8"):
            continue

        try:
            notes = get_notes(key)
        except Exception as e:
            print(f"Skipping {key} due to notes error: {e}")
            continue

        notes_text = " ".join(n.get("notes", "") for n in notes)
        score, action = score_contact(contact, notes_text)

        if score < 10:
            continue

        try:
            write_back(key, score, action, today)
            top_leads.append(f"{contact.get('name')} — {score} — {action}")
        except Exception as e:
            print(f"Write-back failed for {key}: {e}")

    if top_leads:
        try:
            send_summary_email(top_leads)
        except Exception as e:
            print(f"Email sending failed: {e}")

if __name__ == "__main__":
    main()
