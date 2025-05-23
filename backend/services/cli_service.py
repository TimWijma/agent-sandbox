import os
from dotenv import load_dotenv
from logger import logger
from datetime import datetime
from typing import Optional
from models.tools import ToolType
from models.chat import ChatRequest, Message, ChatRole, Conversation
from services.llm_service import LLMService
from services.tool_manager import ToolManager
from services.conversation_manager import ConversationManager

import argparse
import html

from prompt_toolkit import Application, HTML, print_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window, VSplit, HSplit, Container
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.margins import ScrollbarMargin

load_dotenv()

llm = LLMService()
tool_manager = ToolManager()
conversation_manager = ConversationManager()

style = Style.from_dict({
    'selected': 'bg:#336699 #ffffff',
    'unselected': 'bg:#222222 #cccccc',
    'header': 'bg:#444444 #ffffff bold',
    'footer': 'bg:#444444 #ffffff italic',
    'user': '#00AA00',
    'assistant': '#00AAAA',
    'system': '#FF0000',
    'input-field': 'bg:#1a1a1a #ffffff',
    'history-text': '#bbbbbb',
    'scrollbar': 'bg:#555555 #888888', # This style key is for the overall app style, not directly for ScrollbarMargin
})

def open_chat_command(conversation_id: int):
    logger.info(f"Opening conversation {conversation_id}")
    conversation = conversation_manager.load_conversation(conversation_id)
    
    history_buffer = Buffer(name='history', multiline=True)

    def populate_history():
        lines = []
        for msg in filter(lambda m: m.role != ChatRole.SYSTEM, conversation.messages):
            if msg.role == ChatRole.USER:
                lines.append(f"[{msg.created_at}] <User>: {msg.content}")
            elif msg.role == ChatRole.ASSISTANT:
                lines.append(f"[{msg.created_at}] <Assistant>: {msg.content}")
            elif msg.role == ChatRole.SYSTEM:
                lines.append(f"[{msg.created_at}] <System>: {msg.content}")

        history_buffer.text = "\n".join(lines)
        history_buffer.cursor_position = len(history_buffer.text)
        
    populate_history()
    
    kb = KeyBindings()
    @kb.add('c-c')
    @kb.add('q')
    def _(event):
        logger.info("Exiting application")
        event.app.exit()
        
    @kb.add('enter')
    def _(event):
        conversation = conversation_manager.load_conversation(conversation_id)
        populate_history()
        logger.info(f"Redrawing history for conversation {conversation_id}")
        event.app.invalidate()
        
    history_height = D.exact(os.get_terminal_size().lines - 3)

    layout = Layout(
        container = HSplit([
            Window(
                content=FormattedTextControl(HTML(f'<header>Chat: {conversation.title} (ID: {conversation.id})</header>')),
                height=D.exact(1),
                style='class:header', # Apply the defined 'header' style class
            ),
            Window(
                content=BufferControl(buffer=history_buffer), # Display the content of history_buffer
                wrap_lines=True, # Wrap long lines
                height=history_height,
                # Scrollbar is a margin, not part of the content style
                right_margins=[ScrollbarMargin(display_arrows=True)],
                always_hide_cursor=True, # Hide cursor in history window
            ),
            Window(
                content=FormattedTextControl(HTML('<footer>Press <system>Q</system> or <system>Ctrl+C</system> to quit.</footer>')),
                height=D.exact(1),
                style='class:footer', # Apply the defined 'footer' style class
            ),
        ]),
        focused_element=history_buffer, # Set the history buffer as the focused element
    )
    
    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=style,
    )
    
    try:
        app.run() # Run the prompt_toolkit application
    except EOFError:
        print_formatted_text(HTML('<system>Chat session ended unexpectedly (EOFError).</system>'))
        logger.error("Chat session ended with EOFError.")
        app.exit()
    except KeyboardInterrupt:
        print_formatted_text(HTML('<system>Chat session interrupted.</system>'))
        logger.info("Chat session interrupted by user (KeyboardInterrupt).")
        app.exit()
    finally:
        # Optional: Save conversation on exit, though llm.send_message handles it
        # conversation_manager.save_conversation(conversation)
        print_formatted_text(HTML(f'<footer-info>Exiting chat for conversation ID {conversation.id}.</footer-info>'))
        logger.info(f"Chat session for conversation {conversation_id} closed.")

 
def main():
    parser = argparse.ArgumentParser(
        description="LLM Agent CLI for managing conversations.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # 'open' command - this is our starting point
    open_parser = subparsers.add_parser("open", help="Open an existing conversation for viewing.")
    open_parser.add_argument("id", type=int, help="The ID of the conversation to open.")
    open_parser.set_defaults(func=open_chat_command)

    args = parser.parse_args()
    
    # Execute the chosen command
    if hasattr(args, 'func'):
        # Pass args.id if the function expects it (like 'open' and 'delete')
        if 'id' in args and args.id is not None:
            args.func(args.id)
        else:
            args.func()
    else:
        parser.print_help()



if __name__ == "__main__":
    main()