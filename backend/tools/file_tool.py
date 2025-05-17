from tools.base_tool import BaseTool


class FileTool(BaseTool):
    def run(self, input: str) -> str:
        return input