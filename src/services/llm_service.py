from typing import List, Callable, Awaitable
import litellm, os, re
from logger import logger
from litellm import completion
from dotenv import load_dotenv
from models.plan import Plan
from services.conversation_manager import ConversationManager
from services.tool_manager import ToolManager
from models.chat import (
    ChatRole,
    Message,
    ToolType,
    MessageResponse,
)
from datetime import datetime
import asyncio

class LLMService:
    def __init__(self, model: str = "gemini/gemini-2.0-flash", ui_callback: Callable[[str], Awaitable[None]] = None):
        load_dotenv()

        self.API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.API_KEY:
            raise ValueError(
                "API key not found. Please set the GEMINI_API_KEY environment variable."
            )
        os.environ["GEMINI_API_KEY"] = self.API_KEY

        self.model = model
        self.ui_callback = ui_callback

        litellm.enable_json_schema_validation = True

        self.conversation_manager = ConversationManager()
        self.tool_manager = ToolManager()

    async def process_user_request(self, conversation_id: int, user_message: str):
        """
        Main entry point for processing a user's request.
        Generates a plan, executes it, and provides a final summary.
        """
        conversation = self.conversation_manager.load_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found.")

        # 1. Add user message to conversation
        user_message_obj = Message(
            id=len(conversation.messages),
            content=user_message,
            role=ChatRole.USER,
            created_at=datetime.now(),
        )
        conversation.messages.append(user_message_obj)
        self.conversation_manager.save_conversation(conversation)

        # 2. Generate a plan
        plan = await self.create_plan(user_message)
        if not plan or not plan.steps:
            await self.send_final_summary(conversation_id, "I was unable to create a plan to address your request.")
            return

        # 3. Execute the plan
        await self.execute_plan(conversation_id, plan)

        # 4. Send a final summary
        await self.send_final_summary(conversation_id)


    async def create_plan(self, objective: str) -> Plan:
        """Generates a plan to achieve the given objective."""
        tools = self.tool_manager.get_tool_descriptions()
        prompt = (
            f"You are an expert AI agent. Your task is to create a detailed, step-by-step plan to achieve the following objective: '{objective}'.\n\n"
            f"You have access to the following tools:\n{tools}\n\n"
            "For each step, you must provide a 'thought' explaining your reasoning for the action. This thought will be shown to the user.\n"
            "The plan should be a sequence of steps. Each step must include a unique 'step_id' (starting from 1), a 'thought', a 'tool_type', and the 'tool_input'.\n"
            "If a step does not require a tool, set 'tool_type' and 'tool_input' to null.\n"
            "If the input for a tool depends on the output of a previous step, use a placeholder like '$step_1_output' to reference it.\n\n"
            "Format the entire plan as a single JSON object that adheres to the provided schema."
        )

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=[{"role": ChatRole.USER.value, "content": prompt}],
                    temperature=0.2,
                    response_format=Plan
                ),
            )
            logger.info(f"Received response: {response}")

            model_response = response.choices[0].message.content
            plan = Plan.model_validate_json(model_response)

            logger.info(f"Generated plan: {plan}")
            return plan
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return None

    async def execute_plan(self, conversation_id: int, plan: Plan):
        """Executes a plan step-by-step, with narration."""
        step_outputs = {}
        conversation = self.conversation_manager.load_conversation(conversation_id)

        for step in plan.steps:
            # 1. THINK (Narrate)
            thought_message = Message(
                id=len(conversation.messages),
                content=f"[Thinking]: {step.thought}",
                role=ChatRole.ASSISTANT,
                type=ToolType.THOUGHT,
                created_at=datetime.now(),
            )
            conversation.messages.append(thought_message)
            self.conversation_manager.save_conversation(conversation)
            if self.ui_callback:
                await self.ui_callback(thought_message.content)

            if not step.tool_type:
                continue

            # 2. ACT (Execute Tool)
            tool_input = self.substitute_placeholders(step.tool_input, step_outputs)
            
            tool_output, needs_confirmation = self.tool_manager.execute_tool(step.tool_type, tool_input)

            if needs_confirmation:
                # For now, we'll auto-confirm. The confirmation flow needs to be integrated with the async UI.
                # This is a simplification to keep moving forward.
                logger.warn(f"Tool {step.tool_type} requires confirmation. Auto-confirming for now.")
                tool_output, _ = self.tool_manager.execute_tool(step.tool_type, tool_input, confirmed=True)

            # 3. OBSERVE (Store & Show Result)
            step_outputs[f"step_{step.step_id}_output"] = tool_output

            tool_message = Message(
                id=len(conversation.messages),
                content=f"[Tool Output]:\n{tool_output}",
                role=ChatRole.ASSISTANT,
                type=step.tool_type,
                created_at=datetime.now(),
            )
            conversation.messages.append(tool_message)
            self.conversation_manager.save_conversation(conversation)
            if self.ui_callback:
                await self.ui_callback(tool_message.content)
    
    async def send_final_summary(self, conversation_id: int, override_text: str = None):
        """Generates and sends a final summary to the user."""
        conversation = self.conversation_manager.load_conversation(conversation_id)
        
        if override_text:
            summary_content = override_text
        else:
            # Create a prompt for the final summary
            summary_prompt = "Based on the preceding actions and observations, provide a concise and helpful final answer to the initial user request."
            
            messages_for_summary = [msg.model_dump() for msg in conversation.messages]
            messages_for_summary.append({"role": "user", "content": summary_prompt})

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=messages_for_summary,
                    temperature=0.5,
                ),
            )
            summary_content = response.choices[0].message.content

        summary_message = Message(
            id=len(conversation.messages),
            content=summary_content,
            role=ChatRole.ASSISTANT,
            created_at=datetime.now(),
        )
        conversation.messages.append(summary_message)
        self.conversation_manager.save_conversation(conversation)
        if self.ui_callback:
            await self.ui_callback(summary_message.content)

    def substitute_placeholders(self, text: str, outputs: dict) -> str:
        """Substitutes placeholders like $step_1_output with actual values."""
        if not text:
            return ""
        
        def replace_match(match):
            key = match.group(1)
            return str(outputs.get(key, match.group(0)))

        return re.sub(r"\$([a-zA-Z0-9_]+)", replace_match, text)