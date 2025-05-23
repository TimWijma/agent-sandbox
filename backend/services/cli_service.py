import os
from datetime import datetime
from typing import Optional
from models.tools import ToolType
from services.llm_service import LLMService
from services.tool_manager import ToolManager
from services.conversation_manager import ConversationManager
from dotenv import load_dotenv
from models.chat import ChatRequest, Message, ChatRole, Conversation

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
    'assitant': '#00AAAA',
    'system': '#FF0000',
    'input-field': 'bg:#1a1a1a #ffffff',
    'history-text': '#bbbbbb',
    'scrollbar': 'bg:#555555 #888888', # This style key is for the overall app style, not directly for ScrollbarMargin
})

# --- Interactive List Selector ---
def interactive_list_selector(items: list[tuple[str, any]], title: str = "Select an item") -> Optional[any]:
    """
    Presents an interactive list to the user, allowing selection with arrow keys.
    Returns the value of the selected item or None if cancelled.
    """
    if not items:
        print(f"No items to display for '{title}'.")
        return None

    selected_index = 0
    
    # Create a buffer to hold the selected index, so it can be updated by key bindings
    selected_index_buffer = Buffer(name='selected_index')
    selected_index_buffer.text = str(selected_index)

    def get_list_content():
        """Generates the formatted text for the list display."""
        lines = []
        for i, (display_text, _) in enumerate(items):
            escaped_text = html.escape(display_text) # Escape HTML special characters
            if i == int(selected_index_buffer.text):
                lines.append(f'<selected>> {escaped_text}</selected>')
            else:
                lines.append(f'<unselected>  {escaped_text}</unselected>')
        return HTML('\n'.join(lines)) # Corrected: Wrap the entire joined string in HTML()

    kb = KeyBindings()

    @kb.add('up')
    def _(event):
        current_index = int(selected_index_buffer.text)
        new_index = max(0, current_index - 1)
        selected_index_buffer.text = str(new_index)

    @kb.add('down')
    def _(event):
        current_index = int(selected_index_buffer.text)
        new_index = min(len(items) - 1, current_index + 1)
        selected_index_buffer.text = str(new_index)

    @kb.add('enter')
    def _(event):
        event.app.exit(result=items[int(selected_index_buffer.text)][1]) # Return the value

    @kb.add('c-c') # Ctrl+C to exit
    @kb.add('q')   # 'q' to exit
    def _(event):
        event.app.exit(result=None) # Return None on cancel

    layout = Layout(
        container=HSplit([
            Window(FormattedTextControl(HTML(f'<header>{title}</header>')), height=D.exact(1)),
            Window(FormattedTextControl(get_list_content),
                   wrap_lines=True,
                   right_margins=[ScrollbarMargin(display_arrows=True)],
                   ) if items else Window(FormattedTextControl(HTML("<unselected>No items to display.</unselected>"))), # Handle empty list
            Window(FormattedTextControl(HTML('<footer>Use <unselected>↑↓</unselected> to navigate, <selected>Enter</selected> to select, <system>Q/Ctrl+C</system> to quit.</footer>')), height=D.exact(1)),
        ]),
        focused_element=None # No specific element needs focus initially
    )

    app = Application(layout=layout, key_bindings=kb, style=style, full_screen=True)
    result = app.run()
    return result

# --- CLI Commands ---

def create_new_conversation_command():
    """CLI command to create a new conversation."""
    conversation = conversation_manager.create_conversation()
    print(f"Created new conversation: ID {conversation.id}, Title: '{conversation.title}'")
    return conversation

def list_conversations_command():
    """CLI command to list all available conversations interactively."""
    conversations = conversation_manager.load_all_conversations()
    if not conversations:
        print("No conversations found.")
        return

    # Prepare items for the interactive selector
    items = []
    sorted_conversations = sorted(conversations.values(), key=lambda c: c.id)
    for conv in sorted_conversations:
        display_text = f"ID: {conv.id:<5} Title: '{conv.title}' (Messages: {len(conv.messages)}, Last Updated: {conv.updated_at.strftime('%Y-%m-%d %H:%M')})"
        items.append((display_text, conv.id)) # (display_text, value_to_return)

    selected_conv_id = interactive_list_selector(items, title="Select a Conversation to Open")

    if selected_conv_id is not None:
        print(f"Opening conversation ID: {selected_conv_id}...")
        open_chat_command(selected_conv_id)
    else:
        print("Conversation selection cancelled.")


def open_chat_command(conversation_id: int):
    """CLI command to open an interactive chat session for a given conversation ID."""
    conversation = conversation_manager.load_conversation(conversation_id)
    if not conversation:
        print(f"Error: Conversation with ID {conversation_id} not found.")
        return

    # --- Chat UI elements ---
    input_buffer = Buffer(name='input_buffer', multiline=False)

    def get_formatted_chat_history():
        """Updates the history buffer with formatted messages."""
        lines = []
        for msg in conversation.messages:
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            escaped_content = html.escape(msg.content)
            if msg.role == ChatRole.USER:
                lines.append(f'<user>[{time_str}] You: {escaped_content}</user>')
            elif msg.role == ChatRole.ASSISTANT:
                lines.append(f'<assistant>[{time_str}] Assistant: {escaped_content}</assistant>')
            else: # For other roles like TOOL
                lines.append(f'<system>[{time_str}] {msg.role.value.upper()}: {escaped_content}</system>')
        # history_buffer.text = HTML('\n'.join(lines))
        # # Scroll to bottom if history is updated
        # history_buffer.cursor_position = len(history_buffer.text) # Move cursor to end to scroll
        return HTML('\n'.join(lines))

    # Initial history display
    get_formatted_chat_history() # Call to get formatted chat history

    kb = KeyBindings()

    @kb.add('enter')
    def _(event):
        """Handle Enter key: process message."""
        user_input = input_buffer.text.strip()
        input_buffer.text = '' # Clear input field

        if not user_input:
            # Don't process empty messages, just redraw
            return

        event.app.invalidate() # Invalidate the app to refresh the display

        # Process LLM response in a non-blocking way (or in a separate thread if complex)
        # For simplicity, we'll do it synchronously here, but in a real app,
        # you'd show a "typing..." indicator and do this async.
        try:
            llm.send_message(conversation.id, user_input)
        except Exception as e:
            print_formatted_text(HTML(f'<system>An error occurred: {e}</system>'))
        finally:
            event.app.invalidate() # Invalidate the app to refresh the display

    @kb.add('c-c') # Ctrl+C to exit
    @kb.add('q')   # 'q' to exit
    def _(event):
        event.app.exit() # Exit the application

    layout = Layout(
        container=HSplit([
            # Header
            Window(FormattedTextControl(HTML(f'<header>Chat: {conversation.title} (ID: {conversation.id})</header>')), height=D.exact(1)),
            # History display area
            Window(FormattedTextControl(get_formatted_chat_history), 
                   wrap_lines=True, 
                   height=D.exact(os.get_terminal_size().lines - 5), # Adjust height dynamically
                   right_margins=[ScrollbarMargin(display_arrows=True)],
                   always_hide_cursor=True # Hide cursor in history window
                   ),
            # Input field
            Window(FormattedTextControl(HTML('<input-field>You: </input-field>')), height=D.exact(1), dont_extend_width=True),
            Window(BufferControl(buffer=input_buffer), height=D.exact(1), style='class:input-field'),
            # Window(FormattedTextControl(HTML('<input-field>You: </input-field>')), height=D.exact(1), dont_extend_width=True),
            # Window(BufferControl(buffer=input_buffer), height=D.exact(1), style='input-field'),
            # Footer
            Window(FormattedTextControl(HTML('<footer>Type message and <selected>Enter</selected>, <system>Q/Ctrl+C</system> to quit.</footer>')), height=D.exact(1)),
        ]),
        focused_element=input_buffer # Focus on the input field
    )

    app = Application(layout=layout, key_bindings=kb, style=style, full_screen=True)
    app.run()
    print(f"Exiting chat for conversation ID {conversation.id}.")


def delete_conversation_command(conversation_id: int):
    """CLI command to delete a conversation by its ID."""
    if conversation_manager.delete_conversation(conversation_id):
        print(f"Conversation with ID {conversation_id} deleted successfully.")
    else:
        print(f"Error: Conversation with ID {conversation_id} not found.")

def main():
    parser = argparse.ArgumentParser(
        description="LLM Agent CLI for managing conversations.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # 'new' command
    new_parser = subparsers.add_parser("new", help="Create a new conversation.")
    new_parser.set_defaults(func=create_new_conversation_command)

    # 'list' command
    list_parser = subparsers.add_parser("list", help="List all conversations interactively and open selected.")
    list_parser.set_defaults(func=list_conversations_command)

    # 'open' command
    open_parser = subparsers.add_parser("open", help="Open an existing conversation for interactive chat.")
    open_parser.add_argument("id", type=int, help="The ID of the conversation to open.")
    open_parser.set_defaults(func=open_chat_command)

    # 'delete' command
    delete_parser = subparsers.add_parser("delete", help="Delete a conversation.")
    delete_parser.add_argument("id", type=int, help="The ID of the conversation to delete.")
    delete_parser.set_defaults(func=delete_conversation_command)

    args = parser.parse_args()
    
    # Call the function associated with the chosen subcommand
    if args.command == "open" or args.command == "delete":
        args.func(args.id)
    else:
        args.func()

if __name__ == "__main__":
    main()
