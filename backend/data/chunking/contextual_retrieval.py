from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from llm_client import get_llm_client
from dotenv import load_dotenv
from manage_env import get_env
import asyncio

load_dotenv()


CONTEXT_CHUNK_SEPARATOR = "===CR==="


async def contextualize_chunk(
    parent_document: str,
    target_chunk: str,
    llm_client: BaseChatModel,
    provider_name: str = "generic",
) -> str:
    """
    Generates context for a chunk using a LangChain BaseChatModel.
    Supports Anthropic-specific prompt caching if enabled.
    """

    system_prompt_text = (
        "You are an AI assistant specialized in text processing for RAG systems. "
        "Your task is to provide a brief context (1-3 sentences maximum) for a specific "
        "chunk of text, situating it within the broader parent document. "
        "Output ONLY the context string, without any introductory or conversational phrases."
    )

    try:
        # Check if we need to apply Anthropic's specific caching structure
        if provider_name == "anthropic":
            messages = [
                SystemMessage(content=system_prompt_text),
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"<document>\n{parent_document}\n</document>\n\n",
                            "cache_control": {"type": "ephemeral"},
                        },
                        {
                            "type": "text",
                            "text": f"<chunk>\n{target_chunk}\n</chunk>\n\nPlease generate the context for this chunk.",
                        },
                    ]
                ),
            ]
        else:
            # Standard LangChain abstraction for OpenAI, Groq, Ollama, and non-cached Anthropic
            user_prompt_text = (
                f"<document>\n{parent_document}\n</document>\n\n"
                f"<chunk>\n{target_chunk}\n</chunk>\n\n"
                "Please generate the context for this chunk."
            )
            messages = [
                SystemMessage(content=system_prompt_text),
                HumanMessage(content=user_prompt_text),
            ]

        # Execute the unified LangChain invoke method
        response = await llm_client.ainvoke(messages)

        # Extract the text content from the AIMessage object
        generated_context = str(response.content).strip()

        # Combine the generated context with the original chunk
        final_contextualized_text = (
            f"[CONTEXT]: {generated_context}{CONTEXT_CHUNK_SEPARATOR}{target_chunk}"
        )
        return final_contextualized_text

    except Exception as process_error:
        print(f"Error during context generation: {process_error}")
        return target_chunk


if __name__ == "__main__":
    load_dotenv()

    CONTEXTUAL_LLM_PROVIDER = get_env("CONTEXTUAL_LLM_PROVIDER")
    CONTEXTUAL_LLM_MODEL_NAME = get_env("CONTEXTUAL_LLM_MODEL_NAME")
    CONTEXTUAL_LLM_BASE_URL = get_env("CONTEXTUAL_LLM_BASE_URL")
    CONTEXTUAL_LLM_API_KEY = get_env("CONTEXTUAL_LLM_API_KEY")
    CONTEXTUAL_LLM_TEMPERATURE = get_env("CONTEXTUAL_LLM_TEMPERATURE")

    chat_model = get_llm_client(
        provider=CONTEXTUAL_LLM_PROVIDER,
        temperature=float(CONTEXTUAL_LLM_TEMPERATURE),
        api_key=CONTEXTUAL_LLM_API_KEY,
        base_url=CONTEXTUAL_LLM_BASE_URL,
        model_name=CONTEXTUAL_LLM_MODEL_NAME,
    )

    sample_document = (
        "Acme Corp announced its Q3 earnings today. The company reported a revenue "
        "of $5 billion, up 15% year-over-year. The CEO, Jane Doe, stated that the growth "
        "was primarily driven by the new Cloud Infrastructure division."
    )

    sample_target = "The CEO, Jane Doe, stated that the growth was primarily driven by the new Cloud Infrastructure division."

    print(f"Executing with {CONTEXTUAL_LLM_MODEL_NAME}\n")

    result = asyncio.run(contextualize_chunk(
        parent_document=sample_document,
        target_chunk=sample_target,
        llm_client=chat_model,
        provider_name=CONTEXTUAL_LLM_PROVIDER,
    ))

    print("--- CONTEXTUALIZED CHUNK ---")
    print(result)