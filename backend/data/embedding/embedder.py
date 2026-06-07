import os
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from ..tools.common import read_json_file, write_json_file
from embedding_utils import assign_code_blocks_to_chunks

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(SCRIPT_DIR, "..", "output", "documents")
CHUNKS_DIR = os.path.join(SCRIPT_DIR, "..", "output", "chunks")
CHROMA_DIR = os.path.join(SCRIPT_DIR, "..", "output", "production", "chromadb")
FOLDERS = ["jenkins_docs", "plugin_docs", "discourse_topics", "reddit_threads", "code_blocks"]
CB_PATH = Path(DOCUMENTS_DIR, "code_blocks")


CHUNK_ID_TEMPLATE ="{}_C_{}"

CODE_BLOCK_PLACEHOLDER_PATTERN = r"\[\[CODE_BLOCK_(\d+)\]\]"
PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"


def bind_chunks_to_code_blocks(chunks: list[Document], doc_id: str) -> list[Document]:
    """
       Bind each chunk to its specific code blocks by placing its ID inside the corresponding code block metadata.

       Returns: 
            tuple[list[Document], list[str]]: Chunk list
    """

    cbs = []
    cb_files = [file for file in CB_PATH.glob(f'CB_{doc_id}*.json') if file.is_file()]

    for cb_file in cb_files: 
        data = read_json_file(cb_file)
        cbs.append(Document(page_content=data["page_content"], metadata=data["metadata"], id=data["id"]))

    results = assign_code_blocks_to_chunks(chunks, cbs, CODE_BLOCK_PLACEHOLDER_PATTERN) 

    updated_chunks: list[Document] = []
    updated_cbs: list[Document] = []
    
    for r in results:
        chunk: Document = r["chunk"]
        code_blocks: list[Document] = r["code_blocks"]

        chunk.metadata["n_cbs"] = len(code_blocks)

        updated_chunks.append(chunk)

        for code_block in code_blocks:
            code_block.metadata["related_chunk_id"] = chunk.id
            updated_cbs.append(code_block)

    for up_cb in updated_cbs:
        write_json_file(str(CB_PATH / f"{up_cb.id}.json"), up_cb.model_dump())

    return updated_chunks


def process_doc(doc: Document, text_splitter: RecursiveCharacterTextSplitter) -> tuple[list[Document], list[str]]:
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
            page_content=text_fragment,
            metadata=chunk_metadata,
            id=chunk_id
        )

        chunk_ids.append(chunk_id)
        processed_chunks.append(chunk_doc)

    return processed_chunks, chunk_ids


def process_docs_with_sliding_window(documents: list[Document], source: str) -> tuple[list[Document], list[str]]:
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

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0 
    )

    for doc in documents:
        # Splitting document in chunks
        chunks, c_ids = process_doc(doc, text_splitter)
        updated_chunks = chunks

        if source != "code_blocks":
           updated_chunks = bind_chunks_to_code_blocks(chunks, str(doc.id))

        processed_chunks.extend(updated_chunks)
        chunk_ids.extend(c_ids)

        
    return processed_chunks, chunk_ids


def start_embedder():
    """ Start embedder. """
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") # 384 dim 

    vector_store = Chroma(
        collection_name="persistent_docs",
        embedding_function=embedding_model, 
        persist_directory=CHROMA_DIR
        #host="" only if there's a chromadb instance running
    )

    for source in FOLDERS:
        SOURCE_DIR = Path(DOCUMENTS_DIR, source)
        documents: list[Document] = []

        for file_path in SOURCE_DIR.glob('*.json'):
            data = read_json_file(file_path)
            doc = Document(page_content=data["page_content"], metadata=data["metadata"], id=data["id"])
            documents.append(doc)
        
        if not documents: continue

        chunks, chunk_ids = process_docs_with_sliding_window(documents, source)

        for i in range(0, len(chunks)):
            write_json_file(CHUNKS_DIR + f"/{source}/{chunk_ids[i]}.json", chunks[i].model_dump())

        print("SOURCE: ", source)
        print("LENGTH: ", len(chunk_ids))
        batch_size = 5000 
        for i in range(0, len(chunks), batch_size):
            print(f"vectorized and stored {i} chunks from {source}")
            batch = chunks[i : i + batch_size]
            batch_ids = chunk_ids[i : i + batch_size]

            # Delete the previous chunks with the same id
            vector_store.delete(ids=batch_ids)

            # Add the new ones
            ids = vector_store.add_documents(batch, ids=batch_ids)
            

if __name__ == "__main__":
    start_embedder()
 
