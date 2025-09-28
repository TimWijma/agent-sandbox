from typing import Type
from tools.base_tool import BaseTool
from logger import logger
import re
import sys
import io
from pydantic import BaseModel, Field

class CodeInput(BaseModel):
    code: str = Field(..., description="The Python code to be executed.")

class CodeTool(BaseTool):
    name = "python_interpreter"
    description = "Executes a block of Python code in a restricted environment. The code should be self-contained."
    schema: Type[BaseModel] = CodeInput

    def requires_confirmation(self) -> bool:
        return True

    def preview(self, **kwargs) -> str:
        code = kwargs.get("code", "")
        clean_code = self.extract_code_blocks(code)
        return f"!!  CODE OPERATION PREVIEW !!\nAbout to execute Python code:\n\n{clean_code}\n\nDo you want to proceed? (y/n)"

    def run(self, **kwargs) -> str:
        code = kwargs.get("code")
        if not code:
            return "Error: 'code' is a required field."
        
        clean_code = self.extract_code_blocks(code)

        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            logger.info(f"Executing code tool command: {clean_code}")

            # Create a restricted namespace
            namespace = {
                "os": __import__("os"),
                "sys": __import__("sys"),
                "math": __import__("math"),
                "re": __import__("re"),
            }

            exec(clean_code, {"__builtins__": __builtins__}, namespace)

            output_str = redirected_output.getvalue()
            if output_str:
                logger.info(f"Code tool command output: {output_str}")
                return f"Code executed successfully:\n{output_str}"
            else:
                logger.info("Code tool command executed successfully with no output.")
                return "Code executed successfully with no output."

        except SyntaxError as e:
            error_message = f"Syntax error in code block: {e}"
            logger.error(error_message)
            return error_message
        except Exception as e:
            error_message = f"Error executing code block: {e}"
            logger.error(error_message)
            captured_output = redirected_output.getvalue()
            if captured_output:
                logger.error(f"Captured output before error: {captured_output}")
                return f"Error executing code block: {error_message}\nCaptured output:\n{captured_output}"
            else:
                return f"Error executing code block: {error_message}"
        finally:
            sys.stdout = old_stdout
            redirected_output.close()

    def extract_code_blocks(self, input_str: str) -> str:
        """Extract code blocks from the input string."""
        if not input_str:
            return ""
        pattern = r"```(?:python)?\s*(.*?)\s*```"
        match = re.search(pattern, input_str, re.DOTALL)

        if match:
            return match.group(1).strip()

        return input_str.strip()