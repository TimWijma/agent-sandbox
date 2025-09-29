import os
import sys
import asyncio
from datetime import datetime
import textwrap
from typing import Optional

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.document import Document

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import logger
from models.chat import ChatRole, Conversation, Message, MessageType
from services.llm_service import LLMService

class CLIService:
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()
        self.original_working_dir = os.getcwd()

        self.ui_update_queue = asyncio.Queue()
        self.llm_service = LLMService(ui_callback=self._ui_update_callback)
        self.conversation_manager = self.llm_service.conversation_manager
        self.conversation: Conversation = None

        self.is_processing = False
        self.mode = "selection"
        self.input_height = 2

        self.setup_ui()

    async def _ui_update_callback(self, message: str | Message):
        await self.ui_update_queue.put(message)

    async def _process_ui_updates(self):
        while True:
            message = await self.ui_update_queue.get()
            if isinstance(message, Message):
                message = self.get_formatted_message(message)
            else:
                message = f"[Assistant]: {message}"

            self.append_to_view(f"{message}\n")
            self.ui_update_queue.task_done()

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
            if hasattr(self, "input_buffer"):
                self.app.layout.focus(self.input_buffer)

    def get_header_text(self):
        if self.mode == "conversation" and self.conversation:
            try:
                token_info = self.conversation.get_total_tokens()
                return f"AI Agent CLI - CWD: {self.working_dir} | Tokens: {token_info['total_tokens']} (In: {token_info['input_tokens']}, Out: {token_info['output_tokens']})"
            except Exception as e:
                logger.error(f"Could not get token info: {e}")
        return f"AI Agent CLI - CWD: {self.working_dir}"

    def create_layout(self):
        header_text = self.get_header_text()
        windows = [
            Window(content=FormattedTextControl(text=header_text), height=1),
            Window(content=BufferControl(buffer=self.view_buffer, focusable=True), wrap_lines=True),
        ]
        if self.mode == "conversation":
            windows.extend([
                Window(height=1, content=FormattedTextControl(lambda: "─" * get_app().output.get_size().columns)),
                Window(content=BufferControl(buffer=self.input_buffer, focusable=True), height=self.input_height, wrap_lines=True),
            ])
        self.layout = Layout(HSplit(windows))

    def setup_ui(self):
        self.input_buffer = Buffer(multiline=False)
        self.view_buffer = Buffer(read_only=True)
        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            if self.mode == "selection":
                self.handle_selection()
            elif self.mode == "conversation" and not self.is_processing:
                self.send_message_non_blocking()

        @kb.add("c-c")
        def _(event):
            event.app.exit()

        @kb.add("tab")
        def _(event):
            if self.app.layout.has_focus(self.input_buffer):
                self.app.layout.focus(self.view_buffer)
            else:
                self.app.layout.focus(self.input_buffer)

        @kb.add("s-tab")
        def _(event):
            if self.mode == "conversation":
                self.switch_mode("selection")

        @kb.add("c-d")
        def _(event):
            if self.mode == "selection":
                selected_option = self.get_selected_option()
                if selected_option and selected_option.isdigit():
                    self.conversation_manager.delete_conversation(int(selected_option))
                    self.update_selection_display()

        self.create_layout()
        self.app = Application(layout=self.layout, key_bindings=kb, full_screen=True, mouse_support=True)

        if self.mode == "selection":
            self.update_selection_display()
        elif self.mode == "conversation":
            self.update_message_display()
            self.app.layout.focus(self.input_buffer)

    def update_header(self):
        if hasattr(self, "layout") and self.layout:
            header_window = self.layout.container.children[0]
            header_window.content = FormattedTextControl(text=self.get_header_text())
            self.app.invalidate()

    def get_formatted_messages(self) -> str:
        messages = self.conversation.messages if self.conversation else []
        formatted_text = ""
        for message in messages:
            formatted_text += self.get_formatted_message(message)
        return formatted_text
    
    def get_formatted_message(self, message: Message) -> str:
        if message.role == ChatRole.USER:
            return f"[User]: {message.content}\n"
        elif message.role == ChatRole.ASSISTANT:
            if message.type == MessageType.PLAN:
                return f"[Assistant - Plan]: {message.content}\n"
            elif message.type == MessageType.TOOL:
                return f"[Assistant - Tool]: {message.content}\n"
            else:
                return f"[Assistant]: {message.content}\n"
        return f"[{message.role}]: {message.content}\n"

    def append_to_view(self, text: str):
        width = get_app().output.get_size().columns
        wrapped_text = "\n".join(textwrap.wrap(text, width=width, replace_whitespace=False, drop_whitespace=False))
        
        current_text = self.view_buffer.text
        new_text = f"{current_text}{wrapped_text}"
        self.view_buffer.set_document(Document(new_text, cursor_position=len(new_text)), bypass_readonly=True)
        self.app.invalidate()

    def update_message_display(self, load_conversation: bool = True):
        if load_conversation:
            self.conversation = self.conversation_manager.load_conversation(self.conversation.id)
        self.update_header()
        raw_text = self.get_formatted_messages()
        self.view_buffer.set_document(Document(raw_text), bypass_readonly=True)
        self.app.invalidate()

    def update_selection_display(self):
        self.conversations = self.conversation_manager.load_conversations()
        formatted_text = "Conversations:\n"
        for idx, conv in self.conversations.items():
            created_date = conv.created_at.strftime("%Y-%m-%d-%H:%M:%S")
            formatted_text += f"{idx:2}. {conv.title:<30} {created_date:>10}\n"
        formatted_text += " +. Create New Conversation"
        self.view_buffer.set_document(Document(formatted_text), bypass_readonly=True)
        self.app.invalidate()

    def get_selected_option(self) -> str:
        line_text = self.view_buffer.document.current_line
        if line_text.strip() and not line_text.startswith("Conversations:"):
            try:
                return line_text.split(".")[0].strip()
            except IndexError:
                return ""
        return ""

    def handle_selection(self):
        selected_option = self.get_selected_option()
        if selected_option == "+":
            self.create_new_conversation()
        elif selected_option.isdigit():
            self.open_conversation(int(selected_option))

    def open_conversation(self, conversation_id):
        self.conversation = self.conversation_manager.load_conversation(conversation_id)
        self.switch_mode("conversation")

    def create_new_conversation(self):
        new_conversation = self.conversation_manager.create_conversation()
        self.open_conversation(new_conversation.id)

    async def send_message_async(self):
        message = self.input_buffer.text.strip()
        if message:
            self.is_processing = True
            self.input_buffer.text = ""
            self.append_to_view(f"[User]: {message}\n")
            try:
                await self.llm_service.process_user_request(self.conversation.id, message)
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                self.append_to_view(f"[Error]: {e}\n")
            finally:
                self.is_processing = False
                self.update_header() # Refresh token count

    def send_message_non_blocking(self):
        if not self.is_processing:
            asyncio.create_task(self.send_message_async())

    async def _run_async(self):
        # Start the UI update processing task
        ui_task = asyncio.create_task(self._process_ui_updates())
        
        try:
            # Run the application
            await self.app.run_async()
        finally:
            # Clean up the UI update task
            ui_task.cancel()
            try:
                await ui_task
            except asyncio.CancelledError:
                pass

    def run(self):
        print("AI Agent CLI started. Press 'Enter' to send, 'Shift+Tab' to switch to selection mode, 'Ctrl+C' to exit.")
        asyncio.run(self._run_async())


def main():
    working_dir = os.getcwd()
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
                chat_app.open_conversation(int(sys.argv[1]))
        chat_app.run()
    except KeyboardInterrupt:
        print("\nExiting AI Agent CLI.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()