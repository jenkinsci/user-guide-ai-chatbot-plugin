from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr
from langchain_core.documents import Document
from qdrant_client.conversions.common_types import Record
from difflib import SequenceMatcher


def qdrant_record_to_langchain_doc(records: list[Record]) -> list[Document]:
    """
    Converts a Qdrant record list in a Langchain Document list.
    """
    docs = []

    for r in records:
        payload = r.payload or {}

        page_content = payload.pop("page_content", "")

        metadata = {**payload["metadata"]}

        docs.append(Document(id=r.id, page_content=page_content, metadata=metadata))

    return docs


def remove_chunk_overlap(chunks: list[str]) -> str:
    """Join a chunk list removing the duplicated parts at the ends."""
    if not chunks:
        return ""

    reconstructed_text = chunks[0]

    for i in range(1, len(chunks)):
        next_chunk = chunks[i]

        max_overlap_search = min(len(reconstructed_text), len(next_chunk))

        match = SequenceMatcher(
            None,
            reconstructed_text[-max_overlap_search:],
            next_chunk[:max_overlap_search],
        ).find_longest_match(0, max_overlap_search, 0, max_overlap_search)

        if match.b == 0 and (match.a + match.size) == max_overlap_search:
            reconstructed_text += next_chunk[match.size :]
        else:
            reconstructed_text += next_chunk

    return reconstructed_text


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
