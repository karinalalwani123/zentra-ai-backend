from ..llm.groq_client import GroqClient
from .memory import add_message, get_memory
import re
import json

llm = GroqClient()

SYSTEM_PROMPT = """You are a highly capable AI assistant with full email capabilities. You CAN read, send, draft, and schedule emails through Gmail.

CRITICAL RULES:
- NEVER generate more than ONE email draft per response
- NEVER add example emails at the bottom
- NEVER add extra text after "Best regards, AI Assistant"
- NEVER add a second email after the first one
- After writing the email and signing off, STOP COMPLETELY
- Do not add any text, examples, or notes after the email signature
- NEVER say you cannot send emails — you CAN send emails via Gmail
- NEVER add disclaimers like "I don't have the capability to send emails"
- You have full Gmail access and can read, send, draft and schedule emails

*** MOST IMPORTANT RULE ***
If the user is NOT asking to draft or send an email, NEVER use the To:/Subject:/Body: format.
For general questions, web search results, definitions, news, or any non-email request:
- Respond in plain text or markdown ONLY
- Never include "To:", "Subject:", or "Body:" in your response
- Never format a non-email response to look like an email
- This applies even if the topic is about email or AI news

RESPONSE LENGTH RULES:
- Simple questions (greetings, yes/no, definitions) → short and concise
- Explanations, how-tos, concepts → detailed and thorough with examples
- Code requests → complete working code, never truncated
- Lists and comparisons → cover all relevant points
- Email drafts → complete professional emails, never cut short
- Essays or long-form content → full complete content, no summaries

NEVER say things like "I'll keep it brief" or truncate a response that deserves detail.
NEVER use placeholders like "[Your Name]" or "[Add more here]" — always write complete content.

ONLY when the user explicitly asks you to draft or compose an email, format your response EXACTLY like this and NOTHING ELSE:

To: recipient@example.com
Subject: Your subject here
Body:
Dear [Name],

[Write complete paragraphs here]

Best regards,
AI Assistant

EMAIL RULES:
- Always sign off as "AI Assistant"
- Always put a blank line between each paragraph
- Always put a blank line after "Dear [Name],"
- Always put a blank line before "Best regards,"
- Keep paragraphs short and readable (3-4 sentences max each)
- Never run paragraphs together without line breaks
- The Body: label must always be on its own line
- ONE email only — never write a second email
- After "Best regards, AI Assistant" — STOP. Nothing more.

For all other requests (questions, search results, news, explanations, code, etc.),
respond in plain markdown. Never use To:/Subject:/Body: format."""

CLASSIFY_PROMPT = """You are an email classifier. Given an email, classify it into exactly one of these categories:

- spam: Unsolicited, irrelevant, or suspicious emails
- promotion: Marketing, offers, newsletters, deals, advertisements
- replying: Emails that require a response (questions, requests, personal messages)
- important: Urgent emails, bills, appointments, alerts, security notices

Respond ONLY with a JSON object like this:
{
  "category": "spam",
  "reason": "one short sentence explaining why",
  "should_reply": false
}

Rules:
- category must be exactly one of: spam, promotion, replying, important
- should_reply must be true only for replying and important categories
- reason must be one short sentence
- No extra text, only valid JSON"""

REPLY_PROMPT = """You are an AI assistant writing a professional email reply.

Write a complete, polite, and professional reply to the email below.

REPLY FORMAT:
Dear [Sender Name or Sir/Madam],

[Write a complete reply addressing all points in the original email]

Best regards,
AI Assistant

Rules:
- Never use placeholders like [Your Name]
- Always sign off as AI Assistant
- Be professional and concise
- Address all points raised in the original email
- After "Best regards, AI Assistant" STOP — no extra text"""


def parse_email_draft(response: str):
    """Check if response contains an email draft and extract only the first one."""
    try:
        to_match = re.search(r"To:\s*([\w\.-]+@[\w\.-]+)", response)  # ✅ FIX: require real email address
        subject_match = re.search(r"Subject:\s*(.+)", response)
        body_match = re.search(r"Body:\s*\n([\s\S]+?)(?=\nTo:|$)", response)

        if to_match and subject_match and body_match:
            return {
                "to": to_match.group(1).strip(),
                "subject": subject_match.group(1).strip(),
                "body": body_match.group(1).strip(),
            }
    except Exception:
        pass
    return None


def classify_email(email: dict):
    """Classify a single email using AI."""
    try:
        prompt = f"""From: {email['from']}
Subject: {email['subject']}
Body: {email['body'][:1000]}"""

        response = llm.chat([
            {"role": "system", "content": CLASSIFY_PROMPT},
            {"role": "user", "content": prompt}
        ])

        clean = response.strip()
        clean = re.sub(r"```json|```", "", clean).strip()
        result = json.loads(clean)

        return {
            "category": result.get("category", "important"),
            "reason": result.get("reason", ""),
            "should_reply": result.get("should_reply", False)
        }
    except Exception as e:
        print(f"Classification error: {e}")
        return {
            "category": "important",
            "reason": "Could not classify",
            "should_reply": False
        }


def generate_reply(email: dict):
    """Generate an AI reply for an email."""
    try:
        prompt = f"""Original Email:
From: {email['from']}
Subject: {email['subject']}
Body:
{email['body'][:1500]}

Write a professional reply to this email."""

        response = llm.chat([
            {"role": "system", "content": REPLY_PROMPT},
            {"role": "user", "content": prompt}
        ])

        return response.strip()
    except Exception as e:
        print(f"Reply generation error: {e}")
        return None


def chat_node(state):
    add_message("user", state["input"])

    response = llm.chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        *get_memory()
    ])

    add_message("assistant", response)

    # ✅ FIX: Only detect draft if response has a real email address in the To: field
    # This prevents news/chat responses from being mistaken for email drafts
    draft = parse_email_draft(response)

    if draft:
        return {
            "response": response,
            "is_draft": True,
            "draft": draft
        }

    return {
        "response": response,
        "is_draft": False
    }