from tools.base_tool import BaseTool
from logger import logger
from googlesearch import search
from pydantic import BaseModel, Field
from typing import Type, Optional

class SearchInput(BaseModel):
    query: str = Field(..., description="The search query.")
    region: Optional[str] = Field(default=None, description="The region to search in (e.g., 'us', 'uk').")

class SearchTool(BaseTool):
    name = "google_search"
    description = "Performs a Google search and returns the top 3 results (title, URL, and description)."
    schema: Type[BaseModel] = SearchInput

    def requires_confirmation(self) -> bool:
        return True

    def preview(self, **kwargs) -> str:
        query = kwargs.get("query", "").strip()
        region = kwargs.get("region")
        
        preview_text = f"!!  SEARCH PREVIEW !!\nAbout to search Google for:\n'{query}'"
        if region:
            preview_text += f" in region '{region}'"
        preview_text += "\n\nDo you want to proceed? (y/n)"
        return preview_text

    def run(self, **kwargs) -> str:
        query = kwargs.get("query")
        if not query:
            return "Error: 'query' is a required field."
        
        region = kwargs.get("region")

        logger.info(f"Searching for: '{query}'" + (f" in region '{region}'" if region else ""))

        try:
            # Using advanced=True returns a generator of (title, url, description) tuples
            search_generator = search(query, num_results=3, advanced=True, lang='en')
            results = list(search_generator)
            
            if not results:
                return "No results found."

            formatted_results = []
            for title, url, description in results:
                formatted_results.append(f"Title: {title}\nURL: {url}\nDescription: {description}\n")

            return "\n".join(formatted_results)

        except Exception as e:
            error_message = f"An unexpected error occurred during search: {e}"
            logger.error(error_message)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return error_message