from enum import Enum

class ToolType(str, Enum):
    GENERAL = "general"
    CALCULATOR = "calculator"
    CODE = "code"
    COMMAND = "command"