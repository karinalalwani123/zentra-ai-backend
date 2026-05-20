from ..prompts import TRIAGE_PROMPT

def triage_node(state, llm):
    email_text = f"""
Subject: {state.subject}
From: {state.sender}
Body: {state.body}
"""

    result = llm.chat([
        {"role": "system", "content": TRIAGE_PROMPT},
        {"role": "user", "content": email_text}
    ])

    state.triage = result.strip()
    return state