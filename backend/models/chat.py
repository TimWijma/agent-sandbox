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

# The response format for the LLM
class MessageResponse(BaseModel):
    type: ToolType
    content: str

class Message(BaseModel):
    id: int
    content: str
    type: ToolType
    role: ChatRole
    created_at: datetime
    original_message: str | None = None
    confirmed: bool | None = None  # True if tool was confirmed, False if declined, None for non-tool messages
    pending_confirmation: bool = False  # True if this message is waiting for user confirmation
    input_tokens: int = 0  # Number of input tokens for this message
    output_tokens: int = 0  # Number of output tokens for this message

class Conversation(BaseModel):
    id: int
    title: str
    messages: list[Message]
    created_at: datetime
    updated_at: datetime
    
    def get_total_tokens(self) -> dict[str, int]:
        """Calculate total input and output tokens for the conversation"""
        total_input = sum(message.input_tokens for message in self.messages)
        total_output = sum(message.output_tokens for message in self.messages)
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output
        }

# class MessageContent(BaseModel):
#     type: ToolType
#     original_message: str
#     content: str
