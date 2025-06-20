from enum import Enum

class ToolType(str, Enum):
    GENERAL = "general"
    CALCULATOR = "calculator"
    FILE = "file"
    COMMAND = "command"