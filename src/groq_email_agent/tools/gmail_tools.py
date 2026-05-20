from .gmail_auth import get_gmail_service
import base64
import re
from email.mime.text import MIMEText


def get_email_body(payload):
    """Extract full body text from email payload."""
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    body += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif "parts" in part:
                # Nested parts
                for subpart in part["parts"]:
                    if subpart["mimeType"] == "text/plain":
                        data = subpart["body"].get("data", "")
                        if data:
                            body += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body.strip()


def get_unread_emails():
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"]
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages[:5]:
        data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = data.get("payload", {}).get("headers", [])

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")
        reply_to = next((h["value"] for h in headers if h["name"] == "Reply-To"), sender)
        snippet = data.get("snippet", "")

        # Extract full body
        body = get_email_body(data.get("payload", {}))

        # Extract sender email address
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", sender)
        sender_email = email_match.group(0) if email_match else sender

        emails.append({
            "id": msg["id"],
            "from": sender,
            "from_email": sender_email,
            "reply_to": reply_to,
            "subject": subject,
            "date": date,
            "snippet": snippet,
            "body": body[:2000] if body else snippet,  # limit to 2000 chars
        })

    return emails


def send_email(to, subject, body):
    service = get_gmail_service()

    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()


def reply_email(to, subject, body, thread_id=None):
    """Send a reply to an email."""
    service = get_gmail_service()

    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    message_body = {"raw": raw}
    if thread_id:
        message_body["threadId"] = thread_id

    service.users().messages().send(
        userId="me",
        body=message_body
    ).execute()