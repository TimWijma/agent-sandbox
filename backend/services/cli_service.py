import os
import sys
import asyncio
from datetime import datetime
from typing import Optional

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.document import Document

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import logger
from models.chat import ChatRole, Conversation, Message
from services.llm_service import LLMService

class CLIService:
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()
        self.original_working_dir = os.getcwd()

        self.llm_service = LLMService()
        self.conversation_manager = self.llm_service.conversation_manager
        self.conversation: Conversation = None

        self.pending_response: Optional[asyncio.Task] = None
        self.is_waiting_for_response = False
        
        self.mode = "selection"

        self.setup_ui()
        
    def switch_mode(self, mode: str):
        if mode not in ["selection", "conversation"]:
            raise ValueError("Invalid mode. Use 'selection' or 'conversation'.")

        self.mode = mode
        self.create_layout()
        self.app.layout = self.layout
        
        if self.mode == "selection":
            self.update_selection_display()
            self.app.layout.focus(self.view_buffer)
        elif self.mode == "conversation":
            self.update_message_display()
            if hasattr(self, 'input_buffer'):
                self.app.layout.focus(self.input_buffer)

    def create_layout(self):
        windows = [
            Window(
                content=FormattedTextControl(text=f"AI Agent CLI - CWD: {self.working_dir}"),
                height=1,
            ),
            Window(
                content=BufferControl(
                    buffer=self.view_buffer,
                    focusable=True
                ),
                wrap_lines=True,
            ),            
        ]
        
        if self.mode == "conversation":
            windows.extend([
                Window(height=1, content=FormattedTextControl(text="─" * 50)),
                Window(
                    content=BufferControl(buffer=self.input_buffer, focusable=True),
                    height=1,
                    wrap_lines=True,
                ),
            ])

        self.layout = Layout(HSplit(windows))
        
    def setup_ui(self):
        self.input_buffer = Buffer(multiline=False)
        self.view_buffer = Buffer(read_only=True)
        
        kb = KeyBindings()
        
        @kb.add('enter')
        def handle_enter(event):
            if self.mode == "selection":
                self.handle_selection()
            elif self.mode == "conversation":
                self.send_message_non_blocking()
                
        @kb.add('c-c')
        def exit_app(event):
            event.app.exit()
        
        # Switch focus between input and message buffer
        @kb.add('tab')
        def switch_focus(event):
            if event.app.layout.has_focus(self.input_buffer):
                event.app.layout.focus(self.view_buffer)
            else:
                event.app.layout.focus(self.input_buffer)

        @kb.add('s-tab')
        def toggle_mode(event):
            if self.mode == "conversation":
                self.switch_mode("selection")
                
        @kb.add('c-d')
        def delete_conversation(event):
            if self.mode == "selection":
                selected_option = self.get_selected_option()
                if selected_option and selected_option.isdigit():
                    conversation_id = int(selected_option)
                    self.conversation_manager.delete_conversation(conversation_id)
                    logger.info(f"Deleted conversation {conversation_id}")
                    self.update_selection_display()

        self.create_layout()

        self.app = Application(
            layout=self.layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,
        )
        print("AI Agent CLI started. Press 'Tab' to switch modes, 'Enter' to select or send messages, and 'Ctrl+C' to exit.")
        
        if self.mode == "selection":
            self.update_selection_display()
        elif self.mode == "conversation":
            self.update_message_display()
            self.app.layout.focus(self.input_buffer)
        
    def get_formatted_messages(self) -> str:
        messages = self.conversation.messages if self.conversation else []
        formatted_text = ""
        for message in messages:
            role = message.role
            content = message.content
            
            if role == ChatRole.USER:
                formatted_text += f"[User]: {content}\n"
            elif role == ChatRole.ASSISTANT:
                formatted_text += f"[Assistant]: {content}\n"

        return formatted_text

    def update_message_display(self, load_conversation: bool = True):
        if load_conversation:
            self.conversation = self.conversation_manager.load_conversation(self.conversation.id)

        logger.info("Updating message display")
        logger.debug(self.get_formatted_messages())
        self.view_buffer.set_document(
            Document(self.get_formatted_messages()),
            bypass_readonly=True
        )
        
        self.app.invalidate()
        
    def update_selection_display(self):
        self.conversations = self.conversation_manager.load_conversations()
        
        formatted_text = "Conversations:\n"
        for idx, conv in self.conversations.items():
            formatted_text += f"{idx}. {conv.title} (Created: {conv.created_at})\n"

        formatted_text += "+. New Conversation"
    
        self.view_buffer.set_document(
            Document(formatted_text),
            bypass_readonly=True
        )
        
        self.app.invalidate()

    def get_selected_option(self) -> str:
        line_text = self.get_current_line_text()
        
        if line_text.strip() and not line_text.startswith("Conversations:"):
            try:
                selected_option = line_text.split('.')[0].strip()
                return selected_option
            except IndexError:
                logger.error(f"Invalid selection: {line_text}")
                return ""

    def handle_selection(self):
        selected_option = self.get_selected_option()

        if selected_option == '+':
            self.create_new_conversation()
        else:
            selected_id = int(selected_option)
            if selected_id in self.conversations:
                logger.info(f"Selected conversation: {selected_id}")
                self.open_conversation(selected_id)
            else:
                logger.error(f"Invalid selection: {selected_option}")
                return

    def open_conversation(self, conversation_id):
        """Open an existing conversation by ID"""
        self.conversation = self.conversation_manager.load_conversation(conversation_id)
        self.switch_mode("conversation")
        logger.info(f"Opened conversation {conversation_id}")

    def create_new_conversation(self):
        """Create a new conversation and switch to conversation mode"""
        new_conversation = self.conversation_manager.create_conversation()
        new_conversation_id = new_conversation.id
        
        self.open_conversation(new_conversation_id)
        logger.info(f"Created new conversation {new_conversation_id}")

    async def send_message_async(self):
        message = self.input_buffer.text.strip()
        if message:
            save_message = message
            
            self.conversation.messages.append(Message(
                id=len(self.conversation.messages),
                content=message,
                type="general",
                role=ChatRole.USER,
                created_at=datetime.now()
            ))
            
            self.input_buffer.text = ""
            self.update_message_display(load_conversation=False)
            self.is_waiting_for_response = True

            try:
                self.pending_response = asyncio.create_task(
                    self.llm_service.send_message(self.conversation.id, message)
                )
                
                await self.pending_response
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                self.input_buffer.text = save_message
                return
            finally:
                self.is_waiting_for_response = False
                self.pending_response = None
                self.update_message_display()


    def send_message_non_blocking(self):
        """Non-blocking wrapper that can be called from synchronous code"""
        if not self.is_waiting_for_response:
            # Create new event loop if one doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Schedule the async function
            asyncio.create_task(self.send_message_async())


    def get_current_line_text(self) -> str:
        """Get the text of the line where the cursor is currently positioned"""
        document = self.view_buffer.document
        return document.current_line

    def run(self):
        self.app.run()


def main():
    working_dir = os.getcwd()
    
    if not os.path.exists(working_dir):
        logger.error(f"Working directory does not exist: {working_dir}")
        sys.exit(1)
        
    if not os.path.isdir(working_dir):
        logger.error(f"Working directory is not a directory: {working_dir}")
        sys.exit(1)
        
    print(f"Starting AI Agent CLI in directory: {working_dir}")
    
    try:
        chat_app = CLIService(working_dir)

        if len(sys.argv) > 1:
            if sys.argv[1] == "new":
                chat_app.create_new_conversation()
            elif sys.argv[1].isdigit():
                conversation_id = int(sys.argv[1])
                chat_app.open_conversation(conversation_id)

        chat_app.run()
    except KeyboardInterrupt:
        print("\nExiting AI Agent CLI.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()