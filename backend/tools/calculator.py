from asteval import Interpreter
from tools.base import BaseTool
import math
from logger import logger

class CalculatorTool(BaseTool):
    def __init__(self):
        self.aeval = Interpreter()
        self.aeval.symtable['math'] = math

    def run(self, input: str) -> str:
        return self.calculate(input)

    def calculate(self, expression: str) -> str:
        logger.info(f"Calculating expression: {expression}")

        result = self.aeval(expression)
        if self.aeval.error:
            logger.error(f"Error calculating expression: {self.aeval.error}")
            return f"Error: {self.aeval.error}"
        
        logger.info(f"Result: {result}")

        return str(result)