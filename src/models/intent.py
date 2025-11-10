from pydantic import BaseModel, Field
from enum import Enum


class IntentType(str, Enum):
    CONVERSATIONAL = "conversational"  # Questions about capabilities, greetings, clarifications
    SIMPLE_TOOL = "simple_tool"  # Single tool execution
    COMPLEX_TASK = "complex_task"  # Requires planning and multiple steps


class IntentClassification(BaseModel):
    intent_type: IntentType = Field(
        ..., 
        description="The classified intent type of the user's request"
    )
    reasoning: str = Field(
        ..., 
        description="Brief explanation of why this intent was chosen"
    )
    suggested_tool: str | None = Field(
        default=None,
        description="For SIMPLE_TOOL intents, the suggested tool to use"
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether the request needs clarification before proceeding"
    )
    clarification_question: str | None = Field(
        default=None,
        description="If clarification is needed, the question to ask the user"
    )
