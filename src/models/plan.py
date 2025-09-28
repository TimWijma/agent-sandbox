from pydantic import BaseModel, Field
from models.tools import ToolType


class Step(BaseModel):
    step_id: int = Field(..., description="A unique identifier for this step, starting from 1.")
    thought: str = Field(..., description="The AI's reasoning for this step, to be shown to the user.")
    tool_type: ToolType | None = Field(default=None, description="The type of tool to be used for this step, if any.")
    tool_input: str | None = Field(default=None, description="The input for the tool as a JSON string, if applicable.")

class StepMessage(BaseModel):
    step: Step = Field(..., description="The details of the step being executed.")
    message: str = Field(..., description="A message to be sent to the user about this step.")
    plan_complete: bool = Field(..., description="Indicates if the entire plan has been completed after this step.")

class Plan(BaseModel):
    steps: list[Step]

    def __str__(self) -> str:
        output = "Plan:\n"
        for step in self.steps:
            output += f"Step {step.step_id}:\n"
            output += f"  Thought: {step.thought}\n"
            if step.tool_type:
                output += f"  Tool: {step.tool_type}\n"
            if step.tool_input:
                output += f"  Tool Input: {step.tool_input}\n"
            output += "\n"
        return output