from tools.base_tool import BaseTool
from logger import logger
import subprocess
from pydantic import BaseModel, Field
from typing import Type

class CommandInput(BaseModel):
    command: str = Field(..., description="The shell command to be executed.")

class CommandTool(BaseTool):
    name = "shell_command"
    description = "Executes a shell command on the user's system. Use with extreme caution."
    schema: Type[BaseModel] = CommandInput

    def requires_confirmation(self) -> bool:
        return True

    def preview(self, **kwargs) -> str:
        command = kwargs.get("command", "").strip()
        return f"!!  COMMAND PREVIEW !!\nAbout to execute shell command:\n'{command}'\n\nThis will run on your system. Do you want to proceed? (y/n)"

    def run(self, **kwargs) -> str:
        command = kwargs.get("command")
        if not command:
            return "Error: 'command' is a required field."
        
        command = command.strip()

        try:
            logger.info(f"Executing shell command: {command}")

            result = subprocess.run(command, shell=True, text=True, capture_output=True, check=False)

            logger.info(f"Command executed with return code: {result.returncode}")

            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout.strip()}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr.strip()}\n"

            if result.returncode != 0:
                error_message = f"Command failed with return code {result.returncode}.\n{output}"
                logger.error(error_message)
                return error_message
            else:
                logger.info(f"Command output: {output}")
                if not output:
                    return "Command executed successfully with no output."
                return output

        except Exception as e:
            error_message = f"An unexpected error occurred while executing command: {e}"
            logger.error(error_message)
            return error_message