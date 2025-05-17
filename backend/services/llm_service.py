from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

class LLMService:
    def __init__(self, model: str = "gemini-2.0-flash", system_prompt_path: str = "prompts/system_message.txt"):
        self.API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.API_KEY:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")

        self.client = genai.Client(api_key=self.API_KEY)
        self.model = model

        try:
            with open(system_prompt_path, "r") as file:
                self.system_message = file.read()
        except FileNotFoundError:
            self.system_message = "You are a helpful assistant. Answer the user's questions to the best of your ability."

        self.config = types.GenerateContentConfig(
            system_instruction=self.system_message,
            temperature=0.1
        )

    def send_message(self, message: str) -> str:
        user_prompt = types