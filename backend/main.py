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
conversations: dict[int, Conversation] = {}

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
        result = []
        for conversation in conversations.values():
            result.append({
                "id": conversation.id,
                "title": conversation.title,
                "messages": [],
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=Conversation)
async def create_chat():
    try:
        conversation_id = len(conversations) + 1
        conversation = Conversation(
            id=conversation_id,
            title=f"New Conversation {conversation_id}",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        conversations[conversation_id] = conversation

        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/{conversation_id}/messages", response_model=Message)
async def chat(conversation_id: int, request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    messages = conversations.get(conversation_id).messages
    
    user_message = Message(
        id=len(messages),
        conversation_id=conversation_id,
        content=request.message,
        type=ToolType.GENERAL,
        role=ChatRole.USER,
        created_at=datetime.now(),
    )
    messages.append(user_message)

    try:
        llm_response = llm.send_message(conversation_id, request.message)
        tool_type, tool_output = tool_manager.handle_message(llm_response)

        model_message = Message(
            id=len(messages),
            conversation_id=conversation_id,
            content=tool_output,
            type=tool_type,
            role=ChatRole.MODEL,
            created_at=datetime.now(),
            original_message=llm_response,
        )
        messages.append(model_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return model_message
    
@app.get("/chat/{conversation_id}", response_model=Conversation)
async def get_chat_history(conversation_id: int):
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        
        return conversations.get(conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{conversation_id}")
async def delete_chat(conversation_id: int):
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        
        del conversations[conversation_id]
        return {"detail": "Conversation deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))