import os
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path
from ..tools.common import read_json_file, write_json_file
from ..models import DataSource


def embedder(sources: list[DataSource], output_dir: Path):
    """Start embedder."""
    CHUNKS_DIR = output_dir / "chunks"
    CHROMA_DIR = output_dir / "production" / "chromadb"

    SOURCES = [*[s.value for s in sources], "code_blocks"]
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  # 384 dim

    vector_store = Chroma(
        collection_name="persistent",
        embedding_function=embedding_model,
        persist_directory=str(CHROMA_DIR),
        # host="" only if there's a chromadb instance running
    )

    for source in SOURCES:
        SOURCE_CHUNKS_DIR = CHUNKS_DIR / source
        chunks: list[Document] = []
        chunk_ids: list[str] = []

        for file_path in SOURCE_CHUNKS_DIR.glob("*.json"):
            data = read_json_file(file_path)
            chunk = Document(
                page_content=data["page_content"],
                metadata=data["metadata"],
                id=data["id"],
            )
            chunks.append(chunk)
            chunk_ids.append(chunk.id)  # type: ignore

        chunks_length = len(chunk_ids)
        print(f"Embedding {source}: {chunks_length} chunks")

        batch_size = 5000
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            batch_ids = chunk_ids[i : i + batch_size]

            # Delete the previous chunks with the same id
            vector_store.delete(ids=batch_ids)

            # Add the new ones
            ids = vector_store.add_documents(batch, ids=batch_ids)
            print(f"Stored {i + batch_size} chunks from {source}")

    print("CHUNKS EMBEDDED AND STORED: ", vector_store._collection.count())


def start_embedder(sources: list[DataSource], output_dir: Path):
    print("--------- START EMBEDDING PHASE ---------")
    embedder(sources, output_dir)
    print("--------- END EMBEDDING PHASE ---------")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    start_embedder(
        [
            DataSource.JENKINS_DOCS,
            DataSource.PLUGIN_DOCS,
            DataSource.DISCOURSE_TOPICS,
            DataSource.REDDIT_THREADS,
        ],
        OUTPUT_DIR,
    )
