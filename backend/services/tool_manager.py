from tools.calculator_tool import CalculatorTool
from tools.file_tool import FileTool
from tools.base_tool import BaseTool
from tools.command_tool import CommandTool
from models.tools import ToolType
import re
from typing import Optional
from logger import logger

class ToolManager:
    TOOL_PATTERN = re.compile(r"^USE_(\w+):\s*(.+)", re.IGNORECASE | re.DOTALL)

    def __init__(self):
        self.tool_registry: dict[ToolType, BaseTool] = {
            ToolType.CALCULATOR: CalculatorTool(),
            ToolType.FILE: FileTool(),
            ToolType.COMMAND: CommandTool()
        }

        logger.info("ToolManager initialized with tools: %s", list(self.tool_registry.keys()))

    def parse_message(self, message: str) -> Optional[tuple[ToolType, str]]:
        match = self.TOOL_PATTERN.match(message)
        if not match:
            return None
        
        tool_name = match.group(1).lower()
        tool_input = match.group(2).strip()

        try:
            tool_type = ToolType(tool_name)
        except ValueError:
            raise ValueError(f"Tool '{tool_name}' is not a valid tool type.")
        if tool_type not in self.tool_registry:
            raise ValueError(f"Tool '{tool_type}' not found in registry.")

        return tool_type, tool_input
    
    def execute_tool(self, tool_type: ToolType, tool_input: str) -> str:
        if tool_type not in self.tool_registry:
            raise ValueError(f"Tool '{tool_type}' not found in registry.")
        
        tool = self.tool_registry[tool_type]
        return tool.run(tool_input)
    
    def handle_message(self, message: str) -> tuple[ToolType, str]:
        parsed_message = self.parse_message(message)
        if parsed_message:
            tool_type, tool_input = parsed_message
            return tool_type, tool_input
        
        return ToolType.GENERAL, message