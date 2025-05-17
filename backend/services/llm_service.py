from google import genai
from google.genai import types
import os
from logger import logger

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
            logger.warning(f"System prompt file '{system_prompt_path}' not found. Using default system message.")
            self.system_message = "You are a helpful assistant. Answer the user's questions to the best of your ability."

        self.config = types.GenerateContentConfig(
            system_instruction=self.system_message,
            temperature=0.5
        )

        self.chat = self.client.chats.create(
            model=self.model,
            config = self.config
        )

        logger.info("LLMService initialized with model: %s", self.model)

    def create_chat(self):
        self.chat = self.client.chats.create(
            model=self.model,
            config=self.config
        )
        logger.info("New chat created with model: %s", self.model)

    def send_message(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("User message cannot be empty.")
        
        logger.info("User message sent: %s", user_message)
        response = self.chat.send_message(user_message)
        logger.info("Response received: %s", response.text)
        
        return response.text
    
    def get_history(self) -> list[str]:
        history = self.chat.get_history() or []

        return [(msg.role, msg.parts[0].text) for msg in history if msg.parts]
    
    def clear_history(self):
        self.create_chat()
        logger.info("Chat history cleared.")

        return True