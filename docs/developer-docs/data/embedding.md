# Embedding

## Overview
This module handles the embedding phase of the data pipeline. It reads previously generated JSON chunk files from the filesystem, reconstructs them into LangChain `Document` objects, and uploads them in batches to a Qdrant vector store for semantic search.

**To run embedding phase:**
```bash
python -m data.embedding.embedder
```

## Functions

### `embedder`
Reads chunk files for specified data sources, reconstructs them into document objects, and inserts them into the vector database in batches.

**Logic and Data Flow:**
1.  **Directory Mapping**: Maps each source to its respective subdirectory inside `{output_dir}/chunks/`.
2.  **Document Reconstruction**: Iterates through all `.json` files in the source directory, reads the content, and reconstructs LangChain `Document` objects using the `page_content`, `metadata`, and `id`.
3.  **Batch Insertion**: To optimize memory and network usage, documents are pushed to the Qdrant vector store in batches of 5,000 using `vector_store.add_documents()`.
