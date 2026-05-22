import re

def route(query: str):
    q = query.lower()

    # If query contains an email address
    has_email_address = bool(re.search(r"[\w\.-]+@[\w\.-]+", query))

    # Cancel intent — check BEFORE everything
    cancel_words = ["cancel", "don't send", "do not send", "stop", "discard", "abort"]
    if any(word in q for word in cancel_words):
        return "cancel_email"

    # Auto reply intent
    auto_reply_words = [
        "auto reply", "autoreply", "reply to email", "reply to mail",
        "reply email", "generate reply", "draft reply", "write reply",
        "respond to email", "respond to mail", "auto respond"
    ]
    if any(word in q for word in auto_reply_words):
        return "auto_reply"

    # Explicit send intent
    send_words = [
        "send email", "send mail", "send it", "send this",
        "send now", "shoot it", "email it", "yes send", "go ahead"
    ]
    is_send = any(word in q for word in send_words)

    # Just "send" alone with no email address = send the pending draft
    if is_send and not has_email_address:
        return "send_email"

    # Draft intent — user wants AI to write an email first
    draft_words = [
        "draft", "compose", "write an email", "write a mail",
        "prepare an email", "send a mail to", "send an email to"
    ]
    is_draft = any(word in q for word in draft_words)

    # Draft+send in one shot
    if is_send and has_email_address and not is_draft:
        return "draft_and_send"

    # Read email intent
    if any(word in q for word in [
        "check email", "unread email", "inbox", "read email",
        "my emails", "read my mail", "read my mails",
        "show emails", "show mails", "get emails",
        "any emails", "any mails", "new emails", "new mails"
    ]):
        return "read_email"

    # ✅ FIX: Expanded web search intent
    if any(word in q for word in [
        "google it", "search the web", "look up online", "browse",
        "latest news", "current news", "today's news", "recent news",
        "what is happening", "news today", "headlines", "top news",
        "search for", "find out", "look up", "search",
        "latest", "recent", "current", "trending",
        "what happened", "today in", "breaking news",
        "2024", "2025", "2026"
    ]):
        return "web"

    # Everything else goes to chat
    return "chat"