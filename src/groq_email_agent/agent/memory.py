from typing import TypedDict
from langgraph.graph import StateGraph

# Per-user memory storage
CHAT_MEMORIES: dict[str, list] = {}

def add_message(role: str, content: str, user_id: str = "default"):
    """Add message to user's memory"""
    if user_id not in CHAT_MEMORIES:
        CHAT_MEMORIES[user_id] = []
    CHAT_MEMORIES[user_id].append({
        "role": role,
        "content": content
    })

def get_memory(user_id: str = "default") -> list:
    """Get last 10 messages for user"""
    return CHAT_MEMORIES.get(user_id, [])[-10:]

def clear_memory(user_id: str = "default"):
    """Clear memory for specific user"""
    if user_id in CHAT_MEMORIES:
        CHAT_MEMORIES[user_id] = []
    print(f"🧹 Memory cleared for {user_id}")

def get_all_memories() -> dict:
    """Get all users memories (for debugging)"""
    return CHAT_MEMORIES