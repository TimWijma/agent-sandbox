from datetime import datetime
from pydantic import BaseModel
from models.tools import ToolType
from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"

class Conversation(BaseModel):
    id: int
    title: str
    messages: list[dict]
    created_at: datetime
    updated_at: datetime

class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    id: int
    conversation_id: int
    content: str
    type: ToolType
    role: ChatRole
    created_at: datetime
    original_message: str | None = None

# class MessageContent(BaseModel):
#     type: ToolType
#     original_message: str
#     content: str
