from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()


def get_vector_store():
    embedding_name = os.getenv("HUGGING_FACE_EMBEDDING_NAME")

    embedding_model = HuggingFaceEmbeddings(model_name=embedding_name)

    chroma_client = chromadb.HttpClient(
        host="localhost",
        port=8000,
        settings=Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials="your-auth-token",
        ),
    )

    vector_store_server = Chroma(
        client=chroma_client,
        collection_name="production_docs",
        embedding_function=embedding_model,
    )

    return vector_store_server
