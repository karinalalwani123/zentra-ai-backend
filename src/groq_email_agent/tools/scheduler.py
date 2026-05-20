import threading
import time
from datetime import datetime
from .gmail_tools import send_email

scheduled_jobs = []

def schedule_email(to, subject, body, send_at: datetime):
    delay = (send_at - datetime.now()).total_seconds()

    if delay < 0:
        return {
            "status": "error",
            "error": "Scheduled time is in the past. Please pick a future date and time."
        }

    job = {
        "to": to,
        "subject": subject,
        "body": body,
        "send_at": send_at,
        "status": "pending"
    }

    scheduled_jobs.append(job)

    def send_later():
        time.sleep(delay)
        try:
            send_email(to, subject, body)
            job["status"] = "sent"
            print(f"Scheduled email sent to {to}")
        except Exception as e:
            job["status"] = "failed"
            print(f"Failed to send scheduled email: {e}")

    thread = threading.Thread(target=send_later, daemon=True)
    thread.start()

    return {"status": "scheduled", "send_at": send_at.isoformat()}


def get_scheduled_jobs():
    return [
        {
            "to": j["to"],
            "subject": j["subject"],
            "send_at": j["send_at"].isoformat(),
            "status": j["status"]
        }
        for j in scheduled_jobs
    ]