import os
import json
import pkg_resources
from typing import Optional
from models.chat import Conversation, Message, ToolType, ChatRole
from datetime import datetime
from logger import logger

class ConversationManager:
    def __init__(self):
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_file_dir)

        try:
            self.CONVERSATION_DIR = os.path.join(project_root, "conversations")
        except Exception as e:
            logger.error(f"Failed to set conversation directory: {e}")
            self.CONVERSATION_DIR = "conversations"

        self._create_conversation_dir()
        
        try:
            self.system_message_path = os.path.join(project_root, "prompts", "system_message.txt")
        except Exception as e:
            logger.error(f"Failed to set system message path: {e}")
            self.system_message_path = "prompts/system_message.txt"

        
        self.system_message = None

    def _load_system_message(self):
        if not os.path.exists(self.system_message_path):
            raise ValueError(f"System message file not found at {self.system_message_path}.")
        if not os.path.isfile(self.system_message_path):
            raise ValueError(f"System message path is not a file: {self.system_message_path}.")
        
        with open(self.system_message_path, "r") as file:
            self.system_message = file.read().strip()
        
        if not self.system_message:
            raise ValueError("System message is empty.")

    def _create_conversation_dir(self):
        os.makedirs(self.CONVERSATION_DIR, exist_ok=True)

    def _get_conversation_file_path(self, conversation_id: int) -> str:
        return os.path.join(self.CONVERSATION_DIR, f"conversation_{conversation_id}.json")
    
    def load_conversations(self) -> dict[int, Conversation]:
        conversations: dict[Conversation] = {}
        for filename in os.listdir(self.CONVERSATION_DIR):
            if filename.startswith("conversation_") and filename.endswith(".json"):
                try:
                    conversation_id_str = filename.replace("conversation_", "").replace(".json", "")
                    conversation_id = int(conversation_id_str)

                    file_path = self._get_conversation_file_path(conversation_id)
                    with open(file_path, "r") as file:
                        conversation_data = json.load(file)
                        conversation = Conversation.model_validate(conversation_data)
                        conversations[conversation_id] = conversation
                        
                except (ValueError, json.JSONDecodeError) as e:
                    logger.error(f"Error loading conversation from {filename}: {e}")

        conversations = dict(sorted(conversations.items(), key=lambda item: item[0]))
        logger.info(f"Loaded {len(conversations)} conversations.")

        return conversations

    def load_conversation(self, conversation_id: int) -> Optional[Conversation]:
        file_path = self._get_conversation_file_path(conversation_id)
        if not os.path.exists(file_path):
            logger.info(f"Conversation file {file_path} does not exist.")
            return None
        try:
            with open(file_path, "r") as file:
                conversation_data = json.load(file)
                conversation = Conversation.model_validate(conversation_data)
                
                return conversation
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error loading conversation from {file_path}: {e}")
            return None

    def create_conversation(self) -> Conversation:
        if not self.system_message:
            self._load_system_message()

        conversation_id = self.get_next_conversation_id()

        system_message = Message(
            id=0,
            content=self.system_message,
            type=ToolType.GENERAL,
            role=ChatRole.SYSTEM,
            created_at=datetime.now(),
            input_tokens=0,
            output_tokens=0
        )

        conversation = Conversation(
            id=conversation_id,
            title=f"New Conversation {conversation_id}",
            messages=[system_message],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        self.save_conversation(conversation)
        return conversation

    def save_conversation(self, conversation: Conversation):
        if not conversation or not conversation.id:
            logger.info("Conversation ID is missing.")
            return
            
        file_path = self._get_conversation_file_path(conversation.id)
        try:
            with open(file_path, "w") as file:
                conversation_json = conversation.model_dump()
                conversation_json["created_at"] = conversation.created_at.isoformat()
                conversation_json["updated_at"] = conversation.updated_at.isoformat()
                for message in conversation_json["messages"]:
                    message["created_at"] = message["created_at"].isoformat()
                json.dump(conversation_json, file, indent=4)
                logger.info(f"Conversation {conversation.id} saved to {file_path}.")
        except IOError as e:
            logger.error(f"Error saving conversation to {file_path}: {e}")

    def delete_conversation(self, conversation_id: int) -> bool:
        file_path = self._get_conversation_file_path(conversation_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Conversation {conversation_id} deleted.")
            return True
        else:
            logger.info(f"Conversation file {file_path} does not exist.")
            return False
        
    def get_next_conversation_id(self) -> int:
        existing_files = [f for f in os.listdir(self.CONVERSATION_DIR) if f.startswith("conversation_") and f.endswith(".json")]
        if not existing_files:
            return 1
        else:
            existing_ids = [int(f.replace("conversation_", "").replace(".json", "")) for f in existing_files]
            return max(existing_ids) + 1