from tools.calculator_tool import CalculatorTool
from tools.file_tool import FileTool
from tools.base_tool import BaseTool
import re
from typing import Optional

# tool_registry: dict[str, BaseTool] = {
#     "calculator": CalculatorTool()
# }

# def execute_tool(tool_name: str, tool_input: str) -> str:
#     if tool_name not in tool_registry:
#         raise ValueError(f"Tool '{tool_name}' not found in registry.")
    
#     tool = tool_registry[tool_name]
#     return tool.run(tool_input)


class ToolManager:
    TOOL_PATTERN = re.compile(r"^USE_(\w+):\s*(.+)", re.IGNORECASE | re.DOTALL)

    def __init__(self):
        self.tool_registry: dict[str, BaseTool] = {
            "calculator": CalculatorTool(),
            "file": FileTool()
        }

    def parse_message(self, message: str) -> Optional[tuple[str, str]]:
        match = self.TOOL_PATTERN.match(message)
        if not match:
            return None
        
        tool_name = match.group(1).lower()
        tool_input = match.group(2).strip()

        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        
        return tool_name, tool_input
    
    def execute_tool(self, tool_name: str, tool_input: str) -> str:
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        
        tool = self.tool_registry[tool_name]
        return tool.run(tool_input)
    
    def handle_message(self, message: str) -> str:
        parsed_message = self.parse_message(message)
        if parsed_message:
            tool_name, tool_input = parsed_message
            return self.execute_tool(tool_name, tool_input)
        
        return message