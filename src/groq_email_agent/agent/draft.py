from ..prompts import DRAFT_PROMPT

def draft_node(state, llm):
    email_text = f"""
Subject: {state.subject}
From: {state.sender}
Body: {state.body}
"""

    draft = llm.chat([
        {"role": "system", "content": DRAFT_PROMPT},
        {"role": "user", "content": email_text}
    ])

    state.draft = draft
    return state