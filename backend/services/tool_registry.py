from tools.calculator import CalculatorTool
from tools.base import BaseTool

tool_registry: dict[str, BaseTool] = {
    "calculator": CalculatorTool()
}

def execute_tool(tool_name: str, tool_input: str) -> str:
    if tool_name not in tool_registry:
        raise ValueError(f"Tool '{tool_name}' not found in registry.")
    
    tool = tool_registry[tool_name]
    return tool.run(tool_input)