from datetime import datetime
from pydantic import BaseModel
from models.plan import Plan
from models.tools import ToolType
from enum import Enum


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatRequest(BaseModel):
    message: str


class MessageType(str, Enum):
    TEXT = "text"
    PLAN = "plan"
    TOOL = "tool"

class Message(BaseModel):
    id: int
    content: str | Plan
    type: MessageType | None = None
    role: ChatRole
    created_at: datetime = datetime.now()
    confirmed: bool | None = (
        None  # True if tool was confirmed, False if declined, None for non-tool messages
    )
    pending_confirmation: bool = (
        False  # True if this message is waiting for user confirmation
    )
    input_tokens: int = 0  # Number of input tokens for this message
    output_tokens: int = 0  # Number of output tokens for this message

    def set_token_usage(self, usage: dict):
        """Set token usage from LLM response"""
        self.input_tokens = usage.get("prompt_tokens", 0)
        self.output_tokens = usage.get("completion_tokens", 0)


class Conversation(BaseModel):
    id: int
    title: str
    messages: list[Message]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def get_total_tokens(self) -> dict[str, int]:
        """Calculate total input and output tokens for the conversation"""
        total_input = sum(message.input_tokens for message in self.messages)
        total_output = sum(message.output_tokens for message in self.messages)
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }
