from typing import Optional
from tools.base_tool import BaseTool
from logger import logger
import re
import sys
import io

class FileTool(BaseTool):
    def run(self, input: str) -> str:
        clean_code = self.extract_code_blocks(input)
        
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        
        try:
            logger.info(f"Executing file tool command: {clean_code}")
            exec(clean_code, 
                 {
                    "os": __import__('os'),
                    "sys": __import__('sys'),
                }, {})
            
            output_str = redirected_output.getvalue()
            if output_str:
                logger.info(f"File tool command output: {output_str}")
                return f"File tool command executed successfully:\n{output_str}"
            else:
                logger.info("File tool command executed successfully with no output.")
                return "File tool command executed successfully with no output."
            
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
        match = re.search(pattern, input, re.DOTALL) # DOTALL is crucial here
        
        if match:
            return match.group(1).strip()
        
        return input.strip()