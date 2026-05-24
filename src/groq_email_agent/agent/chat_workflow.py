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
if not firebase_admin._apps:
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ===== FIRESTORE HELPERS =====
def get_pending_email(user_id: str) -> dict:
    doc = db.collection("pending_emails").document(user_id).get()
    return doc.to_dict() if doc.exists else {}

def set_pending_email(user_id: str, draft: dict):
    db.collection("pending_emails").document(user_id).set(draft)

def delete_pending_email(user_id: str):
    db.collection("pending_emails").document(user_id).delete()

def get_cached_emails(user_id: str) -> list:
    doc = db.collection("cached_emails").document(user_id).get()
    return doc.to_dict().get("emails", []) if doc.exists else []

def set_cached_emails(user_id: str, emails: list):
    db.collection("cached_emails").document(user_id).set({"emails": emails})


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

# ===== ROUTER NODE =====
def router_node(state: ChatState) -> ChatState:
    state["mode"] = route(state["message"])
    print(f"🔍 Mode: {state['mode']}")
    return state

# ===== MEMORY MANAGEMENT NODES =====
def add_to_memory_node(state: ChatState) -> ChatState:
    if state["mode"] not in ["cancel_email"]:
        add_message("user", state["message"])
    return state

def update_memory_with_response_node(state: ChatState) -> ChatState:
    if state["response"]:
        add_message("assistant", state["response"])
    return state

# ===== CHAT NODE =====
def chat_node_handler(state: ChatState) -> ChatState:
    if state["mode"] in ["chat", "draft_and_send"]:
        response = chat_node({"input": state["message"]})
        state["response"] = response.get("response", "")
        state["is_draft"] = response.get("is_draft", False)
        state["draft"] = response.get("draft", None)

        if state["is_draft"] and state["draft"]:
            state["pending_email"] = state["draft"]
            # ✅ FIX: Save to Firestore instead of in-memory dict
            set_pending_email(state["user_id"], state["draft"])
            print(f"📧 Draft saved to Firestore for {state['user_id']}")

    return state

# ===== EMAIL READING NODE =====
def read_email_node_handler(state: ChatState) -> ChatState:
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
        # ✅ FIX: Save to Firestore
        set_cached_emails(state["user_id"], classified)
        state["is_email_list"] = True
        state["emails"] = classified
        state["response"] = f"📬 You have {len(classified)} unread emails."

    return state

# ===== AUTO REPLY NODE =====
def auto_reply_node_handler(state: ChatState) -> ChatState:
    if state["mode"] == "auto_reply":
        index_match = re.search(r"\d+", state["message"])
        index = int(index_match.group(0)) - 1 if index_match else 0

        # ✅ FIX: Load from Firestore
        cached = get_cached_emails(state["user_id"])
        state["cached_emails"] = cached

        if not cached:
            state["response"] = "Please read emails first."
            return state

        if index >= len(cached):
            state["response"] = f"Email {index + 1} not found."
            return state

        email = cached[index]
        reply_text = generate_reply(email)

        if not reply_text:
            state["response"] = "❌ Could not generate reply."
            return state

        draft = {
            "to": email["from_email"],
            "subject": f"Re: {email['subject']}",
            "body": reply_text,
            "thread_id": email.get("id")
        }
        state["pending_email"] = draft
        # ✅ FIX: Save to Firestore
        set_pending_email(state["user_id"], draft)

        state["response"] = f"To: {draft['to']}\nSubject: {draft['subject']}\nBody:\n{reply_text}"
        state["is_draft"] = True
        state["draft"] = draft

    return state

# ===== SEND EMAIL NODE =====
def send_email_node_handler(state: ChatState) -> ChatState:
    if state["mode"] == "send_email":
        # ✅ FIX: Load from Firestore
        pending = get_pending_email(state["user_id"])
        state["pending_email"] = pending

        if pending:
            try:
                send_email(
                    pending["to"],
                    pending["subject"],
                    pending["body"],
                )
                state["response"] = f"✅ Email sent to {pending['to']}."
                # ✅ FIX: Delete from Firestore
                delete_pending_email(state["user_id"])
            except Exception as e:
                state["response"] = f"❌ Failed: {str(e)}"
        else:
            state["response"] = "No draft found."

    return state

# ===== CANCEL EMAIL NODE =====
def cancel_email_node_handler(state: ChatState) -> ChatState:
    if state["mode"] == "cancel_email":
        pending = get_pending_email(state["user_id"])
        if pending:
            # ✅ FIX: Delete from Firestore
            delete_pending_email(state["user_id"])
            state["response"] = "❌ Draft cancelled."
        else:
            state["response"] = "No draft to cancel."

    return state

# ===== WEB SEARCH NODE =====
def web_search_node_handler(state: ChatState) -> ChatState:
    if state["mode"] == "web":
        from datetime import date
        today = date.today().strftime("%d %B %Y")

        search_query = f"{state['message']} {today}"
        results = search_web(search_query)

        direct_answer = results.get("answer", "")
        top = results.get("results", [])[:3]  # ← Only top 3

        # Limit content to 500 chars per result
        context = "\n\n".join([
            f"Source: {r['title']}\n"
            f"Content: {r['content'][:500]}"  # ← Limit chars
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

RULES:
- Use only results above
- Never use training data
- For prices: show exact figure and source
- For news: show headlines and source
- End with: Source: [name] | Date: {today}"""
        })
        state["response"] = response.get("response", "")

    return state

# ===== CLEAR MEMORY NODE =====
def clear_memory_node(state: ChatState) -> ChatState:
    if state["mode"] == "send_email":
        clear_memory()
        print(f"🧹 Memory cleared for {state['user_id']}")
    return state

# ===== ROUTING LOGIC =====
def route_to_handler(state: ChatState) -> str:
    return state["mode"]

# ===== BUILD GRAPH =====
def build_chat_graph():
    graph = StateGraph(ChatState)

    graph.add_node("router", router_node)
    graph.add_node("add_memory", add_to_memory_node)
    graph.add_node("chat", chat_node_handler)
    graph.add_node("read_email", read_email_node_handler)
    graph.add_node("auto_reply", auto_reply_node_handler)
    graph.add_node("send_email", send_email_node_handler)
    graph.add_node("cancel_email", cancel_email_node_handler)
    graph.add_node("web_search", web_search_node_handler)
    graph.add_node("update_memory", update_memory_with_response_node)
    graph.add_node("clear_memory", clear_memory_node)

    graph.set_entry_point("router")
    graph.add_edge("router", "add_memory")

    graph.add_conditional_edges(
        "add_memory",
        route_to_handler,
        {
            "chat": "chat",
            "draft_and_send": "chat",
            "read_email": "read_email",
            "auto_reply": "auto_reply",
            "send_email": "send_email",
            "cancel_email": "cancel_email",
            "web": "web_search",
        }
    )

    for node in ["chat", "read_email", "auto_reply", "web_search"]:
        graph.add_edge(node, "update_memory")

    graph.add_edge("send_email", "clear_memory")
    graph.add_edge("clear_memory", "update_memory")
    graph.add_edge("cancel_email", "update_memory")
    graph.add_edge("update_memory", END)

    return graph.compile()

# ===== MAIN WORKFLOW FUNCTION =====
def run_chat_workflow(user_id: str, message: str):
    try:
        graph = build_chat_graph()

        # ✅ FIX: Load pending email from Firestore
        pending = get_pending_email(user_id)

        state = {
            "user_id": user_id,
            "message": message,
            "mode": None,
            "response": "",
            "is_draft": False,
            "draft": None,
            "is_email_list": False,
            "emails": [],
            "pending_email": pending,
            "cached_emails": get_cached_emails(user_id),
            "memory": get_memory(),
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