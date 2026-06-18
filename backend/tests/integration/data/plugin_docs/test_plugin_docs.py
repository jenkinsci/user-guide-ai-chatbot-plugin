from data.preprocessing.processors import start_processors
from data.formatting.formatters import start_formatters
from data.chunking.chunker import start_chunker
from data.embedding.embedder import embedder
from data.models import DataSource
from pathlib import Path
from langchain_chroma import Chroma
from tests.mock_data.mock_collector_output_data import (
    COLLECTOR_OUTPUT_PLUGIN_DOCS,
)
from tests.integration.data.utils import ephemeral_vector_db
from data.tools.common import write_json_file


def test_plugin_docs(tmp_path: Path, ephemeral_vector_db: Chroma):
    SOURCE = DataSource.PLUGIN_DOCS

    # Setup (MOCKED Collection Phase)
    output_dir = tmp_path / "output"
    raw_dir = output_dir / "raw"
    output_dir.mkdir()
    raw_dir.mkdir()
    write_json_file(raw_dir / f"{SOURCE.value}.json", COLLECTOR_OUTPUT_PLUGIN_DOCS)

    # Preprocessing
    start_processors([SOURCE], output_dir)
    assert (
        output_dir / "processed" / f"{SOURCE.value}.json"
    ).exists(), "Preprocessing failed"

    # Formatting
    start_formatters([SOURCE], output_dir)
    assert (output_dir / "documents" / f"{SOURCE.value}").exists(), "Formatting failed"
    assert (output_dir / "documents" / "code_blocks").exists(), "No codeblocks found"

    # Chunking Phase
    start_chunker([SOURCE], output_dir)
    source_dir = output_dir / "chunks" / SOURCE.value
    assert source_dir.exists(), "Chunking failed"
    chunk_files = list(source_dir.iterdir())
    assert len(chunk_files) > 0, "No chunks produced"

    # Embedding Phase
    embedder([SOURCE], output_dir, ephemeral_vector_db)
    results = ephemeral_vector_db.similarity_search("jenkins", k=1)
    assert len(results) > 0
