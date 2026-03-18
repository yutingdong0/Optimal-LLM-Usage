import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from utils import load_all_chats, get_chat, save_chat, generate_ai_response, get_stats

app = FastAPI(title="FastAPI Ollama Chat")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

class MessageRequest(BaseModel):
    content: str
    title: str | None = None

@app.get("/")
async def root(request: Request):
    chats = load_all_chats()
    return templates.TemplateResponse("chat.html", {"request": request, "chats": chats})

@app.get("/chat/{chat_id}")
async def get_chat_history(chat_id: str):
    chat_data = get_chat(chat_id)
    if chat_data is None:
        return JSONResponse(status_code=404, content={"message": "Chat not found"})
    return chat_data

@app.post("/chat/{chat_id}/message")
async def send_message(chat_id: str, message: MessageRequest):
    chat_data = get_chat(chat_id) or {"id": chat_id, "messages": []}
    
    if message.title:
        chat_data["title"] = message.title

    chat_data["messages"].append({"role": "user", "content": message.content})
    ai_content, eval_count = await generate_ai_response(chat_data["messages"])
    chat_data["messages"].append({"role": "assistant", "content": ai_content})
    chat_data["tokens_used"] = chat_data.get("tokens_used", 0) + eval_count
    
    save_chat(chat_id, chat_data)
    
    return {"role": "assistant", "content": ai_content}

@app.get("/stats")
async def stats():
    return get_stats()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5010, reload=True)
