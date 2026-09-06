from langchain_core.messages import (
    HumanMessage,
    BaseMessageChunk,
)
from langgraph.types import StreamMode
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState
from typing import AsyncIterator, Sequence
from .tools.tools import fetch_context_from_db
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from .agent import Agent
from manage_env import get_env
import asyncio

DEBUG_MODE = get_env("DEBUG_MODE").lower() == "true"
E2E_TEST = get_env("E2E_TEST").lower() == "true"
LANGFUSE_TRACING = get_env("LANGFUSE_TRACING").lower() == "true"
LANGSMITH_TRACING = get_env("LANGSMITH_TRACING").lower() == "true"
LANGGRAPH_RECURSION_LIMIT = int(get_env("LANGGRAPH_RECURSION_LIMIT") or 10)


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
    app = Agent(chat_id, prompt, context, checkpointer).create_state_graph()

    callbacks: list = []
    metadata = {}
    langfuse_handler = None
    if LANGFUSE_TRACING:
        from langfuse.langchain import CallbackHandler

        langfuse_handler = CallbackHandler()
        callbacks.append(langfuse_handler)
        metadata.update(
            {"langfuse_session_id": str(chat_id), "langfuse_tags": ["prod"]}
        )

    if LANGSMITH_TRACING:
        metadata.update(
            {
                "environment": "prod",
            }
        )

    execution_config: RunnableConfig = {
        "configurable": {"thread_id": str(chat_id)},
        "recursion_limit": LANGGRAPH_RECURSION_LIMIT,
        "callbacks": callbacks,
        "metadata": metadata,
    }

    input_message: MessagesState = {"messages": [HumanMessage(content=prompt)]}

    try:
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

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Execution interrupted: {str(e)}")
        yield "**System Error:** The AI encountered an unexpected issue. Please try again."


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
    app = Agent(chat_id, prompt, context, checkpointer).create_state_graph()

    callbacks: list = []
    metadata = {}
    langfuse_handler = None
    if LANGFUSE_TRACING:
        from langfuse.langchain import CallbackHandler

        langfuse_handler = CallbackHandler()
        callbacks.append(langfuse_handler)
        metadata.update(
            {"langfuse_session_id": str(chat_id), "langfuse_tags": ["debug"]}
        )

    if LANGSMITH_TRACING:
        metadata.update(
            {
                "environment": "debug",
            }
        )

    execution_config: RunnableConfig = {
        "configurable": {"thread_id": str(chat_id)},
        "recursion_limit": LANGGRAPH_RECURSION_LIMIT,
        "callbacks": callbacks,
        "metadata": metadata,
    }

    print("EXECUTION_CONFIG: ", execution_config)

    input_message: MessagesState = {"messages": [HumanMessage(content=prompt)]}

    print("\n=== AGENT EXECUTION STARTED ===")
    print(f"[USER PROMPT]: {prompt}")

    current_print_context = None

    stream_node: Sequence[StreamMode] = ["messages", "updates"]

    try:
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
                            and isinstance(msg.content, str)  # type: ignore
                            and msg.content
                        ):
                            if current_print_context != "router_thought":
                                print("\n[ROUTER THOUGHT]: ", end="", flush=True)
                                current_print_context = "router_thought"
                            print(msg.content, end="", flush=True)

                        if hasattr(msg, "tool_call_chunks") and msg.tool_call_chunks:
                            for chunk in msg.tool_call_chunks:  # type: ignore
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

                for node_name, state_update in payload.items():  # type: ignore
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

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Execution interrupted: {str(e)}")
        yield "**System Error:** The AI encountered an unexpected issue. Please try again."

    finally:
        print("\n=== AGENT EXECUTION FINISHED ===\n")


async def execute_agent_mock(prompt: str) -> AsyncIterator[str]:
    mock_response = f"Mocked response for prompt: {prompt}"

    chunks = mock_response.split(" ")

    for chunk in chunks:
        yield chunk + " "
        await asyncio.sleep(0.05)


async def execute_agent(
    prompt: str,
    chat_id: int,
    db_session: AsyncSession,
    checkpointer: AsyncPostgresSaver,
) -> AsyncIterator[str]:

    if E2E_TEST:
        generator = execute_agent_mock(prompt)
    elif DEBUG_MODE:
        generator = execute_agent_debug(prompt, chat_id, db_session, checkpointer)
    else:
        generator = execute_agent_prod(prompt, chat_id, db_session, checkpointer)

    async for chunk in generator:
        yield chunk
