from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    BaseMessageChunk,
    ToolMessage,
    AIMessage,
)
from langgraph.types import StreamMode
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from typing import Literal, AsyncIterator, Sequence
from .tools.tools import get_tool_list, fetch_context_from_db
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from manage_env import get_env
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from langchain_core.messages import ToolCall
from .prompts import ROUTER_SYSTEM_PROMPT, FINAL_LLM_SYSTEM_PROMPT
from .utils import get_llm_client
import uuid

DEBUG_MODE = get_env("DEBUG_MODE").upper() == "TRUE"

ROUTER_LLM_PROVIDER = get_env("ROUTER_LLM_PROVIDER")
ROUTER_LLM_MODEL_NAME = get_env("ROUTER_LLM_MODEL_NAME")
ROUTER_LLM_BASE_URL = get_env("ROUTER_LLM_BASE_URL")
ROUTER_LLM_API_KEY = get_env("ROUTER_LLM_API_KEY")
ROUTER_LLM_TEMPERATURE = float(get_env("ROUTER_LLM_TEMPERATURE"))

FINAL_LLM_PROVIDER = get_env("FINAL_LLM_PROVIDER")
FINAL_LLM_MODEL_NAME = get_env("FINAL_LLM_MODEL_NAME")
FINAL_LLM_BASE_URL = get_env("FINAL_LLM_BASE_URL")
FINAL_LLM_API_KEY = get_env("FINAL_LLM_API_KEY")
FINAL_LLM_TEMPERATURE = float(get_env("FINAL_LLM_TEMPERATURE"))


class RouterDecision(BaseModel):
    thought: str = Field(description="Your internal reasoning about what to do next.")
    action: Literal["TOOL_CALL", "READY", "OUT_OF_SCOPE"] = Field(
        description="The action to take."
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="If action is TOOL_CALL, the exact name of the tool to use (e.g., 'get_build_details'). Otherwise, null.",
    )
    tool_arguments: Optional[Dict[str, Any]] = Field(
        default=None,
        description="If action is TOOL_CALL, a JSON object containing the arguments for the tool. Otherwise, null.",
    )


class Agent:

    def __init__(
        self, chat_id: int, context: dict, checkpointer: AsyncPostgresSaver
    ) -> None:
        router_llm = get_llm_client(
            provider=ROUTER_LLM_PROVIDER,
            model_name=ROUTER_LLM_MODEL_NAME,
            api_key=ROUTER_LLM_API_KEY,
            base_url=ROUTER_LLM_BASE_URL,
            temperature=ROUTER_LLM_TEMPERATURE,
        )
        self.structured_router = router_llm.with_structured_output(RouterDecision)

        self.final_llm = get_llm_client(
            provider=FINAL_LLM_PROVIDER,
            model_name=FINAL_LLM_MODEL_NAME,
            api_key=FINAL_LLM_API_KEY,
            base_url=FINAL_LLM_BASE_URL,
            temperature=FINAL_LLM_TEMPERATURE,
        )

        self.checkpointer = checkpointer
        self.tools = get_tool_list(chat_id, context)

    def router_node(self, state: MessagesState) -> dict:
        """
        The Router reads the conversation, generates a structured decision,
        and we manually convert that decision into a proper LangChain ToolCall.
        """
        messages = state["messages"]
        system_prompt = SystemMessage(content=ROUTER_SYSTEM_PROMPT)
        router_input = [system_prompt] + messages

        decision: RouterDecision = self.structured_router.invoke(router_input)  # type: ignore
        result: dict = {}

        if decision.action == "TOOL_CALL" and decision.tool_name:
            tool_call = ToolCall(
                name=decision.tool_name,
                args=decision.tool_arguments or {},
                id=f"call_{uuid.uuid4().hex[:8]}",
            )

            ai_msg = AIMessage(
                content=f"<thought>\n{decision.thought}\n</thought>",
                tool_calls=[tool_call],
            )
            result = {"messages": [ai_msg]}

        elif decision.action == "READY":
            ai_msg = AIMessage(
                content=f"<thought>\n{decision.thought}\n</thought>\n[READY]"
            )
            result = {"messages": [ai_msg]}

        else:
            ai_msg = AIMessage(
                content=f"<thought>\n{decision.thought}\n</thought>\n[OUT OF SCOPE]"
            )
            result = {"messages": [ai_msg]}

        return result

    def generate_final_response_node(
        self, state: MessagesState, config: RunnableConfig
    ) -> dict:
        """
        The Final LLM takes the conversation history and generates the final response.
        We intercept the Router's last message, extract its decision, remove it from
        the message history, and inject the instruction dynamically into the System Prompt.
        """
        messages = state["messages"]
        last_message = messages[-1]
        last_content = str(last_message.content).upper()

        filtered_messages = messages[:-1]

        dynamic_instruction = ""

        if "[OUT OF SCOPE]" in last_content:
            dynamic_instruction = (
                "\n\nCRITICAL DIRECTIVE FROM ROUTER: "
                "The user query is strictly OUT OF SCOPE. "
                "You MUST politely decline to answer in a single sentence."
                "Do NOT attempt to solve the issue or provide a tutorial."
                "Answer with: 'I cannot assist you with this question.'"
            )

        final_system_prompt_content = FINAL_LLM_SYSTEM_PROMPT + dynamic_instruction
        system_prompt = SystemMessage(content=final_system_prompt_content)
        generation_input = [system_prompt] + filtered_messages

        final_response = self.final_llm.invoke(generation_input, config=config)

        return {"messages": [final_response]}

    def handle_tool_error_node(self, state: MessagesState) -> dict:
        """
        Catch malformed tool calls (e.g., bad JSON syntax) and return a message
        instructing the LLM to fix the syntax and try again.
        """
        last_message = state["messages"][-1]

        error_messages = []

        for invalid_call in last_message.invalid_tool_calls:  # type: ignore

            error_description = invalid_call.get("error", "Unknown JSON error")
            tool_name = invalid_call.get("name", "UnknownTool")
            call_id = invalid_call.get("id", "unknown_id")

            error_msg = (
                f"Error in tool call syntax for '{tool_name}'. "
                f"System Error: {error_description}. "
                "Please fix your JSON format and call the tool again."
            )

            error_messages.append(
                ToolMessage(content=error_msg, tool_call_id=call_id, name=tool_name)
            )

        return {"messages": error_messages}

    def router_condition(
        self,
        state: MessagesState,
    ) -> Literal["tools", "generate_final_response", "handle_tool_error"]:
        """
        Check the last message from the router.
        It parses the explicit tags or tool calls to determine the next graph node.
        """
        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage) and last_message.invalid_tool_calls:
            return "handle_tool_error"

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        if isinstance(last_message.content, str):
            content_upper = last_message.content.upper()

            if "[READY]" in content_upper or "[OUT OF SCOPE]" in content_upper:
                return "generate_final_response"

        return "generate_final_response"

    def create_state_graph(
        self,
    ):

        workflow = StateGraph(MessagesState)

        workflow.add_node("router", self.router_node)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("generate_final_response", self.generate_final_response_node)
        workflow.add_node("handle_tool_error", self.handle_tool_error_node)

        workflow.add_edge(START, "router")

        workflow.add_conditional_edges(
            "router",
            self.router_condition,
            {
                "tools": "tools",
                "handle_tool_error": "handle_tool_error",
                "generate_final_response": "generate_final_response",
            },
        )

        workflow.add_edge("tools", "router")

        workflow.add_edge("handle_tool_error", "router")

        workflow.add_edge("generate_final_response", END)

        return workflow.compile(checkpointer=self.checkpointer)


async def execute_agent_prod(
    prompt: str,
    chat_id: int,
    db_session: AsyncSession,
    checkpointer: AsyncPostgresSaver,
):
    """
    Executes the agent and yields the final response chunk by chunk.
    Streams both "messages" (for frontend tokens) and "updates" (for state debugging).
    """
    context = await fetch_context_from_db(chat_id, db_session)
    app = Agent(chat_id, context, checkpointer).create_state_graph()

    execution_config: RunnableConfig = {"configurable": {"thread_id": str(chat_id)}}

    input_message: MessagesState = {"messages": [HumanMessage(content=prompt)]}

    async for stream_mode, payload in app.astream(
        input_message, config=execution_config, stream_mode=["messages"]
    ):
        if stream_mode == "messages":
            msg, metadata = payload

            if isinstance(metadata, dict):
                current_node = metadata.get("langgraph_node")

                if current_node == "generate_final_response":
                    if isinstance(msg, BaseMessageChunk) and isinstance(
                        msg.content, str
                    ):
                        if msg.content:
                            yield msg.content


async def execute_agent_debug(
    prompt: str,
    chat_id: int,
    db_session: AsyncSession,
    checkpointer: AsyncPostgresSaver,
):
    """
    Executes the agent and yields the final response chunk by chunk.
    Streams both "messages" (for frontend tokens) and "updates" (for state debugging).
    """
    context = await fetch_context_from_db(chat_id, db_session)
    app = Agent(chat_id, context, checkpointer).create_state_graph()

    execution_config: RunnableConfig = {"configurable": {"thread_id": str(chat_id)}}

    input_message: MessagesState = {"messages": [HumanMessage(content=prompt)]}

    print("\n=== AGENT EXECUTION STARTED ===")
    print(f"[USER PROMPT]: {prompt}")

    current_print_context = None

    stream_node: Sequence[StreamMode] = ["messages", "updates"]

    async for stream_mode, payload in app.astream(
        input_message, config=execution_config, stream_mode=stream_node
    ):

        # --- MESSAGES (Real-time token streaming for UI & Thoughts) ---
        if stream_mode == "messages":
            msg, metadata = payload

            if isinstance(metadata, dict):
                current_node = metadata.get("langgraph_node")

                if current_node == "router":
                    if (
                        hasattr(msg, "content")
                        and isinstance(msg.content, str)
                        and msg.content
                    ):
                        if current_print_context != "router_thought":
                            print("\n[ROUTER THOUGHT]: ", end="", flush=True)
                            current_print_context = "router_thought"
                        print(msg.content, end="", flush=True)

                    if hasattr(msg, "tool_call_chunks") and msg.tool_call_chunks:
                        for chunk in msg.tool_call_chunks:
                            if chunk.get("name"):
                                print(
                                    f"\n\n[ROUTER ACTION]: Preparing to call tool -> {chunk['name']}"
                                )
                                current_print_context = "router_action"

                elif current_node == "generate_final_response":
                    if isinstance(msg, BaseMessageChunk) and isinstance(
                        msg.content, str
                    ):
                        if msg.content:
                            yield msg.content

        # --- UPDATES (State transitions between nodes for Debugging) ---
        elif stream_mode == "updates":
            # payload is a dictionary representing what the node just returned
            # Example: {"router": {"messages": [AIMessage(...)]}}

            for node_name, state_update in payload.items():
                print(f"\n\n[STATE TRANSITION] >>> Node '{node_name}' finished.")

                messages_added = state_update.get("messages", [])

                # Ensure it's a list so we can iterate over it safely
                if not isinstance(messages_added, list):
                    messages_added = [messages_added]

                for m in messages_added:
                    msg_type = m.__class__.__name__

                    # Truncate content to keep the console clean
                    content_preview = str(m.content)[:150].replace("\n", " ")
                    if len(str(m.content)) > 150:
                        content_preview += "..."

                    print(f"  -> Added {msg_type}: {content_preview}")

                    # If the message contains tool calls, print them explicitly
                    if hasattr(m, "tool_calls") and m.tool_calls:
                        tools_requested = [tc["name"] for tc in m.tool_calls]
                        print(f"  -> Tools Requested: {tools_requested}")

                print("-" * 60)
                current_print_context = "state_transition"

    print("\n=== AGENT EXECUTION FINISHED ===\n")


async def execute_agent(
    prompt: str,
    chat_id: int,
    db_session: AsyncSession,
    checkpointer: AsyncPostgresSaver,
) -> AsyncIterator[str]:

    generator: AsyncIterator[str]
    if DEBUG_MODE:
        generator = execute_agent_debug(prompt, chat_id, db_session, checkpointer)
    else:
        generator = execute_agent_prod(prompt, chat_id, db_session, checkpointer)

    async for chunk in generator:
        yield chunk
