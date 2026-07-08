from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from manage_env import get_env
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams, Filter
from .manage_jwt import generate_admin_token
from functools import lru_cache

load_dotenv()


@lru_cache(maxsize=1)
def get_vector_store():
    """
    Returns a QdrantVectorStore instance, which is cached after the first function execution.
    Uses a Hybrid retriever with a Dense and Sparse Embedding.
    """
    QDRANT_HOST = get_env("QDRANT_HOST")
    QDRANT_PORT = int(get_env("QDRANT_PORT"))
    QDRANT_URL = f"{QDRANT_HOST}:{QDRANT_PORT}"
    QDRANT_SSL = get_env("QDRANT_SSL").lower() == "true"
    QDRANT_COLLECTION_NAME = get_env("QDRANT_COLLECTION_NAME")
    QDRANT_SECRET_KEY = get_env("QDRANT_SECRET_KEY")

    HUGGING_FACE_EMBEDDING_NAME = get_env("HUGGING_FACE_EMBEDDING_NAME")
    EMBEDDING_SIZE = int(get_env("EMBEDDING_SIZE"))
    FAST_EMBED_SPARSE_MODEL_NAME = get_env("FAST_EMBED_SPARSE_MODEL_NAME")

    admin_token = None
    if QDRANT_SECRET_KEY:
        admin_token = generate_admin_token(QDRANT_SECRET_KEY)

    qdrant_client = QdrantClient(url=QDRANT_URL, https=QDRANT_SSL, api_key=admin_token)

    dense_embeddings = HuggingFaceEmbeddings(model_name=HUGGING_FACE_EMBEDDING_NAME)
    sparse_embeddings = FastEmbedSparse(model_name=FAST_EMBED_SPARSE_MODEL_NAME)

    if not qdrant_client.collection_exists(QDRANT_COLLECTION_NAME):
        qdrant_client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE)
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            },
        )

    vectorstore = QdrantVectorStore(
        client=qdrant_client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name="dense",
        sparse_vector_name="sparse",
    )

    return vectorstore


if __name__ == "__main__":
    load_dotenv()
    qdrant_vectorstore = get_vector_store()
    result = qdrant_vectorstore.similarity_search("jenkins", k=3)
    print(result)
