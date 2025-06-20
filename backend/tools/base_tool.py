from abc import ABC, abstractmethod
from typing import Optional, Tuple

class BaseTool(ABC):
    @abstractmethod
    def run(self, input: str) -> str:
        pass
    
    def requires_confirmation(self) -> bool:
        """Override this method to indicate if the tool requires user confirmation"""
        return False
    
    def preview(self, input: str) -> str:
        """Override this method to provide a preview of what the tool will do"""
        return f"Will execute: {input}"
    
    def execute_with_confirmation(self, input: str, confirmed: bool = False) -> Tuple[str, bool]:
        """
        Execute the tool with confirmation support.
        Returns (result, needs_confirmation)
        """
        if self.requires_confirmation() and not confirmed:
            preview = self.preview(input)
            return preview, True
        else:
            result = self.run(input)
            return result, False