import os
from logger import logger
from litellm import completion
from dotenv import load_dotenv
from services.conversation_manager import ConversationManager
from services.tool_manager import ToolManager
from models.chat import ChatRole, Message, ToolType
from datetime import datetime
import asyncio


class LLMService:
    def __init__(self, model: str = "gemini/gemini-2.0-flash"):
        load_dotenv()

        self.API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.API_KEY:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")
        os.environ["GEMINI_API_KEY"] = self.API_KEY

        self.model = model

        self.conversation_manager = ConversationManager()
        self.tool_manager = ToolManager()

    async def send_message(self, conversation_id: int, user_message: str) -> Message:
        user_message = user_message.strip()
        if not user_message:
            logger.error("User message cannot be empty.")
            raise ValueError("User message cannot be empty.")

        conversation = self.conversation_manager.load_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation with ID {conversation_id} not found.")
            raise ValueError(f"Conversation with ID {conversation_id} not found.")

        if user_message.lower() in ['y', 'yes', 'n', 'no']:
            return await self.handle_confirmation(conversation_id, user_message.lower(), conversation)

        user_message_obj = Message(
            id=len(conversation.messages),
            content=user_message,
            type=ToolType.GENERAL,
            role=ChatRole.USER,
            created_at=datetime.now()
        )
        logger.info(f"User message: {user_message_obj.content}")

        conversation.messages.append(user_message_obj)
        self.conversation_manager.save_conversation(conversation)

        conversation_messages = [
            {
                "role": message.role.value,
                "content": message.content if message.type == ToolType.GENERAL else message.original_message
            }
            for message in conversation.messages
            if not message.pending_confirmation
        ]
        
        logger.info(f"Sending message to LLM: {conversation_messages}")
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: completion(
                model=self.model,
                messages=conversation_messages,
                temperature=0.5,
            )
        )

        # Extract the model response
        model_response = response.choices[0].message.content
        model_response = model_response.strip()
        
        tool_type, tool_input = self.tool_manager.handle_message(model_response)
        if tool_type != ToolType.GENERAL:
            logger.info(f"Executing tool: {tool_type} with input: {tool_input}")
            tool_output, needs_confirmation = self.tool_manager.execute_tool(tool_type, tool_input)
            
            if needs_confirmation:
                self.tool_manager.store_pending_confirmation(str(conversation_id), tool_type, tool_input)
                message_content = tool_output
                pending_confirmation = True
            else:
                logger.info(f"Tool response: {tool_output}")
                message_content = f"Tool '{tool_type.value}' executed with result: {tool_output}"
                pending_confirmation = False
        else:
            message_content = model_response
            pending_confirmation = False
        
        model_message = Message(
            id=len(conversation.messages),
            content=message_content,
            type=tool_type,
            role=ChatRole.ASSISTANT,
            created_at=datetime.now(),
            original_message=model_response if tool_type != ToolType.GENERAL else None,
            pending_confirmation=pending_confirmation
        )
        logger.info(f"Received response from LLM: {model_response}")

        # Add model response to conversation
        conversation.messages.append(model_message)

        # Save updated conversation
        self.conversation_manager.save_conversation(conversation)

        return model_message

    async def handle_confirmation(self, conversation_id: int, response: str, conversation) -> Message:
        """Handle user confirmation for pending tool execution"""
        pending = self.tool_manager.get_pending_confirmation(str(conversation_id))
        
        if not pending:
            # No pending confirmation, treat as regular message
            return await self.send_message(conversation_id, response)
        
        tool_type, tool_input = pending
        
        # Find the pending confirmation message
        pending_message = None
        for message in reversed(conversation.messages):
            if message.pending_confirmation and message.type == tool_type:
                pending_message = message
                break
        
        if not pending_message:
            logger.error("Could not find pending confirmation message")
            # Fallback to old behavior
            return await self.send_message(conversation_id, response)
        
        if response in ['y', 'yes']:
            # User confirmed, execute the tool
            logger.info(f"User confirmed execution of {tool_type} tool")
            tool_output, _ = self.tool_manager.execute_tool(tool_type, tool_input, confirmed=True)
            message_content = f"Tool '{tool_type.value}' executed with result: {tool_output}"
            confirmed = True
        else:
            # User declined
            logger.info(f"User declined execution of {tool_type} tool")
            message_content = f"Tool '{tool_type.value}' execution cancelled by user."
            confirmed = False
        
        # Update the pending message with the result
        pending_message.content = message_content
        pending_message.pending_confirmation = False
        pending_message.confirmed = confirmed
        
        self.conversation_manager.save_conversation(conversation)
        
        return pending_message