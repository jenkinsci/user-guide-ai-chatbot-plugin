import pytest
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb


@pytest.fixture(scope="module")
def ephemeral_vector_db():
    # Setup: Create an in-memory Chroma database strictly for testing
    in_memory_client = chromadb.EphemeralClient()
    test_embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    temporary_db = Chroma(
        client=in_memory_client,
        collection_name="test_jenkins_pipeline",
        embedding_function=test_embedding_model,
    )

    yield temporary_db

    # Teardown: Clean up the DB
    temporary_db.delete_collection()
