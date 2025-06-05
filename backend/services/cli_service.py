#!/usr/bin/env python3
"""
Simple CLI Chat Application using prompt_toolkit 3.0.51
"""

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.document import Document
from datetime import datetime
import asyncio

from services.conversation_manager import ConversationManager


class CLIService:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.conversation = self.conversation_manager.load_conversation(1)
        
        self.messages = [message.content for message in self.conversation.messages]
        
        self.setup_ui()
        
    def setup_ui(self):
        self.input_buffer = Buffer(multiline=False)

        self.message_buffer = Buffer(read_only=True)
        
        kb = KeyBindings()
        
        @kb.add('enter')
        def send_message(event):
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
                event.app.layout.focus(self.message_buffer)
            else:
                event.app.layout.focus(self.input_buffer)
                
        self.layout = Layout(
            HSplit([
                Window(
                    content=BufferControl(
                        buffer=self.message_buffer,
                        focusable=True
                    ),
                    wrap_lines=True,
                ),
                Window(height=1, content=FormattedTextControl(text="─" * 50)),
                Window(
                    content=BufferControl(buffer=self.input_buffer, focusable=True),
                    height=1,
                    wrap_lines=True,
                ),
                Window(
                    height=1,
                    content=FormattedTextControl(
                        text="Type your message and press Enter to send. Ctrl+C to exit."
                    )
                ),
            ])
        )
        
        self.app = Application(
            layout=self.layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,
        )

        self.update_message_display()
        self.app.layout.focus(self.input_buffer)
    
    def get_formatted_messages(self):
        formatted_text = "\n".join(self.messages)
        return formatted_text

    def update_message_display(self):
        self.message_buffer.set_document(
            Document(self.get_formatted_messages()),
            bypass_readonly=True
        )
        
        self.app.invalidate()
    
    def run(self):
        print("Starting CLI Chat Application...")
        print("Use Ctrl+C to exit")
        self.app.run()

if __name__ == "__main__":
    chat_app = CLIService()
    chat_app.run()