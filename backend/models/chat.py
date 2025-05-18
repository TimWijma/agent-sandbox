from pydantic import BaseModel
from models.tools import ToolType
from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"

class Conversation(BaseModel):
    id: str
    title: str
    messages: list[dict]
    created_at: str
    updated_at: str

class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    role: ChatRole
    type: ToolType
    message: str

# class MessageContent(BaseModel):
#     type: ToolType
#     original_message: str
#     content: str
