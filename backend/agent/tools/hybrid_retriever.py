from vectordb.vector_store import get_vector_store
from langchain_core.documents import Document
from qdrant_client.http.models import models
from langchain_core.tools import tool


async def hybrid_retriever(query: str, metadata: dict, k: int = 2) -> list[Document]:
    """
    Make a query using Qdrant Hybrid Retriever

    Args:
        query (str)
        metadata (dict): Filter using metadata
        k (int): Get top k results

    Returns:
        list[Document]
    """
    fields = []
    for key, value in metadata.items():
        fields.append(
            models.FieldCondition(
                key=f"metadata.{key}", match=models.MatchValue(value=value)
            )
        )

    metadata_filter = models.Filter(must=fields)
    try:
        return await get_vector_store().asimilarity_search(
            query=query, k=k, filter=metadata_filter
        )
    except Exception:
        return []


if __name__ == "__main__":
    query = "Jenkins EC2 memory"
    results = hybrid_retriever(query, metadata={"data_source": "reddit_threads"})
    print(results)
