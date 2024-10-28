# conversation_history.py

def load_conversation_history():
    default_system_prompt = {
        "role": "system",
        "content": """You are Jarvis, an AI assistant. Be direct, concise, and helpful. 
        Use casual language and be modern and human-like."""
    }
    # Simply return default prompt and empty list - no file loading
    return default_system_prompt, []

def save_conversation_history(system_prompt, current_conversation):
    # Empty implementation since we're only keeping memory per run
    pass
