from langchain_core.messages import (
    SystemMessage,
    ToolMessage,
    AIMessage,
    ToolCall,
    trim_messages,
)
import tiktoken
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from typing import Literal
from .tools.tools import get_tool_list
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from manage_env import get_env
from pydantic import BaseModel, Field
from .prompts import ROUTER_SYSTEM_PROMPT, FINAL_LLM_SYSTEM_PROMPT
from llm_client import get_llm_client
from langchain_core.tools import tool

ROUTER_LLM_PROVIDER = get_env("ROUTER_LLM_PROVIDER")
ROUTER_LLM_MODEL_NAME = get_env("ROUTER_LLM_MODEL_NAME")
ROUTER_LLM_BASE_URL = get_env("ROUTER_LLM_BASE_URL")
ROUTER_LLM_API_KEY = get_env("ROUTER_LLM_API_KEY")
ROUTER_LLM_TEMPERATURE = float(get_env("ROUTER_LLM_TEMPERATURE"))
ROUTER_LLM_MAX_TOKENS = max(int(get_env("ROUTER_LLM_MAX_TOKENS")), 4000)

FINAL_LLM_PROVIDER = get_env("FINAL_LLM_PROVIDER")
FINAL_LLM_MODEL_NAME = get_env("FINAL_LLM_MODEL_NAME")
FINAL_LLM_BASE_URL = get_env("FINAL_LLM_BASE_URL")
FINAL_LLM_API_KEY = get_env("FINAL_LLM_API_KEY")
FINAL_LLM_TEMPERATURE = float(get_env("FINAL_LLM_TEMPERATURE"))
FINAL_LLM_MAX_TOKENS = max(int(get_env("FINAL_LLM_MAX_TOKENS")), 4000)


local_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens_locally(messages: list) -> int:
    total_tokens = 0
    for msg in messages:
        total_tokens += len(local_encoder.encode(str(msg.content)))
    return total_tokens


class RoutingArgs(BaseModel):
    current_knowledge: str = Field(description="Summary of what you discovered so far.")
    current_hypothesis: str = Field(
        description="What you think is causing the problem."
    )


@tool(args_schema=RoutingArgs)
def ready_to_answer(current_knowledge: str, current_hypothesis: str):
    """Call this tool ONLY when you have gathered enough logs/code to answer the user's Jenkins question."""
    pass


@tool(args_schema=RoutingArgs)
def declare_out_of_scope(current_knowledge: str, current_hypothesis: str):
    """Call this tool ONLY when the user's query is completely unrelated to DevOps, Jenkins, or pipelines."""
    pass


class Agent:
    def __init__(
        self, chat_id: int, prompt: str, context: dict, checkpointer: AsyncPostgresSaver
    ) -> None:
        router_llm = get_llm_client(
            provider=ROUTER_LLM_PROVIDER,
            model_name=ROUTER_LLM_MODEL_NAME,
            api_key=ROUTER_LLM_API_KEY,
            base_url=ROUTER_LLM_BASE_URL,
            temperature=ROUTER_LLM_TEMPERATURE,
        )

        self.final_llm = get_llm_client(
            provider=FINAL_LLM_PROVIDER,
            model_name=FINAL_LLM_MODEL_NAME,
            api_key=FINAL_LLM_API_KEY,
            base_url=FINAL_LLM_BASE_URL,
            temperature=FINAL_LLM_TEMPERATURE,
        )

        self.checkpointer = checkpointer
        self.tools = get_tool_list(chat_id, context, prompt) + [
            ready_to_answer,
            declare_out_of_scope,
        ]
        self.native_router = router_llm.bind_tools(self.tools)

        self.system_prompt = SystemMessage(content=ROUTER_SYSTEM_PROMPT)
        self.know_ws = False

    async def router_node(self, state: MessagesState) -> dict:
        """
        The Router reads the conversation, generates a structured decision,
        and we manually convert that decision into a proper LangChain ToolCall.
        """
        messages = state["messages"]

        # Check if the last tool call failed
        if messages:
            last_msg = messages[-1]

            if isinstance(last_msg, ToolMessage):
                content_upper = str(last_msg.content).upper()

                if "[MISSING_CONTEXT]" in content_upper:
                    print(
                        f"\nCIRCUIT BREAKER -> Tool failed ({last_msg.name}). Bypassing Router LLM to prevent loops."
                    )
                    ai_msg = AIMessage(
                        content="[MISSING_CONTEXT]: The tool returned an error or the context is missing. I must stop trying and alert the final agent."
                    )
                    return {"messages": [ai_msg]}

        trimmed_history = trim_messages(
            messages,
            max_tokens=ROUTER_LLM_MAX_TOKENS - 2000,
            strategy="last",
            token_counter=count_tokens_locally,
            include_system=False,
            allow_partial=False,
        )
        router_input = [self.system_prompt] + trimmed_history

        response = await self.native_router.ainvoke(router_input)

        if not response.tool_calls:
            fake_thought = f"Model bypassed tools and generated raw text"
            ai_msg = AIMessage(content=f"[READY]: {fake_thought}")
            return {"messages": [ai_msg]}

        selected_tools: list[ToolCall] = []

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name == "ready_to_answer":
                knowledge = tool_args.get("current_knowledge", "")
                hypothesis = tool_args.get("current_hypothesis", "")

                combined_thought = f"Knowledge: {knowledge}\nHypothesis: {hypothesis}"
                ai_msg = AIMessage(content=f"[READY]: {combined_thought}")
                return {"messages": [ai_msg]}

            elif tool_name == "declare_out_of_scope":
                knowledge = tool_args.get("current_knowledge", "")
                hypothesis = tool_args.get("current_hypothesis", "")

                combined_thought = f"Knowledge: {knowledge}\nHypothesis: {hypothesis}"
                ai_msg = AIMessage(content=f"[OUT_OF_SCOPE]: {combined_thought}")
                return {"messages": [ai_msg]}

            elif tool_name == "get_workspace_file" and not self.know_ws:
                tool_call: ToolCall = {
                    "name": "get_workspace_tree",
                    "args": {},
                    "id": tool_call.get("id"),
                }

            if tool_call["name"] == "get_workspace_tree":
                self.know_ws = True
            selected_tools.append(tool_call)

        ai_msg = AIMessage(
            content=f"\nExecuting following tools: {selected_tools}",
            tool_calls=selected_tools,
        )

        return {"messages": [ai_msg]}

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

    async def router_condition(
        self,
        state: MessagesState,
    ) -> Literal["tools", "generate_final_response", "handle_tool_error"]:
        """
        Check the last message from the router.
        It parses the explicit tags or tool calls to determine the next graph node.
        """
        messages = state["messages"]
        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.invalid_tool_calls:
            return "handle_tool_error"

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        return "generate_final_response"

    async def generate_final_response_node(
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

        trimmed_history = trim_messages(
            messages[:-1],
            max_tokens=FINAL_LLM_MAX_TOKENS - 2000,
            strategy="last",
            token_counter=count_tokens_locally,
            include_system=False,
            allow_partial=False,
        )

        dynamic_instruction = ""

        if "[MISSING_CONTEXT]" in last_content:
            dynamic_instruction = (
                "\n\nCRITICAL DIRECTIVE FROM ROUTER: "
                "The required logs or context are missing. "
                "You MUST answer EXACTLY with: 'I don't have context information about this, please upload the context and try again.'"
                "Do NOT attempt to guess the solution."
            )
        elif "[OUT_OF_SCOPE]" in last_content:
            dynamic_instruction = (
                "\n\nCRITICAL DIRECTIVE FROM ROUTER: "
                "The user query is strictly OUT OF SCOPE. "
                "You MUST politely decline to answer in a single sentence. "
                "Answer with: 'I cannot assist you with this question.'"
            )
        elif "[READY]" in last_content:
            dynamic_instruction = (
                "\n\nCRITICAL DIRECTIVE FROM ROUTER: "
                "The router found useful information to answer the user's question."
                "You have to use the data to provide the user with a helpful answer."
            )

        final_system_prompt_content = FINAL_LLM_SYSTEM_PROMPT + dynamic_instruction
        system_prompt = SystemMessage(content=final_system_prompt_content)
        generation_input = [system_prompt] + trimmed_history

        final_response = await self.final_llm.ainvoke(generation_input, config=config)

        return {"messages": [final_response]}

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
