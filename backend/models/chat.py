from datetime import datetime
from pydantic import BaseModel
from models.tools import ToolType
from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"



class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    id: int
    content: str
    type: ToolType
    role: ChatRole
    created_at: datetime
    original_message: str | None = None

class Conversation(BaseModel):
    id: int
    title: str
    messages: list[Message]
    created_at: datetime
    updated_at: datetime

# class MessageContent(BaseModel):
#     type: ToolType
#     original_message: str
#     content: str
