from pydantic import BaseModel
from models.tools import ToolType
from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    role: ChatRole
    type: ToolType
    message: str