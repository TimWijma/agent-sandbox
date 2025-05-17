from services.llm_service import LLMService
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
llm = LLMService()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    try:
        response = llm.send_message(request.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return ChatResponse(response=response)