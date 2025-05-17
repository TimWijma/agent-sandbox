from models.tools import ToolType
from services.llm_service import LLMService
from services.tool_manager import ToolManager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models.chat import ChatRequest, ChatResponse, ChatRole

load_dotenv()

llm = LLMService()
tool_manager = ToolManager()
app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    try:
        llm_response = llm.send_message(request.message)
        response_type, response_message = tool_manager.handle_message(llm_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return ChatResponse(role=ChatRole.MODEL, type=response_type, message=response_message)

@app.get("/chat", response_model=list[ChatResponse])
async def get_chat_history():
    try:
        history = llm.get_history()
        return [ChatResponse(role=role, message=message, type=ToolType.GENERAL) for role, message in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/clear")
async def clear_chat():
    try:
        llm.clear_history()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))