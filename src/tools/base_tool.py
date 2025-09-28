from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, Type
from pydantic import BaseModel, ValidationError
from logger import logger

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of the tool's purpose."""
        pass

    @property
    @abstractmethod
    def schema(self) -> Type[BaseModel]:
        """The Pydantic model for the tool's input."""
        pass

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

    def requires_confirmation(self) -> bool:
        """Override this method to indicate if the tool requires user confirmation"""
        return False

    def preview(self, **kwargs) -> str:
        """Override this method to provide a preview of what the tool will do"""
        params_str = self.create_params_string(kwargs)
        if params_str:
            return f"Will execute: {self.name} (with parameters: {params_str})"
        return f"Will execute: {self.name}"

    def create_params_string(self, params: Dict[str, Any]) -> str:
        """
        Create a string representation of parameters for logging or display.
        Filters out None values.
        """
        return ", ".join(
            f"{key}={value}" for key, value in params.items() if value is not None
        )

    def execute_with_confirmation(
        self, tool_input: str, confirmed: bool = False
    ) -> Tuple[str, bool]:
        """
        Execute the tool with confirmation support.
        Returns (result, needs_confirmation)
        """
        try:
            # The tool_input is a JSON string, parse it into a dictionary
            input_dict = self.schema.model_validate_json(tool_input)
            kwargs = input_dict.model_dump()
        except ValidationError as e:
            logger.error(f"Tool input validation failed for {self.name}: {e}")
            return f"Error: Invalid input format for {self.name}. Expected a JSON object matching the schema. {e}", False
        except Exception as e:
            logger.error(f"Failed to parse tool input for {self.name}: {e}")
            return f"Error: Failed to parse tool input. Expected a valid JSON string. {e}", False


        if self.requires_confirmation() and not confirmed:
            preview = self.preview(**kwargs)
            return preview, True
        else:
            result = self.run(**kwargs)
            return result, False