from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr


def get_llm_client(
    provider: str,
    model_name: str,
    api_key: str = "",
    base_url: str = "",
    temperature: float = 0.0,
) -> BaseChatModel:
    """
    Factory function to initialize the correct LLM client based on the provider.
    All returned objects inherit from BaseChatModel, making them fully interchangeable
    inside LangGraph.
    """
    provider = provider.lower()

    if provider == "openai":
        return ChatOpenAI(
            model=model_name, api_key=SecretStr(api_key), temperature=temperature
        )

    elif provider == "groq":
        return ChatGroq(
            model=model_name, api_key=SecretStr(api_key), temperature=temperature
        )

    elif provider == "ollama":
        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
        )

    elif provider == "anthropic":
        return ChatAnthropic(
            model_name=model_name,
            api_key=SecretStr(api_key),
            temperature=temperature,
            timeout=60,
            stop=[],
        )

    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
