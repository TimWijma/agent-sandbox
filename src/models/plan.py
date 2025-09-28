from pydantic import BaseModel, Field
from models.tools import ToolType


class Step(BaseModel):
    step_id: int = Field(..., description="A unique identifier for this step, starting from 1.")
    thought: str = Field(..., description="The agent's reasoning or thought process for this step, which will be shown to the user.")
    tool_type: ToolType | None = Field(default=None, description="The type of tool to be used for this step, if any.")
    tool_input: str | None = Field(default=None, description="The input for the tool, if a tool is being used.")


class Plan(BaseModel):
    steps: list[Step]