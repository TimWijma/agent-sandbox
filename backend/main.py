from datetime import datetime
from models.tools import ToolType
from services.llm_service import LLMService
from services.tool_manager import ToolManager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models.chat import ChatRequest, Message, ChatRole, Conversation

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

@app.get("/chat", response_model=list[Conversation])
async def get_chats():
    try:
        conversations = llm.load_conversations()
        
        if not conversations:
            raise HTTPException(status_code=404, detail="No conversations found.")
        
        return conversations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=Conversation)
async def create_chat():
    try:
        conversation = llm.create_conversation()
        if not conversation:
            raise HTTPException(status_code=500, detail="Failed to create conversation.")

        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/{conversation_id}/messages", response_model=Message)
async def chat(conversation_id: int, request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    conversation = llm.load_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    try:
        llm_response = llm.send_message(conversation_id, request.message)
        # tool_type, tool_output = tool_manager.handle_message(llm_response)

        return llm_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/chat/{conversation_id}", response_model=Conversation)
async def get_chat_history(conversation_id: int):
    try:
        conversation = llm.load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.delete("/chat/{conversation_id}")
# async def delete_chat(conversation_id: int):
#     try:
#         conversation = llm.load_conversation(conversation_id)
#         if not conversation:
#             raise HTTPException(status_code=404, detail="Conversation not found.")
        
#         llm.delete_conversation(conversation_id)