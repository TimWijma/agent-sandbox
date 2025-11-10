from typing import Callable, Awaitable
import litellm, os, re
from logger import logger
from litellm import completion
from dotenv import load_dotenv
from models.plan import Plan, StepMessage
from models.intent import IntentClassification, IntentType
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
    def __init__(
        self,
        model: str = "gemini/gemini-2.5-flash-lite",
        ui_callback: Callable[[str | Message], Awaitable[None]] = None,
    ):
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

    async def classify_intent(
        self, conversation_id: int, user_message: str
    ) -> IntentClassification:
        """
        Classifies the user's intent to determine how to process the request.
        This is a lightweight operation to avoid unnecessary planning.
        """
        conversation = self.conversation_manager.load_conversation(conversation_id)

        # Get available tools for context
        tools = self.tool_manager.get_tool_descriptions()

        # Build context from recent conversation history (last 5 messages)
        recent_messages = (
            conversation.messages[-5:]
            if len(conversation.messages) > 5
            else conversation.messages
        )
        conversation_context = "\n".join(
            [
                f"{msg.role.value}: {msg.content if isinstance(msg.content, str) else '[Plan]'}"
                for msg in recent_messages[:-1]  # Exclude the current user message
            ]
        )

        prompt = (
            f"You are an AI assistant classifier. Analyze the user's request and classify it into one of three categories:\n\n"
            f"1. CONVERSATIONAL: Questions about your capabilities, greetings, chitchat, requests for explanation, or clarifications about previous responses.\n"
            f"   Examples: 'What can you do?', 'Hello!', 'How does that work?', 'Can you explain that?'\n\n"
            f"2. SIMPLE_TOOL: Requests that can be accomplished with a single tool execution.\n"
            f"   Examples: 'Calculate 5 + 3', 'Search for Python tutorials', 'Run ls command'\n\n"
            f"3. COMPLEX_TASK: Requests that require multiple steps, planning, or coordination of multiple tools.\n"
            f"   Examples: 'Find all Python files and count their lines', 'Create a new project structure', 'Debug this error'\n\n"
            f"Available tools:\n{tools}\n\n"
            f"Recent conversation context:\n{conversation_context}\n\n"
            f"User's current request: '{user_message}'\n\n"
            f"Classify this request and provide reasoning. If it's a SIMPLE_TOOL request, suggest which tool to use. "
            f"If the request is ambiguous or needs clarification, set requires_clarification to True and provide a clarification question."
        )

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=[
                        {
                            "role": ChatRole.SYSTEM.value,
                            "content": "You are an expert intent classifier. Be conservative with tool usage - prefer CONVERSATIONAL for questions about capabilities.",
                        },
                        {"role": ChatRole.USER.value, "content": prompt},
                    ],
                    temperature=0.1,  # Low temperature for consistent classification
                    response_format=IntentClassification,
                ),
            )

            model_response = response.choices[0].message.content
            intent = IntentClassification.model_validate_json(model_response)

            logger.info(f"Intent classified: {intent}")
            return intent
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            # Default to conversational on error to be safe
            return IntentClassification(
                intent_type=IntentType.CONVERSATIONAL,
                reasoning="Error during classification, defaulting to conversational mode",
                requires_clarification=False,
            )

    async def handle_conversational(self, conversation_id: int, user_message: str):
        """Handles conversational requests with direct LLM response."""
        conversation = self.conversation_manager.load_conversation(conversation_id)

        # Build conversation history for context
        messages_for_llm = [
            {
                "role": ChatRole.SYSTEM.value,
                "content": self.conversation_manager.system_message,
            }
        ]

        # Add recent conversation context (last 10 messages)
        for msg in conversation.messages[-10:]:
            if isinstance(msg.content, str):
                messages_for_llm.append(
                    {"role": msg.role.value, "content": msg.content}
                )

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=messages_for_llm,
                    temperature=0.7,
                ),
            )

            response_content = response.choices[0].message.content

            response_message = Message(
                id=len(conversation.messages),
                content=response_content,
                role=ChatRole.ASSISTANT,
                type=MessageType.TEXT,
                created_at=datetime.now(),
            )
            response_message.set_token_usage(response.usage)

            conversation.messages.append(response_message)
            self.conversation_manager.save_conversation(conversation)

            if self.ui_callback:
                await self.ui_callback(response_message)

        except Exception as e:
            logger.error(f"Error in conversational handler: {e}")

    async def handle_simple_tool(
        self, conversation_id: int, user_message: str, suggested_tool: str = None
    ):
        """Handles simple single-tool requests."""
        conversation = self.conversation_manager.load_conversation(conversation_id)

        # Get tool info
        tools = self.tool_manager.get_tool_descriptions()

        # Ask LLM to determine the exact tool and input
        prompt = (
            f"The user wants to perform a simple action: '{user_message}'\n\n"
            f"Available tools:\n{tools}\n\n"
            f"Determine the appropriate tool to use and the input for that tool. "
            f"Respond with a JSON object containing 'tool_type' and 'tool_input' (as a JSON string)."
        )

        # For now, fall back to complex task handling
        # This will be implemented more robustly in the next iteration
        await self.handle_complex_task(conversation_id, user_message)

    async def handle_complex_task(self, conversation_id: int, user_message: str):
        """Handles complex tasks that require planning and multiple steps."""
        # This is the existing plan-based execution
        plan = await self.create_plan(conversation_id, user_message)
        if not plan or not plan.steps:
            logger.error("Failed to create a valid plan.")
            return

        await self.execute_plan(conversation_id, plan)

    async def process_user_request(self, conversation_id: int, user_message: str):
        """
        Main entry point for processing a user's request.
        Classifies intent, then routes to appropriate handler.
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

        try:
            # 2. Classify the intent
            intent = await self.classify_intent(conversation_id, user_message)
            if not intent:
                logger.error("Failed to classify intent.")
                return

            logger.info(
                f"Classified intent as: {intent.intent_type} - {intent.reasoning}"
            )

            # 3. Handle clarification if needed
            if intent.requires_clarification and intent.clarification_question:
                clarification_message = Message(
                    id=len(conversation.messages),
                    content=intent.clarification_question,
                    role=ChatRole.ASSISTANT,
                    type=MessageType.TEXT,
                    created_at=datetime.now(),
                )
                conversation.messages.append(clarification_message)
                self.conversation_manager.save_conversation(conversation)
                if self.ui_callback:
                    await self.ui_callback(clarification_message)
                return

            # 4. Route based on intent type
            if intent.intent_type == IntentType.CONVERSATIONAL:
                await self.handle_conversational(conversation_id, user_message)
            elif intent.intent_type == IntentType.SIMPLE_TOOL:
                await self.handle_simple_tool(
                    conversation_id, user_message, intent.suggested_tool
                )
            elif intent.intent_type == IntentType.COMPLEX_TASK:
                await self.handle_complex_task(conversation_id, user_message)
        except Exception as e:
            logger.error(f"Error processing user request: {e}")

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
                        {
                            "role": ChatRole.SYSTEM.value,
                            "content": self.conversation_manager.system_message,
                        },
                        {"role": ChatRole.USER.value, "content": prompt},
                    ],
                    temperature=0.2,
                    response_format=Plan,
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

        conversation.messages.append(
            Message(
                id=len(conversation.messages),
                content=plan_prompt,
                role=ChatRole.USER,
                type=MessageType.TEXT,
            )
        )
        self.conversation_manager.save_conversation(conversation)

        llm_initial_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: completion(
                model=self.model,
                messages=[{"role": ChatRole.USER.value, "content": plan_prompt}],
                temperature=0.2,
                response_format=StepMessage,
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
            await self.ui_callback(current_message)

        # Now, loop through steps until plan is complete
        while not current_step.plan_complete:
            current_step = current_step.step
            tool_input = self.substitute_placeholders(
                current_step.tool_input, step_outputs
            )

            tool_output, needs_confirmation = self.tool_manager.execute_tool(
                current_step.tool_type, tool_input
            )

            if needs_confirmation:
                # For now, we'll auto-confirm. The confirmation flow needs to be integrated with the async UI.
                # This is a simplification to keep moving forward.
                logger.warning(
                    f"Tool {current_step.tool_type} requires confirmation. Auto-confirming for now."
                )
                tool_output, _ = self.tool_manager.execute_tool(
                    current_step.tool_type, tool_input, confirmed=True
                )

            step_outputs[f"step_{current_step.step_id}_output"] = tool_output

            tool_message = Message(
                id=len(conversation.messages),
                content=tool_output,
                role=ChatRole.ASSISTANT,
                type=MessageType.TOOL,
                created_at=datetime.now(),
            )

            conversation.messages.append(tool_message)
            self.conversation_manager.save_conversation(conversation)
            if self.ui_callback:
                await self.ui_callback(tool_message)

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
                    response_format=StepMessage,
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
                await self.ui_callback(current_step_message)

    def substitute_placeholders(self, text: str, outputs: dict) -> str:
        """Substitutes placeholders like $step_1_output with actual values."""
        if not text:
            return ""

        def replace_match(match):
            key = match.group(1)
            return str(outputs.get(key, match.group(0)))

        return re.sub(r"\$([a-zA-Z0-9_]+)", replace_match, text)
