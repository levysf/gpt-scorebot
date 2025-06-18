import os
from datetime import datetime
import csv
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = "aiassistant@levysf.com"
TO_EMAIL = "joe@levysf.com"

def generate_csv():
    contacts = [
        ["Contact Name", "Note Summary", "GPT Score", "Next Action"],
        ["Valerie Astorian", "Interested in 1031 exchanges. Meeting set for next Wednesday.", "12", "Follow-up soon"],
        ["Paul and Jan Chafee", "Good meeting about potential 1031 exchange. Gross $17K/month.", "14", "Follow-up soon"],
        ["Tom Au", "Not ready to sell this year. Call back in October.", "5", "Monitor"]
    ]
    csv_path = "/tmp/gpt_scores.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(contacts)
    return csv_path

def send_email():
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject="GPT Score Report – Daily Lead Summary",
        html_content="<p>Attached is your daily GPT lead scoring report.</p>",
    )
    file_path = generate_csv()
    with open(file_path, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode()
        attachedFile = Attachment(
            FileContent(encoded),
            FileName("gpt_scores.csv"),
            FileType("text/csv"),
            Disposition("attachment")
        )
        message.attachment = attachedFile
    sg.send(message)

if __name__ == "__main__":
    send_email()
