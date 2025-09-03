from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any


class BaseTool(ABC):
    @abstractmethod
    def run(self, input: str, **kwargs) -> str:
        pass

    def requires_confirmation(self) -> bool:
        """Override this method to indicate if the tool requires user confirmation"""
        return False

    def preview(self, input: str, **kwargs) -> str:
        """Override this method to provide a preview of what the tool will do"""
        params_str = self.create_params_string(kwargs)
        if params_str:
            return f"Will execute: {input} (with parameters: {params_str})"
        return f"Will execute: {input}"

    def create_params_string(self, params: Dict[str, Any]) -> str:
        """
        Create a string representation of parameters for logging or display.
        Filters out None values.
        """
        return ", ".join(
            f"{key}={value}" for key, value in params.items() if value is not None
        )

    def execute_with_confirmation(
        self, input: str, confirmed: bool = False, **kwargs
    ) -> Tuple[str, bool]:
        """
        Execute the tool with confirmation support.
        Returns (result, needs_confirmation)
        """
        if self.requires_confirmation() and not confirmed:
            preview = self.preview(input, **kwargs)
            return preview, True
        else:
            result = self.run(input, **kwargs)
            return result, False
