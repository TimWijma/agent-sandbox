from tools.base_tool import BaseTool
from logger import logger
import subprocess

class CommandTool(BaseTool):
    def run(self, input: str) -> str:
        command = input.strip()
                
        try:
            logger.info(f"Executing shell command: {command}")

            result = subprocess.run(command, shell=True, text=True, capture_output=True)

            logger.info(f"Command executed with return code: {result.returncode}")
            
            if result.returncode != 0:
                error_message = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
                logger.error(error_message)
                return error_message
            else:
                logger.info(f"Command output: {result.stdout.strip()}")
                return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_message = f"Command execution failed: {e}"
            logger.error(error_message)
            return error_message
        except Exception as e:
            error_message = f"Error executing command: {e}"
            logger.error(error_message)
            return error_message