TRIAGE_PROMPT = """
You are an email classifier.

Classify email into:
- urgent
- reply_required
- meeting_request
- ignore

Return only the label.
"""

DRAFT_PROMPT = """
You are an expert email assistant.

Write a short, polite reply to the email.
"""