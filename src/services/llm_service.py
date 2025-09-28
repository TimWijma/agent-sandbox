from typing import List, Callable, Awaitable
import litellm, os, re
from logger import logger
from litellm import completion
from dotenv import load_dotenv
from models.plan import Plan, StepMessage
from services.conversation_manager import ConversationManager
from services.tool_manager import ToolManager
from models.chat import (
    ChatRole,
    Message,
    MessageType,
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

        # # 2. Generate a plan
        plan = await self.create_plan(conversation_id, user_message)
        if not plan or not plan.steps:
            logger.error("Failed to create a valid plan.")
            # Optionally, inform the user about the failure


            # await self.send_final_summary(conversation_id, "I was unable to create a plan to address your request.")
            return

        # 3. Execute the plan
        await self.execute_plan(conversation_id, plan)

        # # 4. Send a final summary
        # await self.send_final_summary(conversation_id)


    async def create_plan(self, conversation_id: int, objective: str) -> Plan:
        """Generates a plan to achieve the given objective."""
        conversation = self.conversation_manager.load_conversation(conversation_id)

        tools = self.tool_manager.get_tool_descriptions()
        prompt = (
            f"You are an expert AI agent. Your task is to create a detailed, step-by-step plan to achieve the following objective: '{objective}'.\n\n"
            f"You have access to the following tools:\n{tools}\n\n"
            "For each step, you must provide a 'thought' explaining your reasoning for the action. This thought will be shown to the user.\n"
            "The plan should be a sequence of steps. Each step must include a unique 'step_id' (starting from 1), a 'thought', a 'tool_type', and the 'tool_input'.\n"
            "If a step does not require a tool, set 'tool_type' and 'tool_input' to None.\n"
            "If the input for a tool depends on the output of a previous step, use a placeholder like '$step_1_output' to reference it.\n\n"
            "Format the entire plan as a single JSON object that adheres to the provided schema."
            "For each tool type, ensure the 'tool_input' is a JSON string matching the tool's input schema.\n"
        )

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=[
                        {"role": ChatRole.SYSTEM.value, "content": self.conversation_manager.system_message},
                        {"role": ChatRole.USER.value, "content": prompt}],
                    temperature=0.2,
                    response_format=Plan
                ),
            )
            logger.info(f"Received response: {response}")

            model_response = response.choices[0].message.content
            plan = Plan.model_validate_json(model_response)

            plan_message = Message(
                id=len(conversation.messages),
                content=plan,
                role=ChatRole.ASSISTANT,
                type=MessageType.PLAN,
            )
            plan_message.set_token_usage(response.usage)
            
            conversation.messages.append(plan_message)
            self.conversation_manager.save_conversation(conversation)

            logger.info(f"Generated plan: {plan}")
            return plan
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return None

    async def execute_plan(self, conversation_id: int, plan: Plan):
        """Executes a plan step-by-step, with narration."""
        step_outputs = {}
        conversation = self.conversation_manager.load_conversation(conversation_id)

        # First, show the LLM the entire plan for context
        plan_prompt = (
            f"The following is the plan you created to achieve the user's objective:\n{plan}\n\n"
            "You will now execute this plan step-by-step. For each step, first narrate your thought process, then execute the tool if applicable, and finally observe and store the result.\n"
            "The output of each tool execution will be fed back to you for use in subsequent steps.\n"
            "Once all steps have been successfully executed, you will provide a final summary to the user, and set the `plan_complete` boolean to True\n"
            "Begin with Step 1."
        )

        conversation.messages.append(Message(
            id=len(conversation.messages),
            content=plan_prompt,
            role=ChatRole.USER,
            type=MessageType.TEXT,
        ))
        self.conversation_manager.save_conversation(conversation)

        llm_initial_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: completion(
                model=self.model,
                messages=[
                    {"role": ChatRole.USER.value, "content": plan_prompt}
                ],
                temperature=0.2,
                response_format=StepMessage
            ),
        )

        logger.info(f"Received initial response: {llm_initial_response}")
        model_response = llm_initial_response.choices[0].message.content
        current_step = StepMessage.model_validate_json(model_response)

        current_message = Message(
            id=len(conversation.messages),
            content=current_step.message,
            role=ChatRole.ASSISTANT,
            type=MessageType.TEXT,
        )
        current_message.set_token_usage(llm_initial_response.usage)
        conversation.messages.append(current_message)
        self.conversation_manager.save_conversation(conversation)

        logger.info(f"Starting plan execution with initial message: {current_step}")

        if self.ui_callback:
            await self.ui_callback(current_step.message)

        # Now, loop through steps until plan is complete
        while not current_step.plan_complete:
            current_step = current_step.step
            tool_input = self.substitute_placeholders(current_step.tool_input, step_outputs)

            tool_output, needs_confirmation = self.tool_manager.execute_tool(current_step.tool_type, tool_input)

            if needs_confirmation:
                # For now, we'll auto-confirm. The confirmation flow needs to be integrated with the async UI.
                # This is a simplification to keep moving forward.
                logger.warning(f"Tool {current_step.tool_type} requires confirmation. Auto-confirming for now.")
                tool_output, _ = self.tool_manager.execute_tool(current_step.tool_type, tool_input, confirmed=True)

            step_outputs[f"step_{current_step.step_id}_output"] = tool_output

            tool_message = Message(
                id=len(conversation.messages),
                content=f"[Tool Output]:\n{tool_output}",
                role=ChatRole.ASSISTANT,
                type=MessageType.TOOL,
                created_at=datetime.now(),
            )

            conversation.messages.append(tool_message)
            self.conversation_manager.save_conversation(conversation)
            if self.ui_callback:
                await self.ui_callback(tool_message.content)

            # Now, inform the LLM of the tool output and ask for the next step
            followup_msg = (
                f"The full plan is:\n{plan}\n\n"
                f"The output of the previous step (Step {current_step.step_id}) is as follows:\n{tool_output}\n\n"
                "Based on this result, please provide the next step in the plan. If the plan is complete, set `plan_complete` to True.\n"
                "Format your response as a JSON object adhering to the StepMessage schema."
            )
            llm_followup_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=[{"role": ChatRole.USER.value, "content": followup_msg}],
                    temperature=0.2,
                    response_format=StepMessage
                ),
            )
            model_response = llm_followup_response.choices[0].message.content
            current_step = StepMessage.model_validate_json(model_response)
            current_step_message = Message(
                id=len(conversation.messages),
                content=current_step.message,
                role=ChatRole.ASSISTANT,
                type=MessageType.TEXT,
            )
            current_step_message.set_token_usage(llm_followup_response.usage)
            conversation.messages.append(current_step_message)
            self.conversation_manager.save_conversation(conversation)

            logger.info(f"Proceeding to next step with message: {current_step}")

            if self.ui_callback:
                await self.ui_callback(current_step.message)

    
    # async def send_final_summary(self, conversation_id: int, override_text: str = None):
    #     """Generates and sends a final summary to the user."""
    #     conversation = self.conversation_manager.load_conversation(conversation_id)
        
    #     if override_text:
    #         summary_content = override_text
    #     else:
    #         # Create a prompt for the final summary
    #         summary_prompt = "Based on the preceding actions and observations, provide a concise and helpful final answer to the initial user request."
            
    #         messages_for_summary = [msg.model_dump() for msg in conversation.messages]
    #         messages_for_summary.append({"role": "user", "content": summary_prompt})

    #         response = await asyncio.get_event_loop().run_in_executor(
    #             None,
    #             lambda: completion(
    #                 model=self.model,
    #                 messages=messages_for_summary,
    #                 temperature=0.5,
    #             ),
    #         )
    #         summary_content = response.choices[0].message.content

    #     summary_message = Message(
    #         id=len(conversation.messages),
    #         content=summary_content,
    #         role=ChatRole.ASSISTANT,
    #         created_at=datetime.now(),
    #     )
    #     conversation.messages.append(summary_message)
    #     self.conversation_manager.save_conversation(conversation)
    #     if self.ui_callback:
    #         await self.ui_callback(summary_message.content)

    def substitute_placeholders(self, text: str, outputs: dict) -> str:
        """Substitutes placeholders like $step_1_output with actual values."""
        if not text:
            return ""
        
        def replace_match(match):
            key = match.group(1)
            return str(outputs.get(key, match.group(0)))

        return re.sub(r"\$([a-zA-Z0-9_]+)", replace_match, text)
    
    def get_token_count(self, usage: dict) -> tuple[int, int]:
        """Calculates total tokens used from the usage dictionary."""

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        return input_tokens, output_tokens
    