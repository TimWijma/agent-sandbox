from asteval import Interpreter
from tools.base_tool import BaseTool
import math
from logger import logger
from pydantic import BaseModel, Field
from typing import Type

class CalculatorInput(BaseModel):
    expression: str = Field(..., description="The mathematical expression to evaluate.")

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluates a mathematical expression and returns the result."
    schema: Type[BaseModel] = CalculatorInput

    def __init__(self):
        self.aeval = Interpreter()
        self.aeval.symtable["math"] = math

    def run(self, **kwargs) -> str:
        expression = kwargs.get("expression")
        if not expression:
            return "Error: 'expression' is a required field."
        return self.calculate(expression)

    def calculate(self, expression: str) -> str:
        logger.info(f"Calculating expression: {expression}")

        result = self.aeval(expression)
        if self.aeval.error:
            error_message = f"Error calculating expression: {self.aeval.error}"
            logger.error(error_message)
            # Extract the actual error message from the asteval error object
            detailed_error = self.aeval.error[0].get_error()
            return f"Error: {detailed_error}"

        logger.info(f"Result: {result}")
        return str(result)