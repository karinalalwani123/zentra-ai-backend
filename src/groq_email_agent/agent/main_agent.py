import re
from .router import route
from .chat import chat_node, classify_email, generate_reply
from .memory import clear_memory
from ..tools.web_search import search_web
from ..tools.gmail_tools import send_email, get_unread_emails, reply_email

# Store pending email across turns (in-memory, per session)
pending_email = {}

# Store fetched emails for auto-reply reference
cached_emails = []


def extract_email_address(text: str):
    match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    return match.group(0).strip() if match else None


def extract_email_details(response_text: str, query: str = ""):
    # --- Strict format ---
    to_match = re.search(r"To:\s*([\w\.-]+@[\w\.-]+)", response_text)
    subject_match = re.search(r"Subject:\s*(.+)", response_text)
    body_match = re.search(r"Body:\s*(.+)", response_text, re.DOTALL)

    if to_match and subject_match and body_match:
        return {
            "to": to_match.group(1).strip(),
            "subject": subject_match.group(1).strip(),
            "body": body_match.group(1).strip(),
        }

    # --- Fallback: To + Subject found but no Body label ---
    if to_match and subject_match:
        subject = subject_match.group(1).strip()
        to = to_match.group(1).strip()
        body_fallback = re.search(r"(Dear .+?)(?:To:|Please note|$)", response_text, re.DOTALL)
        body = body_fallback.group(1).strip() if body_fallback else response_text.strip()
        return {"to": to, "subject": subject, "body": body}

    # --- Fallback: get email from original query ---
    query_email = extract_email_address(query)
    if query_email and subject_match:
        body_fallback = re.search(r"(Dear .+?)(?:Please note|$)", response_text, re.DOTALL)
        body = body_fallback.group(1).strip() if body_fallback else response_text.strip()
        return {
            "to": query_email,
            "subject": subject_match.group(1).strip(),
            "body": body,
        }

    # --- Last resort ---
    if query_email:
        subject_guess = re.search(r"about (.+?)(?:\.|$)", query, re.IGNORECASE)
        subject = subject_guess.group(1).strip() if subject_guess else "No Subject"
        return {
            "to": query_email,
            "subject": subject,
            "body": response_text.strip(),
        }

    return None


def run_system(query: str):
    global pending_email, cached_emails

    mode = route(query)
    print(f"🔍 Mode: {mode} | Query: {query}")

    # --- SEND PENDING DRAFT ---
    if mode == "send_email":
        if pending_email:
            try:
                send_email(
                    pending_email["to"],
                    pending_email["subject"],
                    pending_email["body"],
                )
                sent_to = pending_email["to"]
                pending_email = {}
                clear_memory()
                return {"response": f"✅ Email sent successfully to {sent_to}."}
            except Exception as e:
                return {"response": f"❌ Failed to send email: {str(e)}"}
        else:
            return {"response": "No email draft found. Please say something like 'draft an email to x@gmail.com about topic'."}

    # --- CANCEL PENDING DRAFT ---
    elif mode == "cancel_email":
        if pending_email:
            pending_email = {}
            clear_memory()
            return {"response": "❌ Email draft cancelled."}
        else:
            return {"response": "No pending email draft to cancel."}

    # --- READ EMAIL with classification ---
    elif mode == "read_email":
        emails = get_unread_emails()

        if not emails:
            return {"response": "📭 You have no unread emails.", "emails": []}

        classified = []
        for email in emails:
            classification = classify_email(email)
            classified.append({
                **email,
                "category": classification["category"],
                "reason": classification["reason"],
                "should_reply": classification["should_reply"],
            })

        cached_emails = classified

        return {
            "response": f"📬 You have {len(classified)} unread emails. Here's what I found:",
            "emails": classified,
            "is_email_list": True
        }

    # --- AUTO REPLY ---
    elif mode == "auto_reply":
        index_match = re.search(r"\d+", query)
        index = int(index_match.group(0)) - 1 if index_match else 0

        if not cached_emails:
            return {"response": "Please read your emails first by saying 'read email'."}

        if index >= len(cached_emails):
            return {"response": f"Email {index + 1} not found. You have {len(cached_emails)} emails."}

        email = cached_emails[index]

        reply_text = generate_reply(email)
        if not reply_text:
            return {"response": "❌ Could not generate a reply. Please try again."}

        pending_email = {
            "to": email["from_email"],
            "subject": f"Re: {email['subject']}",
            "body": reply_text,
            "thread_id": email.get("id")
        }

        draft_display = f"To: {pending_email['to']}\nSubject: {pending_email['subject']}\nBody:\n{reply_text}"

        return {
            "response": draft_display,
            "is_draft": True,
            "draft": pending_email
        }

    # --- WEB SEARCH ---
    elif mode == "web":
        results = search_web(query)
        top = results.get("results", [])[:3]
        context = "\n\n".join([f"{r['title']}:\n{r['content']}" for r in top])
        return chat_node({
            "input": f"Answer this question: {query}\n\nUse this context:\n{context}"
        })

    # --- CHAT ---
    else:
        result = chat_node({"input": query})
    response_text = result.get("response", "")

    # ✅ FIX: Only treat as draft if BOTH conditions are met:
    # 1. Response contains a real email address
    # 2. The user's query actually requested an email action
    EMAIL_INTENT_KEYWORDS = [
        "draft", "compose", "write an email", "send an email",
        "email to", "mail to", "prepare an email"
    ]

    user_wants_email = any(kw in query.lower() for kw in EMAIL_INTENT_KEYWORDS)
    has_email_address = bool(re.search(r"[\w\.-]+@[\w\.-]+", response_text))

    if user_wants_email and has_email_address:
        details = extract_email_details(response_text, query)
        if details:
            pending_email = details
            print(f"📧 Pending email saved: {pending_email['to']} | {pending_email['subject']}")
            return {
                "response": response_text,
                "is_draft": True,
                "draft": details
            }

    return {"response": response_text, "is_draft": False}