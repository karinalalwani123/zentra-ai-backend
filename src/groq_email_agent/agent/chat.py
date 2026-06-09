from ..llm.groq_client import GroqClient
from .memory import add_message, get_memory
import re
import json

llm = GroqClient()

SYSTEM_PROMPT = """You are a highly capable AI assistant called ZENTRA AI with full email capabilities. You CAN read, send, draft, and schedule emails through Gmail.

CRITICAL RULES:
- NEVER generate more than ONE email draft per response
- NEVER add example emails at the bottom
- NEVER add extra text after "Best regards, ZENTRA AI"
- NEVER add a second email after the first one
- After writing the email and signing off, STOP COMPLETELY
- Do not add any text, examples, or notes after the email signature
- NEVER say you cannot send emails — you CAN send emails via Gmail
- NEVER add disclaimers like "I don't have the capability to send emails"
- You have full Gmail access and can read, send, draft and schedule emails

*** MOST IMPORTANT RULE ***
ONLY generate an email draft when user EXPLICITLY says:
- "draft an email"
- "compose an email"
- "write an email to"
- "send an email to"
- "prepare an email"

NEVER use To:/Subject:/Body: format for:
- General questions ("teach me french", "explain python")
- Learning requests ("how to cook", "teach me math")
- News or search results
- Recipes or instructions
- Any non-email request
- Even if the topic mentions email or communication

For ALL non-email requests:
- Respond in plain text or markdown ONLY
- Never include "To:", "Subject:", or "Body:" in your response
- Never format a non-email response to look like an email

RESPONSE LENGTH RULES:
- Simple questions (greetings, yes/no, definitions) → short and concise
- Explanations, how-tos, concepts → detailed and thorough with examples
- Code requests → complete working code, never truncated
- Lists and comparisons → cover all relevant points
- Email drafts → complete professional emails, never cut short
- Essays or long-form content → full complete content, no summaries
- Recipes → include ALL ingredients with measurements and numbered steps
- Language learning → include examples, pronunciation, and exercises

NEVER say things like "I'll keep it brief" or truncate a response that deserves detail.
NEVER use placeholders like "[Your Name]" or "[Add more here]" — always write complete content.

ONLY when the user explicitly asks to draft or compose an email, format your response EXACTLY like this and NOTHING ELSE:

To: recipient@example.com
Subject: Your subject here
Body:
Dear [Name],

[Write complete paragraphs here]

Best regards,
ZENTRA AI

EMAIL RULES:
- Always sign off as "ZENTRA AI"
- Always put a blank line between each paragraph
- Always put a blank line after "Dear [Name],"
- Always put a blank line before "Best regards,"
- Keep paragraphs short and readable (3-4 sentences max each)
- Never run paragraphs together without line breaks
- The Body: label must always be on its own line
- ONE email only — never write a second email
- After "Best regards, ZENTRA AI" — STOP. Nothing more.

For all other requests (questions, search results, news, explanations, recipes, language learning, code, etc.),
respond in plain markdown. NEVER use To:/Subject:/Body: format."""

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
ZENTRA AI

Rules:
- Never use placeholders like [Your Name]
- Always sign off as ZENTRA AI
- Be professional and concise
- Address all points raised in the original email
- After "Best regards, ZENTRA AI" STOP — no extra text"""


def parse_email_draft(response: str):
    """Check if response contains an email draft and extract only the first one."""
    try:
        # Only detect draft if response has a real email address in To: field
        to_match = re.search(r"To:\s*([\w\.-]+@[\w\.-]+)", response)
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


def truncate_to_first_email(response: str) -> str:
    """Keep only the first email draft if multiple exist."""
    first_to = response.find("To:")
    if first_to == -1:
        return response
    second_to = response.find("\nTo:", first_to + 1)
    if second_to != -1:
        return response[:second_to].strip()
    return response


def chat_node(state):
    user_id = state.get("user_id", "default")

    # DON'T add user message — add_to_memory_node already did it
    # add_message("user", state["input"], user_id)  ← REMOVED

    response = llm.chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        *get_memory(user_id)
    ])

    # Only save assistant response
    add_message("assistant", response, user_id)

    response = truncate_to_first_email(response)
    draft = parse_email_draft(response)

    if draft:
        return {"response": response, "is_draft": True, "draft": draft}

    return {"response": response, "is_draft": False}
