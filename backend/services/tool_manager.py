from models.chat import MessageResponse
from models.tools import ToolType

from tools.base_tool import BaseTool
from tools.calculator_tool import CalculatorTool
from tools.code_tool import CodeTool
from tools.command_tool import CommandTool
from tools.search_tool import SearchTool

import re

from typing import Optional, Tuple
from logger import logger


class ToolManager:
    TOOL_PATTERN = re.compile(r"^USE_(\w+):\s*(.+)", re.IGNORECASE | re.DOTALL)

    def __init__(self):
        self.tool_registry: dict[ToolType, BaseTool] = {
            ToolType.CALCULATOR: CalculatorTool(),
            ToolType.CODE: CodeTool(),
            ToolType.COMMAND: CommandTool(),
            ToolType.SEARCH: SearchTool(),
        }

        self.pending_confirmations: dict[str, Tuple[ToolType, str]] = {}

        logger.info(
            "ToolManager initialized with tools: %s", list(self.tool_registry.keys())
        )

    def execute_tool(
        self, tool_type: ToolType, tool_input: str, confirmed: bool = False, **kwargs
    ) -> Tuple[str, bool]:
        """
        Execute a tool with confirmation support.
        Returns (result, needs_confirmation)
        """
        if tool_type not in self.tool_registry:
            raise ValueError(f"Tool '{tool_type}' not found in registry.")

        tool = self.tool_registry[tool_type]
        return tool.execute_with_confirmation(tool_input, confirmed, **kwargs)

    def handle_message(self, message: MessageResponse) -> tuple[ToolType, str, dict]:
        tool_type = message.type
        if tool_type is not ToolType.GENERAL and tool_type not in self.tool_registry:
            raise ValueError(f"Tool type '{tool_type}' is not recognized.")

        # Extract optional parameters
        params = {}
        if message.region is not None:
            params["region"] = message.region

        return tool_type, message.content.strip(), params

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
