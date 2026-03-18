import os
import json
import httpx
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_DATA_DIR = os.path.join(BASE_DIR, "chat_data")
os.makedirs(CHAT_DATA_DIR, exist_ok=True)

OLLAMA_API_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "gemma3:12b"

def load_all_chats():
    chats = []
    for filename in os.listdir(CHAT_DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CHAT_DATA_DIR, filename)
            with open(filepath, "r") as f:
                try:
                    data = json.load(f)
                    chats.append({
                        "id": data.get("id", filename.replace(".json", "")),
                        "title": data.get("title", "New Chat"),
                        "updated_at": data.get("updated_at", "")
                    })
                except json.JSONDecodeError:
                    pass
    chats.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return chats

def get_chat(chat_id: str):
    filepath = os.path.join(CHAT_DATA_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None
    return None

def save_chat(chat_id: str, data: dict):
    filepath = os.path.join(CHAT_DATA_DIR, f"{chat_id}.json")
    
    if not data.get("title") and data.get("messages"):
        first_user_msg = next((m["content"] for m in data["messages"] if m["role"] == "user"), "New Chat")
        data["title"] = first_user_msg[:30] + ("..." if len(first_user_msg) > 30 else "")
        
    data["updated_at"] = datetime.now().isoformat()
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

async def generate_ai_response(messages: list):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    
    eval_count = 0
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_API_URL, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            ai_content = result.get("message", {}).get("content", "Error generating response.")
            eval_count = result.get("eval_count", 0)
    except Exception as e:
        ai_content = f"Sorry, could not connect to Ollama: {str(e)}"
        
    return ai_content, eval_count

def get_stats():
    total_messages = 0
    total_tokens = 0
    chat_count = 0
    
    for filename in os.listdir(CHAT_DATA_DIR):
        if filename.endswith(".json"):
            chat_count += 1
            filepath = os.path.join(CHAT_DATA_DIR, filename)
            with open(filepath, "r") as f:
                try:
                    data = json.load(f)
                    total_messages += len(data.get("messages", []))
                    total_tokens += data.get("tokens_used", 0)
                except json.JSONDecodeError:
                    pass
                    
    return {
        "chat_count": chat_count,
        "total_messages": total_messages,
        "total_tokens": total_tokens
    }
