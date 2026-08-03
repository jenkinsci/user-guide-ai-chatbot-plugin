from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from manage_env import get_env
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams
from qdrant_client.conversions.common_types import PointId, Record
from .manage_jwt import generate_admin_token
from cachetools.func import ttl_cache
from langchain_core.documents import Document

load_dotenv()

QDRANT_COLLECTION_NAME = get_env("QDRANT_COLLECTION_NAME")
TTL_QDRANT_CACHE = 3600


@ttl_cache(maxsize=1, ttl=TTL_QDRANT_CACHE - 1)
def get_qdrant_client():
    """
    Returns a Qdrant client. Result is cached for 3540 seconds.
    """

    QDRANT_HOST = get_env("QDRANT_HOST")
    QDRANT_PORT = int(get_env("QDRANT_PORT"))
    QDRANT_URL = f"{QDRANT_HOST}:{QDRANT_PORT}"
    QDRANT_SSL = get_env("QDRANT_SSL").lower() == "true"
    QDRANT_SECRET_KEY = get_env("QDRANT_SECRET_KEY")

    admin_token = None
    if QDRANT_SECRET_KEY:
        admin_token = generate_admin_token(
            QDRANT_SECRET_KEY
        )  # Admin token expire after 3600s, so function result is cached for a bit less
    return QdrantClient(url=QDRANT_URL, https=QDRANT_SSL, api_key=admin_token)


def get_with_metadata(
    payload_filter: models.Filter, limit: int = 10, offset: PointId = 0
) -> tuple[list[Record], PointId | None]:
    """
    Fetch from vector db using metadata, bypassing vector search entirely.
    """

    retrieved_points, next_page_offset = get_qdrant_client().scroll(
        collection_name=QDRANT_COLLECTION_NAME,
        scroll_filter=payload_filter,
        limit=limit,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )

    return retrieved_points, next_page_offset


@ttl_cache(maxsize=1, ttl=3540)
def get_vector_store():
    """
    Returns a QdrantVectorStore instance, which is cached after the first function execution.
    Uses a Hybrid retriever with a Dense and Sparse Embedding. Result is cached for 3540 seconds.
    """

    HUGGING_FACE_EMBEDDING_NAME = get_env("HUGGING_FACE_EMBEDDING_NAME")
    EMBEDDING_SIZE = int(get_env("EMBEDDING_SIZE"))
    FAST_EMBED_SPARSE_MODEL_NAME = get_env("FAST_EMBED_SPARSE_MODEL_NAME")

    qdrant_client = get_qdrant_client()

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

    payload_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.parent_id",
                match=models.MatchValue(value="J_DOC-UPGRADE-GUIDE-2.504"),
            ),
        ]
    )

    retrieved_points, next_page_offset = get_with_metadata(
        payload_filter=payload_filter, limit=10
    )
