from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from .chat import chat_node, classify_email, generate_reply
from .memory import add_message, get_memory, clear_memory
from .router import route
from ..tools.gmail_tools import send_email, get_unread_emails
from ..tools.web_search import search_web
import re
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# ===== FIRESTORE INIT =====
try:
    if not firebase_admin._apps:
        cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firestore connected successfully")
except Exception as e:
    print(f"❌ Firestore connection failed: {e}")
    db = None

# ===== FIRESTORE HELPERS =====
def get_pending_email(user_id: str) -> dict:
    if not db:
        return {}
    try:
        doc = db.collection("pending_emails").document(user_id).get()
        return doc.to_dict() if doc.exists else {}
    except Exception as e:
        print(f"❌ get_pending_email error: {e}")
        return {}

def set_pending_email(user_id: str, draft: dict):
    if not db:
        return
    try:
        db.collection("pending_emails").document(user_id).set(draft)
    except Exception as e:
        print(f"❌ set_pending_email error: {e}")

def delete_pending_email(user_id: str):
    if not db:
        return
    try:
        db.collection("pending_emails").document(user_id).delete()
    except Exception as e:
        print(f"❌ delete_pending_email error: {e}")

def get_cached_emails(user_id: str) -> list:
    if not db:
        return []
    try:
        doc = db.collection("cached_emails").document(user_id).get()
        return doc.to_dict().get("emails", []) if doc.exists else []
    except Exception as e:
        print(f"❌ get_cached_emails error: {e}")
        return []

def set_cached_emails(user_id: str, emails: list):
    if not db:
        return
    try:
        db.collection("cached_emails").document(user_id).set({"emails": emails})
    except Exception as e:
        print(f"❌ set_cached_emails error: {e}")


class ChatState(TypedDict):
    user_id: str
    message: str
    mode: str
    response: str
    is_draft: bool
    draft: Optional[dict]
    is_email_list: bool
    emails: list
    pending_email: dict
    cached_emails: list
    memory: list

# ===== NODE 1: RESTORE STATE =====
def restore_state_node(state: ChatState) -> ChatState:
    """Restore state from Firestore"""
    state["pending_email"] = get_pending_email(state["user_id"])
    state["cached_emails"] = get_cached_emails(state["user_id"])
    state["memory"] = get_memory(state["user_id"])
    print(f"🔄 State restored for {state['user_id']}")
    return state

# ===== NODE 2: ROUTER =====
def router_node(state: ChatState) -> ChatState:
    """Detect user intent"""
    state["mode"] = route(state["message"])
    print(f"🔍 Mode: {state['mode']} | User: {state['user_id']}")
    return state

# ===== NODE 3: ADD MEMORY =====
def add_to_memory_node(state: ChatState) -> ChatState:
    """Add user message to per-user memory"""
    if state["mode"] not in ["cancel_email"]:
        add_message("user", state["message"], state["user_id"])
    state["memory"] = get_memory(state["user_id"])
    return state

# ===== NODE 4: CHAT =====
def chat_node_handler(state: ChatState) -> ChatState:
    """Handle chat mode using Groq LLM"""
    if state["mode"] in ["chat", "draft_and_send"]:
        response = chat_node({
            "input": state["message"],
            "user_id": state["user_id"]
        })
        state["response"] = response.get("response", "")
        state["is_draft"] = response.get("is_draft", False)
        state["draft"] = response.get("draft", None)

        if state["is_draft"] and state["draft"]:
            state["pending_email"] = state["draft"]
            set_pending_email(state["user_id"], state["draft"])
            print(f"📧 Draft saved to Firestore for {state['user_id']}")

    return state

# ===== NODE 5: READ EMAIL =====
def read_email_node_handler(state: ChatState) -> ChatState:
    """Read and classify emails from Gmail"""
    if state["mode"] == "read_email":
        emails = get_unread_emails()

        if not emails:
            state["response"] = "📭 You have no unread emails."
            state["emails"] = []
            state["is_email_list"] = False
            return state

        classified = []
        for email in emails:
            classification = classify_email(email)
            classified.append({
                **email,
                "category": classification["category"],
                "reason": classification["reason"],
                "should_reply": classification["should_reply"],
            })

        state["cached_emails"] = classified
        set_cached_emails(state["user_id"], classified)
        state["is_email_list"] = True
        state["emails"] = classified
        state["response"] = f"📬 You have {len(classified)} unread emails. Here's what I found:"

    return state

# ===== NODE 6: AUTO REPLY =====
def auto_reply_node_handler(state: ChatState) -> ChatState:
    """Generate professional reply to selected email"""
    if state["mode"] == "auto_reply":
        index_match = re.search(r"\d+", state["message"])
        index = int(index_match.group(0)) - 1 if index_match else 0

        cached = get_cached_emails(state["user_id"])
        state["cached_emails"] = cached

        if not cached:
            state["response"] = "Please read your emails first by saying 'read email'."
            return state

        if index >= len(cached):
            state["response"] = f"Email {index + 1} not found. You have {len(cached)} emails."
            return state

        email = cached[index]
        reply_text = generate_reply(email)

        if not reply_text:
            state["response"] = "❌ Could not generate reply. Please try again."
            return state

        draft = {
            "to": email["from_email"],
            "subject": f"Re: {email['subject']}",
            "body": reply_text,
            "thread_id": email.get("id")
        }
        state["pending_email"] = draft
        set_pending_email(state["user_id"], draft)

        state["response"] = f"To: {draft['to']}\nSubject: {draft['subject']}\nBody:\n{reply_text}"
        state["is_draft"] = True
        state["draft"] = draft

    return state

# ===== NODE 7: SEND EMAIL =====
def send_email_node_handler(state: ChatState) -> ChatState:
    """Send pending email via Gmail API"""
    if state["mode"] == "send_email":
        pending = get_pending_email(state["user_id"])
        state["pending_email"] = pending

        if pending and "to" in pending and "subject" in pending and "body" in pending:
            try:
                send_email(
                    pending["to"],
                    pending["subject"],
                    pending["body"],
                )
                state["response"] = f"✅ Email sent successfully to {pending['to']}."
                delete_pending_email(state["user_id"])
            except Exception as e:
                state["response"] = f"❌ Failed to send email: {str(e)}"
        else:
            state["response"] = "❌ No email draft found. Please draft an email first."

    return state

# ===== NODE 8: CANCEL EMAIL =====
def cancel_email_node_handler(state: ChatState) -> ChatState:
    """Cancel pending draft"""
    if state["mode"] == "cancel_email":
        pending = get_pending_email(state["user_id"])
        if pending:
            delete_pending_email(state["user_id"])
            state["response"] = "❌ Email draft cancelled."
        else:
            state["response"] = "No pending email draft to cancel."

    return state

# ===== NODE 9: WEB SEARCH =====
def web_search_node_handler(state: ChatState) -> ChatState:
    """Search web using Tavily and answer question"""
    if state["mode"] == "web":
        from datetime import date
        today = date.today().strftime("%d %B %Y")

        search_query = f"{state['message']} {today}"
        results = search_web(search_query)

        direct_answer = results.get("answer", "")
        top = results.get("results", [])[:3]

        context = "\n\n".join([
            f"Source: {r['title']}\n"
            f"Content: {r['content'][:500]}"
            for r in top
        ])

        full_context = ""
        if direct_answer:
            full_context += f"Direct Answer: {direct_answer}\n\n"
        full_context += context

        response = chat_node({
            "input": f"""Answer: {state['message']}
Date: {today}

Results:
{full_context}

STRICT RULES:
- Use only results above
- Never use training data
- Show prices exactly as found
- Do NOT add disclaimers
- End with: Source: [name] | Date: {today}""",
            "user_id": state["user_id"]
        })
        state["response"] = response.get("response", "")

    return state

# ===== NODE 10: VALIDATE DRAFT =====
def validate_draft_node(state: ChatState) -> ChatState:
    """Validate draft has required fields"""
    if state["is_draft"] and state["draft"]:
        required = ["to", "subject", "body"]
        if all(field in state["draft"] for field in required):
            state["pending_email"] = state["draft"]
            set_pending_email(state["user_id"], state["draft"])
            print(f"✅ Draft validated for {state['user_id']}")
        else:
            state["response"] = "❌ Draft missing required fields."
            state["is_draft"] = False
    return state

# ===== NODE 11: VALIDATE EMAIL =====
def validate_email_address_node(state: ChatState) -> ChatState:
    """Validate email address format"""
    email_to_check = None

    if state["pending_email"] and "to" in state["pending_email"]:
        email_to_check = state["pending_email"]["to"]
    elif state["draft"] and "to" in state["draft"]:
        email_to_check = state["draft"]["to"]

    if email_to_check:
        if not re.match(r"[\w\.-]+@[\w\.-]+\.\w+", email_to_check):
            state["response"] = f"❌ Invalid email address: {email_to_check}"
            state["pending_email"] = {}
            state["draft"] = None
        else:
            if state["draft"] and not state["pending_email"]:
                state["pending_email"] = state["draft"]
            print(f"✅ Email validated: {email_to_check}")

    return state

# ===== NODE 12: UPDATE MEMORY =====
def update_memory_with_response_node(state: ChatState) -> ChatState:
    """Add assistant response to per-user memory"""
    if state["response"]:
        add_message("assistant", state["response"], state["user_id"])
    state["memory"] = get_memory(state["user_id"])
    return state

# ===== NODE 13: CLEAR MEMORY =====
def clear_memory_node(state: ChatState) -> ChatState:
    """Clear per-user memory after sending email"""
    if state["mode"] == "send_email":
        clear_memory(state["user_id"])
        print(f"🧹 Memory cleared for {state['user_id']}")
    return state

# ===== NODE 14: ERROR HANDLER =====
def error_handler_node(state: ChatState) -> ChatState:
    """Handle any errors in workflow"""
    if not state.get("response"):
        state["response"] = "An error occurred. Please try again."
        print(f"⚠️ Error handler triggered for {state['user_id']}")
    return state

# ===== ROUTING LOGIC =====
def route_to_handler(state: ChatState) -> str:
    return state["mode"]

# ===== BUILD GRAPH =====
def build_chat_graph():
    graph = StateGraph(ChatState)

    # Add all 14 nodes
    graph.add_node("restore_state", restore_state_node)           # 1
    graph.add_node("router", router_node)                         # 2
    graph.add_node("add_memory", add_to_memory_node)              # 3
    graph.add_node("chat", chat_node_handler)                     # 4
    graph.add_node("read_email", read_email_node_handler)         # 5
    graph.add_node("auto_reply", auto_reply_node_handler)         # 6
    graph.add_node("send_email", send_email_node_handler)         # 7
    graph.add_node("cancel_email", cancel_email_node_handler)     # 8
    graph.add_node("web_search", web_search_node_handler)         # 9
    graph.add_node("validate_draft", validate_draft_node)         # 10
    graph.add_node("validate_email", validate_email_address_node) # 11
    graph.add_node("update_memory", update_memory_with_response_node) # 12
    graph.add_node("clear_memory", clear_memory_node)             # 13
    graph.add_node("error_handler", error_handler_node)           # 14

    # Set entry point
    graph.set_entry_point("restore_state")

    # restore_state → router
    graph.add_edge("restore_state", "router")

    # router → add_memory
    graph.add_edge("router", "add_memory")

    # add_memory → conditional routing
    graph.add_conditional_edges(
        "add_memory",
        route_to_handler,
        {
            "chat": "chat",
            "draft_and_send": "chat",
            "read_email": "read_email",
            "auto_reply": "auto_reply",
            "send_email": "validate_email",
            "cancel_email": "cancel_email",
            "web": "web_search",
        }
    )

    # chat → validate_draft → validate_email → update_memory
    graph.add_edge("chat", "validate_draft")
    graph.add_edge("validate_draft", "validate_email")
    graph.add_edge("validate_email", "update_memory")

    # Other handlers → update_memory
    for node in ["read_email", "auto_reply", "web_search", "cancel_email"]:
        graph.add_edge(node, "update_memory")

    # send_email → clear_memory → update_memory
    graph.add_edge("send_email", "clear_memory")
    graph.add_edge("clear_memory", "update_memory")

    # update_memory → error_handler → END
    graph.add_edge("update_memory", "error_handler")
    graph.add_edge("error_handler", END)

    return graph.compile()

# ===== MAIN WORKFLOW FUNCTION =====
def run_chat_workflow(user_id: str, message: str):
    try:
        graph = build_chat_graph()

        state = {
            "user_id": user_id,
            "message": message,
            "mode": None,
            "response": "",
            "is_draft": False,
            "draft": None,
            "is_email_list": False,
            "emails": [],
            "pending_email": {},
            "cached_emails": [],
            "memory": [],
        }

        result = graph.invoke(state)

        return {
            "response": result["response"],
            "is_draft": result["is_draft"],
            "draft": result["draft"],
            "is_email_list": result["is_email_list"],
            "emails": result["emails"],
        }
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"Error: {str(e)}",
            "is_draft": False,
            "draft": None,
            "is_email_list": False,
            "emails": [],
        }