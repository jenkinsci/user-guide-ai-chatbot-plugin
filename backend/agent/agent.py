from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from manage_env import get_env
from typing import Literal
from .agent_tools.tools import get_tool_list
from pydantic import SecretStr


ROUTER_LLM_MODEL_NAME="llama3.1:8b"
ROUTER_LLM_BASE_URL="http://192.168.178.149:11434/v1"
ROUTER_LLM_API_KEY="ollama"
ROUTER_LLM_TEMPERATURE=0

FINAL_LLM_MODEL_NAME="llama3.1:8b"
FINAL_LLM_BASE_URL="http://192.168.178.149:11434/v1"
FINAL_LLM_API_KEY="ollama"
FINAL_LLM_TEMPERATURE=0

""" ROUTER_LLM_MODEL_NAME = get_env("ROUTER_LLM_MODEL_NAME")
ROUTER_LLM_BASE_URL = get_env("ROUTER_LLM_BASE_URL")
ROUTER_LLM_API_KEY = get_env("ROUTER_LLM_API_KEY")
ROUTER_LLM_TEMPERATURE = float(get_env("ROUTER_LLM_TEMPERATURE"))

FINAL_LLM_MODEL_NAME = get_env("FINAL_LLM_MODEL_NAME")
FINAL_LLM_BASE_URL = get_env("FINAL_LLM_BASE_URL")
FINAL_LLM_API_KEY = get_env("FINAL_LLM_API_KEY")
FINAL_LLM_TEMPERATURE = float(get_env("FINAL_LLM_TEMPERATURE")) """

FINAL_LLM_SYSTEM_PROMPT = """
You are a precise and helpful assistant. 
Your ONLY task is to answer the user's question based strictly on the data provided.
"""



def create_state_graph(chat_id: int):


    router_llm = ChatOpenAI(
    base_url=ROUTER_LLM_BASE_URL,
    model=ROUTER_LLM_MODEL_NAME,
    api_key=SecretStr(ROUTER_LLM_API_KEY),
    temperature=ROUTER_LLM_TEMPERATURE
    )
    
    agent_tools = get_tool_list(chat_id)
    router_llm_with_tools = router_llm.bind_tools(agent_tools)

    final_llm = ChatOpenAI(
        base_url=FINAL_LLM_BASE_URL,
        model=FINAL_LLM_MODEL_NAME,
        api_key=SecretStr(FINAL_LLM_API_KEY),
        temperature=FINAL_LLM_TEMPERATURE
    )

    def router_node(state: MessagesState) -> dict:
        """
        The Router reads the conversation and decides whether to call a tool
        or stop searching.
        """
        messages = state["messages"]
        response = router_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def generate_final_response_node(state: MessagesState) -> dict:
        """
        The Final LLM takes the conversation history and generates the final user-facing response.
        We exclude the very last message (the router's confirmation) so the Final LLM 
        does not think the AI has already finished the conversation.
        """
        messages = state["messages"]
        
        filtered_messages = messages[:-1]
        
        system_prompt = SystemMessage(
            content=FINAL_LLM_SYSTEM_PROMPT
        )
        
        # Combine system prompt with the filtered message history
        generation_input = [system_prompt] + filtered_messages
        print(generation_input)
        final_response = final_llm.invoke(generation_input)
        
        return {"messages": [final_response]}


    def router_condition(state: MessagesState) -> Literal["tools", "generate_final_response"]:
        """
        Check the last message from the router. If it called a tool, go to 'tools'.
        If it just output text (meaning it's done searching), go to 'generate_final_response'.
        """
        last_message = state["messages"][-1]
        
        if last_message.tool_calls:
            return "tools"
            
        return "generate_final_response"


    workflow = StateGraph(MessagesState)

    workflow.add_node("router", router_node)
    workflow.add_node("tools", ToolNode(agent_tools))
    workflow.add_node("generate_final_response", generate_final_response_node)

    # Start at the router
    workflow.add_edge(START, "router")

    # The router decides the next step based on the condition
    workflow.add_conditional_edges(
        "router",
        router_condition,
        {
            "tools": "tools",
            "generate_final_response": "generate_final_response"
        }
    )

    # After a tool runs, ALWAYS go back to the router to check if more info is needed
    workflow.add_edge("tools", "router")

    # After the final response is generated, the graph ends
    workflow.add_edge("generate_final_response", END)

    return workflow.compile()

def execute_agent(prompt: str, chat_id: int):
    initial_state = MessagesState({"messages": [HumanMessage(content=prompt)]})
    # TODO: Retrieve old chat history
    
    for event in create_state_graph(chat_id).stream(initial_state, stream_mode="values"):
        last_message = event["messages"][-1]
        last_message.pretty_print()


if __name__ == "__main__":
    user_input = "What is my Jenkins version?"
    execute_agent(user_input, 10)
    