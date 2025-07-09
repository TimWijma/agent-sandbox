from llm_service import LLMService
from googlesearch import search

# llm_service = LLMService()

# llm_service.test(
#     "What is the capital of France? and of netherlands? and what is 10 * 40"  # Example test input
# )  # Example test input


query = "top attractions in paris france"

results = search(query, num_results=3, region="fr")

for item in results:
    print(item)
