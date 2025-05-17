from asteval import Interpreter
from tools.base import BaseTool
import math

class CalculatorTool(BaseTool):
    def __init__(self):
        self.aeval = Interpreter()
        self.aeval.symtable['math'] = math

    def run(self, input: str) -> str:
        return self.calculate(input)

    def calculate(self, expression: str) -> str:
        print(f"Calculating expression: {expression}")
        print("-" * 20)

        result = self.aeval(expression)
        if self.aeval.error:
            print(f"Error calculating expression: {self.aeval.error}")
            print("-" * 20)
            return f"Error: {self.aeval.error}"
        
        print(f"Result: {result}")
        print("-" * 20)

        return str(result)