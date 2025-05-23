import os
# from logger import logger
from litellm import completion
from dotenv import load_dotenv
from services.conversation_manager import ConversationManager
from models.chat import Conversation, Message, ToolType
from datetime import datetime

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

# resp = completion(
#     model="gemini/gemini-2.0-flash",
#     messages=[
#         {
#             "role": "user",
#             "content": "What is the capital of France?"
#         }
#     ]
# )

# print(resp.choices[0].message)

class LLMService:
    def __init__(self, model: str = "gemini-2.0-flash", system_prompt_path: str = "prompts/system_message.txt"):
        self.API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.API_KEY:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")
        os.environ["GEMINI_API_KEY"] = self.API_KEY

        self.model = model
        self.system_prompt_path = system_prompt_path
        self.conversation_manager = ConversationManager()

    def load_conversations(self):
        conversations = self.conversation_manager.load_all_conversations()
        if not conversations:
            raise ValueError("No conversations found.")
        return conversations

    def create_conversation(self):
        conversation_id = self.conversation_manager.get_next_conversation_id()
        conversation = Conversation(
            id=conversation_id,
            title=f"New Conversation {conversation_id}",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.conversation_manager.save_conversation(conversation)
        return conversation

    def load_conversation(self, conversation_id: int) -> Conversation:
        conversation = self.conversation_manager.load_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found.")
        return conversation

    def send_message(self, conversation_id: int, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("User message cannot be empty.")

        conversation = self.conversation_manager.load_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found.")

        user_message = Message(
            id=len(conversation.messages),
            content=user_message,
            type=ToolType.GENERAL,
            role="user",
            created_at=datetime.now()
        )

        # Add user message to conversation
        conversation.messages.append(user_message)

        completion_messages = [
            {
                "role": message.role,
                "content": message.content
            }
            for message in conversation.messages
        ]

        # Call the LLM API
        response = completion(
            model=self.model,
            messages=completion_messages,
            temperature=0.5,
        )

        # Extract the model response
        model_response = response.choices[0].message.content
        model_message = Message(
            id=len(conversation.messages),
            content=model_response,
            type=ToolType.GENERAL,
            role="model",
            created_at=datetime.now()
        )

        # Add model response to conversation
        conversation.messages.append(model_message)

        # Save updated conversation
        self.conversation_manager.save_conversation(conversation)

        return model_response

# class LLMService:
#     def __init__(self, model: str = "gemini-2.0-flash", system_prompt_path: str = "prompts/system_message.txt"):
#         self.API_KEY = os.getenv("GEMINI_API_KEY")
#         if not self.API_KEY:
#             raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")
#         os.environ["GEMINI_API_KEY"] = self.API_KEY
        
#         self.client = genai.Client(api_key=self.API_KEY)
#         self.model = model

#         try:
#             with open(system_prompt_path, "r") as file:
#                 self.system_message = file.read()
#         except FileNotFoundError:
#             logger.warning(f"System prompt file '{system_prompt_path}' not found. Using default system message.")
#             self.system_message = "You are a helpful assistant. Answer the user's questions to the best of your ability."

#         self.config = types.GenerateContentConfig(
#             system_instruction=self.system_message,
#             temperature=0.5
#         )

#         self.chats: dict[int, Chat] = {}

#         logger.info("LLMService initialized with model: %s", self.model)

#     def create_chat(self, conversation_id: int):
#         chat = self.client.chats.create(
#             model=self.model,
#             config=self.config
#         )
#         self.chats[conversation_id] = chat
#         logger.info("New chat created for conversation_id=%s with model: %s", conversation_id, self.model)

#     def send_message(self, conversation_id: int, user_message: str) -> str:
#         user_message = user_message.strip()
#         if not user_message:
#             raise ValueError("User message cannot be empty.")
        
#         if conversation_id not in self.chats:
#             self.create_chat(conversation_id)

#         chat: Chat = self.chats[conversation_id]

#         logger.info("User message sent: %s", user_message)
#         response = chat.send_message(user_message)
#         logger.info("Response received: %s", response.text)
        
#         return response.text