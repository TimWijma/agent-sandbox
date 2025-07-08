from tools.base_tool import BaseTool
from logger import logger
import ddgs


class SearchTool(BaseTool):
    def requires_confirmation(self) -> bool:
        return True

    def preview(self, input: str) -> str:
        query = input.strip()
        return f"⚠️  SEACH PREVIEW ⚠️\nAbout to search for:\n'{query}'\n\n Do you want to proceed? (y/n)"

    def run(self, input: str) -> str:
        return self.search(input)

    def search(self, query: str) -> str:
        logger.info(f"Searching for: {query}")

        return ""
