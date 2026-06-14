import pytest
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

COLLECTION_NAME = "test_collection"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384

@pytest.fixture(scope="module")
def ephemeral_vector_db():
    client = QdrantClient(":memory:")
    test_embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    temporary_db = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=test_embedding_model,
    )

    yield temporary_db

    client.delete_collection(COLLECTION_NAME)