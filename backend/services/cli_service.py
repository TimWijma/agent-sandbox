from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.document import Document
from datetime import datetime

from models.chat import Conversation
from logger import logger
from services.llm_service import LLMService

class CLIService:
    def __init__(self):
        self.llm_service = LLMService()
        self.conversation: Conversation = None
        self.messages = []
        
        self.mode = "selection"
        
        self.load_conversations()
        self.setup_ui()
        
    def switch_mode(self, mode: str):
        if mode not in ["selection", "conversation"]:
            raise ValueError("Invalid mode. Use 'selection' or 'conversation'.")

        self.mode = mode
        self.create_layout()
        self.app.layout = self.layout
        
        if self.mode == "selection":
            self.update_selection_display()
        elif self.mode == "conversation":
            self.update_message_display()
            if hasattr(self, 'input_buffer'):
                self.app.layout.focus(self.input_buffer)

    def load_conversations(self):
        self.conversations = self.llm_service.load_conversations()
        
    def create_layout(self):
        windows = [
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
                line_text = self.get_current_line_text()
                
                if line_text.strip() and not line_text.startswith("Conversations:"):
                    try:
                        first_char = line_text.strip('.')[0].strip()
                        if first_char == '+':
                            self.create_new_conversation()
                        else:
                            selected_index = int(first_char)
                            if selected_index in self.conversations:
                                logger.info(f"Selected conversation: {selected_index}")
                                self.open_conversation(selected_index)
                            else:
                                logger.error(f"Invalid selection: {line_text}")
                                return
                    except (ValueError, IndexError):
                        logger.error(f"Invalid selection: {line_text}")
                        return
                
            elif self.mode == "conversation":
                message = self.input_buffer.text.strip()
                if message:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.messages.append(f"[{timestamp}] You: {message}")
                    self.input_buffer.text = ""
                    self.update_message_display()
                
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

        self.create_layout()

        self.app = Application(
            layout=self.layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,
        )
        
        if self.mode == "selection":
            self.update_selection_display()
        elif self.mode == "conversation":
            self.update_message_display()
            self.app.layout.focus(self.input_buffer)
        
    def get_formatted_messages(self):
        formatted_text = "\n".join(self.messages)
        return formatted_text

    def update_message_display(self):
        logger.info("Updating message display")
        self.view_buffer.set_document(
            Document(self.get_formatted_messages()),
            bypass_readonly=True
        )
        
        self.app.invalidate()
        
    def update_selection_display(self):
        formatted_text = "Conversations:\n"
        for idx, conv in self.conversations.items():
            formatted_text += f"{idx}. {conv.title} (Created: {conv.created_at})\n"

        formatted_text += "+. New Conversation"
    
        self.view_buffer.set_document(
            Document(formatted_text),
            bypass_readonly=True
        )
        
        self.app.invalidate()

    def open_conversation(self, conversation_id):
        """Open an existing conversation by ID"""
        self.conversation = self.llm_service.load_conversation(conversation_id)
        self.messages = [message.content for message in self.conversation.messages]
        self.switch_mode("conversation")
        logger.info(f"Opened conversation {conversation_id}")

    def create_new_conversation(self):
        """Create a new conversation and switch to conversation mode"""
        new_conversation = self.llm_service.create_conversation()
        new_conversation_id = new_conversation.id
        
        self.open_conversation(new_conversation_id)
        logger.info(f"Created new conversation {new_conversation_id}")

    def get_current_line_text(self):
        """Get the text of the line where the cursor is currently positioned"""
        document = self.view_buffer.document
        return document.current_line

    def run(self):
        self.app.run()

if __name__ == "__main__":
    chat_app = CLIService()
    chat_app.run()