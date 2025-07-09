from tools.base_tool import BaseTool
from logger import logger
from googlesearch import search


class SearchTool(BaseTool):
    def requires_confirmation(self) -> bool:
        return True

    def preview(self, input: str, **kwargs) -> str:
        query = input.strip()

        query_params = self.create_params_string(kwargs)

        logger.info(f"Preview - input: {repr(input)}")
        logger.info(f"Preview - query after strip: {repr(query)}")

        return f"!!  SEARCH PREVIEW !!\nAbout to search for:\n'{query}' with params : {query_params}\n\n Do you want to proceed? (y/n)"

    def run(self, input: str, **kwargs) -> str:
        logger.info(f"Run - input: {repr(input)}")
        logger.info(f"Run - kwargs: {kwargs}")
        return self.search(input, **kwargs)

    def search(self, query: str, **kwargs) -> str:
        logger.info(f"Searching for: {query}")
        logger.info(f"Query type: {type(query)}")
        logger.info(f"Query repr: {repr(query)}")

        region = kwargs.get("region", None)

        try:
            results = search(query, num_results=3, region=region)
        except Exception as e:
            logger.error(f"Error during search: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error during search: {e}"

        logger.info(f"Search results: {results}")

        return "\n".join(item for item in results)
