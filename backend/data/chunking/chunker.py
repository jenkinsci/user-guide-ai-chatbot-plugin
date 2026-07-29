from ..models import DataSource
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..tools.common import read_json_file, write_json_file
from .chunking_utils import assign_code_blocks_to_chunks
from pathlib import Path
import os
from uuid import uuid5, NAMESPACE_DNS
import re
from typing import List
from .contextual_retrieval import contextualize_chunk
from manage_env import get_env
from dotenv import load_dotenv
import asyncio
from llm_client import get_llm_client

load_dotenv()


CHUNK_ID_TEMPLATE = "{}_C_{}"

CODE_BLOCK_PLACEHOLDER_PATTERN = r"\[\[CODE_BLOCK_(\d+)\]\]"
PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"

ENABLE_CONTEXTUAL_RETRIEVAL = get_env("ENABLE_CONTEXTUAL_RETRIEVAL").lower() == "true"
CONTEXTUAL_LLM_PROVIDER = get_env("CONTEXTUAL_LLM_PROVIDER")
CONTEXTUAL_LLM_MODEL_NAME = get_env("CONTEXTUAL_LLM_MODEL_NAME")
CONTEXTUAL_LLM_BASE_URL = get_env("CONTEXTUAL_LLM_BASE_URL")
CONTEXTUAL_LLM_API_KEY = get_env("CONTEXTUAL_LLM_API_KEY")
CONTEXTUAL_LLM_TEMPERATURE = get_env("CONTEXTUAL_LLM_TEMPERATURE")


async def contextualize_chunk_list(
    chunk_list: List[Document], output_dir: Path, data_source: str
) -> List[Document]:
    """
    Generates specific context for each chunk in chunk_list.
    """
    documents_dir = output_dir / "documents"
    SOURCE_DIR = documents_dir / data_source
    chunks_len = len(chunk_list)
    llm_client = get_llm_client(
        provider=CONTEXTUAL_LLM_PROVIDER,
        temperature=float(CONTEXTUAL_LLM_TEMPERATURE),
        api_key=CONTEXTUAL_LLM_API_KEY,
        base_url=CONTEXTUAL_LLM_BASE_URL,
        model_name=CONTEXTUAL_LLM_MODEL_NAME,
    )

    for i, c in enumerate(chunk_list):
        entire_document = read_json_file(SOURCE_DIR / f"{c.metadata["parent_id"]}.json")

        new_chunk_content = await contextualize_chunk(
            entire_document["page_content"],
            c.page_content,
            llm_client,
            CONTEXTUAL_LLM_PROVIDER,
        )

        if new_chunk_content:
            c.page_content = new_chunk_content
        print(i, chunks_len)

    return chunk_list


def bind_chunks_to_code_blocks(
    chunks: list[Document], doc_id: str, code_blocks_dir: Path
) -> list[Document]:
    """
    Bind each chunk to its specific code blocks document by placing its ID inside the corresponding code block metadata.

    Returns:
        list[Document]: Chunk list
    """
    cbs_dict: dict[int, Document] = {}
    cb_files = [
        file for file in code_blocks_dir.glob(f"CB_{doc_id}*.json") if file.is_file()
    ]

    for cb_file in cb_files:
        data = read_json_file(cb_file)

        match = re.search(r"_(\d+)\.json$", cb_file.name)
        if match:
            cb_index = int(match.group(1))
            cbs_dict[cb_index] = Document(
                page_content=data["page_content"],
                metadata=data["metadata"],
                id=data["id"],
            )
        else:
            print(f"Could not extract index from filename: {cb_file.name}")

    results = assign_code_blocks_to_chunks(
        chunks, cbs_dict, CODE_BLOCK_PLACEHOLDER_PATTERN
    )

    updated_chunks: list[Document] = []
    updated_cbs: list[Document] = []

    for r in results:
        chunk: Document = r["chunk"]
        code_blocks: list[Document] = r["code_blocks"]

        if len(code_blocks) > 0:
            chunk.metadata["cb_ids"] = [cb.id for cb in code_blocks]

        updated_chunks.append(chunk)

        for code_block in code_blocks:
            code_block.metadata["related_id"] = chunk.id
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
            "parent_id": doc.id,
        }

        chunk_id = CHUNK_ID_TEMPLATE.format(doc.id, current_index)

        # Convert id to UUID (Deterministic). Necessary for Qdrant
        uuid_to_str = str(uuid5(NAMESPACE_DNS, chunk_id))

        # Create the LangChain Document
        chunk_doc = Document(
            page_content=text_fragment, metadata=chunk_metadata, id=uuid_to_str
        )

        chunk_ids.append(chunk_id)
        processed_chunks.append(chunk_doc)

    return processed_chunks, chunk_ids


def process_doc_list(
    documents: list[Document], source: str, code_blocks_dir: Path
) -> tuple[list[Document], list[str]]:
    """
    Process 'jenkins_docs' and 'plugin_docs' using a Hybrid window retrieval (Sliding window - Sentence window).
    Means having a chunk overlap and the hybrid retriever when retrieving a specific chunk will also
    fetch back the n previous chunks and n consequent chunks. A specific function will be used to
    do an Overlap Deduplication so that the text that the LLM will receive won't have any duplications.

    Process 'discourse_topics' and 'reddit_threads' using a Parent-child retrieval.
    Means having no chunk overlap and the hybrid retriever when retrieving a specific chunk will also
    fetch back all the chunks inside the first retrieved chunk parent.

    Args:
        documents (list[Document])
        source (str): source name

    Returns:
        tuple[list[Document], list[str]]: Chunk list and chunk id list
    """
    processed_chunks: list[Document] = []
    chunk_ids = []

    chunk_overlap = (
        100
        if source == DataSource.JENKINS_DOCS.value
        or source == DataSource.PLUGIN_DOCS.value
        else 0
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=chunk_overlap
    )

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


async def chunker(sources: list[DataSource], output_dir: Path, test: bool):
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

        chunks, chunk_ids = process_doc_list(documents, source, CODE_BLOCKS_DIR)
        updated_chunks = chunks

        if ENABLE_CONTEXTUAL_RETRIEVAL and not test:
            updated_chunks = await contextualize_chunk_list(chunks, output_dir, source)

        for i in range(0, len(chunk_ids)):
            path = CHUNKS_DIR / f"{source}/{chunk_ids[i]}.json"
            write_json_file(path, updated_chunks[i].model_dump())


async def start_chunker(
    sources: list[DataSource], output_dir: Path, test: bool = False
):
    print("--------- START CHUNKING PHASE ---------")
    await chunker(sources, output_dir, test)
    print("--------- END CHUNKING PHASE ---------")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    asyncio.run(
        start_chunker(
            [
                DataSource.JENKINS_DOCS,
                DataSource.PLUGIN_DOCS,
                DataSource.DISCOURSE_TOPICS,
                DataSource.REDDIT_THREADS,
            ],
            OUTPUT_DIR,
        )
    )
