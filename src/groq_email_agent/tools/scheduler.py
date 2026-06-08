import threading
import time
from datetime import datetime
from .gmail_tools import send_email
import firebase_admin
from firebase_admin import firestore
import os

# Get Firestore client
def get_db():
    try:
        return firestore.client()
    except Exception as e:
        print(f"❌ Firestore client error: {e}")
        return None

def schedule_email(to: str, subject: str, body: str, send_at: datetime, user_id: str = "default"):
    delay = (send_at - datetime.now()).total_seconds()

    if delay < 0:
        return {
            "status": "error",
            "error": "Scheduled time is in the past. Please pick a future date and time."
        }

    # Save job to Firestore
    db = get_db()
    job_ref = None
    
    if db:
        try:
            job_ref = db.collection("scheduled_emails").document()
            job_data = {
                "id": job_ref.id,
                "to": to,
                "subject": subject,
                "body": body,
                "send_at": send_at.isoformat(),
                "status": "pending",
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            job_ref.set(job_data)
            print(f"✅ Job saved to Firestore: {job_ref.id}")
        except Exception as e:
            print(f"❌ Failed to save job to Firestore: {e}")

    # Start background thread
    def send_later():
        time.sleep(delay)
        try:
            send_email(to, subject, body)
            print(f"✅ Scheduled email sent to {to}")
            if job_ref:
                try:
                    job_ref.update({"status": "sent"})
                except Exception as e:
                    print(f"❌ Failed to update job status: {e}")
        except Exception as e:
            print(f"❌ Failed to send scheduled email: {e}")
            if job_ref:
                try:
                    job_ref.update({"status": "failed", "error": str(e)})
                except Exception as e2:
                    print(f"❌ Failed to update job status: {e2}")

    thread = threading.Thread(target=send_later, daemon=True)
    thread.start()

    return {
        "status": "scheduled",
        "send_at": send_at.isoformat(),
        "job_id": job_ref.id if job_ref else None
    }


def get_scheduled_jobs(user_id: str = "default"):
    """Get all scheduled jobs for a user from Firestore"""
    db = get_db()
    if not db:
        return []
    try:
        docs = db.collection("scheduled_emails")\
            .where("user_id", "==", user_id)\
            .stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"❌ get_scheduled_jobs error: {e}")
        return []


def restore_pending_jobs():
    """Restore pending jobs on server startup"""
    db = get_db()
    if not db:
        print("❌ Cannot restore jobs — Firestore not available")
        return

    try:
        docs = list(db.collection("scheduled_emails")\
            .where("status", "==", "pending")\
            .stream())

        if not docs:
            print("✅ No pending scheduled jobs to restore")
            return

        restored = 0
        for doc in docs:
            job = doc.to_dict()
            try:
                send_at = datetime.fromisoformat(job["send_at"])
                delay = (send_at - datetime.now()).total_seconds()

                if delay <= 0:
                    # Job missed — mark as failed
                    doc.reference.update({
                        "status": "failed",
                        "error": "Server was down when email was scheduled to send"
                    })
                    print(f"❌ Missed job for {job['to']} — marked as failed")
                    continue

                # Restart thread for pending job
                def send_later(j=job, d=doc.reference):
                    time.sleep(delay)
                    try:
                        send_email(j["to"], j["subject"], j["body"])
                        d.update({"status": "sent"})
                        print(f"✅ Restored job sent to {j['to']}")
                    except Exception as e:
                        d.update({"status": "failed", "error": str(e)})
                        print(f"❌ Restored job failed: {e}")

                thread = threading.Thread(target=send_later, daemon=True)
                thread.start()
                restored += 1
                print(f"🔄 Restored job for {job['to']} — sends in {int(delay)}s")

            except Exception as e:
                print(f"❌ Error restoring job: {e}")

        print(f"✅ Restored {restored} pending scheduled jobs")

    except Exception as e:
        print(f"❌ restore_pending_jobs error: {e}")