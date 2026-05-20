CHAT_MEMORY = []

def add_message(role, content):
    CHAT_MEMORY.append({"role": role, "content": content})

def get_memory():
    return CHAT_MEMORY[-10:]

def clear_memory():
    global CHAT_MEMORY
    CHAT_MEMORY = []