from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import threading
import time

from src.groq_email_agent.agent.chat_workflow import run_chat_workflow
from src.groq_email_agent.tools.gmail_tools import get_unread_emails
from src.groq_email_agent.tools.scheduler import schedule_email, get_scheduled_jobs, restore_pending_jobs

import base64
import requests
from email.mime.text import MIMEText

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    message: str
    user_id: str = "default"

class ScheduledEmail(BaseModel):
    to: str
    subject: str
    body: str
    send_at: str
    user_id: str = "default"

class OAuthEmail(BaseModel):
    access_token: str
    to: str
    subject: str
    body: str

# ===== KEEP ALIVE =====
@app.get("/ping")
def ping():
    """Health check endpoint for UptimeRobot"""
    return {"status": "ok", "message": "Backend is awake"}

# ===== CHAT ENDPOINTS =====
@app.post("/chat")
def chat(data: Query):
    result = run_chat_workflow(data.user_id, data.message)
    return result

@app.get("/emails")
def emails():
    return {"emails": get_unread_emails()}

@app.post("/send-email")
def send_mail(email: OAuthEmail):
    message = MIMEText(email.body)
    message["to"] = email.to
    message["subject"] = email.subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    res = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {email.access_token}"},
        json={"raw": raw},
    )

    if res.status_code != 200:
        return {"status": "error", "detail": res.json()}

    return {"status": "sent"}

@app.post("/schedule-email")
def schedule_mail(email: ScheduledEmail):
    send_at = datetime.fromisoformat(email.send_at)
    result = schedule_email(
        email.to,
        email.subject,
        email.body,
        send_at,
        email.user_id
    )
    return result

@app.get("/scheduled-emails")
def get_scheduled(user_id: str = "default"):
    return {"jobs": get_scheduled_jobs(user_id)}

# ===== STARTUP EVENT =====
@app.on_event("startup")
def startup_event():
    # Restore pending scheduled jobs
    try:
        restore_pending_jobs()
    except Exception as e:
        print(f"❌ Failed to restore scheduled jobs: {e}")

    # Keep alive thread
    def keep_alive():
        time.sleep(60)
        while True:
            time.sleep(600)
            try:
                requests.get("https://zentra-ai-backend-cexo.onrender.com/ping", timeout=5)
                print("✅ Keep-alive ping sent")
            except Exception as e:
                print(f"⚠️ Keep-alive ping failed: {e}")

    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    print("🔔 Keep-alive thread started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)