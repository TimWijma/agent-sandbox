from abc import ABC, abstractmethod

class BaseTool(ABC):
    @abstractmethod
    def run(self, input: str) -> str:
        pass