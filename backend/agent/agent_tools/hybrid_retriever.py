from typing import Any
from vectordb.vector_store import get_vector_store
from langchain_core.documents import Document
from qdrant_client.http.models import models


def hybrid_retriever(query: str, metadata: dict = {}, k: int = 2) -> list[Document]:
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
        fields.append(models.FieldCondition(
                key=f"metadata.{key}",
                match=models.MatchValue(value=value)
        ))

    metadata_filter = models.Filter(must=fields)
    return get_vector_store().similarity_search(query=query, k=k, filter=metadata_filter)


if __name__ == "__main__":
    query = "Jenkins EC2 memory"
    results = hybrid_retriever(query, metadata={"data_source": "reddit_threads"})
    print(results)

