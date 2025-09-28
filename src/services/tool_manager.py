import json
from models.tools import ToolType
from tools.base_tool import BaseTool
from tools.calculator_tool import CalculatorTool
from tools.code_tool import CodeTool
from tools.command_tool import CommandTool
from tools.search_tool import SearchTool
from typing import Optional, Tuple
from logger import logger

class ToolManager:
    def __init__(self):
        self.tool_registry: dict[ToolType, BaseTool] = {
            ToolType.CALCULATOR: CalculatorTool(),
            ToolType.PYTHON_INTERPRETER: CodeTool(),
            ToolType.SHELL_COMMAND: CommandTool(),
            ToolType.GOOGLE_SEARCH: SearchTool(),
        }
        self.pending_confirmations: dict[str, Tuple[ToolType, str]] = {}
        logger.info("ToolManager initialized with tools: %s", list(self.tool_registry.keys()))

    def get_tool_descriptions(self) -> str:
        """Returns a JSON string describing all available tools."""
        descriptions = []
        for tool in self.tool_registry.values():
            descriptions.append({
                "name": tool.name,
                "description": tool.description,
                "schema": tool.schema.model_json_schema()
            })
        return json.dumps(descriptions, indent=2)

    def execute_tool(
        self, tool_type: ToolType, tool_input: str, confirmed: bool = False
    ) -> Tuple[str, bool]:
        """
        Execute a tool with confirmation support.
        Returns (result, needs_confirmation)
        """
        if tool_type not in self.tool_registry:
            raise ValueError(f"Tool '{tool_type}' not found in registry.")

        tool = self.tool_registry[tool_type]
        # The tool_input is a JSON string which execute_with_confirmation will parse and validate
        return tool.execute_with_confirmation(tool_input, confirmed)

    def store_pending_confirmation(
        self, conversation_id: str, tool_type: ToolType, tool_input: str
    ):
        """Store a pending confirmation for later execution"""
        self.pending_confirmations[conversation_id] = (tool_type, tool_input)

    def get_pending_confirmation(
        self, conversation_id: str
    ) -> Optional[Tuple[ToolType, str]]:
        """Get and remove a pending confirmation"""
        return self.pending_confirmations.pop(conversation_id, None)