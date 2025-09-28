from enum import Enum


class ToolType(str, Enum):
    GENERAL = "general"
    CALCULATOR = "calculator"
    PYTHON_INTERPRETER = "python_interpreter"
    SHELL_COMMAND = "shell_command"
    GOOGLE_SEARCH = "google_search"