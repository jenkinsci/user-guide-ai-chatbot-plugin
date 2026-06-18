from ..models import DataSource
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..tools.common import read_json_file, write_json_file
from .chunking_utils import assign_code_blocks_to_chunks
from pathlib import Path
import os

CHUNK_ID_TEMPLATE = "{}_C_{}"

CODE_BLOCK_PLACEHOLDER_PATTERN = r"\[\[CODE_BLOCK_(\d+)\]\]"
PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"


def bind_chunks_to_code_blocks(
    chunks: list[Document], doc_id: str, code_blocks_dir: Path
) -> list[Document]:
    """
    Bind each chunk to its specific code blocks by placing its ID inside the corresponding code block metadata.

    Returns:
         tuple[list[Document], list[str]]: Chunk list
    """

    cbs = []
    cb_files = [
        file for file in code_blocks_dir.glob(f"CB_{doc_id}*.json") if file.is_file()
    ]

    for cb_file in cb_files:
        data = read_json_file(cb_file)
        cbs.append(
            Document(
                page_content=data["page_content"],
                metadata=data["metadata"],
                id=data["id"],
            )
        )

    results = assign_code_blocks_to_chunks(chunks, cbs, CODE_BLOCK_PLACEHOLDER_PATTERN)

    updated_chunks: list[Document] = []
    updated_cbs: list[Document] = []

    for r in results:
        chunk: Document = r["chunk"]
        code_blocks: list[Document] = r["code_blocks"]

        if len(code_blocks) > 0:
            chunk.metadata["cb_ids"] = [cb.id for cb in code_blocks]

        updated_chunks.append(chunk)

        for code_block in code_blocks:
            code_block.metadata["related_chunk_id"] = chunk.id
            updated_cbs.append(code_block)

    for up_cb in updated_cbs:
        write_json_file(code_blocks_dir / f"{up_cb.id}.json", up_cb.model_dump())

    return updated_chunks


def process_doc(
    doc: Document, text_splitter: RecursiveCharacterTextSplitter
) -> tuple[list[Document], list[str]]:
    """
    Process a specific Document and returns a chunk list the chunk id list

    Returns:
        tuple[list[Document], list[str]]: Chunk list and chunk id list
    """

    processed_chunks = []
    chunk_ids = []

    text_fragments = text_splitter.split_text(doc.page_content)
    total_chunks = len(text_fragments)

    for current_index, text_fragment in enumerate(text_fragments):
        # Build the exact metadata needed for the window logic
        chunk_metadata = {
            **doc.metadata,
            "chunk_index": current_index,
            "total_chunks": total_chunks,
        }

        chunk_id = CHUNK_ID_TEMPLATE.format(doc.id, current_index)

        # Create the LangChain Document
        chunk_doc = Document(
            page_content=text_fragment, metadata=chunk_metadata, id=chunk_id
        )

        chunk_ids.append(chunk_id)
        processed_chunks.append(chunk_doc)

    return processed_chunks, chunk_ids


def process_docs_with_sliding_window(
    documents: list[Document], source: str, code_blocks_dir: Path
) -> tuple[list[Document], list[str]]:
    """
    Process Documents using a sliding window approach.
    Means no chunk overlap and the hybrid retriever when retrieving a specific chunk will also
    fetch back the n previous chunks and n consequent chunks.

    Args:
        documents (list[Document])
        source (str): source name

    Returns:
        tuple[list[Document], list[str]]: Chunk list and chunk id list
    """
    processed_chunks: list[Document] = []
    chunk_ids = []

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)

    for doc in documents:
        # Splitting document in chunks
        chunks, c_ids = process_doc(doc, text_splitter)
        updated_chunks = chunks

        if source != "code_blocks":
            updated_chunks = bind_chunks_to_code_blocks(
                chunks, str(doc.id), code_blocks_dir
            )

        processed_chunks.extend(updated_chunks)
        chunk_ids.extend(c_ids)

    return processed_chunks, chunk_ids


def chunker(sources: list[DataSource], output_dir: Path):
    """Start embedder."""

    DOCUMENTS_DIR = output_dir / "documents"
    CODE_BLOCKS_DIR = DOCUMENTS_DIR / "code_blocks"
    CHUNKS_DIR = output_dir / "chunks"

    SOURCES = [*[s.value for s in sources], "code_blocks"]

    for source in SOURCES:
        SOURCE_DIR = DOCUMENTS_DIR / source
        documents: list[Document] = []

        for file_path in SOURCE_DIR.glob("*.json"):
            data = read_json_file(file_path)
            doc = Document(
                page_content=data["page_content"],
                metadata=data["metadata"],
                id=data["id"],
            )
            documents.append(doc)

        documents_length = len(documents)
        if documents_length > 0:
            print(f"Chunking {source}: {documents_length} documents")
        else:
            print(f"No document for {source}")
            continue

        chunks, chunk_ids = process_docs_with_sliding_window(
            documents, source, CODE_BLOCKS_DIR
        )

        for i in range(0, len(chunk_ids)):
            path = CHUNKS_DIR / f"{source}/{chunk_ids[i]}.json"
            write_json_file(path, chunks[i].model_dump())


def start_chunker(sources: list[DataSource], output_dir: Path):
    print("--------- START CHUNKING PHASE ---------")
    chunker(sources, output_dir)
    print("--------- END CHUNKING PHASE ---------")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    start_chunker(
        [
            DataSource.JENKINS_DOCS,
            DataSource.PLUGIN_DOCS,
            DataSource.DISCOURSE_TOPICS,
            DataSource.REDDIT_THREADS,
        ],
        OUTPUT_DIR,
    )
