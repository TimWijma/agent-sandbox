import os
# from logger import logger
from litellm import completion
from dotenv import load_dotenv
from services.conversation_manager import ConversationManager
from models.chat import ChatRole, Conversation, Message, ToolType
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
    def __init__(self, model: str = "gemini/gemini-2.0-flash", system_prompt_path: str = "prompts/system_message.txt"):
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

    def send_message(self, conversation_id: int, user_message: str) -> Message:
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
            role=ChatRole.USER,
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
            role=ChatRole.ASSISTANT,
            created_at=datetime.now()
        )

        # Add model response to conversation
        conversation.messages.append(model_message)

        # Save updated conversation
        self.conversation_manager.save_conversation(conversation)

        return model_message