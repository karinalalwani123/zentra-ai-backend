import threading
import time
from datetime import datetime
from .gmail_tools import send_email
from firebase_admin import firestore

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
            "error": "Scheduled time is in the past."
        }

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
            print(f"❌ Failed to save job: {e}")

    def send_later():
        print(f"⏰ Thread sleeping {delay:.0f}s for {to}")
        time.sleep(delay)
        print(f"⏰ Thread woke up — sending to {to}")

        if job_ref:
            try:
                current = job_ref.get()
                if not current.exists:
                    print(f"⚠️ Job missing — skipping")
                    return
                if current.to_dict().get("status") != "pending":
                    print(f"⚠️ Job already processed — skipping")
                    return
                # Claim job atomically
                job_ref.update({"status": "sending"})
            except Exception as e:
                print(f"❌ Status check failed: {e}")
                return

        try:
            send_email(to, subject, body)
            print(f"✅ Scheduled email sent to {to}")
            if job_ref:
                job_ref.update({"status": "sent"})
        except Exception as e:
            print(f"❌ Failed: {e}")
            if job_ref:
                job_ref.update({"status": "failed", "error": str(e)})

    thread = threading.Thread(target=send_later, daemon=True)
    thread.start()

    return {
        "status": "scheduled",
        "send_at": send_at.isoformat(),
        "job_id": job_ref.id if job_ref else None
    }


def get_scheduled_jobs(user_id: str = "default"):
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
    db = get_db()
    if not db:
        return

    try:
        # Step 1 — Reset thread_active jobs back to pending
        active_docs = list(db.collection("scheduled_emails")
            .where("status", "==", "thread_active")
            .stream())

        for doc in active_docs:
            doc.reference.update({"status": "pending"})
            print(f"🔄 Reset thread_active job back to pending")

        # Wait for Firestore to update
        if active_docs:
            time.sleep(1)

        # Step 2 — Get all pending jobs
        docs = list(db.collection("scheduled_emails")
            .where("status", "==", "pending")
            .stream())

        if not docs:
            print("✅ No pending jobs to restore")
            return

        restored = 0
        for doc in docs:
            try:
                # Re-fetch fresh status
                fresh = doc.reference.get()
                if not fresh.exists:
                    continue
                job = fresh.to_dict()
                if job.get("status") != "pending":
                    continue

                send_at = datetime.fromisoformat(job["send_at"])
                delay = (send_at - datetime.now()).total_seconds()

                if delay <= 0:
                    # Overdue — claim and send immediately
                    doc.reference.update({"status": "sending"})
                    print(f"⚡ Overdue job — sending immediately to {job['to']}")
                    try:
                        send_email(job["to"], job["subject"], job["body"])
                        doc.reference.update({"status": "sent"})
                        print(f"✅ Overdue job sent to {job['to']}")
                    except Exception as e:
                        doc.reference.update({"status": "failed", "error": str(e)})
                        print(f"❌ Overdue job failed: {e}")
                else:
                    # Future job — claim as thread_active
                    doc.reference.update({"status": "thread_active"})

                    def send_later(j=job, d=doc.reference, dl=delay):
                        print(f"⏰ Restored thread sleeping {dl:.0f}s for {j['to']}")
                        time.sleep(dl)
                        try:
                            current = d.get()
                            if not current.exists or current.to_dict().get("status") != "thread_active":
                                print(f"⚠️ Job state changed — skipping")
                                return
                            d.update({"status": "sending"})
                            send_email(j["to"], j["subject"], j["body"])
                            d.update({"status": "sent"})
                            print(f"✅ Restored job sent to {j['to']}")
                        except Exception as e:
                            d.update({"status": "failed", "error": str(e)})
                            print(f"❌ Restored job failed: {e}")

                    thread = threading.Thread(target=send_later, daemon=True)
                    thread.start()
                    restored += 1
                    print(f"🔄 Restored job for {job['to']} in {int(delay)}s")

            except Exception as e:
                print(f"❌ Error processing job: {e}")

        print(f"✅ Restored {restored} pending jobs")

    except Exception as e:
        print(f"❌ restore_pending_jobs error: {e}")