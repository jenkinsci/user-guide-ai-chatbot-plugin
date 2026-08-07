from typing import List, Dict, Any
from manage_env import get_env
import requests
from langchain_core.documents import Document

RERANKER_PROVIDER = get_env("RERANKER_PROVIDER")
RERANKER_BASE_URL = get_env("RERANKER_BASE_URL")
RERANKER_MODEL_NAME = get_env("RERANKER_MODEL_NAME")
RERANKER_API_KEY = get_env("RERANKER_API_KEY")


def get_reranked_documents(
    search_query: str,
    documents_list: List[Document],
) -> List[Dict[str, Any]]:
    """
    Reranks a list of documents using an agnostic provider approach.
    Returns a sorted list of dictionaries with 'index', 'score', and 'text'.
    """

    request_headers: Dict[str, str] = {"Content-Type": "application/json"}
    if RERANKER_API_KEY:
        request_headers["Authorization"] = f"Bearer {RERANKER_API_KEY}"

    request_payload: Dict[str, Any] = {}

    texts = [d.page_content for d in documents_list]

    if RERANKER_PROVIDER in ["infinity", "cohere", "jina", "voyage"]:
        request_payload = {
            "model": RERANKER_MODEL_NAME,
            "query": search_query,
            "documents": texts,
            "return_documents": False,
        }
    elif RERANKER_PROVIDER == "tei":
        request_payload = {"query": search_query, "texts": texts}
    else:
        raise ValueError(f"Unsupported provider format: {RERANKER_PROVIDER}")

    try:
        api_response = requests.post(
            url=f"{RERANKER_BASE_URL}rerank",
            headers=request_headers,
            json=request_payload,
        )
        api_response.raise_for_status()
        parsed_response = api_response.json()
    except requests.exceptions.RequestException as error:
        raise Exception(f"API request failed: {error}")

    standardized_results: List[Dict[str, Any]] = []

    if RERANKER_PROVIDER in ["infinity", "cohere", "jina", "voyage"]:
        raw_results = parsed_response.get("results", [])
        for item in raw_results:
            doc_index = item.get("index")
            doc_score = item.get("relevance_score", 0.0)

            if doc_index is not None and doc_index < len(documents_list):
                standardized_results.append(
                    {
                        "index": doc_index,
                        "score": doc_score,
                        "document": documents_list[doc_index],
                    }
                )

    elif RERANKER_PROVIDER == "tei":
        for item in parsed_response:
            doc_index = item.get("index")
            doc_score = item.get("score", 0.0)

            if doc_index is not None and doc_index < len(documents_list):
                standardized_results.append(
                    {
                        "index": doc_index,
                        "score": doc_score,
                        "document": documents_list[doc_index],
                    }
                )

    standardized_results.sort(key=lambda x: x["score"], reverse=True)

    return standardized_results
