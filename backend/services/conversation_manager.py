import os
import json
from typing import Optional
from models.chat import Conversation

class ConversationManager:
    def __init__(self):
        self.CONVERSATION_DIR = "conversations"

        self._create_conversation_dir()

    def _create_conversation_dir(self):
        os.makedirs(self.CONVERSATION_DIR, exist_ok=True)

    def _get_conversation_file_path(self, conversation_id: int) -> str:
        return os.path.join(self.CONVERSATION_DIR, f"conversation_{conversation_id}.json")
    
    def load_all_conversations(self):
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
                    print(f"Error loading conversation from {filename}: {e}")
        return conversations

    def load_conversation(self, conversation_id: int) -> Optional[Conversation]:
        file_path = self._get_conversation_file_path(conversation_id)
        if not os.path.exists(file_path):
            print(f"Conversation file {file_path} does not exist.")
            return None
        try:
            with open(file_path, "r") as file:
                conversation_data = json.load(file)
                conversation = Conversation.model_validate(conversation_data)
                return conversation
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error loading conversation from {file_path}: {e}")
            return None

    def save_conversation(self, conversation: Conversation):
        if not conversation or not conversation.id:
            print("Conversation ID is missing.")
            return
            
        file_path = self._get_conversation_file_path(conversation.id)
        try:
            with open(file_path, "w") as file:
                conversation_json = conversation.model_dump()
                json.dump(conversation_json, file, indent=4)
        except IOError as e:
            print(f"Error saving conversation to {file_path}: {e}")

    def delete_conversation(self, conversation_id: int) -> bool:
        file_path = self._get_conversation_file_path(conversation_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Conversation {conversation_id} deleted.")
            return True
        else:
            print(f"Conversation file {file_path} does not exist.")
            return False
        
    def get_next_conversation_id(self) -> int:
        existing_files = [f for f in os.listdir(self.CONVERSATION_DIR) if f.startswith("conversation_") and f.endswith(".json")]
        if not existing_files:
            return 1
        else:
            existing_ids = [int(f.replace("conversation_", "").replace(".json", "")) for f in existing_files]
            return max(existing_ids) + 1