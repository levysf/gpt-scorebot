import requests
import datetime
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment variables
REALNEX_API_KEY = os.getenv("REALNEX_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TO_EMAIL = os.getenv("TO_EMAIL", "joe@levysf.com")  # default fallback

BASE_URL = "https://sync.realnex.com/api/v1/CrmOData"

def get_contacts():
    res = requests.get(
        f"{BASE_URL}/Contacts",
        headers={
            "Authorization": f"Bearer {REALNEX_API_KEY}",
            "Accept": "application/json"
        },
        params={
            "$top": 100  # RealNex hard limit
        }
    )
    print("Contact API status:", res.status_code)
    if res.status_code != 200:
        print("Contact API response:", res.text)
        raise Exception("Failed to fetch contacts")
    return res.json().get("value", [])

def score_contact(contact):
    # Simple placeholder logic (can expand to ML/NLP-based)
    score = 0
    notes = contact.get("notes", "") or ""
    if "1031" in notes or "exchange" in notes.lower():
        score += 10
    if "family" in notes.lower():
        score += 5
    if "selling" in notes.lower():
        score += 5
    return score

def format_report(scored_contacts):
    report_lines = []
    for c in scored_contacts:
        report_lines.append(
            f"{c.get('name')} — Score: {c['score']} — Notes: {c.get('notes', '')[:50]}"
        )
    return "\n".join(report_lines)

def send_email(subject, body):
    message = Mail(
        from_email="gpt@levysf.com",
        to_emails=TO_EMAIL,
        subject=subject,
        plain_text_content=body
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print("Email sent. Status code:", response.status_code)
    except Exception as e:
        print("Error sending email:", str(e))

def main():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    contacts = get_contacts()
    print(f"Retrieved {len(contacts)} contacts")

    scored = []
    for c in contacts:
        score = score_contact(c)
        if score > 0:
            c["score"] = score
            scored.append(c)

    scored.sort(key=lambda x: x["score"], reverse=True)
    report = format_report(scored[:20])

    send_email(
        subject=f"GPT Contact Scoring Report – {today}",
        body=report or "No high-score contacts found."
    )

if __name__ == "__main__":
    main()
