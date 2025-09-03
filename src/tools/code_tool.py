from typing import Optional
from tools.base_tool import BaseTool
from logger import logger
import re
import sys
import io


class CodeTool(BaseTool):
    def requires_confirmation(self) -> bool:
        return True

    def preview(self, input: str) -> str:
        clean_code = self.extract_code_blocks(input)
        return f"!!  CODE OPERATION PREVIEW !!\nAbout to execute Python code:\n\n{clean_code}\n\nDo you want to proceed? (y/n)"

    def run(self, input: str) -> str:
        clean_code = self.extract_code_blocks(input)

        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            logger.info(f"Executing code tool command: {clean_code}")

            namespace = {
                "os": __import__("os"),
                "sys": __import__("sys"),
            }

            exec(clean_code, namespace, namespace)

            output_str = redirected_output.getvalue()
            if output_str:
                logger.info(f"Code tool command output: {output_str}")
                return f"Code tool command executed successfully:\n{output_str}"
            else:
                logger.info("Code tool command executed successfully with no output.")
                return "Code tool command executed successfully with no output."

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

    def extract_code_blocks(self, input: str) -> Optional[str]:
        """Extract code blocks from the input string."""
        pattern = r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```"
        match = re.search(pattern, input, re.DOTALL)  # DOTALL is crucial here

        if match:
            return match.group(1).strip()

        return input.strip()
