import os
from logger import logger
from litellm import completion
from dotenv import load_dotenv
from services.conversation_manager import ConversationManager
from models.chat import ChatRole, Conversation, Message, ToolType
from datetime import datetime

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

class LLMService:
    def __init__(self, model: str = "gemini/gemini-2.0-flash", system_message_path: str = "prompts/system_message.txt"):
        self.API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.API_KEY:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")
        os.environ["GEMINI_API_KEY"] = self.API_KEY

        self.model = model

        self.conversation_manager = ConversationManager(system_message_path=system_message_path)

    # def load_conversations(self) -> dict[int, Conversation]:
    #     conversations = self.conversation_manager.load_conversations()
    #     if not conversations:
    #         raise ValueError("No conversations found.")
    #     return conversations

    # def create_conversation(self):
    #     conversation = self.conversation_manager.create_conversation()

    #     return conversation

    # def load_conversation(self, conversation_id: int) -> Conversation:
    #     conversation = self.conversation_manager.load_conversation(conversation_id, include_system_message=False)

    #     if not conversation:
    #         raise ValueError(f"Conversation with ID {conversation_id} not found.")
    #     return conversation

    def send_message(self, conversation_id: int, user_message: str) -> Message:
        user_message = user_message.strip()
        if not user_message:
            logger.error("User message cannot be empty.")
            raise ValueError("User message cannot be empty.")

        conversation = self.conversation_manager.load_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation with ID {conversation_id} not found.")
            raise ValueError(f"Conversation with ID {conversation_id} not found.")

        user_message = Message(
            id=len(conversation.messages),
            content=user_message,
            type=ToolType.GENERAL,
            role=ChatRole.USER,
            created_at=datetime.now()
        )
        logger.info(f"User message: {user_message.content}")

        conversation.messages.append(user_message)
        self.conversation_manager.save_conversation(conversation)

        conversation_messages = [
            {
                "role": message.role.value,
                "content": message.content
            }
            for message in conversation.messages
        ]
        
        logger.info(f"Sending message to LLM: {conversation_messages}")
        
        # Call the LLM API
        response = completion(
            model=self.model,
            messages=conversation_messages,
            temperature=0.5,
        )

        # Extract the model response
        model_response = response.choices[0].message.content
        model_response = model_response.strip()
        model_message = Message(
            id=len(conversation.messages),
            content=model_response,
            type=ToolType.GENERAL,
            role=ChatRole.ASSISTANT,
            created_at=datetime.now()
        )
        logger.info(f"Received response from LLM: {model_response}")

        # Add model response to conversation
        conversation.messages.append(model_message)

        # Save updated conversation
        self.conversation_manager.save_conversation(conversation)

        return model_message